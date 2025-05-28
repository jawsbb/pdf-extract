#!/usr/bin/env python3
"""
🏠 Extracteur de Propriétaires PDF
Script de démarrage simplifié pour clients non techniques
"""

import subprocess
import sys
import webbrowser
import time
import threading
from pathlib import Path

def print_banner():
    """Afficher la bannière de démarrage"""
    print("=" * 60)
    print("🏠 EXTRACTEUR DE PROPRIÉTAIRES PDF")
    print("=" * 60)
    print("🚀 Interface web moderne avec drag & drop")
    print("🎭 Mode démo disponible (sans clé API)")
    print("📊 Export automatique en CSV/Excel")
    print("=" * 60)
    print()

def check_dependencies():
    """Vérifier les dépendances essentielles"""
    print("🔍 Vérification des dépendances...")
    
    try:
        import streamlit
        print("✅ Streamlit installé")
    except ImportError:
        print("❌ Streamlit manquant")
        print("💡 Installez avec: pip install -r requirements.txt")
        return False
    
    try:
        import pandas
        print("✅ Pandas installé")
    except ImportError:
        print("❌ Pandas manquant")
        return False
    
    # Vérifier que le fichier principal existe
    if not Path("streamlit_app.py").exists():
        print("❌ Fichier streamlit_app.py manquant")
        return False
    
    if not Path("pdf_extractor.py").exists():
        print("❌ Fichier pdf_extractor.py manquant")
        return False
    
    print("✅ Toutes les dépendances sont prêtes")
    return True

def open_browser_delayed():
    """Ouvrir le navigateur après 3 secondes"""
    time.sleep(3)
    webbrowser.open("http://localhost:8501")

def main():
    """Fonction principale"""
    print_banner()
    
    if not check_dependencies():
        print("\n❌ Veuillez installer les dépendances avant de continuer")
        print("💡 Commande: pip install -r requirements.txt")
        input("\nAppuyez sur Entrée pour quitter...")
        return
    
    print("🚀 Démarrage de l'application...")
    print("📱 L'interface s'ouvrira automatiquement dans votre navigateur")
    print("🌐 URL: http://localhost:8501")
    print("\n⏳ Patientez quelques secondes...")
    
    # Ouvrir le navigateur automatiquement
    browser_thread = threading.Thread(target=open_browser_delayed, daemon=True)
    browser_thread.start()
    
    try:
        # Lancer Streamlit avec les bonnes options
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false",
            "--server.headless", "true"
        ])
    except KeyboardInterrupt:
        print("\n👋 Application arrêtée proprement")
    except Exception as e:
        print(f"\n❌ Erreur lors du démarrage: {e}")
        input("\nAppuyez sur Entrée pour quitter...")

if __name__ == "__main__":
    main() 