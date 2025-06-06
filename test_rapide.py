#!/usr/bin/env python3
"""
Test rapide pour voir immédiatement le problème
"""

import os
import sys
from pathlib import Path

def test_immediat():
    print("🚀 TEST IMMEDIAT")
    print("=" * 20)
    
    # 1. API Key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Pas d'API Key OpenAI")
        print("   export OPENAI_API_KEY='sk-...'")
        return
    print("✅ API Key présente")
    
    # 2. PDF
    pdfs = list(Path("input").glob("*.pdf")) if Path("input").exists() else []
    if not pdfs:
        print("❌ Pas de PDF dans input/")
        print("   Mets un PDF dans le dossier 'input/'")
        return
    print(f"✅ PDF: {pdfs[0].name}")
    
    # 3. Import
    try:
        from pdf_extractor import PDFPropertyExtractor
        print("✅ Import OK")
    except Exception as e:
        print(f"❌ Import échoué: {e}")
        return
    
    # 4. Test minimal
    try:
        extractor = PDFPropertyExtractor()
        print("✅ Extracteur créé")
        
        # Test une seule méthode
        print(f"\n🧪 Test sur {pdfs[0].name}:")
        
        # Test pdfplumber seulement
        tables = extractor.extract_tables_with_pdfplumber(pdfs[0])
        batie = len(tables.get('prop_batie', []))
        non_batie = len(tables.get('non_batie', []))
        print(f"   📋 Tables: {batie} bâties, {non_batie} non-bâties")
        
        if batie == 0 and non_batie == 0:
            print("   ❌ pdfplumber ne trouve rien")
            print("   💡 Ton PDF est probablement scanné (image)")
            print("   💡 Ou format non standard")
            
            # Fallback simple
            print("\n🆘 Test OpenAI direct:")
            result = extractor.process_single_pdf(pdfs[0])
            print(f"   🎯 Méthode classique: {len(result)} propriétés")
            
        else:
            print("   ✅ pdfplumber trouve des tableaux")
            print("   🔄 Test OpenAI...")
            
            owners = extractor.extract_owners_make_style(pdfs[0])
            print(f"   👤 OpenAI: {len(owners)} propriétaires")
            
            if owners:
                print("   ✅ OpenAI fonctionne")
                print("   🔄 Test complet Make...")
                
                result = extractor.process_like_make(pdfs[0])
                print(f"   🎯 Make complet: {len(result)} propriétés")
                
                if result:
                    print("   🎉 SUCCÈS TOTAL!")
                else:
                    print("   ❌ Échec fusion Make")
            else:
                print("   ❌ OpenAI ne trouve pas de propriétaires")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_immediat() 