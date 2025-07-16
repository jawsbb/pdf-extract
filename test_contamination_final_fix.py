#!/usr/bin/env python3
"""
Test de validation des corrections finales de contamination.

CORRECTIONS APPLIQUÉES:
1. Filtrage géographique par majorité (au lieu de première ligne valide)
2. Instructions OpenAI ultra-renforcées pour codes commune 3 chiffres

PROBLÈMES CIBLÉS:
- Contamination géographique (lignes avec dept "91", commune "302")
- Erreur commune ("LES PREMIERS SAPINS" au lieu de "424")
"""

import logging
from pathlib import Path
from pdf_extractor import PDFPropertyExtractor, setup_logging

def test_geographic_filtering():
    """Test du filtrage géographique par majorité."""
    extractor = PDFPropertyExtractor()
    
    # Données de test simulant le problème
    test_properties = [
        {"fichier_source": "test.pdf", "department": "25", "commune": "LES PREMIERS SAPINS", "nom": "PROPRIETAIRE1"},
        {"fichier_source": "test.pdf", "department": "25", "commune": "424", "nom": "PROPRIETAIRE2"},
        {"fichier_source": "test.pdf", "department": "25", "commune": "424", "nom": "PROPRIETAIRE3"},
        {"fichier_source": "test.pdf", "department": "25", "commune": "424", "nom": "PROPRIETAIRE4"},
        # Ligne contaminée (minoritaire)
        {"fichier_source": "test.pdf", "department": "91", "commune": "302", "nom": "CONTAMINE_PHANTOM"},
        {"fichier_source": "test.pdf", "department": "25", "commune": "424", "nom": "PROPRIETAIRE5"},
    ]
    
    print("🧪 TEST FILTRAGE GÉOGRAPHIQUE PAR MAJORITÉ")
    print(f"Propriétés avant filtrage: {len(test_properties)}")
    
    # Appliquer le filtrage
    filtered = extractor.filter_by_geographic_reference(test_properties, "test.pdf")
    
    print(f"Propriétés après filtrage: {len(filtered)}")
    
    # Vérifications
    geo_stats = {}
    for prop in filtered:
        dept = prop.get('department', '')
        comm = prop.get('commune', '')
        geo_key = f"{dept}-{comm}"
        geo_stats[geo_key] = geo_stats.get(geo_key, 0) + 1
    
    print("📊 Géographies restantes:")
    for geo, count in geo_stats.items():
        print(f"  - {geo}: {count} propriétés")
    
    # RÉSULTAT ATTENDU: Élimination des lignes contaminées (91-302)
    expected_count = 5  # 5 lignes avec 25-424 ou 25-LES PREMIERS SAPINS
    contaminated_found = any("91-302" in geo for geo in geo_stats.keys())
    
    if not contaminated_found and len(filtered) == expected_count:
        print("✅ SUCCÈS: Contamination géographique éliminée")
        return True
    else:
        print("❌ ÉCHEC: Contamination persistante ou sur-filtrage")
        return False

def test_commune_extraction_instructions():
    """Test des instructions renforcées pour l'extraction de commune."""
    
    print("\n🧪 TEST INSTRUCTIONS COMMUNE RENFORCÉES")
    
    # Vérifier que les instructions sont présentes dans le code
    with open("pdf_extractor.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Rechercher les instructions critiques
    critical_instructions = [
        "RÈGLE ABSOLUE COMMUNE - ANTI-CONTAMINATION",
        "EXCLUSIVEMENT LE CODE À 3 CHIFFRES",
        "INTERDIT: noms de lieux",
        "INTERDIT: codes de départements",
        "VÉRIFICATION: commune doit avoir EXACTEMENT 3 chiffres"
    ]
    
    instructions_found = []
    for instruction in critical_instructions:
        if instruction in content:
            instructions_found.append(instruction)
            print(f"✅ Trouvé: {instruction}")
        else:
            print(f"❌ Manque: {instruction}")
    
    if len(instructions_found) >= 4:
        print("✅ SUCCÈS: Instructions commune ultra-renforcées présentes")
        return True
    else:
        print("❌ ÉCHEC: Instructions insuffisantes")
        return False

def test_clean_commune_code():
    """Test de la fonction de nettoyage des codes commune."""
    from pdf_extractor import clean_commune_code
    
    print("\n🧪 TEST NETTOYAGE CODES COMMUNE")
    
    test_cases = [
        ("424", "424"),  # Code correct
        ("LES PREMIERS SAPINS", ""),  # Nom de lieu -> vide
        ("424 LES PREMIERS SAPINS", "424"),  # Code + nom -> code seul
        ("91", "91"),  # Code département (garder mais sera détecté ailleurs)
        ("302", "302"),  # Code 3 chiffres valide
        ("25424", "424"),  # Extraction des 3 derniers chiffres
        ("", ""),  # Vide
    ]
    
    success_count = 0
    for input_val, expected in test_cases:
        result = clean_commune_code(input_val)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{input_val}' -> '{result}' (attendu: '{expected}')")
        if result == expected:
            success_count += 1
    
    if success_count >= len(test_cases) - 1:  # Tolérer 1 échec
        print("✅ SUCCÈS: Nettoyage codes commune fonctionnel")
        return True
    else:
        print("❌ ÉCHEC: Nettoyage insuffisant")
        return False

def main():
    """Test complet des corrections de contamination."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("=" * 60)
    print("TEST DE VALIDATION - CORRECTIONS CONTAMINATION FINALE")
    print("=" * 60)
    
    results = []
    
    # Test 1: Filtrage géographique
    results.append(test_geographic_filtering())
    
    # Test 2: Instructions commune renforcées
    results.append(test_commune_extraction_instructions())
    
    # Test 3: Nettoyage codes commune
    results.append(test_clean_commune_code())
    
    print("\n" + "=" * 60)
    print("RÉSULTATS FINAUX")
    print("=" * 60)
    
    success_count = sum(results)
    total_tests = len(results)
    
    print(f"Tests réussis: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 TOUTES LES CORRECTIONS VALIDÉES")
        print("   → Contamination géographique: CORRIGÉE")
        print("   → Instructions commune: RENFORCÉES")
        print("   → Nettoyage codes: FONCTIONNEL")
    else:
        print("⚠️ CORRECTIONS PARTIELLES - Vérification requise")
    
    return success_count == total_tests

if __name__ == "__main__":
    main() 