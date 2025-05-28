#!/usr/bin/env python3
"""
Script de démarrage pour l'extracteur PDF en ligne
Permet de choisir entre différentes interfaces web
"""

import os
import sys
import subprocess
import webbrowser
import time
import threading
from pathlib import Path

def print_banner():
    """Afficher la bannière de démarrage"""
    print("=" * 60)
    print("🏠 EXTRACTEUR DE PROPRIÉTAIRES PDF - VERSION WEB")
    print("=" * 60)
    print()

def check_dependencies():
    """Vérifier les dépendances"""
    print("🔍 Vérification des dépendances...")
    
    # Vérifier Python
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ requis")
        return False
    
    # Vérifier les modules Python
    required_modules = ['streamlit', 'pandas', 'openai', 'pdf2image', 'PIL']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"❌ Modules manquants: {', '.join(missing_modules)}")
        print("💡 Installez avec: pip install -r requirements_streamlit.txt")
        return False
    
    print("✅ Toutes les dépendances sont installées")
    return True

def start_streamlit():
    """Démarrer l'application Streamlit"""
    print("🚀 Démarrage de l'interface Streamlit...")
    print("📱 Interface moderne avec drag & drop")
    print("🎭 Mode démo disponible (sans API OpenAI)")
    print()
    
    # Démarrer Streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Application arrêtée")

def start_react_dev():
    """Démarrer l'application React en mode développement"""
    print("🚀 Démarrage de l'interface React...")
    print("⚛️ Interface ultra-moderne avec animations")
    print("🔄 Rechargement automatique")
    print()
    
    frontend_path = Path("frontend")
    if not frontend_path.exists():
        print("❌ Dossier frontend non trouvé")
        return
    
    # Vérifier Node.js
    try:
        subprocess.run(["node", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Node.js non installé")
        print("💡 Installez Node.js depuis https://nodejs.org")
        return
    
    # Installer les dépendances si nécessaire
    if not (frontend_path / "node_modules").exists():
        print("📦 Installation des dépendances React...")
        subprocess.run(["npm", "install"], cwd=frontend_path)
    
    # Démarrer React
    try:
        subprocess.run(["npm", "start"], cwd=frontend_path)
    except KeyboardInterrupt:
        print("\n👋 Application arrêtée")

def start_backend():
    """Démarrer le backend Flask"""
    print("🔧 Démarrage du backend Flask...")
    
    backend_path = Path("backend")
    if not backend_path.exists():
        print("❌ Dossier backend non trouvé")
        return
    
    # Démarrer Flask
    try:
        os.chdir(backend_path)
        subprocess.run([sys.executable, "app.py"])
    except KeyboardInterrupt:
        print("\n👋 Backend arrêté")

def start_full_stack():
    """Démarrer frontend + backend"""
    print("🚀 Démarrage de l'application complète...")
    print("⚛️ Frontend React + 🔧 Backend Flask")
    print()
    
    # Démarrer le backend en arrière-plan
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()
    
    # Attendre que le backend démarre
    time.sleep(3)
    
    # Démarrer le frontend
    start_react_dev()

def open_browser(url, delay=3):
    """Ouvrir le navigateur après un délai"""
    time.sleep(delay)
    webbrowser.open(url)

def main():
    """Menu principal"""
    print_banner()
    
    if not check_dependencies():
        input("\nAppuyez sur Entrée pour quitter...")
        return
    
    print("\n🎯 Choisissez votre interface :")
    print("1. 📱 Streamlit (Recommandé - Simple et rapide)")
    print("2. ⚛️ React + Flask (Avancé - Interface moderne)")
    print("3. 🔧 Backend Flask seulement")
    print("4. ❓ Aide et informations")
    print("0. 🚪 Quitter")
    print()
    
    while True:
        choice = input("Votre choix (1-4, 0 pour quitter) : ").strip()
        
        if choice == "1":
            # Ouvrir le navigateur automatiquement
            browser_thread = threading.Thread(
                target=open_browser, 
                args=("http://localhost:8501",), 
                daemon=True
            )
            browser_thread.start()
            start_streamlit()
            break
            
        elif choice == "2":
            # Ouvrir le navigateur pour React
            browser_thread = threading.Thread(
                target=open_browser, 
                args=("http://localhost:3000",), 
                daemon=True
            )
            browser_thread.start()
            start_full_stack()
            break
            
        elif choice == "3":
            # Ouvrir le navigateur pour l'API
            browser_thread = threading.Thread(
                target=open_browser, 
                args=("http://localhost:5000/api/health",), 
                daemon=True
            )
            browser_thread.start()
            start_backend()
            break
            
        elif choice == "4":
            print("\n📚 INFORMATIONS :")
            print("• Streamlit : Interface simple, idéale pour débuter")
            print("• React : Interface moderne avec animations")
            print("• Backend : API REST pour intégrations")
            print()
            print("🔑 Configuration OpenAI :")
            print("• Créez un fichier .env avec OPENAI_API_KEY=votre_clé")
            print("• Ou utilisez le mode démo dans Streamlit")
            print()
            print("🌐 URLs après démarrage :")
            print("• Streamlit : http://localhost:8501")
            print("• React : http://localhost:3000")
            print("• API : http://localhost:5000")
            print()
            
        elif choice == "0":
            print("👋 Au revoir !")
            break
            
        else:
            print("❌ Choix invalide, essayez encore")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Application interrompue")
    except Exception as e:
        print(f"\n❌ Erreur : {e}")
        input("Appuyez sur Entrée pour quitter...") 