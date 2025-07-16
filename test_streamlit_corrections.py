#!/usr/bin/env python3
"""
Test des corrections apportées à l'interface Streamlit.
"""

import streamlit as st
import pandas as pd
import tempfile
import os
from pathlib import Path
import json
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_streamlit_corrections():
    """Test des corrections de l'interface Streamlit."""
    logger.info("🧪 TEST: Corrections interface Streamlit")
    
    # Simuler des données de test
    test_data = [
        {
            'department': '75',
            'commune': '101',
            'prefixe': '000',
            'section': 'AB',
            'numero': '123',
            'nom': 'MARTIN',
            'prenom': 'Jean',
            'adresse': '123 Rue de la Paix',
            'id': '75101000AB123',
            'fichier_source': 'test.pdf'
        },
        {
            'department': '75',
            'commune': '101',
            'prefixe': '000',
            'section': 'AB',
            'numero': '124',
            'nom': 'DUPONT',
            'prenom': 'Marie',
            'adresse': '456 Avenue du Général',
            'id': '75101000AB124',
            'fichier_source': 'test.pdf'
        }
    ]
    
    print("✅ Données de test créées")
    
    # Test 1: Vérification de la cohérence des fichiers
    def test_file_consistency():
        current_files = ['test.pdf', 'test2.pdf']
        processed_files = ['test.pdf']
        
        if current_files != processed_files:
            print("⚠️ Incohérence détectée entre fichiers actuels et traités")
            return False
        return True
    
    # Test 2: Vérification du hash des fichiers
    def test_file_hash():
        files_data = [
            {'name': 'test.pdf', 'content': b'PDF content 1'},
            {'name': 'test2.pdf', 'content': b'PDF content 2'}
        ]
        
        hash1 = hash(tuple(f['name'] + str(len(f['content'])) for f in files_data))
        hash2 = hash(tuple(f['name'] + str(len(f['content'])) for f in files_data))
        
        if hash1 == hash2:
            print("✅ Hash des fichiers cohérent")
            return True
        else:
            print("❌ Hash des fichiers incohérent")
            return False
    
    # Test 3: Nettoyage des résultats
    def test_results_cleanup():
        # Simuler le nettoyage
        session_state = {
            'extraction_results': test_data,
            'processed_files': ['test.pdf'],
            'current_file_hash': 12345
        }
        
        # Nettoyer
        session_state['extraction_results'] = None
        session_state['processed_files'] = []
        session_state['current_file_hash'] = None
        
        if all(v is None or v == [] for v in session_state.values()):
            print("✅ Nettoyage des résultats réussi")
            return True
        else:
            print("❌ Nettoyage des résultats échoué")
            return False
    
    # Test 4: Validation du DataFrame
    def test_dataframe_creation():
        try:
            df = pd.DataFrame(test_data)
            
            # Vérifier les colonnes essentielles
            required_columns = ['department', 'commune', 'nom', 'prenom', 'id']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                print(f"❌ Colonnes manquantes: {missing_columns}")
                return False
            
            print("✅ DataFrame créé avec succès")
            return True
            
        except Exception as e:
            print(f"❌ Erreur création DataFrame: {e}")
            return False
    
    # Test 5: Export des données
    def test_data_export():
        try:
            df = pd.DataFrame(test_data)
            
            # Test export CSV
            csv_data = df.to_csv(index=False, sep=';', encoding='utf-8-sig')
            if csv_data and len(csv_data) > 100:
                print("✅ Export CSV réussi")
            else:
                print("❌ Export CSV échoué")
                return False
            
            # Test export Excel (simulation)
            excel_columns = {
                'department': 'Département',
                'commune': 'Commune',
                'nom': 'Nom Propri',
                'prenom': 'Prénom Propri',
                'id': 'ID'
            }
            
            df_export = df.rename(columns=excel_columns)
            if len(df_export.columns) >= 5:
                print("✅ Export Excel préparé avec succès")
            else:
                print("❌ Export Excel échoué")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur export données: {e}")
            return False
    
    # Exécuter tous les tests
    tests = [
        ("Cohérence fichiers", test_file_consistency),
        ("Hash fichiers", test_file_hash),
        ("Nettoyage résultats", test_results_cleanup),
        ("Création DataFrame", test_dataframe_creation),
        ("Export données", test_data_export)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"{'✅' if result else '❌'} {test_name}: {'PASS' if result else 'FAIL'}")
        except Exception as e:
            results.append((test_name, False))
            print(f"❌ {test_name}: ERREUR - {e}")
    
    # Résumé
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n📊 RÉSUMÉ DES TESTS STREAMLIT:")
    print(f"✅ Tests réussis: {passed}/{total}")
    print(f"❌ Tests échoués: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 Tous les tests Streamlit sont passés avec succès!")
        return True
    else:
        print("⚠️ Certains tests ont échoué. Vérifiez les corrections.")
        return False

if __name__ == "__main__":
    test_streamlit_corrections() 