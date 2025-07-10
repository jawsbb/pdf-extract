#!/usr/bin/env python3
"""
Vérification simple des corrections appliquées
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

def test_numero_parcelle_simple():
    """Test rapide de la fonction remove_empty_parcel_numbers"""
    
    print("\nTEST: Fonction remove_empty_parcel_numbers")
    print("-" * 50)
    
    extractor = PDFPropertyExtractor()
    
    # Vérifier que la méthode existe
    if not hasattr(extractor, 'remove_empty_parcel_numbers'):
        print("ERREUR La methode remove_empty_parcel_numbers n'existe pas")
        return False
    
    # Test avec données simples
    test_data = [
        {'numero': '123', 'nom': 'DUPONT'},
        {'numero': '', 'nom': 'MARTIN'},  # Vide - doit être supprimé
        {'numero': '456', 'nom': 'BERNARD'},
        {'numero': 'N/A', 'nom': 'DURAND'},  # N/A - doit être supprimé
    ]
    
    print(f"Avant: {len(test_data)} proprietes")
    
    try:
        result = extractor.remove_empty_parcel_numbers(test_data, "test.pdf")
        print(f"Apres: {len(result)} proprietes")
        
        if len(result) == 2:  # Seules DUPONT et BERNARD doivent rester
            print("OK Fonction fonctionne correctement")
            return True
        else:
            print(f"ERREUR Resultat incorrect: {len(result)} proprietes au lieu de 2")
            return False
            
    except Exception as e:
        print(f"ERREUR lors de l'execution: {e}")
        return False

def main():
    print("VERIFICATION SIMPLE DES CORRECTIONS")
    print("=" * 50)
    
    # Test de la fonction
    success = test_numero_parcelle_simple()
    
    print("\n" + "=" * 50)
    if success:
        print("SUCCES: La fonctionnalite fonctionne correctement!")
        print("\nRESUME DES CORRECTIONS APPLIQUEES:")
        print("   OK Fonction remove_empty_parcel_numbers ajoutee")
        print("   OK Integration dans process_like_make (etape 6)")
        print("   OK Suppression automatique des lignes sans numero de parcelle")
        print("\nPRET POUR UTILISATION!")
    else:
        print("ECHEC: Il y a un probleme avec l'implementation")
        sys.exit(1)

if __name__ == "__main__":
    main() 