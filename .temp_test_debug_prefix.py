#!/usr/bin/env python3
"""
Test de diagnostic pour voir exactement ce qui se passe avec la séparation des préfixes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pdf_extractor import PDFPropertyExtractor

def test_debug_prefix():
    """Test de diagnostic pour voir exactement ce qui se passe"""
    
    print("🔍 TEST DE DIAGNOSTIC - SÉPARATION DES PRÉFIXES")
    print("=" * 60)
    
    extractor = PDFPropertyExtractor()
    
    # Simuler les données que vous voyez dans vos résultats
    test_data = [
        {
            'section': '302A',
            'prefixe': '',
            'department': '25',
            'commune': '227',
            'numero': '90',
            'nom': 'TEST'
        },
        {
            'section': '302AB', 
            'prefixe': '',
            'department': '25',
            'commune': '227',
            'numero': '91',
            'nom': 'TEST2'
        },
        {
            'section': '001ZD', 
            'prefixe': '',
            'department': '25',
            'commune': '227',
            'numero': '92',
            'nom': 'TEST3'
        },
        {
            'section': 'ZB',  # Test sans préfixe collé
            'prefixe': '',
            'department': '25',
            'commune': '227',
            'numero': '93',
            'nom': 'TEST4'
        }
    ]
    
    print("🔍 DONNÉES AVANT TRAITEMENT:")
    for i, item in enumerate(test_data):
        print(f"  {i+1}. section='{item['section']}', prefixe='{item['prefixe']}'")
    
    print("\n🔧 TRAITEMENT...")
    result = extractor.separate_stuck_prefixes(test_data)
    
    print("\n✅ DONNÉES APRÈS TRAITEMENT:")
    for i, item in enumerate(result):
        print(f"  {i+1}. section='{item['section']}', prefixe='{item['prefixe']}'")
    
    print("\n📊 RÉSUMÉ:")
    changes = 0
    for i, (before, after) in enumerate(zip(test_data, result)):
        if before['section'] != after['section'] or before['prefixe'] != after['prefixe']:
            changes += 1
            print(f"  ✂️ Changement {i+1}: '{before['section']}' → section='{after['section']}', prefixe='{after['prefixe']}'")
    
    if changes == 0:
        print("  ❌ Aucun changement détecté - Il y a un problème !")
    else:
        print(f"  ✅ {changes} changement(s) détecté(s)")
    
    return result

if __name__ == "__main__":
    test_debug_prefix()