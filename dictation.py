#!/usr/bin/env python3
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

"""
Script de dictée vocale avec commandes de ponctuation.
Utilise Vosk pour la reconnaissance vocale en français et xdotool pour la saisie du texte.

Dépendances:
- vosk: pour la reconnaissance vocale
- sounddevice: pour la capture audio
- xdotool: pour simuler la saisie clavier
"""

# Configuration
CONFIG = {
    "samplerate": 16000,
    "blocksize": 8000,
    "model_path": os.path.expanduser("~/vosk-model-fr-0.6-linto-2.2.0"),
    "feedback_sounds": {
        "start": "/usr/share/sounds/freedesktop/stereo/service-login.oga",
        "stop": "/usr/share/sounds/freedesktop/stereo/service-logout.oga",
        "error": "/usr/share/sounds/freedesktop/stereo/dialog-error.oga"
    }
}

# Dictionnaire des commandes vocales
COMMANDES_VOCALES = {
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
    # Commandes de contrôle
    "pause dictée": "__PAUSE__",
    "reprendre dictée": "__RESUME__",
    "arrêter dictée": "__STOP__",
    "effacer": "__BACKSPACE__",
    "supprimer ligne": "__DELETE_LINE__",
}

class DictationEngine:
    def __init__(self):
        if not os.path.exists(CONFIG["model_path"]):
            self.play_sound("error")
            print("Le modèle spécifié est introuvable.")
            sys.exit(1)

        self.model = Model(CONFIG["model_path"])
        self.recognizer = KaldiRecognizer(self.model, CONFIG["samplerate"])
        self.audio_queue = queue.Queue()
        self.running = False
        self.paused = False
        self.last_text = ""

    def audio_callback(self, indata, frames, time, status):
        """Callback pour la capture audio"""
        if status:
            print(f"Erreur audio: {status}")
            self.play_sound("error")
        self.audio_queue.put(bytes(indata))

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

    def run(self):
        """Démarre le moteur de dictée"""
        self.running = True
        self.play_sound("start")

        print("Dictée vocale démarrée...")
        print("Commandes disponibles:", ", ".join(COMMANDES_VOCALES.keys()))
        
        try:
            with sd.RawInputStream(samplerate=CONFIG["samplerate"],
                                 blocksize=CONFIG["blocksize"],
                                 dtype='int16',
                                 channels=1,
                                 callback=self.audio_callback):
                
                while self.running:
                    try:
                        data = self.audio_queue.get(timeout=1.0)
                    except queue.Empty:
                        continue

                    if self.recognizer.AcceptWaveform(data):
                        result = json.loads(self.recognizer.Result())
                        text = result.get("text", "").strip()
                        
                        if text:
                            text_traite = self.traiter_texte(text)
                            if text_traite:
                                quoted_text = shlex.quote(text_traite)
                                os.system(f"xdotool type {quoted_text}")
                                self.last_text = text_traite

        except KeyboardInterrupt:
            print("\nArrêt de la dictée...")
        except Exception as e:
            print(f"Erreur: {e}")
            self.play_sound("error")
        finally:
            self.play_sound("stop")

def signal_handler(signum, frame):
    """Gestionnaire de signal pour arrêt propre"""
    print("\nSignal d'arrêt reçu...")
    if hasattr(signal_handler, 'engine'):
        signal_handler.engine.running = False

def main():
    # Configuration du gestionnaire de signal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Création et démarrage du moteur
    engine = DictationEngine()
    signal_handler.engine = engine
    engine.run()

if __name__ == "__main__":
    main()

