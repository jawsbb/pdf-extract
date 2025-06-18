#!/usr/bin/env python3
"""
Test de correction du formatage des sections selon les nouvelles spécifications client.
Format : DÉPARTEMENT(2) + COMMUNE(3) + PRÉFIXE(3) + SECTION(2) + NUMÉRO(4) = 14 caractères
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pdf_extractor import PDFPropertyExtractor

def test_current_id_format():
    """Test le format actuel pour identifier le problème"""
    print("🔍 TEST DU PROBLÈME ACTUEL - SECTIONS À UN CARACTÈRE")
    print("Problème rapporté : le 0 doit être en PREMIÈRE position, pas en seconde")
    print("=" * 70)
    
    extractor = PDFPropertyExtractor()
    
    # Cas problématiques rapportés par le client
    test_cases = [
        # (dept, commune, section, numero, description)
        ("25", "424", "A", "90", "Section A → devrait être 0A (pas A0)"),
        ("51", "179", "B", "6", "Section B → devrait être 0B (pas B0)"),
        ("34", "049", "C", "123", "Section C → devrait être 0C (pas C0)"),
        ("25", "227", "ZC", "5", "Section ZC → devrait rester ZC"),
        ("48", "000", "ZD", "77", "Section ZD → devrait rester ZD"),
    ]
    
    print("📋 TESTS AVEC LE CODE ACTUEL :")
    for dept, commune, section, numero, description in test_cases:
        # Test avec le code actuel
        result = extractor.generate_unique_id(dept, commune, section, numero)
        
        print(f"   {description}")
        print(f"   Input: Dept={dept}, Commune={commune}, Section={section}, Numero={numero}")
        print(f"   Résultat actuel: {result} (longueur: {len(result)})")
        
        # Analyser le problème
        if len(section) == 1:
            # Extraire la partie section de l'ID (positions 5-8 dans l'ancien format)
            if len(result) == 14:
                id_section = result[5:9]  # Ancien format avec section sur 4 caractères
                print(f"   Section dans ID: '{id_section}' ← PROBLÈME DÉTECTÉ")
            else:
                print(f"   ⚠️ Longueur ID incorrecte: {len(result)}")
        print()
    
    return True

def test_corrected_format():
    """Test le format corrigé selon les spécifications client"""
    print("\n🎯 FORMAT CORRIGÉ SELON SPÉCIFICATIONS CLIENT")
    print("Format : DEPT(2) + COMM(3) + PRÉFIXE(3) + SECTION(2) + NUMÉRO(4) = 14 caractères")
    print("RÈGLE : Zéros de compensation AVANT les caractères (0A, pas A0)")
    print("=" * 70)
    
    # Cas attendus selon les spécifications
    expected_cases = [
        # (dept, commune, prefixe, section, numero, expected_id)
        ("25", "424", "000", "A", "90", "254240000A0090"),   # Section A → 0A
        ("51", "179", "000", "B", "6", "511790000B0006"),     # Section B → 0B  
        ("34", "049", "000", "C", "123", "340490000C0123"),   # Section C → 0C
        ("25", "227", "000", "ZC", "5", "25227000ZC0005"),    # Section ZC (déjà 2 car.)
        ("48", "000", "000", "ZD", "77", "48000000ZD0077"),   # Section ZD (déjà 2 car.)
    ]
    
    print("📋 RÉSULTATS ATTENDUS :")
    for dept, commune, prefixe, section, numero, expected in expected_cases:
        print(f"   Dept={dept}, Commune={commune}, Préfixe={prefixe}, Section={section}, Numero={numero}")
        print(f"   → ID attendu: {expected}")
        
        # Vérifier la composition
        expected_dept = dept.zfill(2)
        expected_comm = commune.zfill(3) 
        expected_pref = prefixe.zfill(3)
        expected_sect = section if len(section) == 2 else f"0{section}"
        expected_num = numero.zfill(4)
        
        composed = f"{expected_dept}{expected_comm}{expected_pref}{expected_sect}{expected_num}"
        status = "✅" if composed == expected else "❌"
        print(f"   Composition: {expected_dept}+{expected_comm}+{expected_pref}+{expected_sect}+{expected_num} = {composed} {status}")
        print()

if __name__ == "__main__":
    test_current_id_format()
    test_corrected_format() 