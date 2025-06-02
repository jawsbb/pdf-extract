#!/usr/bin/env python3
"""
Script de test pour vérifier la configuration avant déploiement
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test des imports essentiels"""
    try:
        import streamlit as st
        print("✅ Streamlit importé avec succès")
    except ImportError as e:
        print(f"❌ Erreur import Streamlit: {e}")
        return False
        
    try:
        import PyMuPDF
        print("✅ PyMuPDF importé avec succès")
    except ImportError as e:
        print(f"❌ Erreur import PyMuPDF: {e}")
        return False
        
    try:
        import openai
        print("✅ OpenAI importé avec succès")
    except ImportError as e:
        print(f"❌ Erreur import OpenAI: {e}")
        return False
        
    try:
        from pdf_extractor import PDFPropertyExtractor
        print("✅ Module pdf_extractor importé avec succès")
    except ImportError as e:
        print(f"❌ Erreur import pdf_extractor: {e}")
        return False
        
    return True

def test_files():
    """Test de la présence des fichiers essentiels"""
    files_to_check = [
        "streamlit_app.py",
        "pdf_extractor.py", 
        "requirements.txt",
        ".streamlit/config.toml",
        ".streamlit/secrets.toml"
    ]
    
    all_good = True
    for file_path in files_to_check:
        if Path(file_path).exists():
            print(f"✅ {file_path} trouvé")
        else:
            print(f"❌ {file_path} manquant")
            all_good = False
            
    return all_good

def test_gitignore():
    """Test du .gitignore"""
    gitignore_path = Path(".gitignore")
    if not gitignore_path.exists():
        print("❌ .gitignore manquant")
        return False
        
    content = gitignore_path.read_text()
    if ".streamlit/secrets.toml" in content:
        print("✅ .gitignore configuré pour les secrets")
        return True
    else:
        print("❌ .gitignore ne protège pas les secrets")
        return False

def main():
    print("🧪 Test de configuration pour déploiement Streamlit\n")
    
    tests = [
        ("Imports des modules", test_imports),
        ("Présence des fichiers", test_files), 
        ("Configuration .gitignore", test_gitignore)
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        if not test_func():
            all_passed = False
            
    print("\n" + "="*50)
    if all_passed:
        print("🎉 Tous les tests passent ! Prêt pour le déploiement.")
        print("👉 Suivez maintenant le GUIDE_DEPLOIEMENT.md")
    else:
        print("⚠️  Certains tests échouent. Corrigez les erreurs avant de déployer.")
        
if __name__ == "__main__":
    main() 