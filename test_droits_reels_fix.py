#!/usr/bin/env python3
"""
Test rapide pour vérifier la correction des droits réels.
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

def test_droit_reel_correction():
    """Test rapide de la correction des droits réels"""
    
    print("\nTEST: Correction des droits reels")
    print("-" * 40)
    
    extractor = PDFPropertyExtractor()
    
    # Test avec données simulées
    test_owner = {
        'nom': 'DUPONT',
        'prenom': 'Jean',
        'droit_reel': 'Proprietaire'  # Clé avec underscore
    }
    
    test_prop = {
        'numero': '123',
        'designation_parcelle': 'Test parcelle'
    }
    
    # Test de la fonction merge_like_make
    try:
        result = extractor.merge_like_make(test_owner, test_prop, 'TEST001', 'non_batie', 'test.pdf')
        
        print(f"Entree: droit_reel = '{test_owner['droit_reel']}'")
        print(f"Sortie: droit_reel = '{result['droit_reel']}'")
        
        if result['droit_reel'] == 'Proprietaire':
            print("RESULTAT: OK - Correction fonctionnelle")
            return True
        else:
            print("RESULTAT: ECHEC - Droit reel vide ou incorrect")
            return False
            
    except Exception as e:
        print(f"ERREUR lors du test: {e}")
        return False

if __name__ == "__main__":
    success = test_droit_reel_correction()
    print(f"\nStatut final: {'SUCCESS' if success else 'FAILED'}") 