#!/usr/bin/env python3
"""
Test rapide du système adaptatif multi-format
"""

import os
import sys
from pathlib import Path
from pdf_extractor import PDFPropertyExtractor

def test_adaptatif():
    """Test du nouveau système adaptatif"""
    print("🧪 TEST SYSTÈME ADAPTATIF MULTI-FORMAT")
    print("=" * 50)
    
    # Initialiser l'extracteur
    api_key = os.getenv('OPENAI_API_KEY', 'demo_key')
    extractor = PDFPropertyExtractor("input", "output")
    
    # Chercher des PDFs de test
    input_dir = Path("input")
    if not input_dir.exists():
        print("❌ Dossier 'input' introuvable")
        return
    
    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        print("❌ Aucun PDF trouvé dans le dossier 'input'")
        return
    
    print(f"📄 {len(pdf_files)} PDF(s) trouvé(s)")
    
    # Tester le premier PDF
    test_pdf = pdf_files[0]
    print(f"\n🔍 Test avec: {test_pdf.name}")
    
    try:
        # Traitement avec le nouveau système adaptatif
        result = extractor.process_single_pdf(test_pdf)
        
        print(f"\n✅ RÉSULTAT:")
        print(f"   📊 {len(result)} propriété(s) extraite(s)")
        
        if result:
            # Afficher le premier résultat
            first_prop = result[0]
            print(f"\n📋 PREMIER PROPRIÉTAIRE:")
            for key, value in first_prop.items():
                if value:  # Afficher seulement les champs non vides
                    print(f"   {key}: {value}")
            
            # Compter les champs vides
            empty_fields = sum(1 for v in first_prop.values() if not v)
            total_fields = len(first_prop)
            completion_rate = ((total_fields - empty_fields) / total_fields) * 100
            
            print(f"\n📈 TAUX DE COMPLÉTION: {completion_rate:.1f}%")
            print(f"   ✅ Remplis: {total_fields - empty_fields}/{total_fields}")
            print(f"   ❌ Vides: {empty_fields}/{total_fields}")
    
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_adaptatif()