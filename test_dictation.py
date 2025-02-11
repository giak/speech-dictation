#!/usr/bin/env python3

import unittest
import os
import json
from unittest.mock import Mock, patch
import numpy as np
from dictation import DictationEngine, CONFIG, MODEL_CONFIG, COMMANDES_VOCALES

class TestDictationEngine(unittest.TestCase):
    """Tests unitaires pour le moteur de dictée vocale"""

    def setUp(self):
        """
        Préparation de l'environnement de test.
        Cette méthode est appelée avant chaque test.
        """
        # Mock du modèle Vosk pour éviter de charger le vrai modèle
        with patch('dictation.Model'), patch('dictation.KaldiRecognizer'):
            self.engine = DictationEngine()
            # Désactive les sons pendant les tests
            self.engine.play_sound = Mock()

    def test_traiter_texte_commandes_simples(self):
        """Test du traitement des commandes vocales simples"""
        # Test des commandes de ponctuation
        self.assertEqual(self.engine.traiter_texte("virgule"), ",")
        self.assertEqual(self.engine.traiter_texte("point"), ".")
        self.assertEqual(self.engine.traiter_texte("point d'interrogation"), "?")

    def test_traiter_texte_commandes_doubles(self):
        """Test du traitement des commandes vocales composées"""
        self.assertEqual(self.engine.traiter_texte("point d'interrogation"), "?")
        self.assertEqual(self.engine.traiter_texte("nouvelle ligne"), "\n")

    def test_remove_noise_words(self):
        """Test de la suppression des mots parasites"""
        text = "euh bonjour hum comment bah allez vous"
        expected = "bonjour comment allez vous"
        self.assertEqual(self.engine.remove_noise_words(text), expected)

    def test_correct_capitalization(self):
        """Test de la correction de la capitalisation"""
        # Test capitalisation après point
        text = "bonjour. comment allez-vous. france est un pays."
        expected = "Bonjour. Comment allez-vous. France est un pays."
        self.assertEqual(self.engine.correct_capitalization(text), expected)

    def test_format_numbers(self):
        """Test du formatage des nombres"""
        text = "j'ai zéro pomme et trois poires"
        expected = "j'ai 0 pomme et 3 poires"
        self.assertEqual(self.engine.format_numbers(text), expected)

    def test_correct_spacing(self):
        """Test de la correction des espaces"""
        text = "Bonjour  ,  comment  allez  vous  ?"
        expected = "Bonjour, comment allez vous?"
        self.assertEqual(self.engine.correct_spacing(text), expected)

    def test_correct_punctuation(self):
        """Test de la correction de la ponctuation"""
        text = "Bonjour , comment allez vous ?"
        expected = "Bonjour, comment allez vous?"
        self.assertEqual(self.engine.correct_punctuation(text), expected)

    def test_apply_context_rules(self):
        """Test des règles de correction contextuelle"""
        # Test conjugaison après pronom
        self.assertEqual(
            self.engine.apply_context_rules("parler", "je", None),
            "parle"
        )
        self.assertEqual(
            self.engine.apply_context_rules("parler", "nous", None),
            "parlons"
        )

    def test_is_speech(self):
        """Test de la détection d'activité vocale"""
        # Crée un signal audio synthétique de test
        # Signal fort (parole)
        strong_signal = np.ones(1000) * 0.8
        self.assertTrue(self.engine.is_speech(strong_signal))
        
        # Signal faible (silence)
        weak_signal = np.ones(1000) * 0.1
        self.assertFalse(self.engine.is_speech(weak_signal))

    def test_update_context(self):
        """Test de la mise à jour du contexte"""
        text = "bonjour comment allez vous"
        self.engine.update_context(text)
        self.assertEqual(len(self.engine.context), 4)
        self.assertEqual(self.engine.context[-1], "vous")

    def test_handle_command(self):
        """Test du gestionnaire de commandes"""
        # Test pause
        self.engine.handle_command("__PAUSE__")
        self.assertTrue(self.engine.paused)
        
        # Test reprise
        self.engine.handle_command("__RESUME__")
        self.assertFalse(self.engine.paused)

    @patch('os.system')
    def test_process_accumulated_buffer(self, mock_system):
        """Test du traitement du buffer accumulé"""
        # Mock du recognizer
        self.engine.recognizer = Mock()
        self.engine.recognizer.Result = Mock(return_value='{"text": "bonjour"}')
        self.engine.recognizer.AcceptWaveform = Mock(return_value=True)
        
        # Ajoute des données au buffer
        self.engine.audio_queue.put(b"test_data")
        self.engine.process_accumulated_buffer()
        
        # Vérifie que xdotool a été appelé avec le bon texte
        mock_system.assert_called_with("xdotool type bonjour")

def main():
    unittest.main()

if __name__ == '__main__':
    main() 