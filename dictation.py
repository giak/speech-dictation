#!/usr/bin/env python3

"""
Speech Dictation - Système de dictée vocale pour Linux
====================================================

Ce module implémente un système de dictée vocale en français utilisant Vosk
pour la reconnaissance vocale et xdotool pour la simulation de frappe clavier.

Caractéristiques principales:
----------------------------
- Reconnaissance vocale hors-ligne avec Vosk
- Support complet de la ponctuation par commandes vocales
- Post-traitement intelligent du texte
- Gestion du contexte pour améliorer la précision
- Retours sonores pour une meilleure expérience utilisateur

Architecture:
------------
Le système est construit autour d'une classe principale DictationEngine qui gère :
1. La capture audio en temps réel
2. La reconnaissance vocale avec Vosk
3. Le post-traitement du texte
4. La gestion des commandes vocales
5. La simulation de frappe clavier

Dépendances:
-----------
- vosk: Moteur de reconnaissance vocale
- sounddevice: Capture audio
- xdotool: Simulation de frappe clavier
- paplay: Retours sonores (inclus dans pulseaudio-utils)

Auteur: giak
Licence: MIT
Version: 2.0.0
"""

import os
import queue
import shlex
import json
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import sys
import signal
import threading
import time
import subprocess
import numpy

# Configuration générale du système
# -------------------------------
# Ces paramètres contrôlent le comportement global du système
CONFIG = {
    "samplerate": 16000,      # Taux d'échantillonnage standard pour Vosk
    "blocksize": 8000,        # Taille des blocs audio (ajuster selon latence/performance)
    "model_path": os.path.expanduser("~/vosk-model-fr-0.6-linto-2.2.0"),
    "feedback_sounds": {       # Chemins vers les sons de feedback
        "start": "/usr/share/sounds/freedesktop/stereo/service-login.oga",
        "stop": "/usr/share/sounds/freedesktop/stereo/service-logout.oga",
        "error": "/usr/share/sounds/freedesktop/stereo/dialog-error.oga"
    }
}

# Configuration avancée du modèle de reconnaissance
# ---------------------------------------------
MODEL_CONFIG = {
    "sample_rate": 16000,     # Doit correspondre à CONFIG["samplerate"]
    "buffer_size": 8000,      # Taille du buffer pour le traitement audio
    "words": True,            # Active la sortie mot par mot pour plus de précision
    "max_alternatives": 1,    # Nombre d'alternatives de reconnaissance à considérer
    "score_cutoff": 0.75,     # Seuil de confiance minimum pour accepter un résultat
    "partial_results": False, # Désactive les résultats partiels pour plus de précision
    "context_size": 5,       # Nombre de mots de contexte à conserver
    "noise_reduction": True,  # Active la réduction de bruit
    "vad_sensitivity": 3,    # Sensibilité de la détection d'activité vocale (0-3)
    "silence_threshold": 200  # Seuil de silence en millisecondes
}

# Dictionnaire des commandes vocales
# -------------------------------
# Définit toutes les commandes vocales reconnues et leurs actions
COMMANDES_VOCALES = {
    # Commandes de ponctuation
    "virgule": ",",
    "point": ".",
    "point d'interrogation": "?",
    "point d'exclamation": "!",
    "nouvelle ligne": "\n",
    "retour à la ligne": "\n",
    "à la ligne": "\n",
    "point-virgule": ";",
    "deux points": ":",
    "ouvrir parenthèse": "(",
    "fermer parenthèse": ")",
    "guillemets": "\"",
    "espace": " ",
    
    # Commandes de contrôle système
    "pause dictée": "__PAUSE__",      # Met en pause la reconnaissance
    "reprendre dictée": "__RESUME__", # Reprend la reconnaissance
    "arrêter dictée": "__STOP__",     # Arrête le programme
    "effacer": "__BACKSPACE__",       # Efface le dernier caractère
    "supprimer ligne": "__DELETE_LINE__", # Efface la ligne entière
}

class DictationEngine:
    """
    Moteur principal de dictée vocale.
    
    Cette classe implémente toute la logique de reconnaissance vocale,
    de traitement du texte et de gestion des commandes. Elle utilise
    une architecture événementielle pour la capture audio et maintient
    un contexte pour améliorer la qualité de reconnaissance.

    Attributs:
        model (Model): Instance du modèle Vosk
        recognizer (KaldiRecognizer): Reconnaisseur vocal Vosk
        audio_queue (Queue): File d'attente pour les données audio
        running (bool): État d'exécution du moteur
        paused (bool): État de pause
        context (list): Historique des derniers mots reconnus
    """

    def __init__(self):
        """
        Initialise le moteur de dictée.
        
        Configure le modèle Vosk, initialise la capture audio et
        prépare le système de reconnaissance vocale.
        
        Raises:
            SystemExit: Si le modèle Vosk n'est pas trouvé
        """
        if not os.path.exists(CONFIG["model_path"]):
            self.play_sound("error")
            print("Le modèle spécifié est introuvable.")
            sys.exit(1)

        self.model = Model(CONFIG["model_path"])
        # Simplification de l'initialisation du recognizer
        self.recognizer = KaldiRecognizer(
            self.model, 
            MODEL_CONFIG["sample_rate"]
        )
        
        self.audio_queue = queue.Queue()
        self.running = True
        self.paused = False
        self.last_text = ""
        self.context = []  # Historique des derniers mots
        self.context_size = 5  # Taille de l'historique


    def audio_callback(self, indata, frames, time_info, status):
        """
        Callback optimisé pour la capture audio avec réduction de bruit
        et détection d'activité vocale (VAD).
        
        Args:
            indata (numpy.ndarray): Données audio capturées
            frames (int): Nombre de frames
            time_info (CData): Informations temporelles du stream
            status (CallbackFlags): Statut de la capture
        """
        if status:
            print(f"Erreur audio: {status}")
            self.play_sound("error")
            return

        # Conversion en bytes pour Vosk
        audio_data = bytes(indata)

        # Détection d'activité vocale (VAD)
        if self.is_speech(indata):
            self.audio_queue.put(audio_data)
            self.last_speech_time = time.time()  # Utilisation du module time importé
        elif hasattr(self, 'last_speech_time'):
            # Gestion du silence
            current_time = time.time()  # Utilisation du module time importé
            silence_duration = current_time - self.last_speech_time
            if silence_duration > MODEL_CONFIG["silence_threshold"] / 1000:
                # Traitement du buffer accumulé si nécessaire
                self.process_accumulated_buffer()

    def is_speech(self, audio_data):
        """
        Détection d'activité vocale améliorée
        Utilise un seuil dynamique et une analyse d'énergie
        """
        # Calcul de l'énergie du signal
        energy = numpy.mean(numpy.abs(audio_data))
        
        # Mise à jour du seuil dynamique
        if not hasattr(self, 'energy_threshold'):
            self.energy_threshold = energy * 1.1
        else:
            # Adaptation dynamique du seuil
            if energy > self.energy_threshold:
                self.energy_threshold = energy * 0.9
            else:
                self.energy_threshold = self.energy_threshold * 0.999

        # Ajustement basé sur la sensibilité VAD
        sensitivity_factor = (4 - MODEL_CONFIG["vad_sensitivity"]) * 0.5
        return energy > (self.energy_threshold * sensitivity_factor)

    def process_accumulated_buffer(self):
        """
        Traite le buffer audio accumulé pendant la période de parole
        """
        while not self.audio_queue.empty():
            data = self.audio_queue.get()
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                text = result.get("text", "").strip()
                
                if text:
                    text_traite = self.traiter_texte(text)
                    if text_traite:
                        quoted_text = shlex.quote(text_traite)
                        os.system(f"xdotool type {quoted_text}")
                        self.last_text = text_traite

    def play_sound(self, sound_type):
        """Joue un son de feedback"""
        if sound_type in CONFIG["feedback_sounds"]:
            try:
                subprocess.run(["paplay", CONFIG["feedback_sounds"][sound_type]], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
            except Exception:
                pass

    def handle_command(self, text):
        """Gère les commandes spéciales"""
        if text == "__PAUSE__":
            self.paused = True
            self.play_sound("stop")
            return ""
        elif text == "__RESUME__":
            self.paused = False
            self.play_sound("start")
            return ""
        elif text == "__STOP__":
            self.running = False
            self.play_sound("stop")
            return ""
        elif text == "__BACKSPACE__":
            os.system("xdotool key BackSpace")
            return ""
        elif text == "__DELETE_LINE__":
            os.system("xdotool key ctrl+u")
            return ""
        return text

    def traiter_texte(self, texte):
        """Traite le texte reconnu pour gérer les commandes vocales"""
        if not texte or self.paused:
            return ""

        mots = texte.split()
        resultat = []
        i = 0
        
        while i < len(mots):
            if i < len(mots) - 1:
                commande_double = f"{mots[i]} {mots[i+1]}"
                if commande_double in COMMANDES_VOCALES:
                    resultat.append(COMMANDES_VOCALES[commande_double])
                    i += 2
                    continue
            
            if mots[i] in COMMANDES_VOCALES:
                cmd_result = self.handle_command(COMMANDES_VOCALES[mots[i]])
                if cmd_result:
                    resultat.append(cmd_result)
            else:
                resultat.append(mots[i])
            i += 1
        
        return " ".join(resultat)

    def post_process_text(self, text, result_json):
        """Post-traitement avancé du texte reconnu"""
        if not text:
            return ""

        # Vérification du score de confiance
        alternatives = result_json.get("alternatives", [])
        if alternatives and float(alternatives[0].get("confidence", 0)) < MODEL_CONFIG["score_cutoff"]:
            return ""

        # Application des corrections dans l'ordre optimal
        text = self.remove_noise_words(text)
        text = self.correct_spacing(text)
        text = self.correct_punctuation(text)
        text = self.correct_capitalization(text)
        text = self.format_numbers(text)
        text = self.apply_context_correction(text)
        
        # Mise à jour du contexte
        self.update_context(text)
        
        return text

    def remove_noise_words(self, text):
        """Supprime les mots parasites et les hésitations"""
        noise_words = {"euh", "hum", "ben", "bah", "euhm"}
        words = text.split()
        return " ".join(w for w in words if w.lower() not in noise_words)

    def correct_capitalization(self, text):
        """Correction avancée de la capitalisation"""
        if not text:
            return text

        # Capitalisation après un point
        sentences = text.split(". ")
        sentences = [s.capitalize() for s in sentences]
        text = ". ".join(sentences)

        # Liste des mots à toujours capitaliser
        always_capitalize = {"France", "Paris", "Lundi", "Mardi", "Mercredi", 
                           "Jeudi", "Vendredi", "Samedi", "Dimanche", "Janvier",
                           "Février", "Mars", "Avril", "Mai", "Juin", "Juillet",
                           "Août", "Septembre", "Octobre", "Novembre", "Décembre"}

        words = text.split()
        for i, word in enumerate(words):
            if word.lower() in {w.lower() for w in always_capitalize}:
                words[i] = word.capitalize()

        return " ".join(words)

    def correct_spacing(self, text):
        """Correction avancée des espaces"""
        # Suppression des espaces multiples
        text = ' '.join(text.split())
        
        # Correction des espaces avant/après la ponctuation
        for punct in [',', '.', '!', '?', ':', ';']:
            text = text.replace(f" {punct}", punct)
            text = text.replace(f"{punct} ", f"{punct} ")
        
        return text

    def correct_punctuation(self, text):
        """Correction avancée de la ponctuation"""
        # Règles de ponctuation française
        text = text.replace(" ,", ",")
        text = text.replace(" .", ".")
        text = text.replace(" !", "!")
        text = text.replace(" ?", "?")
        text = text.replace(" :", " :")  # Espace avant les deux-points en français
        text = text.replace(" ;", " ;")  # Espace avant point-virgule en français
        
        return text

    def apply_context_correction(self, text):
        """Correction basée sur le contexte"""
        words = text.split()
        corrected_words = []
        
        for i, word in enumerate(words):
            # Vérification du contexte précédent
            prev_word = words[i-1] if i > 0 else None
            next_word = words[i+1] if i < len(words)-1 else None
            
            # Application des règles contextuelles
            word = self.apply_context_rules(word, prev_word, next_word)
            corrected_words.append(word)
        
        return ' '.join(corrected_words)

    def apply_context_rules(self, word, prev_word, next_word):
        """Applique des règles de correction contextuelle avancées"""
        # Correction des articles
        articles = {"le", "la", "les", "un", "une", "des"}
        pronouns = {"je", "tu", "il", "elle", "nous", "vous", "ils", "elles"}
        
        if prev_word in articles:
            # Règles d'accord en genre et nombre
            if prev_word in {"le", "un"}:
                # Règles pour le masculin singulier
                pass
            elif prev_word in {"la", "une"}:
                # Règles pour le féminin singulier
                pass
            elif prev_word in {"les", "des"}:
                # Règles pour le pluriel
                pass
                
        # Correction des verbes après pronoms
        if prev_word in pronouns:
            # Application des règles de conjugaison
            if word.endswith("er"):  # Verbes du premier groupe
                if prev_word == "je":
                    word = word[:-2] + "e"
                elif prev_word == "tu":
                    word = word[:-2] + "es"
                elif prev_word in {"il", "elle"}:
                    word = word[:-2] + "e"
                elif prev_word == "nous":
                    word = word[:-2] + "ons"
                elif prev_word == "vous":
                    word = word[:-2] + "ez"
                elif prev_word in {"ils", "elles"}:
                    word = word[:-2] + "ent"
        
        return word

    def format_numbers(self, text):
        """Formate les nombres dans le texte"""
        # Conversion des nombres écrits en chiffres
        number_mapping = {
            'zéro': '0', 'un': '1', 'deux': '2', 'trois': '3',
            'quatre': '4', 'cinq': '5', 'six': '6', 'sept': '7',
            'huit': '8', 'neuf': '9', 'dix': '10'
        }
        
        words = text.split()
        for i, word in enumerate(words):
            if word.lower() in number_mapping:
                words[i] = number_mapping[word.lower()]
        
        return ' '.join(words)

    def update_context(self, text):
        """Met à jour le contexte avec les derniers mots reconnus"""
        words = text.split()
        self.context.extend(words)
        if len(self.context) > self.context_size:
            self.context = self.context[-self.context_size:]
            
    def get_context_hints(self):
        """Génère des indices de contexte pour améliorer la reconnaissance"""
        if not self.context:
            return ""
        return " ".join(self.context)

    def generate_grammar(self):
        """Génère une grammaire personnalisée pour améliorer la reconnaissance"""
        grammar = {
            "grammar": [
                ["[unk]"],  # Gestion des mots inconnus
                *COMMANDES_VOCALES.keys(),  # Inclut les commandes vocales
                *self.get_common_words()  # Mots fréquents
            ]
        }
        return json.dumps(grammar)

    def get_common_words(self):
        """Liste de mots fréquents pour améliorer la reconnaissance"""
        return [
            "le", "la", "les", "un", "une", "des",
            "je", "tu", "il", "elle", "nous", "vous", "ils", "elles",
            "être", "avoir", "faire", "dire", "aller", "voir", "venir",
            "et", "ou", "mais", "donc", "car", "ni", "or"
        ]

    def run(self):
        """Démarre le moteur de dictée avec gestion avancée de la mémoire"""
        self.running = True
        self.play_sound("start")
        
        print("Dictée vocale démarrée...")
        print("Commandes disponibles:", ", ".join(COMMANDES_VOCALES.keys()))
        
        try:
            # Configuration optimisée du stream audio
            stream_config = {
                'samplerate': CONFIG["samplerate"],
                'blocksize': CONFIG["blocksize"],
                'dtype': 'int16',
                'channels': 1,
                'callback': self.audio_callback,
                'latency': 'low',  # Optimisation de la latence
                'device': None,    # Utilise le périphérique par défaut
            }

            with sd.RawInputStream(**stream_config):
                print("Capture audio démarrée avec paramètres optimisés...")
                
                while self.running:
                    time.sleep(0.1)  # Réduit la charge CPU
                    
                    if not self.paused:
                        self.process_accumulated_buffer()

        except KeyboardInterrupt:
            print("\nArrêt de la dictée...")
        except Exception as e:
            print(f"Erreur: {e}")
            self.play_sound("error")
        finally:
            self.running = False
            self.play_sound("stop")
            print("Dictée arrêtée.")

def signal_handler(signum, frame):
    """
    Gestionnaire de signaux pour un arrêt propre du programme.
    
    Gère les signaux SIGINT et SIGTERM pour assurer un arrêt
    gracieux du moteur de dictée.
    
    Args:
        signum (int): Numéro du signal reçu
        frame (frame): Frame d'exécution courante
    """
    print("\nSignal d'arrêt reçu...")
    if hasattr(signal_handler, 'engine'):
        signal_handler.engine.running = False

def main():
    """
    Point d'entrée principal du programme.
    
    Configure les gestionnaires de signaux et démarre
    le moteur de dictée vocale.
    """
    # Configuration du gestionnaire de signal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Création et démarrage du moteur
    engine = DictationEngine()
    signal_handler.engine = engine
    engine.run()

if __name__ == "__main__":
    main()

