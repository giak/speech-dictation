#!/usr/bin/env python3
import os
import queue
import shlex
import json
import sounddevice as sd
from vosk import Model, KaldiRecognizer

"""
Script de dictée vocale avec commandes de ponctuation.
Utilise Vosk pour la reconnaissance vocale en français et xdotool pour la saisie du texte.

Dépendances:
- vosk: pour la reconnaissance vocale
- sounddevice: pour la capture audio
- xdotool: pour simuler la saisie clavier
"""

# Chemin vers le modèle français
model_path = os.path.expanduser("~/vosk-model-fr-0.6-linto-2.2.0")

# Dictionnaire des commandes vocales et leurs équivalents en texte
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
    "espace": " "    
}

if not os.path.exists(model_path):
    print("Le modèle spécifié est introuvable.")
    exit(1)

# Initialisation du modèle Vosk et du système de reconnaissance
model = Model(model_path)
recognizer = KaldiRecognizer(model, 16000)
audio_queue = queue.Queue()

def audio_callback(indata, frames, time, status):
    """
    Callback appelé par sounddevice pour traiter les données audio capturées.
    
    Args:
        indata: Données audio capturées
        frames: Nombre de frames
        time: Timestamp
        status: Status de la capture
    """
    if status:
        print(status)
    audio_queue.put(bytes(indata))

def traiter_texte(texte):
    """
    Traite le texte reconnu pour gérer les commandes vocales.
    Remplace les commandes vocales par leurs équivalents en ponctuation.
    
    Args:
        texte (str): Texte reconnu par Vosk
        
    Returns:
        str: Texte traité avec les commandes remplacées par leur ponctuation
    """
    mots = texte.split()
    resultat = []
    i = 0
    
    while i < len(mots):
        # Vérifier les commandes à deux mots (ex: "point d'interrogation")
        if i < len(mots) - 1:
            commande_double = f"{mots[i]} {mots[i+1]}"
            if commande_double in COMMANDES_VOCALES:
                resultat.append(COMMANDES_VOCALES[commande_double])
                i += 2
                continue
        
        # Vérifier les commandes à un mot
        if mots[i] in COMMANDES_VOCALES:
            resultat.append(COMMANDES_VOCALES[mots[i]])
        else:
            resultat.append(mots[i])
        i += 1
    
    return " ".join(resultat)

def main():
    """
    Fonction principale qui:
    1. Configure et démarre la capture audio
    2. Affiche les commandes disponibles
    3. Traite en continu le flux audio pour la reconnaissance vocale
    4. Convertit le texte reconnu en commandes de saisie via xdotool
    """
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=audio_callback):
        print("Parlez dans le microphone...")
        print("Commandes disponibles:", ", ".join(COMMANDES_VOCALES.keys()))
        
        while True:
            data = audio_queue.get()
            if recognizer.AcceptWaveform(data):
                result = recognizer.Result()
                result_dict = json.loads(result)
                text = result_dict.get("text", "").strip()
                if text:
                    text_traite = traiter_texte(text)
                    quoted_text = shlex.quote(text_traite)
                    os.system(f"xdotool type {quoted_text}")

if __name__ == "__main__":
    main()

