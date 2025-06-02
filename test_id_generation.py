# Test de la génération d'ID selon les spécifications
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pdf_extractor import PDFPropertyExtractor

def test_id_generation():
    extractor = PDFPropertyExtractor()
    
    # Tests selon les exemples fournis
    test_cases = [
        # (dept, commune, section, numero, expected_result)
        ("48", "000", "B", "77", "480000000B0077"),  # 48 + 000 + 0000B + 0077 = 14 caractères
        ("00", "000", "ZD", "5", "00000000ZD0005"),  # 00 + 000 + 000ZD + 0005 = 14 caractères
        ("00", "000", "C", "74", "000000000C0074"),  # 00 + 000 + 0000C + 0074 = 14 caractères  
        ("25", "227", "ZD", "5", "25227000ZD0005"),  # 25 + 227 + 000ZD + 0005 = 14 caractères (exemple officiel)
        ("51", "179", "ZY", "6", "51179000ZY0006"),  # 51 + 179 + 000ZY + 0006 = 14 caractères
        ("34", "049", "A", "123", "340490000A0123"),  # 34 + 049 + 0000A + 0123 = 14 caractères
    ]
    
    print("Test de génération d'ID - Format : Département(2) + Commune(3) + Section(5) + Numéro(4)")
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
        print()
    
    if all_passed:
        print("🎉 TOUS LES TESTS SONT PASSÉS !")
    else:
        print("⚠️  CERTAINS TESTS ONT ÉCHOUÉ")
    
    return all_passed

if __name__ == "__main__":
    test_id_generation() 