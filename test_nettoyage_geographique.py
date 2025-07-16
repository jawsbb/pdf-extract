#!/usr/bin/env python3
"""
Test du nettoyage géographique - Fonction clean_inconsistent_location_data
"""
import logging
from pdf_extractor import PDFPropertyExtractor

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_clean_inconsistent_location_data():
    """Test de la fonction de nettoyage géographique"""
    
    # Créer une instance de l'extracteur
    extractor = PDFPropertyExtractor()
    
    # Données de test avec incohérences géographiques
    test_properties = [
        {
            'nom': 'MARTIN',
            'prenom': 'PIERRE',
            'department': '21',
            'commune': '026',
            'section': 'A',
            'numero': '123'
        },
        {
            'nom': 'DUPONT',
            'prenom': 'MARIE',
            'department': '21',
            'commune': '026',
            'section': 'B',
            'numero': '456'
        },
        {
            'nom': 'BERNARD',
            'prenom': 'PAUL',
            'department': '68',  # Département incohérent
            'commune': '057',    # Commune incohérente
            'section': 'C',
            'numero': '789'
        },
        {
            'nom': 'LECLERC',
            'prenom': 'SOPHIE',
            'department': '21',
            'commune': '026',
            'section': 'D',
            'numero': '101'
        }
    ]
    
    print("🧪 Test du nettoyage géographique")
    print("="*60)
    
    print("\n📋 Données avant nettoyage :")
    for i, prop in enumerate(test_properties):
        print(f"  {i+1}. {prop['nom']} {prop['prenom']} - {prop['department']}/{prop['commune']}")
    
    # Test de la fonction
    cleaned_properties = extractor.clean_inconsistent_location_data(test_properties, "test.pdf")
    
    print("\n📋 Données après nettoyage :")
    for i, prop in enumerate(cleaned_properties):
        print(f"  {i+1}. {prop['nom']} {prop['prenom']} - {prop['department']}/{prop['commune']}")
    
    # Vérification
    print("\n🔍 Vérification :")
    print(f"  - Propriétés avant : {len(test_properties)}")
    print(f"  - Propriétés après : {len(cleaned_properties)}")
    
    # Vérifier que seules les propriétés avec 21/026 sont gardées
    valid_count = 0
    for prop in cleaned_properties:
        if prop['department'] == '21' and prop['commune'] == '026':
            valid_count += 1
    
    print(f"  - Propriétés avec localisation cohérente : {valid_count}")
    
    if valid_count == len(cleaned_properties):
        print("✅ Test réussi : toutes les propriétés ont la localisation majoritaire")
    else:
        print("❌ Test échoué : des propriétés incohérentes subsistent")
    
    return len(cleaned_properties) == 3  # Doit garder 3 propriétés sur 4

def test_properties_without_location():
    """Test avec propriétés sans données géographiques"""
    
    extractor = PDFPropertyExtractor()
    
    test_properties = [
        {
            'nom': 'MARTIN',
            'prenom': 'PIERRE',
            'section': 'A',
            'numero': '123'
        },
        {
            'nom': 'DUPONT',
            'prenom': 'MARIE',
            'department': '',  # Vide
            'commune': '',     # Vide
            'section': 'B',
            'numero': '456'
        }
    ]
    
    print("\n🧪 Test avec propriétés sans données géographiques")
    print("="*60)
    
    cleaned_properties = extractor.clean_inconsistent_location_data(test_properties, "test_vide.pdf")
    
    print(f"  - Propriétés avant : {len(test_properties)}")
    print(f"  - Propriétés après : {len(cleaned_properties)}")
    
    # Doit garder toutes les propriétés car pas de données géographiques
    if len(cleaned_properties) == len(test_properties):
        print("✅ Test réussi : propriétés sans données géographiques conservées")
        return True
    else:
        print("❌ Test échoué : propriétés supprimées à tort")
        return False

def test_coherent_location():
    """Test avec localisation cohérente"""
    
    extractor = PDFPropertyExtractor()
    
    test_properties = [
        {
            'nom': 'MARTIN',
            'prenom': 'PIERRE',
            'department': '21',
            'commune': '026',
            'section': 'A',
            'numero': '123'
        },
        {
            'nom': 'DUPONT',
            'prenom': 'MARIE',
            'department': '21',
            'commune': '026',
            'section': 'B',
            'numero': '456'
        }
    ]
    
    print("\n🧪 Test avec localisation cohérente")
    print("="*60)
    
    cleaned_properties = extractor.clean_inconsistent_location_data(test_properties, "test_coherent.pdf")
    
    print(f"  - Propriétés avant : {len(test_properties)}")
    print(f"  - Propriétés après : {len(cleaned_properties)}")
    
    # Doit garder toutes les propriétés
    if len(cleaned_properties) == len(test_properties):
        print("✅ Test réussi : localisation cohérente, toutes les propriétés conservées")
        return True
    else:
        print("❌ Test échoué : propriétés supprimées à tort")
        return False

if __name__ == "__main__":
    print("🧪 TESTS DE NETTOYAGE GÉOGRAPHIQUE")
    print("="*80)
    
    # Exécuter les tests
    test1 = test_clean_inconsistent_location_data()
    test2 = test_properties_without_location()
    test3 = test_coherent_location()
    
    print("\n📊 RÉSULTATS DES TESTS")
    print("="*80)
    print(f"  - Test incohérences géographiques : {'✅ RÉUSSI' if test1 else '❌ ÉCHOUÉ'}")
    print(f"  - Test sans données géographiques : {'✅ RÉUSSI' if test2 else '❌ ÉCHOUÉ'}")
    print(f"  - Test localisation cohérente : {'✅ RÉUSSI' if test3 else '❌ ÉCHOUÉ'}")
    
    if all([test1, test2, test3]):
        print("\n🎉 TOUS LES TESTS RÉUSSIS ! La fonction de nettoyage géographique fonctionne correctement.")
    else:
        print("\n❌ CERTAINS TESTS ONT ÉCHOUÉ ! Vérifiez le code.") 