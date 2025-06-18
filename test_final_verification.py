#!/usr/bin/env python3
"""
Test final de vérification de la correction de génération d'ID.
Vérifie tous les cas selon les spécifications exactes du client.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pdf_extractor import PDFPropertyExtractor

def test_final_verification():
    """Test final selon les spécifications exactes du client"""
    print("🎯 TEST FINAL - GÉNÉRATION D'ID SELON SPÉCIFICATIONS CLIENT")
    print("Format : DÉPARTEMENT(2) + COMMUNE(3) + PRÉFIXE(3) + SECTION(2) + NUMÉRO(4) = 14 caractères")
    print("RÈGLE : Zéros de compensation AVANT les caractères renseignés")
    print("=" * 90)
    
    extractor = PDFPropertyExtractor()
    
    # Cas de test exhaustifs selon les spécifications client
    test_cases = [
        # (dept, commune, prefixe, section, numero, expected_id, description)
        
        # 🔧 CAS PROBLÉMATIQUES RAPPORTÉS PAR LE CLIENT
        ("25", "424", "", "A", "90", "254240000A0090", "Section A → 0A (CORRECTION PRINCIPALE)"),
        ("51", "179", "", "B", "6", "511790000B0006", "Section B → 0B"),  
        ("34", "049", "", "C", "123", "340490000C0123", "Section C → 0C"),
        
        # ✅ CAS DÉJÀ CORRECTS (2 caractères)
        ("25", "227", "", "ZC", "5", "25227000ZC0005", "Section ZC → ZC (déjà 2 caractères)"),
        ("48", "000", "", "ZD", "77", "48000000ZD0077", "Section ZD → ZD (déjà 2 caractères)"),
        
        # 🔢 CAS AVEC PRÉFIXES
        ("25", "424", "302", "A", "90", "25424302A0090", "Avec préfixe 302, Section A → 0A"),
        ("51", "179", "001", "ZY", "6", "51179001ZY0006", "Avec préfixe 001, Section ZY → ZY"),
        
        # 📏 CAS LIMITES
        ("01", "001", "000", "A", "1", "010010000A0001", "Valeurs minimales"),
        ("99", "999", "999", "ZZ", "9999", "99999999ZZ9999", "Valeurs maximales"),
        
        # 🔄 CAS DE DÉPASSEMENT
        ("123", "4567", "890", "ABC", "12345", "23567890BC2345", "Troncature si dépassement"),
    ]
    
    print("📋 TESTS EXHAUSTIFS :")
    all_passed = True
    
    for dept, commune, prefixe, section, numero, expected, description in test_cases:
        # Test avec le code corrigé
        result = extractor.generate_unique_id(dept, commune, section, numero, prefixe)
        status = "✅ OK" if result == expected else "❌ ERREUR"
        
        if result != expected:
            all_passed = False
        
        print(f"{status} {description}")
        print(f"      Input: Dept={dept}, Commune={commune}, Préfixe={prefixe}, Section={section}, Numero={numero}")
        print(f"      Attendu : {expected} (longueur: {len(expected)})")
        print(f"      Obtenu  : {result} (longueur: {len(result)})")
        
        if result != expected:
            print(f"      ❌ DIFFÉRENCE DÉTECTÉE!")
        
        # Analyser la composition détaillée
        if len(result) == 14:
            dept_part = result[0:2]
            comm_part = result[2:5] 
            pref_part = result[5:8]
            sect_part = result[8:10]
            num_part = result[10:14]
            print(f"      Composition: {dept_part}+{comm_part}+{pref_part}+{sect_part}+{num_part}")
            
            # Vérifications spécifiques
            checks = []
            if len(section) == 1:
                expected_sect = f"0{section}"
                if sect_part == expected_sect:
                    checks.append(f"✅ Section '{section}' → '{sect_part}' (zéro AVANT)")
                else:
                    checks.append(f"❌ Section '{section}' → '{sect_part}' (attendu: '{expected_sect}')")
            
            if len(prefixe or "000") <= 3:
                expected_pref = (prefixe or "000").zfill(3)
                if pref_part == expected_pref:
                    checks.append(f"✅ Préfixe '{prefixe}' → '{pref_part}'")
                else:
                    checks.append(f"❌ Préfixe '{prefixe}' → '{pref_part}' (attendu: '{expected_pref}')")
            
            for check in checks:
                print(f"      {check}")
        print()
    
    # 🎯 VÉRIFICATION SPÉCIALE : Cas rapportés par le client
    print("🔍 VÉRIFICATION SPÉCIALE - CAS RAPPORTÉS PAR LE CLIENT :")
    client_cases = [
        ("25", "424", "", "A", "90", "Section A doit donner 0A (pas A0)"),
        ("51", "179", "", "B", "6", "Section B doit donner 0B (pas B0)"),
    ]
    
    for dept, commune, prefixe, section, numero, description in client_cases:
        result = extractor.generate_unique_id(dept, commune, section, numero, prefixe)
        sect_part = result[8:10]  # Position de la section dans l'ID
        
        if section == "A" and sect_part == "0A":
            print(f"      ✅ {description} → CORRIGÉ !")
        elif section == "B" and sect_part == "0B":
            print(f"      ✅ {description} → CORRIGÉ !")
        else:
            print(f"      ❌ {description} → PROBLÈME PERSISTANT")
            all_passed = False
    
    # Résumé final
    print("\n" + "=" * 90)
    if all_passed:
        print("🎉 ✅ CORRECTION PARFAITEMENT RÉUSSIE !")
        print("✅ Toutes les sections avec un seul caractère ont le zéro en PREMIÈRE position")
        print("✅ Le format DEPT(2)+COMM(3)+PRÉFIXE(3)+SECTION(2)+NUMÉRO(4) = 14 caractères est respecté")
        print("✅ Le problème rapporté par le client est RÉSOLU")
    else:
        print("⚠️ ❌ Des problèmes persistent - Vérification nécessaire")
    
    return all_passed

if __name__ == "__main__":
    test_final_verification() 