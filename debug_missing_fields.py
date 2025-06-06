#!/usr/bin/env python3
"""
Debug des champs manquants dans l'extraction Make
"""

import os
import sys
from pathlib import Path
from pdf_extractor import PDFPropertyExtractor

def debug_missing_fields():
    print("🔍 DEBUG CHAMPS MANQUANTS")
    print("=" * 40)
    
    # Test sur un PDF
    pdfs = list(Path("input").glob("*.pdf")) if Path("input").exists() else []
    if not pdfs:
        print("❌ Pas de PDF dans input/")
        return
    
    extractor = PDFPropertyExtractor()
    pdf_path = pdfs[0]
    
    print(f"\n🧪 Test sur: {pdf_path.name}")
    
    # 1. Test pdfplumber seul
    print("\n📋 DONNÉES PDFPLUMBER:")
    tables = extractor.extract_tables_with_pdfplumber(pdf_path)
    
    batie = tables.get('prop_batie', [])
    non_batie = tables.get('non_batie', [])
    
    print(f"   Propriétés bâties: {len(batie)}")
    if batie:
        print("   Première bâtie:", list(batie[0].keys()))
        for key, value in batie[0].items():
            if value:
                print(f"     {key}: {value}")
    
    print(f"   Propriétés non-bâties: {len(non_batie)}")
    if non_batie:
        print("   Première non-bâtie:", list(non_batie[0].keys()))
        for key, value in non_batie[0].items():
            if value:
                print(f"     {key}: {value}")
    
    # 2. Test propriétaires OpenAI
    print("\n👤 PROPRIÉTAIRES OPENAI:")
    owners = extractor.extract_owners_make_style(pdf_path)
    print(f"   Nombre: {len(owners)}")
    if owners:
        print("   Premier propriétaire:")
        for key, value in owners[0].items():
            print(f"     {key}: {value}")
    
    # 3. Test fusion complète
    print("\n🔗 FUSION COMPLÈTE:")
    results = extractor.process_like_make(pdf_path)
    print(f"   Résultats finaux: {len(results)}")
    
    if results:
        print("   Premier résultat:")
        for key, value in results[0].items():
            status = "✅" if value else "❌"
            print(f"     {status} {key}: '{value}'")
        
        # Statistiques
        print("\n📊 STATISTIQUES:")
        empty_fields = {}
        for result in results:
            for key, value in result.items():
                if not value:
                    empty_fields[key] = empty_fields.get(key, 0) + 1
        
        total = len(results)
        for field, count in empty_fields.items():
            percent = (count / total) * 100
            print(f"   {field}: {count}/{total} vides ({percent:.1f}%)")

if __name__ == "__main__":
    debug_missing_fields() 