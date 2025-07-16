#!/usr/bin/env python3
"""
Test pour valider la correction des communes avec préfixe COM.
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour importer pdf_extractor
sys.path.append(str(Path(__file__).parent))

from pdf_extractor import PDFPropertyExtractor

def test_com_commune_detection():
    """Test la détection des communes avec préfixe COM"""
    
    print("TEST: Détection des communes avec préfixe COM")
    print("=" * 50)
    
    extractor = PDFPropertyExtractor()
    
    # Test des cas problématiques
    test_cases = [
        {
            'nom': 'COM COMMUNE DE HAUTEPIERRE LE CHATELET',
            'prenom': '',
            'expected_nom': 'COM COMMUNE DE HAUTEPIERRE LE CHATELET',
            'expected_prenom': '',
            'description': 'Commune avec préfixe COM'
        },
        {
            'nom': 'COMMUNE DE PARIS',
            'prenom': '',
            'expected_nom': 'COMMUNE DE PARIS',
            'expected_prenom': '',
            'description': 'Commune classique'
        },
        {
            'nom': 'MARTIN JEAN PAUL',
            'prenom': '',
            'expected_nom': 'MARTIN',
            'expected_prenom': 'JEAN PAUL',
            'description': 'Personne physique (doit être parsée)'
        }
    ]
    
    print("\n1. Test de la fonction split_name_intelligently:")
    print("-" * 50)
    
    all_passed = True
    
    for i, test in enumerate(test_cases, 1):
        nom_result, prenom_result = extractor.split_name_intelligently(test['nom'], test['prenom'])
        
        success = (nom_result == test['expected_nom'] and prenom_result == test['expected_prenom'])
        status = "OK" if success else "ERREUR"
        
        if not success:
            all_passed = False
        
        print(f"  {status} Test {i}: {test['description']}")
        print(f"      Entrée: nom='{test['nom']}' prenom='{test['prenom']}'")
        print(f"      Résultat: nom='{nom_result}' prenom='{prenom_result}'")
        print(f"      Attendu: nom='{test['expected_nom']}' prenom='{test['expected_prenom']}'")
        print()
    
    print("\n2. Test de la fonction is_likely_real_owner:")
    print("-" * 50)
    
    owner_test_cases = [
        ('COM COMMUNE DE HAUTEPIERRE LE CHATELET', '', True, 'Commune avec COM'),
        ('COMMUNE DE PARIS', '', True, 'Commune classique'),
        ('VILLE DE LYON', '', True, 'Ville'),
        ('MARTIN', 'Jean', True, 'Personne physique valide'),
        ('RUE DE LA PAIX', '', False, 'Adresse (doit être rejetée)')
    ]
    
    for nom, prenom, expected, description in owner_test_cases:
        result = extractor.is_likely_real_owner(nom, prenom)
        status = "OK" if result == expected else "ERREUR"
        
        if result != expected:
            all_passed = False
        
        print(f"  {status} {description}")
        print(f"      '{nom}' + '{prenom}' → {result} (attendu: {expected})")
        print()
    
    # Résumé
    print("=" * 50)
    if all_passed:
        print("RESULTAT: Tous les tests ont réussi !")
        print("La correction COM fonctionne correctement.")
    else:
        print("RESULTAT: Certains tests ont échoué.")
        print("Vérifier les corrections.")
    print("=" * 50)
    
    return all_passed

if __name__ == "__main__":
    test_com_commune_detection() 