# Dictée Vocale Linux - Français

Un outil de dictée vocale en français pour Linux, utilisant Vosk pour la reconnaissance vocale et xdotool pour la simulation de frappe clavier.

## À propos de Vosk

[Vosk](https://alphacephei.com/vosk/) est un toolkit de reconnaissance vocale open source qui offre plusieurs avantages :

- Fonctionne entièrement hors-ligne
- Supporte plus de 20 langues et dialectes
- Modèles légers (environ 50Mo)
- API de streaming pour une réponse en temps réel
- Vocabulaire reconfigurable
- Identification du locuteur
- Parfait pour les chatbots, assistants virtuels et transcriptions

## Prérequis Système

Le script a été testé sous Linux Mint 22 et devrait fonctionner sur les distributions Ubuntu-based similaires.

## Scénarios d'Installation

Il existe plusieurs méthodes pour installer la dictée vocale. Choisissez celle qui correspond le mieux à votre configuration.

### Méthode 1 : Installation avec pipx (Recommandée)

Cette méthode est recommandée car elle isole les dépendances globalement :

```bash
# Installation de pipx si non installé
sudo apt update
sudo apt install pipx
pipx ensurepath
source ~/.bashrc  # ou source ~/.zshrc si vous utilisez zsh

# Installation des dépendances système
sudo apt install xdotool libportaudio2 python3-full

# Installation des paquets Python via pipx
source .venv/bin/activate && pip install vosk
python3 -m venv .venv && source .venv/bin/activate && pip install sounddevice
source .venv/bin/activate && pip install numpy

# Création du dossier scripts et installation du script
mkdir -p ~/scripts
cd ~/scripts
# Copiez le fichier dictation.py dans ce dossier
chmod +x dictation.py

# Activation de l'environnement virtuel
source .venv/bin/activate
# Exécution du script
python3 dictation.py
```

### Méthode 2 : Installation avec environnement virtuel

Cette méthode isole les dépendances dans un environnement virtuel :

```bash
# Installation des dépendances système
sudo apt update
sudo apt install xdotool libportaudio2 python3-full

# Création et activation de l'environnement virtuel
python3 -m venv .venv
source .venv/bin/activate

# Mise à jour des outils Python
pip install --upgrade pip setuptools

# Installation des dépendances Python
pip install vosk sounddevice numpy

# Exécution du script
python dictation.py
```

### Méthode 3 : Installation système (Non recommandée)

Cette méthode installe les dépendances au niveau système :

```bash
# Installation des dépendances système
sudo apt update
sudo apt install xdotool libportaudio2 python3-full python3-pip

# Installation des dépendances Python
pip3 install vosk sounddevice numpy

# Exécution du script
python3 dictation.py
```

## Installation du Modèle Français

Le modèle français doit être téléchargé séparément :

```bash
# Créer le dossier pour le modèle
cd ~

# Télécharger le modèle français
wget https://github.com/LinTO-ai/model-vosk-fr-0.6-linto-2.2.0/archive/refs/heads/main.zip

# Décompresser le modèle
unzip main.zip

# Renommer le dossier pour correspondre au chemin dans le script
mv model-vosk-fr-0.6-linto-2.2.0-main vosk-model-fr-0.6-linto-2.2.0

# Nettoyer
rm main.zip
```

## Configuration du Microphone

1. Vérifiez que votre microphone est bien détecté :

```bash
arecord -l
```

2. Si nécessaire, réglez le volume du microphone :

```bash
alsamixer
```

Utilisez les flèches pour naviguer et F6 pour sélectionner la carte son.

## Utilisation

1. Activez l'environnement virtuel :

```bash
cd ~/dictee-vocale
source venv/bin/activate
```

2. Lancez le script :

```bash
./dictation.py
```

3. Placez votre curseur où vous souhaitez écrire (traitement de texte, navigateur, etc.)

4. Parlez dans votre microphone. Le texte s'écrira automatiquement.

## Commandes Vocales Disponibles

### Ponctuation et Formatage

Le script reconnaît les commandes suivantes :

- "virgule" → ,
- "point" → .
- "point d'interrogation" → ?
- "point d'exclamation" → !
- "nouvelle ligne" ou "retour à la ligne" ou "à la ligne" → nouvelle ligne
- "point-virgule" → ;
- "deux points" → :
- "ouvrir parenthèse" → (
- "fermer parenthèse" → )
- "guillemets" → "
- "espace" → espace

### Commandes de Contrôle

Commandes pour contrôler la dictée :

- "pause dictée" → Met en pause la reconnaissance vocale
- "reprendre dictée" → Reprend la reconnaissance après une pause
- "arrêter dictée" → Arrête proprement le programme
- "effacer" → Efface le dernier caractère (comme la touche retour arrière)
- "supprimer ligne" → Efface la ligne courante

## Fonctionnalités

### Retours Sonores

Le programme fournit maintenant des retours sonores pour les actions importantes :

- Son de démarrage quand la dictée commence
- Son d'arrêt quand la dictée est mise en pause ou arrêtée
- Son d'erreur en cas de problème

### Gestion des Erreurs

- Gestion robuste des erreurs audio
- Arrêt propre en cas d'interruption (Ctrl+C)
- Feedback visuel et sonore en cas de problème
- Timeout sur la capture audio pour éviter les blocages

### Mode Pause

Vous pouvez maintenant :

1. Mettre la dictée en pause avec la commande "pause dictée"
2. Parler sans que le texte soit transcrit
3. Reprendre la dictée avec "reprendre dictée"

### Contrôle du Texte

Nouvelles fonctionnalités de contrôle :

- Effacement caractère par caractère
- Suppression de ligne entière
- Mémorisation du dernier texte dicté

## Fonctionnalités Avancées

### Optimisation de la Reconnaissance Vocale

Le système intègre maintenant des fonctionnalités avancées pour améliorer la qualité de la reconnaissance :

- Détection d'activité vocale (VAD) avec seuil dynamique
- Réduction de bruit intelligente
- Gestion optimisée du buffer audio
- Seuil de confiance configurable pour les résultats
- Adaptation dynamique à l'environnement sonore

### Post-traitement Intelligent

Le texte reconnu bénéficie d'un traitement sophistiqué :

- Suppression automatique des mots parasites (euh, hum, etc.)
- Correction intelligente de la capitalisation
- Formatage automatique des nombres
- Gestion avancée de la ponctuation française
- Correction contextuelle basée sur la grammaire

### Configuration Avancée

Le script propose une configuration fine via deux dictionnaires principaux :

```python
CONFIG = {
    "samplerate": 16000,      # Taux d'échantillonnage standard
    "blocksize": 8000,        # Taille des blocs audio
    "model_path": "~/vosk-model-fr-0.6-linto-2.2.0",
    "feedback_sounds": {       # Sons de feedback configurables
        "start": "/usr/share/sounds/freedesktop/stereo/service-login.oga",
        "stop": "/usr/share/sounds/freedesktop/stereo/service-logout.oga",
        "error": "/usr/share/sounds/freedesktop/stereo/dialog-error.oga"
    }
}

MODEL_CONFIG = {
    "sample_rate": 16000,     # Doit correspondre à CONFIG["samplerate"]
    "buffer_size": 8000,      # Taille du buffer pour le traitement
    "words": True,            # Sortie mot par mot
    "max_alternatives": 1,    # Alternatives de reconnaissance
    "score_cutoff": 0.75,     # Seuil de confiance minimum
    "partial_results": False, # Désactive les résultats partiels
    "context_size": 5,       # Taille du contexte
    "noise_reduction": True,  # Réduction de bruit
    "vad_sensitivity": 3,    # Sensibilité VAD (0-3)
    "silence_threshold": 200  # Seuil de silence (ms)
}
```

### Optimisation des Performances

Pour obtenir les meilleures performances :

1. Ajustez les paramètres VAD selon votre environnement
2. Configurez le seuil de confiance (`score_cutoff`)
3. Adaptez la taille du buffer selon votre CPU
4. Réglez la sensibilité de détection vocale
5. Optimisez le seuil de silence selon vos besoins

### Gestion du Contexte

Le système maintient un contexte linguistique pour améliorer la reconnaissance :

- Historique des derniers mots reconnus
- Correction contextuelle des verbes
- Gestion des accords en genre et nombre
- Adaptation dynamique aux phrases précédentes

## Communauté et Support

Pour obtenir de l'aide ou contribuer :

- [Discord Vosk](https://discord.gg/kknE9jjVj6)
- [Groupe Telegram](https://t.me/speech_recognition)
- [Reddit](https://www.reddit.com/r/speechtech)
- [Issues GitHub](https://github.com/alphacep/vosk-api/issues)

## Dépannage

### Problèmes de Microphone

1. Vérifiez que votre microphone est bien détecté :

```bash
arecord -l
```

2. Testez l'enregistrement :

```bash
arecord -d 5 test.wav  # Enregistre 5 secondes
aplay test.wav         # Lecture du test
```

### Problèmes de Permissions

Si vous rencontrez des erreurs d'accès au microphone :

```bash
# Ajoutez votre utilisateur au groupe audio
sudo usermod -a -G audio $USER

# Déconnectez-vous et reconnectez-vous pour appliquer les changements
```

### Problèmes de Performance

Si la reconnaissance est lente ou imprécise :

1. Assurez-vous d'être dans un environnement calme
2. Parlez clairement et à un rythme modéré
3. Vérifiez que votre CPU n'est pas surchargé

### Problèmes Courants

1. **Erreur de reconnaissance** :

   - Vérifiez la qualité audio avec `arecord`
   - Testez différents paramètres de microphone
   - Essayez un modèle plus grand

2. **Latence** :
   - Vérifiez la charge CPU
   - Ajustez la taille du buffer audio
   - Utilisez un modèle plus léger si nécessaire

## Arrêt Propre

Le programme peut maintenant être arrêté de plusieurs façons :

- En utilisant la commande vocale "arrêter dictée"
- En appuyant sur Ctrl+C
- En envoyant un signal SIGTERM
- En utilisant la commande "pause dictée" puis Ctrl+C

## Limitations Connues

- La reconnaissance vocale nécessite une connexion internet pour le téléchargement initial du modèle, mais fonctionne hors-ligne ensuite
- Les performances dépendent de la qualité du microphone et de l'environnement sonore
- Le modèle français peut avoir des difficultés avec certains accents ou expressions régionales

## Références

- [Documentation officielle Vosk](https://alphacephei.com/vosk/)
- [Modèles disponibles](https://alphacephei.com/vosk/models)
- [Guide d'adaptation](https://alphacephei.com/vosk/adaptation)

## Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

Les modèles Vosk sont sous [licence Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0).

## Tests Unitaires

Le projet inclut maintenant une suite de tests unitaires pour assurer la qualité et la fiabilité du code.

### Exécution des Tests

Pour exécuter les tests :

```bash
# Tests unitaires standards
python3 -m unittest test_dictation.py -v

# Tests de performance
python3 -m unittest test_performance.py -v

# Tests de performance avec profilage mémoire détaillé
PROFILE_MEMORY=1 python3 -m memory_profiler test_performance.py

# Tests de performance avec profilage CPU
python3 -m cProfile -s cumulative test_performance.py
```

Les tests de performance fournissent des métriques détaillées sur :

- L'utilisation de la mémoire
- Les temps d'exécution
- L'utilisation CPU
- La latence de traitement
- La performance sous charge

Chaque test affiche ses métriques de performance, et le profilage mémoire montre l'évolution de l'utilisation mémoire ligne par ligne.

### Couverture des Tests

Les tests couvrent les fonctionnalités principales :

- Traitement des commandes vocales
- Post-traitement du texte
- Détection d'activité vocale
- Gestion du contexte
- Correction grammaticale
- Formatage des nombres
- Gestion des commandes système

### Ajout de Nouveaux Tests

Pour ajouter de nouveaux tests :

1. Ouvrez `test_dictation.py`
2. Ajoutez une nouvelle méthode de test dans la classe `TestDictationEngine`
3. Le nom de la méthode doit commencer par `test_`
4. Utilisez les assertions de `unittest` pour vérifier les résultats

Exemple :

```python
def test_ma_nouvelle_fonction(self):
    """Description du test"""
    resultat = self.engine.ma_fonction("test")
    self.assertEqual(resultat, "résultat attendu")
```

### Bonnes Pratiques

- Chaque test doit être indépendant
- Utilisez `setUp()` pour la configuration commune
- Documentez chaque test avec un docstring
- Utilisez des mocks pour les dépendances externes
- Testez les cas limites et les erreurs
