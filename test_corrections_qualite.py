#!/usr/bin/env python3
"""
Test des corrections de qualité pour les problèmes spécifiques identifiés
Valide les corrections sur les cas réels de l'utilisateur
"""

from pdf_extractor import PDFPropertyExtractor
import json

def test_contenance_parsing():
    """Test du parsing des contenances avec les formats français"""
    print("🧪 TEST PARSING CONTENANCES")
    print("=" * 30)
    
    extractor = PDFPropertyExtractor()
    
    # Cas de test basés sur les problèmes signalés
    test_cases = [
        # Format français avec espaces
        ("1 216,05", "1216", "Valeur française avec espace et virgule"),
        ("1 098", "1098", "Valeur avec espace (1098m²)"),
        ("10,98", "10", "Valeur décimale → partie entière"),
        
        # Cas déjà corrects
        ("87", "87", "Valeur simple"),
        ("90", "90", "Valeur simple"),
        ("33", "33", "Valeur simple"),
        
        # Cas limites
        ("", "", "Valeur vide"),
        ("N/A", "", "Valeur N/A"),
        ("10ha98a", "1098", "Format mixte ha/a"),
    ]
    
    all_passed = True
    for input_val, expected, description in test_cases:
        result = extractor.parse_contenance_value(input_val)
        status = "✅" if result == expected else "❌"
        if result != expected:
            all_passed = False
        print(f"  {status} '{input_val}' → '{result}' (attendu: '{expected}') - {description}")
    
    print(f"\n🎯 Résultat: {'SUCCÈS' if all_passed else 'ÉCHEC'} - Parsing contenances")
    return all_passed

def test_name_splitting():
    """Test de la séparation intelligente des noms"""
    print("\n🧪 TEST SÉPARATION NOMS/PRÉNOMS")
    print("=" * 35)
    
    extractor = PDFPropertyExtractor()
    
    # Cas de test basés sur les problèmes signalés  
    test_cases = [
        # Cas problématiques identifiés
        ("ALEXIS MOURADOFF", "ALEXIS", "MOURADOFF", "ALEXIS", "Prénom dupliqué"),
        ("MOURADOFF", "MONIQUE", "MOURADOFF", "MONIQUE", "Cas normal"),
        
        # Cas de noms composés
        ("MARIE CLAIRE MARTIN", "", "MARTIN", "MARIE CLAIRE", "Nom composé sans prénom"),
        ("PIERRE MARTIN", "", "MARTIN", "PIERRE", "Nom simple à séparer"),
        ("COMMUNE DE NOYER GOBAN", "", "COMMUNE DE NOYER GOBAN", "", "Personne morale"),
    ]
    
    all_passed = True
    for nom_input, prenom_input, nom_expected, prenom_expected, description in test_cases:
        nom_result, prenom_result = extractor.split_name_intelligently(nom_input, prenom_input)
        status = "✅" if (nom_result == nom_expected and prenom_result == prenom_expected) else "❌"
        if nom_result != nom_expected or prenom_result != prenom_expected:
            all_passed = False
        print(f"  {status} '{nom_input}' + '{prenom_input}' → '{nom_result}' + '{prenom_result}' - {description}")
        if status == "❌":
            print(f"      Attendu: '{nom_expected}' + '{prenom_expected}'")
    
    print(f"\n🎯 Résultat: {'SUCCÈS' if all_passed else 'ÉCHEC'} - Séparation noms")
    return all_passed

def test_address_cleaning():
    """Test du nettoyage des adresses"""
    print("\n🧪 TEST NETTOYAGE ADRESSES")
    print("=" * 28)
    
    extractor = PDFPropertyExtractor()
    
    test_cases = [
        ("2BRUE DES ANCIENNES ECOLES", "2BRUE DES ANCIENNES ECOLES", "Adresse normale"),
        ("1 RUE D AVAT", "1 RUE D AVAT", "Adresse avec apostrophe"),
        ("15 RUE DE LA PAIX", "15 RUE DE LA PAIX", "Adresse standard"),
        ("CONQUAND", "CONQUAND", "Lieu simple"),
        ("", "", "Adresse vide"),
        ("   ", "", "Espaces uniquement"),
    ]
    
    all_passed = True
    for input_addr, expected, description in test_cases:
        result = extractor.clean_address(input_addr)
        status = "✅" if result == expected else "❌"
        if result != expected:
            all_passed = False
        print(f"  {status} '{input_addr}' → '{result}' - {description}")
    
    print(f"\n🎯 Résultat: {'SUCCÈS' if all_passed else 'ÉCHEC'} - Nettoyage adresses")
    return all_passed

def test_deduplication():
    """Test de la déduplication stricte"""
    print("\n🧪 TEST DÉDUPLICATION STRICTE")
    print("=" * 30)
    
    extractor = PDFPropertyExtractor()
    
    # Simuler des données avec doublons basées sur les exemples utilisateur
    test_properties = [
        {
            'nom': 'MOURADOFF', 'prenom': 'MONIQUE', 'section': 'Y', 'numero': '13',
            'department': '51', 'commune': '208', 'numero_majic': 'MBDLJZ',
            'droit_reel': 'Usufruitier', 'fichier_source': 'Y 207.pdf'
        },
        {
            'nom': 'MOURADOFF', 'prenom': 'MONIQUE', 'section': 'Y', 'numero': '13',
            'department': '51', 'commune': '208', 'numero_majic': 'MBDLJZ',
            'droit_reel': 'Usufruitier', 'fichier_source': 'Y 13, 16, 17, 18.pdf'  # Doublon différent fichier
        },
        {
            'nom': 'ALEXIS MOURADOFF', 'prenom': 'ALEXIS', 'section': 'Y', 'numero': '13',
            'department': '51', 'commune': '208', 'numero_majic': 'MBWBBC',
            'droit_reel': 'Nu-propriétaire', 'fichier_source': 'Y 207.pdf'  # Différent droit réel
        }
    ]
    
    deduplicated = extractor.deduplicate_batch_results(test_properties)
    
    print(f"  Propriétés initiales: {len(test_properties)}")
    print(f"  Après déduplication: {len(deduplicated)}")
    
    # Vérifier que le doublon du même usufruitier a été supprimé
    usufruitiers = [p for p in deduplicated if p['droit_reel'] == 'Usufruitier']
    nu_proprietaires = [p for p in deduplicated if p['droit_reel'] == 'Nu-propriétaire']
    
    success = len(usufruitiers) == 1 and len(nu_proprietaires) == 1
    status = "✅" if success else "❌"
    
    print(f"  {status} Usufruitiers uniques: {len(usufruitiers)}")
    print(f"  {status} Nu-propriétaires uniques: {len(nu_proprietaires)}")
    
    print(f"\n🎯 Résultat: {'SUCCÈS' if success else 'ÉCHEC'} - Déduplication")
    return success

def test_integration_exemple_utilisateur():
    """Test d'intégration avec un exemple complet de l'utilisateur"""
    print("\n🧪 TEST INTÉGRATION EXEMPLE UTILISATEUR")
    print("=" * 40)
    
    extractor = PDFPropertyExtractor()
    
    # Simuler les données problématiques de l'utilisateur
    owner_data = {
        'nom': 'ALEXIS MOURADOFF',  # Nom fusionné avec prénom
        'prenom': 'ALEXIS',         # Prénom dupliqué
        'street_address': '2BRUE DES ANCIENNES ECOLES',
        'post_code': '33600',
        'city': 'PESSAC',
        'numero_proprietaire': 'MBWBBC',
        'department': '51',
        'commune': '208',
        'droit reel': 'Nu-propriétaire'
    }
    
    prop_data = {
        'Sec': 'Y',
        'N° Plan': '13',
        'Adresse': 'SUR LES NAUX REMEMBRES',
        'HA': '10',        # Problème : hectares incohérents  
        'A': '87',         # Ares
        'CA': '90'         # Centiares
    }
    
    # Test de la fusion corrigée
    merged = extractor.merge_like_make(owner_data, prop_data, "512080000Y0013", 'non_batie', 'Y 207.pdf')
    
    print("  Données après corrections:")
    print(f"    Nom: '{merged['nom']}' (avant: 'ALEXIS MOURADOFF')")
    print(f"    Prénom: '{merged['prenom']}' (avant: 'ALEXIS')")  
    print(f"    Section: '{merged['section']}'")
    print(f"    Contenance HA: '{merged['contenance_ha']}'")
    print(f"    Contenance A: '{merged['contenance_a']}'")
    print(f"    Contenance CA: '{merged['contenance_ca']}'")
    print(f"    Adresse: '{merged['voie']}'")
    
    # Vérifications
    checks = [
        (merged['nom'] == 'MOURADOFF', "Nom corrigé"),
        (merged['prenom'] == 'ALEXIS', "Prénom conservé"),
        (merged['contenance_ha'] == '10', "Contenance HA parsée"),
        (merged['contenance_a'] == '87', "Contenance A parsée"),
        (merged['contenance_ca'] == '90', "Contenance CA parsée"),
        (merged['voie'] != '', "Adresse présente")
    ]
    
    all_passed = all(check[0] for check in checks)
    
    for passed, description in checks:
        status = "✅" if passed else "❌"
        print(f"  {status} {description}")
    
    print(f"\n🎯 Résultat: {'SUCCÈS' if all_passed else 'ÉCHEC'} - Intégration complète")
    return all_passed

def main():
    """Exécute tous les tests de corrections de qualité"""
    print("🔧 TESTS DES CORRECTIONS DE QUALITÉ")
    print("=" * 50)
    
    tests = [
        test_contenance_parsing(),
        test_name_splitting(),
        test_address_cleaning(),
        test_deduplication(),
        test_integration_exemple_utilisateur()
    ]
    
    passed = sum(tests)
    total = len(tests)
    
    print("\n" + "=" * 50)
    print(f"📊 RÉSULTATS FINAUX: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 TOUTES LES CORRECTIONS FONCTIONNENT PARFAITEMENT!")
        print("✅ Vos données seront maintenant nettoyées automatiquement")
    else:
        print("⚠️ Certaines corrections nécessitent des ajustements")
    
    print("\n💡 Pour tester sur vos PDFs:")
    print("   python start.py")

if __name__ == "__main__":
    main() 