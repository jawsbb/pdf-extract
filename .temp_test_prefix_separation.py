#!/usr/bin/env python3
"""
Test pour vérifier la séparation automatique des préfixes collés.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pdf_extractor import PDFPropertyExtractor

def test_prefix_separation():
    """Teste la séparation automatique des préfixes collés."""
    
    print("🔍 TEST DE SÉPARATION AUTOMATIQUE DES PRÉFIXES")
    print("=" * 60)
    
    extractor = PDFPropertyExtractor()
    
    # Cas de test avec préfixes collés
    test_properties = [
        # Cas 1: Préfixe numérique simple collé (302A)
        {
            'department': '25',
            'commune': '424',
            'prefixe': '',  # Vide pour l'instant
            'section': '302A',  # Préfixe collé
            'numero': '90',
            'nom': 'COMMUNE',
            'prenom': 'COM COM'
        },
        # Cas 2: Préfixe numérique double collé (302AB)
        {
            'department': '25',
            'commune': '424', 
            'prefixe': '',  # Vide pour l'instant
            'section': '302AB',  # Préfixe collé
            'numero': '2',
            'nom': 'COMMUNE',
            'prenom': 'COM COM'
        },
        # Cas 3: Préfixe avec zéros (001ZD)
        {
            'department': '51',
            'commune': '179',
            'prefixe': '',  # Vide pour l'instant
            'section': '001ZD',  # Préfixe collé
            'numero': '5',
            'nom': 'LAMBIN',
            'prenom': 'DIDIER'
        },
        # Cas 4: Section normale sans préfixe (A)
        {
            'department': '25',
            'commune': '227',
            'prefixe': '',
            'section': 'A',  # Pas de préfixe collé
            'numero': '123',
            'nom': 'MARTIN',
            'prenom': 'PIERRE'
        },
        # Cas 5: Préfixe déjà présent (ne pas toucher)
        {
            'department': '25',
            'commune': '227',
            'prefixe': 'ZY',  # Déjà présent
            'section': '000ZD',  # Ne pas toucher
            'numero': '5',
            'nom': 'DUPONT',
            'prenom': 'MARIE'
        }
    ]
    
    print("📋 DONNÉES DE TEST AVANT SÉPARATION:")
    for i, prop in enumerate(test_properties):
        print(f"   {i+1}. Section='{prop['section']}' Préfixe='{prop['prefixe']}'")
    
    # Appliquer la séparation automatique
    result_properties = extractor.separate_stuck_prefixes(test_properties)
    
    print("\n📊 RÉSULTATS APRÈS SÉPARATION:")
    success_count = 0
    
    expected_results = [
        {'prefixe': '302', 'section': 'A'},  # Cas 1
        {'prefixe': '302', 'section': 'AB'}, # Cas 2  
        {'prefixe': '001', 'section': 'ZD'}, # Cas 3
        {'prefixe': '', 'section': 'A'},     # Cas 4 (inchangé)
        {'prefixe': 'ZY', 'section': '000ZD'} # Cas 5 (inchangé)
    ]
    
    for i, (result, expected) in enumerate(zip(result_properties, expected_results)):
        prefixe = result.get('prefixe', '')
        section = result.get('section', '')
        expected_prefixe = expected['prefixe']
        expected_section = expected['section']
        
        status = "✅" if (prefixe == expected_prefixe and section == expected_section) else "❌"
        
        if status == "✅":
            success_count += 1
            
        print(f"   {status} Cas {i+1}: Section='{section}' Préfixe='{prefixe}' (attendu: '{expected_section}'/'{expected_prefixe}')")
    
    print(f"\n📊 RÉSULTAT GLOBAL: {success_count}/{len(expected_results)} cas réussis")
    
    if success_count == len(expected_results):
        print("🎉 ✅ SÉPARATION AUTOMATIQUE FONCTIONNE PARFAITEMENT !")
        return True
    else:
        print("⚠️ ❌ Certains cas de séparation ont échoué")
        return False

if __name__ == "__main__":
    success = test_prefix_separation()
    if success:
        print("\n🎯 CONCLUSION: Système prêt à séparer les préfixes collés automatiquement ! ✅")
    else:
        print("\n⚠️ CONCLUSION: Séparation automatique À CORRIGER ❌")