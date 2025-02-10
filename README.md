# Dictée Vocale Linux - Français

Un outil de dictée vocale en français pour Linux, utilisant Vosk pour la reconnaissance vocale et xdotool pour la simulation de frappe clavier.

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

## Limitations Connues

- La reconnaissance vocale nécessite une connexion internet pour le téléchargement initial du modèle, mais fonctionne hors-ligne ensuite
- Les performances dépendent de la qualité du microphone et de l'environnement sonore
- Le modèle français peut avoir des difficultés avec certains accents ou expressions régionales

## Support

Pour signaler un bug ou suggérer une amélioration, veuillez ouvrir une issue sur le dépôt GitHub.

## Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.
