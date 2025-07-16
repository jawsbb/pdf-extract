#!/usr/bin/env python3
"""
Test pour valider la fonction de nettoyage géographique appliquée.
"""

import sys
from pathlib import Path

# Import du module principal
try:
    from pdf_extractor import PDFPropertyExtractor
    print("OK Import reussi de pdf_extractor")
except ImportError as e:
    print(f"ERREUR d'import: {e}")
    sys.exit(1)

def test_nettoyage_geographique():
    """Test de la fonction clean_inconsistent_location_data avec cas réels"""
    
    print("\nTEST: Nettoyage des incohérences géographiques")
    print("=" * 50)
    
    extractor = PDFPropertyExtractor()
    
    # Simuler les données problématiques de l'utilisateur
    test_properties = [
        # 5 premières lignes - référence: 25-424 (majoritaire)
        {
            'departement': '25',
            'commune': '424', 
            'nom': 'COM COMMUNE DE HAUTEPIERRE LE CHATELET',
            'fichier_source': 'ZY6.pdf',
            'designation_parcelle': 'LES COMBES'
        },
        {
            'departement': '25',
            'commune': '424',
            'nom': 'COM COMMUNE DE HAUTEPIERRE LE CHATELET', 
            'fichier_source': 'ZY6.pdf',
            'designation_parcelle': 'LES COMBES'
        },
        {
            'departement': '25',
            'commune': '424',
            'nom': 'COM COMMUNE DE HAUTEPIERRE LE CHATELET',
            'fichier_source': 'ZY6.pdf', 
            'designation_parcelle': 'RIGOLE'
        },
        {
            'departement': '25',
            'commune': '424',
            'nom': 'COM COMMUNE DE HAUTEPIERRE LE CHATELET',
            'fichier_source': 'ZY6.pdf',
            'designation_parcelle': 'RIGOLE'
        },
        {
            'departement': '25',
            'commune': '424',
            'nom': 'COM COMMUNE DE HAUTEPIERRE LE CHATELET',
            'fichier_source': 'ZY6.pdf',
            'designation_parcelle': 'LES COMBES'
        },
        
        # Lignes incohérentes qui doivent être supprimées
        {
            'departement': '76',  # Différent !
            'commune': '302',     # Différent !
            'nom': 'ROUCHE',
            'fichier_source': 'ZY6.pdf',
            'designation_parcelle': 'LA LECHIERE'
        },
        {
            'departement': '76',
            'commune': '302', 
            'nom': 'ROUCHE',
            'fichier_source': 'ZY6.pdf',
            'designation_parcelle': 'TETE DE COMTOIS'
        },
        {
            'departement': '76',
            'commune': '302',
            'nom': 'ROUCHE', 
            'fichier_source': 'ZY6.pdf',
            'designation_parcelle': 'CHAMPS DE VAYE'
        }
    ]
    
    print(f"Données d'entrée: {len(test_properties)} lignes")
    print("  - Lignes 1-5: département=25, commune=424 (référence)")
    print("  - Lignes 6-8: département=76, commune=302 (incohérentes)")
    
    # Test de la fonction
    try:
        result = extractor.clean_inconsistent_location_data(test_properties, 'test.pdf')
        
        print(f"\nRésultat: {len(result)} lignes conservées")
        
        # Vérifications
        if len(result) == 5:
            print("✅ SUCCÈS: Bon nombre de lignes conservées (5/8)")
        else:
            print(f"❌ ÉCHEC: {len(result)} lignes conservées au lieu de 5")
            return False
            
        # Vérifier que seules les lignes cohérentes sont conservées
        all_25_424 = all(
            prop.get('departement') == '25' and prop.get('commune') == '424' 
            for prop in result
        )
        
        if all_25_424:
            print("✅ SUCCÈS: Toutes les lignes conservées ont département=25, commune=424")
        else:
            print("❌ ÉCHEC: Des lignes incohérentes ont été conservées")
            return False
            
        # Vérifier les noms conservés
        noms_conserves = [prop.get('nom', '') for prop in result]
        communes_uniquement = all('COM COMMUNE' in nom for nom in noms_conserves)
        
        if communes_uniquement:
            print("✅ SUCCÈS: Seules les lignes de la commune ont été conservées")
        else:
            print("❌ ÉCHEC: Des propriétaires incohérents ont été conservés")
            return False
            
        print("\n🎯 RÉSULTAT FINAL: Nettoyage géographique fonctionnel")
        return True
        
    except Exception as e:
        print(f"❌ ERREUR lors du test: {e}")
        return False

if __name__ == "__main__":
    success = test_nettoyage_geographique()
    print(f"\nStatut final: {'SUCCESS' if success else 'FAILED'}") 