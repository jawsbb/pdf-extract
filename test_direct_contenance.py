#!/usr/bin/env python3
"""
Test direct pour vérifier les 3 colonnes contenance
"""

import tempfile
from pathlib import Path
from pdf_extractor import PDFPropertyExtractor

def test_direct_avec_upload():
    print("🧪 TEST DIRECT CONTENANCE")
    print("=" * 30)
    print("📋 Place ton PDF dans le dossier input/ et relance ce script")
    
    # Chercher PDFs
    input_files = list(Path("input").glob("*.pdf")) if Path("input").exists() else []
    
    if not input_files:
        print("❌ Aucun PDF trouvé dans input/")
        print("💡 Place un PDF dans le dossier input/ d'abord")
        return
    
    # Test avec le premier PDF
    pdf_path = input_files[0]
    print(f"📄 Test avec: {pdf_path.name}")
    
    extractor = PDFPropertyExtractor()
    
    # Traitement direct style Make  
    results = extractor.process_like_make(pdf_path)
    
    if not results:
        print("❌ Aucun résultat!")
        return
    
    print(f"\n✅ {len(results)} propriétés extraites")
    
    # Vérifier les nouvelles colonnes
    first_result = results[0]
    print("\n🔍 Colonnes contenance dans le premier résultat:")
    
    # Anciennes vs nouvelles colonnes
    old_cols = ['contenance']
    new_cols = ['contenance_ha', 'contenance_a', 'contenance_ca']
    
    print("\n📊 Vérification:")
    for col in old_cols:
        if col in first_result:
            print(f"   ❌ ANCIEN: {col} = '{first_result[col]}'")
    
    for col in new_cols:
        if col in first_result:
            print(f"   ✅ NOUVEAU: {col} = '{first_result[col]}'")
        else:
            print(f"   ❌ MANQUANT: {col}")
    
    # Export test
    print("\n💾 Test export CSV:")
    with tempfile.TemporaryDirectory() as temp_dir:
        extractor.output_dir = Path(temp_dir)
        csv_path = extractor.export_to_csv(results, "test_contenance.csv")
        
        # Lire l'en-tête CSV pour vérifier les colonnes
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            header = f.readline().strip()
            
        print(f"   📋 En-têtes CSV: {header}")
        
        if 'Contenance HA' in header:
            print("   ✅ Nouvelles colonnes présentes dans CSV!")
        else:
            print("   ❌ Anciennes colonnes dans CSV")

if __name__ == "__main__":
    test_direct_avec_upload() 