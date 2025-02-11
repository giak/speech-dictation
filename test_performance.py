#!/usr/bin/env python3

import unittest
import time
import psutil
import numpy as np
from unittest.mock import Mock, patch
import memory_profiler
import cProfile
import io
import pstats
import os
import platform
from contextlib import contextmanager
from dictation import DictationEngine, CONFIG, MODEL_CONFIG

def run_test_suite():
    """Execute the test suite"""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPerformance)
    return unittest.TextTestRunner(verbosity=2).run(suite)

@memory_profiler.profile
def profile_memory_usage():
    """Fonction principale pour le profilage mémoire"""
    return run_test_suite()

class PerformanceMetrics:
    """Classe utilitaire pour collecter les métriques de performance"""
    
    @staticmethod
    def get_memory_usage():
        """Retourne l'utilisation mémoire actuelle en MB"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024

    @staticmethod
    def measure_time(func):
        """Décorateur pour mesurer le temps d'exécution"""
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            return end_time - start_time
        return wrapper

    @staticmethod
    def profile_function(func):
        """Profile une fonction et retourne les statistiques"""
        profiler = cProfile.Profile()
        profiler.enable()
        result = func()
        profiler.disable()
        
        s = io.StringIO()
        stats = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        stats.print_stats()
        return s.getvalue(), result

class PerformanceReport:
    """Classe pour générer un rapport détaillé des performances"""
    
    # Codes couleur ANSI étendus
    COLORS = {
        'HEADER': '\033[38;5;213m',  # Rose vif
        'BLUE': '\033[38;5;39m',     # Bleu clair
        'GREEN': '\033[38;5;82m',    # Vert vif
        'WARNING': '\033[38;5;214m', # Orange
        'FAIL': '\033[38;5;196m',    # Rouge vif
        'BOLD': '\033[1m',           # Gras
        'UNDERLINE': '\033[4m',      # Souligné
        'DIM': '\033[2m',            # Atténué
        'ITALIC': '\033[3m',         # Italique
        'BG_DARK': '\033[48;5;236m', # Fond gris foncé
        'BG_HEADER': '\033[48;5;237m', # Fond pour les en-têtes
        'RESET_BG': '\033[49m',      # Reset fond
        'END': '\033[0m'             # Reset tout
    }
    
    # Symboles Unicode pour une meilleure présentation
    SYMBOLS = {
        'separator': '│',
        'arrow': '➜',
        'check': '✓',
        'cross': '✗',
        'star_filled': '★',
        'star_empty': '☆',
        'warning': '⚠',
        'info': 'ℹ',
        'bullet': '•',
    }

    def __init__(self):
        self.results = {
            'memory': {},
            'cpu': {},
            'timing': {},
            'system_info': self._get_system_info()
        }
        self.thresholds = self._set_thresholds()

    def _color(self, text, color):
        """Applique une couleur au texte"""
        return f"{self.COLORS[color]}{text}{self.COLORS['END']}"

    def _get_status_color(self, passed, rating):
        """Détermine la couleur en fonction du statut et de la note"""
        if not passed:
            return 'FAIL'
        if rating >= 4:
            return 'GREEN'
        if rating >= 3:
            return 'BLUE'
        if rating >= 2:
            return 'WARNING'
        return 'FAIL'

    def _get_system_info(self):
        """Récupère les informations système"""
        cpu_info = {}
        try:
            cpu_info['count'] = psutil.cpu_count()
            cpu_info['freq'] = psutil.cpu_freq().max if psutil.cpu_freq() else "N/A"
            mem = psutil.virtual_memory()
            cpu_info['total_memory'] = f"{mem.total / (1024**3):.1f} GB"
        except Exception as e:
            cpu_info['error'] = str(e)

        return {
            'platform': platform.platform(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'cpu_info': cpu_info
        }

    def _set_thresholds(self):
        """Définit les seuils de performance en fonction du matériel"""
        cpu_count = psutil.cpu_count() or 4
        total_memory = psutil.virtual_memory().total / (1024**3)  # En GB

        # Facteurs d'ajustement basés sur l'expérience
        memory_factor = 1.2  # Facteur de tolérance pour la mémoire
        cpu_factor = 1.5    # Facteur de tolérance pour le CPU
        time_factor = 2.0   # Facteur de tolérance pour les temps d'exécution

        return {
            # Seuils mémoire plus réalistes
            'memory_baseline': min(200, max(75, total_memory * 0.15)) * memory_factor,  # Au moins 75MB, max 200MB
            'memory_leak': min(50, max(20, total_memory * 0.05)) * memory_factor,       # Au moins 20MB, max 50MB
            
            # Seuils CPU adaptés
            'cpu_usage': min(90, 100 / cpu_count * 3) * cpu_factor,  # Plus tolérant pour le CPU
            
            # Seuils temporels ajustés
            'processing_time': 2.0 * (4 / cpu_count) * time_factor,
            'vad_latency': 0.01 * (4 / cpu_count) * time_factor,
            'buffer_time': max(1.5, 3.0 * (4 / cpu_count)) * time_factor,  # Au moins 1.5s
            'context_time': 0.2 * (4 / cpu_count) * time_factor,
            'concurrent_time': max(2.0, 5.0 * (4 / cpu_count)) * time_factor  # Au moins 2s
        }

    def add_result(self, category, test_name, value, threshold, passed):
        """Ajoute un résultat de test"""
        self.results[category][test_name] = {
            'value': value,
            'threshold': threshold,
            'passed': passed,
            'rating': self._get_performance_rating(value, threshold, passed)
        }

    def _get_performance_rating(self, value, threshold, passed):
        """Calcule une note de performance sur 5 étoiles"""
        if not passed:
            return 1
        if isinstance(value, (int, float)) and isinstance(threshold, (int, float)):
            ratio = value / threshold
            if ratio <= 0.3:
                return 5  # Excellent
            elif ratio <= 0.5:
                return 4  # Très bien
            elif ratio <= 0.7:
                return 3  # Bien
            elif ratio <= 0.9:
                return 2  # Acceptable
            else:
                return 1  # Limite
        return 3  # Par défaut si non comparable

    def _format_header(self, text):
        """Formate un en-tête de section"""
        return (f"{self.COLORS['BG_HEADER']}{self.COLORS['BOLD']}"
                f" {text} {self.COLORS['RESET_BG']}{self.COLORS['END']}")

    def _format_section(self, text):
        """Formate une ligne de section"""
        return f"{self.COLORS['DIM']}{self.SYMBOLS['separator']}{self.COLORS['END']} {text}"

    def generate_report(self):
        """Génère un rapport détaillé des performances"""
        # En-tête du rapport avec cadre
        report = [
            "\n" + "╭" + "─"*78 + "╮",
            f"│{self._color(self.SYMBOLS['info'], 'HEADER')} "
            f"{self._color('RAPPORT DE PERFORMANCE DU SYSTÈME DE DICTÉE VOCALE', 'HEADER'):^76}│",
            "├" + "─"*78 + "┤"
        ]

        # Informations système
        sys_info = self.results['system_info']
        report.extend([
            self._format_header("INFORMATIONS SYSTÈME"),
            self._format_section(f"{self._color('Plateforme:', 'BLUE')} {sys_info['platform']}"),
            self._format_section(f"{self._color('Processeur:', 'BLUE')} {sys_info['processor']}"),
            self._format_section(f"{self._color('Version Python:', 'BLUE')} {sys_info['python_version']}"),
            self._format_section(f"{self._color('Nombre de CPU:', 'BLUE')} {sys_info['cpu_info'].get('count', 'N/A')}"),
            self._format_section(f"{self._color('Fréquence CPU:', 'BLUE')} {sys_info['cpu_info'].get('freq', 'N/A')} MHz"),
            self._format_section(f"{self._color('Mémoire Totale:', 'BLUE')} {sys_info['cpu_info'].get('total_memory', 'N/A')}"),
            "├" + "─"*78 + "┤"
        ])

        # Résultats des tests par catégorie
        categories = {
            'memory': 'PERFORMANCES MÉMOIRE',
            'cpu': 'PERFORMANCES CPU',
            'timing': 'PERFORMANCES TEMPORELLES'
        }

        for cat, title in categories.items():
            if self.results[cat]:
                report.extend([
                    self._format_header(title),
                ])
                for test_name, data in self.results[cat].items():
                    stars = (self.SYMBOLS['star_filled'] * data['rating'] + 
                            self.SYMBOLS['star_empty'] * (5 - data['rating']))
                    status = self.SYMBOLS['check'] if data['passed'] else self.SYMBOLS['cross']
                    color = self._get_status_color(data['passed'], data['rating'])
                    
                    # Formatage coloré du résultat avec indentation
                    status_colored = self._color(status, 'GREEN' if data['passed'] else 'FAIL')
                    stars_colored = self._color(stars, color)
                    value_colored = self._color(f"{data['value']:.3f}", color)
                    
                    report.append(self._format_section(
                        f"{status_colored} {test_name:<25} {value_colored:>8} "
                        f"(seuil: {data['threshold']:<8.3f}) {stars_colored}"
                    ))
                report.append("├" + "─"*78 + "┤")

        # Score global
        total_rating = sum(r['rating'] for cat in ['memory', 'cpu', 'timing']
                         for r in self.results[cat].values())
        total_tests = sum(1 for cat in ['memory', 'cpu', 'timing']
                         for _ in self.results[cat])
        
        if total_tests > 0:
            avg_rating = total_rating / total_tests
            global_stars = (self.SYMBOLS['star_filled'] * int(round(avg_rating)) + 
                          self.SYMBOLS['star_empty'] * (5 - int(round(avg_rating))))
            color = self._get_status_color(avg_rating >= 3, int(round(avg_rating)))
            
            report.extend([
                self._format_header("ÉVALUATION GLOBALE"),
                self._format_section(
                    f"Score moyen: {self._color(f'{avg_rating:.1f}/5.0', color)} "
                    f"{self._color(global_stars, color)}"
                ),
                "├" + "─"*78 + "┤"
            ])

        # Recommandations
        report.extend([
            self._format_header("RECOMMANDATIONS"),
        ])
        
        if avg_rating < 3:
            report.append(self._format_section(
                self._color(f"{self.SYMBOLS['warning']} Performances sous-optimales détectées:", 'WARNING')
            ))
            for cat in categories:
                for test_name, data in self.results[cat].items():
                    if data['rating'] <= 2:
                        report.append(self._format_section(
                            self._color(
                                f"{self.SYMBOLS['bullet']} Optimiser {test_name}: "
                                f"actuel={data['value']:.3f}, "
                                f"cible<{data['threshold']:.3f}",
                                'WARNING'
                            )
                        ))
        else:
            report.append(self._format_section(
                self._color(f"{self.SYMBOLS['check']} Les performances sont globalement satisfaisantes.", 'GREEN')
            ))

        # Note finale
        report.extend([
            "├" + "─"*78 + "┤",
            self._format_section(
                f"{self._color('NOTE:', 'ITALIC')} Les seuils sont adaptés à votre configuration matérielle."
            ),
            "╰" + "─"*78 + "╯"
        ])

        return "\n".join(report)

class TestPerformance(unittest.TestCase):
    """Tests de performance pour le moteur de dictée vocale"""

    @classmethod
    def setUpClass(cls):
        """Configuration initiale pour toute la classe de test"""
        print("\nDémarrage des tests de performance...")
        print("Mesure de l'utilisation mémoire initiale...")
        cls.initial_memory = PerformanceMetrics.get_memory_usage()
        print(f"Mémoire initiale: {cls.initial_memory:.2f} MB")
        cls.performance_report = PerformanceReport()

    def setUp(self):
        """Initialisation pour les tests de performance"""
        with patch('dictation.Model'), patch('dictation.KaldiRecognizer') as mock_recognizer:
            self.engine = DictationEngine()
            self.engine.play_sound = Mock()
            self.engine.recognizer = Mock()
            self.engine.recognizer.Result = Mock(return_value='{"text": "test"}')
            self.engine.recognizer.AcceptWaveform = Mock(return_value=True)
        
        self.test_text = "bonjour comment allez vous aujourd'hui je vais très bien merci " * 10
        self.test_audio = np.random.rand(16000).astype(np.float32)

    def tearDown(self):
        """Nettoyage après chaque test"""
        current_memory = PerformanceMetrics.get_memory_usage()
        print(f"\nMémoire après le test: {current_memory:.2f} MB")
        print(f"Différence: {current_memory - self.initial_memory:.2f} MB")

    def test_memory_usage_baseline(self):
        """Test de l'utilisation mémoire de base"""
        initial_memory = PerformanceMetrics.get_memory_usage()
        threshold = self.performance_report.thresholds['memory_baseline']
        passed = initial_memory < threshold
        self.performance_report.add_result('memory', 'Utilisation mémoire de base',
                                         initial_memory, threshold, passed)
        self.assertLess(initial_memory, threshold)

    @memory_profiler.profile
    def test_memory_leak(self):
        """Test pour détecter les fuites mémoire"""
        initial_memory = PerformanceMetrics.get_memory_usage()
        
        for _ in range(100):
            self.engine.traiter_texte(self.test_text)
            self.engine.process_accumulated_buffer()
        
        final_memory = PerformanceMetrics.get_memory_usage()
        memory_diff = final_memory - initial_memory
        threshold = self.performance_report.thresholds['memory_leak']
        passed = memory_diff < threshold
        self.performance_report.add_result('memory', 'Fuite mémoire',
                                         memory_diff, threshold, passed)
        self.assertLess(memory_diff, threshold)

    def test_processing_speed(self):
        """Test de la vitesse de traitement du texte"""
        @PerformanceMetrics.measure_time
        def process_batch():
            for _ in range(100):
                self.engine.traiter_texte(self.test_text)
        
        elapsed = process_batch()
        threshold = self.performance_report.thresholds['processing_time']
        passed = elapsed < threshold
        self.performance_report.add_result('timing', 'Vitesse de traitement',
                                         elapsed, threshold, passed)
        self.assertLess(elapsed, threshold)

    def test_vad_latency(self):
        """Test de la latence de la détection d'activité vocale"""
        latencies = []
        
        for _ in range(100):
            start_time = time.perf_counter()
            self.engine.is_speech(self.test_audio)
            latency = time.perf_counter() - start_time
            latencies.append(latency)
        
        avg_latency = sum(latencies) / len(latencies)
        threshold = self.performance_report.thresholds['vad_latency']
        passed = avg_latency < threshold
        self.performance_report.add_result('timing', 'Latence VAD',
                                         avg_latency, threshold, passed)
        self.assertLess(avg_latency, threshold)

    def test_buffer_processing_efficiency(self):
        """Test de l'efficacité du traitement du buffer"""
        large_buffer = b"test_data" * 1000
        
        @PerformanceMetrics.measure_time
        def process_buffers():
            for _ in range(50):
                self.engine.audio_queue.put(large_buffer)
                self.engine.process_accumulated_buffer()
        
        elapsed = process_buffers()
        threshold = self.performance_report.thresholds['buffer_time']
        passed = elapsed < threshold
        self.performance_report.add_result('timing', 'Efficacité buffer',
                                         elapsed, threshold, passed)
        self.assertLess(elapsed, threshold)

    def test_context_update_performance(self):
        """Test de la performance de la mise à jour du contexte"""
        long_text = "ceci est un très long texte pour tester la performance " * 100
        
        @PerformanceMetrics.measure_time
        def update_context():
            self.engine.update_context(long_text)
        
        elapsed = update_context()
        threshold = self.performance_report.thresholds['context_time']
        passed = elapsed < threshold
        self.performance_report.add_result('timing', 'Mise à jour contexte',
                                         elapsed, threshold, passed)
        self.assertLess(elapsed, threshold)

    def test_cpu_usage(self):
        """Test de l'utilisation CPU"""
        process = psutil.Process()
        
        time.sleep(0.1)
        initial_cpu_percent = process.cpu_percent()
        time.sleep(0.1)
        
        for _ in range(1000):
            self.engine.traiter_texte(self.test_text)
        
        time.sleep(0.1)
        final_cpu_percent = process.cpu_percent()
        
        cpu_increase = final_cpu_percent - initial_cpu_percent
        threshold = self.performance_report.thresholds['cpu_usage']
        passed = cpu_increase < threshold
        self.performance_report.add_result('cpu', 'Utilisation CPU',
                                         cpu_increase, threshold, passed)
        self.assertLess(cpu_increase, threshold)

    def test_concurrent_processing(self):
        """Test de performance avec traitement concurrent"""
        import threading
        
        def process_batch():
            for _ in range(50):
                self.engine.traiter_texte(self.test_text)
        
        threads = []
        start_time = time.perf_counter()
        
        for _ in range(4):
            thread = threading.Thread(target=process_batch)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        total_time = time.perf_counter() - start_time
        threshold = self.performance_report.thresholds['concurrent_time']
        passed = total_time < threshold
        self.performance_report.add_result('timing', 'Traitement concurrent',
                                         total_time, threshold, passed)
        self.assertLess(total_time, threshold)

    @classmethod
    def tearDownClass(cls):
        """Affiche le rapport de performance à la fin des tests"""
        print(cls.performance_report.generate_report())

def main():
    """Point d'entrée principal pour les tests de performance"""
    if os.environ.get('PROFILE_MEMORY'):
        profile_memory_usage()
    else:
        run_test_suite()

if __name__ == '__main__':
    main() 