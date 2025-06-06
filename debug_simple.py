#!/usr/bin/env python3
"""
Debug ultra simple pour identifier le problème Make
"""

import os
from pathlib import Path
from pdf_extractor import PDFPropertyExtractor

def debug_rapide():
    """Test rapide pour voir ce qui ne marche pas"""
    
    print("🔧 DEBUG RAPIDE")
    print("=" * 30)
    
    # Vérifier API
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY manquante")
        print("💡 Ajoute: export OPENAI_API_KEY='ta-clé-ici'")
        return
    
    print("✅ API Key OK")
    
    # Chercher PDF
    input_dir = Path("input")
    pdfs = list(input_dir.glob("*.pdf")) if input_dir.exists() else []
    
    if not pdfs:
        print("❌ Aucun PDF dans input/")
        print("💡 Mets un PDF dans le dossier 'input/'")
        return
    
    print(f"✅ PDF trouvé: {pdfs[0].name}")
    
    # Test simple
    extractor = PDFPropertyExtractor()
    
    print("\n🧪 TEST EXTRACTION:")
    print("-" * 20)
    
    try:
        result = extractor.process_like_make(pdfs[0])
        print(f"🎯 Résultat: {len(result)} propriétés")
        
        if result:
            print(f"✅ Première propriété trouvée!")
            print(f"   Nom: {result[0].get('nom', 'vide')}")
            print(f"   Section: {result[0].get('section', 'vide')}")
            print(f"   Commune: {result[0].get('commune', 'vide')}")
        else:
            print("❌ Aucune propriété extraite")
            print("\n🔍 TESTS DÉTAILLÉS:")
            
            # Test pdfplumber
            tables = extractor.extract_tables_with_pdfplumber(pdfs[0])
            print(f"   📋 pdfplumber: {len(tables.get('prop_batie', []))} bâtis, {len(tables.get('non_batie', []))} non-bâtis")
            
            # Test OpenAI
            owners = extractor.extract_owners_make_style(pdfs[0])
            print(f"   👤 OpenAI: {len(owners)} propriétaires")
            
            if not tables.get('prop_batie') and not tables.get('non_batie'):
                print("   ❌ pdfplumber ne trouve pas de tableaux")
                print("   💡 PDF peut-être scanné ou format non standard")
                
            if not owners:
                print("   ❌ OpenAI ne trouve pas de propriétaires")
                print("   💡 Vérifie que les noms sont visibles dans le PDF")
                
    except Exception as e:
        print(f"❌ Erreur: {e}")
        print("💡 Vérifie les logs pour plus de détails")

if __name__ == "__main__":
    debug_rapide() 