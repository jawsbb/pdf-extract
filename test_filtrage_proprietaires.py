#!/usr/bin/env python3
"""
Test spécifique pour le filtrage des propriétaires
Vérifie que les lieux-dits sont rejetés et les vrais propriétaires acceptés
"""

import logging
from pdf_extractor import PDFPropertyExtractor

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_filtrage_proprietaires():
    print("🧪 TEST FILTRAGE PROPRIÉTAIRES")
    print("=" * 40)
    
    extractor = PDFPropertyExtractor()
    
    # Cas de test basés sur vos données réelles
    test_cases = [
        # ✅ VRAIS PROPRIÉTAIRES (doivent passer)
        ("MOURADOFF", "MONIQUE", True),
        ("ALEXIS MOURADOFF", "ALEXIS", True),
        ("CAILLIETTE", "CLAUDE ADRIEN LEON", True),
        ("CAILLIETTE", "FRANCINE", True),
        ("CAILLIETTE", "AUDREY", True),
        ("DARTOIS", "MICHELINE", True),
        ("COMMUNE DE NOYER GOBAN", "", True),  # Personne morale
        
        # ❌ FAUX PROPRIÉTAIRES (doivent être rejetés)
        ("MONT DE NOIX", "", False),
        ("COTE DE MANDE", "", False),
        ("SUR LES NAUX REMEMBRES", "", False),
        ("LA RUE D EN HAUT", "", False),
        ("LE MONTANT DU NOYER GOBAIN", "", False),
        ("LA VALLEE DE LONGEVAS", "", False),
        ("VAL DE PUISEAU OUEST", "", False),
        ("GABOIS", "", False),
        ("LES PRINCESSES", "", False),
        ("LA RUEE DU PARC", "", False),
        ("COTAS MARECHAUX", "", False),
        ("VIEILLE RUE D AUXERRE", "", False),
        ("RENVERS DES FORETS", "", False),
        ("CHEMIN BLANC", "", False),
        ("MALVOISINE", "", False),
        ("HAM DE MALVOISINE", "", False),
    ]
    
    print("\n📋 RÉSULTATS DU FILTRAGE:")
    print("-" * 40)
    
    correct_predictions = 0
    total_tests = len(test_cases)
    
    for nom, prenom, expected in test_cases:
        result = extractor.is_likely_real_owner(nom, prenom)
        status = "✅" if result == expected else "❌"
        
        print(f"{status} {nom:30} | {prenom:15} | Prédit: {result:5} | Attendu: {expected}")
        
        if result == expected:
            correct_predictions += 1
    
    print("-" * 40)
    accuracy = correct_predictions / total_tests * 100
    print(f"🎯 PRÉCISION: {correct_predictions}/{total_tests} ({accuracy:.1f}%)")
    
    if accuracy >= 95:
        print("🏆 EXCELLENT! Le filtrage fonctionne parfaitement")
    elif accuracy >= 85:
        print("✅ BON! Le filtrage est satisfaisant")
    else:
        print("⚠️ ATTENTION! Le filtrage nécessite des ajustements")
    
    return accuracy

def test_personnes_morales_acceptance():
    """Test que les personnes morales sont bien acceptées."""
    logger.info("🧪 TEST: Acceptance des personnes morales")
    
    extractor = PDFPropertyExtractor()
    
    # Test des cas problématiques identifiés
    test_cases = [
        # Cas qui était rejeté
        {
            'nom': 'COM COMMUNE DE HAUTEPIERRE LE CHATELET',
            'prenom': '',
            'should_accept': True,
            'description': 'Commune avec préfixe COM'
        },
        # Autres cas de personnes morales
        {
            'nom': 'COMMUNE DE PARIS',
            'prenom': '',
            'should_accept': True,
            'description': 'Commune classique'
        },
        {
            'nom': 'VILLE DE LYON',
            'prenom': '',
            'should_accept': True,
            'description': 'Ville'
        },
        {
            'nom': 'ÉTAT FRANÇAIS',
            'prenom': '',
            'should_accept': True,
            'description': 'État'
        },
        {
            'nom': 'DÉPARTEMENT DU RHÔNE',
            'prenom': '',
            'should_accept': True,
            'description': 'Département'
        },
        {
            'nom': 'SCI IMMOBILIER MARTIN',
            'prenom': '',
            'should_accept': True,
            'description': 'SCI'
        },
        {
            'nom': 'SARL CONSTRUCTION DURAND',
            'prenom': '',
            'should_accept': True,
            'description': 'SARL'
        },
        # Cas qui doivent être rejetés (vraies adresses)
        {
            'nom': 'RUE DE LA PAIX',
            'prenom': '',
            'should_accept': False,
            'description': 'Vraie adresse'
        },
        {
            'nom': 'LIEU-DIT LES CHAMPS',
            'prenom': '',
            'should_accept': False,
            'description': 'Lieu-dit'
        },
        # Cas mixtes
        {
            'nom': 'MARTIN',
            'prenom': 'Jean',
            'should_accept': True,
            'description': 'Personne physique classique'
        }
    ]
    
    results = []
    for test_case in test_cases:
        nom = test_case['nom']
        prenom = test_case['prenom']
        expected = test_case['should_accept']
        description = test_case['description']
        
        result = extractor.is_likely_real_owner(nom, prenom)
        
        status = "✅ PASS" if result == expected else "❌ FAIL"
        logger.info(f"{status} | {description}: '{nom}' -> {result} (attendu: {expected})")
        
        results.append({
            'nom': nom,
            'description': description,
            'result': result,
            'expected': expected,
            'success': result == expected
        })
    
    # Résumé
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    
    logger.info(f"\n📊 RÉSUMÉ: {passed}/{total} tests réussis")
    
    if passed == total:
        logger.info("🎉 TOUS LES TESTS SONT RÉUSSIS!")
        return True
    else:
        logger.error("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        for result in results:
            if not result['success']:
                logger.error(f"   - {result['description']}: '{result['nom']}' -> {result['result']} (attendu: {result['expected']})")
        return False

def test_cas_specifique_hautepierre():
    """Test spécifique pour le cas HAUTEPIERRE qui était rejeté."""
    logger.info("🧪 TEST SPÉCIFIQUE: Cas HAUTEPIERRE")
    
    extractor = PDFPropertyExtractor()
    
    nom = 'COM COMMUNE DE HAUTEPIERRE LE CHATELET'
    prenom = ''
    
    # Test de la fonction principale
    result = extractor.is_likely_real_owner(nom, prenom)
    
    # Test des fonctions auxiliaires
    looks_like_address = extractor.looks_like_address(nom.upper())
    
    logger.info(f"Nom testé: {nom}")
    logger.info(f"is_likely_real_owner: {result}")
    logger.info(f"looks_like_address: {looks_like_address}")
    
    if result:
        logger.info("✅ SUCCÈS: La commune est maintenant acceptée!")
        return True
    else:
        logger.error("❌ ÉCHEC: La commune est encore rejetée")
        return False

if __name__ == "__main__":
    success1 = test_personnes_morales_acceptance()
    success2 = test_cas_specifique_hautepierre()
    
    if success1 and success2:
        print("\n🎉 TOUS LES TESTS SONT RÉUSSIS!")
        print("✅ Les personnes morales ne sont plus rejetées.")
    else:
        print("\n❌ CERTAINS TESTS ONT ÉCHOUÉ")
        exit(1) 