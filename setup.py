#!/usr/bin/env python3
"""
Script d'installation et de configuration automatique.
"""

import os
import sys
import subprocess
from pathlib import Path

def install_dependencies():
    """Installe les dépendances Python."""
    print("📦 Installation des dépendances...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dépendances installées avec succès!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'installation des dépendances: {e}")
        return False

def create_env_file():
    """Crée le fichier .env s'il n'existe pas."""
    env_file = Path(".env")
    example_file = Path("config.env.example")
    
    if env_file.exists():
        print("✅ Le fichier .env existe déjà")
        return True
    
    if example_file.exists():
        # Copier le fichier d'exemple
        with open(example_file, 'r') as src, open(env_file, 'w') as dst:
            dst.write(src.read())
        print("✅ Fichier .env créé à partir de l'exemple")
        print("⚠️  N'oubliez pas d'ajouter votre clé API OpenAI dans le fichier .env")
        return True
    else:
        # Créer un fichier .env basique
        with open(env_file, 'w') as f:
            f.write("# Configuration OpenAI\n")
            f.write("OPENAI_API_KEY=your_openai_api_key_here\n\n")
            f.write("# Configuration optionnelle\n")
            f.write("DEFAULT_SECTION=A\n")
            f.write("DEFAULT_PLAN_NUMBER=123\n")
        print("✅ Fichier .env créé")
        print("⚠️  N'oubliez pas d'ajouter votre clé API OpenAI dans le fichier .env")
        return True

def create_directories():
    """Crée les dossiers nécessaires."""
    directories = ["input", "output"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Dossier {directory}/ créé")

def run_test():
    """Lance le test du système."""
    print("\n🧪 Lancement du test du système...")
    try:
        subprocess.check_call([sys.executable, "test_extractor.py"])
        print("✅ Test terminé avec succès!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def main():
    """Fonction principale d'installation."""
    print("🚀 Installation de l'Extracteur PDF de Propriétaires")
    print("=" * 50)
    
    # Vérifier Python
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 ou supérieur requis")
        sys.exit(1)
    
    print(f"✅ Python {sys.version.split()[0]} détecté")
    
    # Créer les dossiers
    print("\n📁 Création des dossiers...")
    create_directories()
    
    # Créer le fichier .env
    print("\n⚙️ Configuration...")
    create_env_file()
    
    # Installer les dépendances
    print("\n📦 Installation des dépendances...")
    if not install_dependencies():
        print("❌ Échec de l'installation")
        sys.exit(1)
    
    # Lancer le test
    print("\n🧪 Test du système...")
    if run_test():
        print("\n🎉 Installation terminée avec succès!")
        print("\n📋 Prochaines étapes:")
        print("1. Éditez le fichier .env et ajoutez votre clé API OpenAI")
        print("2. Placez vos fichiers PDF dans le dossier input/")
        print("3. Lancez: python pdf_extractor.py")
    else:
        print("\n⚠️ Installation terminée mais le test a échoué")
        print("Vérifiez les dépendances et réessayez")

if __name__ == "__main__":
    main() 