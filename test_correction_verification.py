#!/usr/bin/env python3
"""
Test de vérification de la correction de génération d'ID.
Vérifie que les sections avec un seul caractère ont bien le zéro en PREMIÈRE position.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pdf_extractor import PDFPropertyExtractor

def test_correction_verification():
    """Vérifie que la correction fonctionne selon les spécifications client"""
    print("🔧 VÉRIFICATION DE LA CORRECTION - GÉNÉRATION D'ID")
    print("Vérification : le 0 doit être en PREMIÈRE position pour les sections à un caractère")
    print("=" * 80)
    
    extractor = PDFPropertyExtractor()
    
    # Cas de test selon les spécifications client
    test_cases = [
        # (dept, commune, section, numero, prefixe, expected_id, description)
        ("25", "424", "A", "90", "", "254240000A0090", "Section A → 0A"),
        ("51", "179", "B", "6", "", "511790000B0006", "Section B → 0B"),  
        ("34", "049", "C", "123", "", "340490000C0123", "Section C → 0C"),
        ("25", "227", "ZC", "5", "", "25227000ZC0005", "Section ZC → ZC (déjà 2 car.)"),
        ("48", "000", "ZD", "77", "", "48000000ZD0077", "Section ZD → ZD (déjà 2 car.)"),
        # Cas avec préfixe
        ("25", "424", "A", "90", "302", "25424302A0090", "Avec préfixe 302, Section A → 0A"),
    ]
    
    print("📋 TESTS DE VÉRIFICATION :")
    all_passed = True
    
    for dept, commune, section, numero, prefixe, expected, description in test_cases:
        # Test avec le code corrigé
        result = extractor.generate_unique_id(dept, commune, section, numero, prefixe)
        status = "✅ OK" if result == expected else "❌ ERREUR"
        
        if result != expected:
            all_passed = False
        
        print(f"{status} {description}")
        print(f"      Input: Dept={dept}, Commune={commune}, Section={section}, Numero={numero}, Prefixe={prefixe}")
        print(f"      Attendu : {expected} (longueur: {len(expected)})")
        print(f"      Obtenu  : {result} (longueur: {len(result)})")
        
        if result != expected:
            print(f"      ❌ DIFFÉRENCE DÉTECTÉE!")
        
        # Analyser la composition
        if len(result) == 14:
            dept_part = result[0:2]
            comm_part = result[2:5] 
            pref_part = result[5:8]
            sect_part = result[8:10]
            num_part = result[10:14]
            print(f"      Composition: {dept_part}+{comm_part}+{pref_part}+{sect_part}+{num_part}")
            
            # Vérifier spécifiquement la section
            if len(section) == 1:
                expected_sect = f"0{section}"
                if sect_part == expected_sect:
                    print(f"      ✅ Section correcte: '{section}' → '{sect_part}'")
                else:
                    print(f"      ❌ Section incorrecte: '{section}' → '{sect_part}' (attendu: '{expected_sect}')")
        print()
    
    # Résumé final
    if all_passed:
        print("🎉 ✅ CORRECTION RÉUSSIE ! Toutes les sections sont correctement formatées.")
        print("✅ Les zéros de compensation sont bien placés AVANT les caractères.")
    else:
        print("⚠️ ❌ Des problèmes persistent dans la génération d'ID.")
    
    return all_passed

if __name__ == "__main__":
    test_correction_verification() 