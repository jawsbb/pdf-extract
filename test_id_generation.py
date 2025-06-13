# Test de la génération d'ID selon les spécifications CORRIGÉES - 14 CARACTÈRES
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pdf_extractor import PDFPropertyExtractor

def test_id_generation():
    extractor = PDFPropertyExtractor()
    
    # Tests selon les nouvelles spécifications - 14 CARACTÈRES
    test_cases = [
        # Format : DÉPARTEMENT(2) + COMMUNE(3) + SECTION(4) + PARCELLE(5) = 14 caractères
        # (dept, commune, section, numero, expected_result)
        ("25", "424", "302A", "90", "25424302A00090"),       # 25 + 424 + 302A + 00090 = 14 caractères
        ("25", "424", "302A", "131", "25424302A00131"),      # 25 + 424 + 302A + 00131 = 14 caractères
        ("25", "424", "302A", "146", "25424302A00146"),      # 25 + 424 + 302A + 00146 = 14 caractères
        ("48", "000", "B", "77", "48000000B00077"),          # 48 + 000 + 000B + 00077 = 14 caractères
        ("51", "179", "ZY", "6", "5117900ZY00006"),          # 51 + 179 + 00ZY + 00006 = 14 caractères
        ("34", "049", "A", "123", "34049000A00123"),         # 34 + 049 + 000A + 00123 = 14 caractères
        ("00", "000", "C", "74", "00000000C00074"),          # 00 + 000 + 000C + 00074 = 14 caractères
    ]
    
    print("Test de génération d'ID - FORMAT 14 CARACTÈRES")
    print("Format : DÉPARTEMENT(2) + COMMUNE(3) + SECTION(4) + PARCELLE(5) = 14 caractères")
    print("Section : garder complète (ex: 302A → 302A, B → 000B)")
    print("=" * 80)
    
    all_passed = True
    for dept, commune, section, numero, expected in test_cases:
        result = extractor.generate_unique_id(dept, commune, section, numero)
        status = "✅ OK" if result == expected else "❌ ERREUR"
        
        if result != expected:
            all_passed = False
        
        print(f"{status} | Dept:{dept} Comm:{commune} Sect:{section} Num:{numero}")
        print(f"      | Attendu : {expected} (longueur: {len(expected)})")
        print(f"      | Obtenu  : {result} (longueur: {len(result)})")
        
        # Analyse détaillée
        print(f"      | Analyse : DEPT({dept}) + COMM({commune}) + SECT({section}) + NUM({numero})")
        print()
    
    if all_passed:
        print("🎉 TOUS LES TESTS SONT PASSÉS !")
    else:
        print("⚠️  CERTAINS TESTS ONT ÉCHOUÉ")
    
    return all_passed

if __name__ == "__main__":
    test_id_generation() 