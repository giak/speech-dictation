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
pipx install vosk
pipx install sounddevice

# Création du dossier scripts et installation du script
mkdir -p ~/scripts
cd ~/scripts
# Copiez le fichier dictation.py dans ce dossier
chmod +x dictation.py
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
pip install vosk sounddevice

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
pip3 install vosk sounddevice

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

## Fonctionnalités Avancées

### Adaptation du Modèle

Vosk permet d'adapter le modèle de reconnaissance pour améliorer la précision :

- Ajout de vocabulaire spécifique
- Adaptation au locuteur
- Personnalisation du modèle de langage

### Performance et Optimisation

Pour obtenir les meilleures performances :

1. Utilisez un microphone de bonne qualité
2. Placez le microphone près de la source sonore
3. Minimisez les bruits de fond
4. Considérez utiliser un modèle plus grand pour plus de précision

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
