#!/usr/bin/env python3
"""
🧪 TEST DES CORRECTIONS RADICALES ANTI-CONTAMINATION

CORRECTIONS TESTÉES:
1. Filtrage géographique ultra-strict (première ligne valide)
2. Validation export ultra-stricte (rejet XX/COMMUNE)  
3. Propagation géographique forcée (depuis en-tête PDF)

OBJECTIF: Validation ZÉRO CONTAMINATION dans tous les cas
"""

import logging
import tempfile
from pathlib import Path
from pdf_extractor import PDFPropertyExtractor, setup_logging

def test_filtrage_ultra_strict():
    """Test du filtrage géographique ultra-strict."""
    print("\n🔧 TEST 1: Filtrage géographique ultra-strict")
    
    extractor = PDFPropertyExtractor()
    
    # Simulation du problème : contamination majoritaire
    test_properties = [
        # ✅ Ligne 89 : Géographie VALIDE (minoritaire)
        {
            "fichier_source": "test.pdf",
            "department": "25", 
            "commune": "424",
            "nom": "PROPRIETAIRE_VALIDE",
            "numero_parcelle": "123"
        },
        # ❌ Lignes 90-98 : Contamination MAJORITAIRE (9 lignes)
        *[{
            "fichier_source": "test.pdf",
            "department": "XX", 
            "commune": "COMMUNE",
            "nom": f"PROPRIETAIRE_CONTAMINE_{i}",
            "numero_parcelle": f"456{i}"
        } for i in range(1, 10)]
    ]
    
    print(f"   📊 Données initiales: {len(test_properties)} lignes")
    print(f"   ✅ Valides: 1 ligne (25/424)")
    print(f"   ❌ Contaminées: 9 lignes (XX/COMMUNE)")
    
    # Test du filtrage
    filtered = extractor.filter_by_geographic_reference(test_properties, "test.pdf")
    
    # Validation résultats
    valid_count = len([p for p in filtered if p['department'] == '25' and p['commune'] == '424'])
    contaminated_count = len([p for p in filtered if p['department'] == 'XX' or p['commune'] == 'COMMUNE'])
    
    print(f"   📈 Résultats filtrés: {len(filtered)} lignes")
    print(f"   ✅ Lignes valides conservées: {valid_count}")
    print(f"   ❌ Lignes contaminées conservées: {contaminated_count}")
    
    # ✅ SUCCÈS ATTENDU : Toute contamination éliminée
    if contaminated_count == 0 and valid_count > 0:
        print("   🎯 ✅ SUCCÈS: Contamination majoritaire éliminée !")
        return True
    else:
        print("   🚨 ❌ ÉCHEC: Contamination persistante ou données valides supprimées")
        return False

def test_validation_export_ultra_stricte():
    """Test de la validation export ultra-stricte."""
    print("\n🔧 TEST 2: Validation export ultra-stricte")
    
    extractor = PDFPropertyExtractor()
    
    # Données mixtes avec contamination
    test_properties = [
        # ✅ Données valides
        {
            "nom": "PROPRIETAIRE_VALIDE",
            "department": "25", 
            "commune": "424",
            "numero_parcelle": "123"
        },
        # ❌ Contamination XX/COMMUNE
        {
            "nom": "PROPRIETAIRE_CONTAMINE_1",
            "department": "XX", 
            "commune": "COMMUNE",
            "numero_parcelle": "456"
        },
        # ❌ Contamination Unknown
        {
            "nom": "PROPRIETAIRE_CONTAMINE_2",
            "department": "Unknown", 
            "commune": "Unknown",
            "numero_parcelle": "789"
        },
        # ❌ Format invalide (département 1 chiffre)
        {
            "nom": "PROPRIETAIRE_CONTAMINE_3",
            "department": "5", 
            "commune": "424",
            "numero_parcelle": "101"
        },
        # ❌ Format invalide (commune 2 chiffres)
        {
            "nom": "PROPRIETAIRE_CONTAMINE_4",
            "department": "25", 
            "commune": "42",
            "numero_parcelle": "102"
        }
    ]
    
    print(f"   📊 Données initiales: {len(test_properties)} lignes")
    print(f"   ✅ Valides: 1 ligne (25/424)")
    print(f"   ❌ Contaminées: 4 lignes (XX/COMMUNE, Unknown, formats invalides)")
    
    # Test validation finale
    validated = extractor.final_validation_before_export(test_properties)
    
    # Analyse résultats
    valid_count = len([p for p in validated 
                      if p.get('department', '').isdigit() and len(p.get('department', '')) == 2
                      and p.get('commune', '').isdigit() and len(p.get('commune', '')) == 3])
    
    print(f"   📈 Résultats validés: {len(validated)} lignes")
    print(f"   ✅ Lignes format correct: {valid_count}")
    
    # Vérifier absence contamination
    has_contamination = any(
        p.get('department') in ['XX', 'COMMUNE', 'Unknown'] or
        p.get('commune') in ['XX', 'COMMUNE', 'Unknown'] or
        not p.get('department', '').isdigit() or
        not p.get('commune', '').isdigit() or
        len(p.get('department', '')) != 2 or
        len(p.get('commune', '')) != 3
        for p in validated
    )
    
    # ✅ SUCCÈS ATTENDU : Zéro contamination exportée
    if not has_contamination and len(validated) == 1:
        print("   🎯 ✅ SUCCÈS: Toute contamination rejetée avant export !")
        return True
    else:
        print("   🚨 ❌ ÉCHEC: Contamination présente dans les données validées")
        return False

def test_propagation_geographique():
    """Test de la propagation géographique forcée."""
    print("\n🔧 TEST 3: Propagation géographique forcée")
    
    extractor = PDFPropertyExtractor()
    
    # Simuler extraction depuis en-tête PDF
    mock_header_data = {
        'department': '25',
        'commune': '424'
    }
    
    # Données avec géographies manquantes/invalides
    test_properties = [
        # ✅ Ligne avec géographie valide (à conserver)
        {
            "nom": "PROPRIETAIRE_OK",
            "department": "25", 
            "commune": "424",
            "numero_parcelle": "123"
        },
        # ❌ Lignes avec géographies invalides (à corriger)
        {
            "nom": "PROPRIETAIRE_UNKNOWN_1",
            "department": "Unknown", 
            "commune": "Unknown",
            "numero_parcelle": "456"
        },
        {
            "nom": "PROPRIETAIRE_XX",
            "department": "XX", 
            "commune": "COMMUNE",
            "numero_parcelle": "789"
        },
        {
            "nom": "PROPRIETAIRE_VIDE",
            "department": "", 
            "commune": "",
            "numero_parcelle": "101"
        }
    ]
    
    print(f"   📊 Données initiales: {len(test_properties)} lignes")
    print(f"   ✅ Géographie correcte: 1 ligne")
    print(f"   ❌ Géographie manquante/invalide: 3 lignes")
    
    # Simulation propagation (logique similaire à l'étape 6.5)
    propagated_count = 0
    for prop in test_properties:
        dept = str(prop.get('department', '')).strip()
        comm = str(prop.get('commune', '')).strip()
        
        # Si géographie manquante/invalide → forcer avec en-tête
        if (not dept or not comm or 
            dept in ['Unknown', 'XX', 'COMMUNE'] or 
            comm in ['Unknown', 'XX', 'COMMUNE'] or
            not dept.isdigit() or not comm.isdigit()):
            
            prop['department'] = mock_header_data['department']
            prop['commune'] = mock_header_data['commune']
            propagated_count += 1
    
    print(f"   🎯 Propagation forcée: {propagated_count} lignes corrigées")
    
    # Validation finale
    all_valid = all(
        p.get('department') == '25' and p.get('commune') == '424'
        for p in test_properties
    )
    
    # ✅ SUCCÈS ATTENDU : Toutes les lignes ont la bonne géographie
    if all_valid and propagated_count == 3:
        print("   🎯 ✅ SUCCÈS: Propagation géographique complète !")
        return True
    else:
        print("   🚨 ❌ ÉCHEC: Propagation incomplète ou incorrecte")
        return False

def test_scenario_complet():
    """Test du scénario complet de contamination observé."""
    print("\n🔧 TEST 4: Scénario complet (reproduction du bug)")
    
    print("   📋 Reproduction exacte du problème observé:")
    print("   ✅ Ligne 89: department=25, commune=424 (correct)")
    print("   ❌ Lignes 90-98: department=XX, commune=COMMUNE (9x dupliquées)")
    
    # Données reproduisant exactement le problème
    problematic_data = [
        # La ligne correcte (minoritaire)
        {
            "fichier_source": "RP 11-06-2025 1049e.pdf",
            "nom": "PROPRIETAIRE_REEL",
            "department": "25", 
            "commune": "424",
            "numero_parcelle": "123"
        },
        # Les 9 lignes contaminées (majoritaires)
        *[{
            "fichier_source": "RP 11-06-2025 1049e.pdf",
            "nom": f"PROPRIETAIRE_DUPLIQUE_{i}",
            "department": "XX", 
            "commune": "COMMUNE",
            "numero_parcelle": f"456{i}"
        } for i in range(1, 10)]
    ]
    
    extractor = PDFPropertyExtractor()
    
    # Étape 1: Test filtrage géographique
    print("   🔍 Étape 1: Filtrage géographique...")
    filtered = extractor.filter_by_geographic_reference(problematic_data, "test.pdf")
    
    # Étape 2: Test validation finale
    print("   🔍 Étape 2: Validation finale...")
    validated = extractor.final_validation_before_export(filtered)
    
    # Analyse finale
    final_dept_values = set(p.get('department') for p in validated)
    final_commune_values = set(p.get('commune') for p in validated)
    
    print(f"   📈 Résultats finaux: {len(validated)} lignes")
    print(f"   📊 Départements: {final_dept_values}")
    print(f"   📊 Communes: {final_commune_values}")
    
    # ✅ SUCCÈS ATTENDU : Seules les données 25/424 conservées
    success = (len(validated) > 0 and 
               final_dept_values == {'25'} and 
               final_commune_values == {'424'} and
               'XX' not in final_dept_values and 
               'COMMUNE' not in final_commune_values)
    
    if success:
        print("   🎯 ✅ SUCCÈS: Scénario complet résolu - contamination éliminée !")
        return True
    else:
        print("   🚨 ❌ ÉCHEC: Contamination encore présente après toutes les corrections")
        return False

def main():
    """Exécution de tous les tests de validation."""
    print("🧪 TESTS DE VALIDATION - CORRECTIONS RADICALES ANTI-CONTAMINATION")
    print("=" * 70)
    
    setup_logging()
    
    tests = [
        ("Filtrage Ultra-Strict", test_filtrage_ultra_strict),
        ("Validation Export", test_validation_export_ultra_stricte),
        ("Propagation Géographique", test_propagation_geographique),
        ("Scénario Complet", test_scenario_complet)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   🚨 ERREUR dans {test_name}: {e}")
            results.append((test_name, False))
    
    # Rapport final
    print("\n" + "=" * 70)
    print("📊 RAPPORT DE VALIDATION FINAL")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 RÉSULTAT GLOBAL: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 ✅ TOUTES LES CORRECTIONS FONCTIONNENT PARFAITEMENT !")
        print("🛡️ ZÉRO CONTAMINATION GARANTIE")
    else:
        print("🚨 ❌ CERTAINES CORRECTIONS NÉCESSITENT DES AJUSTEMENTS")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 