#!/usr/bin/env python3
"""
Test simple du systeme adaptatif - sans emojis
"""

import os
import sys
from pathlib import Path
from pdf_extractor import PDFPropertyExtractor

def test_simple():
    """Test basique du nouveau systeme"""
    print("TEST SYSTEME ADAPTATIF MULTI-FORMAT")
    print("=" * 50)
    
    # Initialiser l'extracteur 
    extractor = PDFPropertyExtractor("input", "output")
    
    # Chercher des PDFs de test
    input_dir = Path("input")
    if not input_dir.exists():
        print("Erreur: Dossier 'input' introuvable")
        return
    
    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        print("Erreur: Aucun PDF trouve dans le dossier 'input'")
        print("Veuillez ajouter des PDFs cadastraux dans le dossier 'input'")
        return
    
    print(f"PDFs trouves: {len(pdf_files)}")
    
    # Tester le premier PDF
    test_pdf = pdf_files[0]
    print(f"Test avec: {test_pdf.name}")
    
    try:
        # Traitement avec le nouveau systeme adaptatif
        result = extractor.process_single_pdf(test_pdf)
        
        print(f"RESULTAT:")
        print(f"   Proprietes extraites: {len(result)}")
        
        if result:
            # Afficher le premier resultat
            first_prop = result[0]
            print(f"PREMIER PROPRIETAIRE:")
            for key, value in first_prop.items():
                if value:  # Afficher seulement les champs non vides
                    print(f"   {key}: {value}")
            
            # Compter les champs vides
            empty_fields = sum(1 for v in first_prop.values() if not v)
            total_fields = len(first_prop)
            completion_rate = ((total_fields - empty_fields) / total_fields) * 100
            
            print(f"TAUX DE COMPLETION: {completion_rate:.1f}%")
            print(f"   Remplis: {total_fields - empty_fields}/{total_fields}")
            print(f"   Vides: {empty_fields}/{total_fields}")
            
            if completion_rate > 80:
                print("EXCELLENT: Tres bonne extraction!")
            elif completion_rate > 60:
                print("BON: Extraction correcte")
            else:
                print("MOYEN: Extraction partielle")
    
    except Exception as e:
        print(f"ERREUR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple()