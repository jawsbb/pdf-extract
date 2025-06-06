#!/usr/bin/env python3
"""
Test spécifique pour les trois colonnes de contenance : HA, A, CA
"""

import os
from pathlib import Path
from pdf_extractor import PDFPropertyExtractor

def test_contenance():
    print("🧪 TEST CONTENANCE HA/A/CA")
    print("=" * 30)
    
    # Vérifier setup
    pdfs = list(Path("input").glob("*.pdf")) if Path("input").exists() else []
    if not pdfs:
        print("❌ Pas de PDF dans input/")
        return
    
    extractor = PDFPropertyExtractor()
    pdf_path = pdfs[0]
    
    print(f"\n📄 Test sur: {pdf_path.name}")
    
    # 1. Test extraction pdfplumber brute
    print("\n📋 Données pdfplumber brutes:")
    tables = extractor.extract_tables_with_pdfplumber(pdf_path)
    
    for prop_type, props in tables.items():
        if props:
            print(f"   {prop_type}: {len(props)} propriétés")
            first_prop = props[0]
            
            # Chercher les colonnes de contenance
            for key in first_prop.keys():
                if key in ['HA', 'A', 'CA', 'Contenance', 'Ctce']:
                    print(f"     {key}: '{first_prop[key]}'")
    
    # 2. Test fusion Make
    print("\n🔗 Fusion Make complète:")
    results = extractor.process_like_make(pdf_path)
    
    if results:
        first_result = results[0]
        print(f"   Résultats: {len(results)}")
        print(f"   Contenance HA: '{first_result.get('contenance_ha', 'MANQUANT')}'")
        print(f"   Contenance A:  '{first_result.get('contenance_a', 'MANQUANT')}'")
        print(f"   Contenance CA: '{first_result.get('contenance_ca', 'MANQUANT')}'")
        
        # Statistiques globales
        print("\n📊 Statistiques contenance:")
        ha_filled = sum(1 for r in results if r.get('contenance_ha'))
        a_filled = sum(1 for r in results if r.get('contenance_a'))
        ca_filled = sum(1 for r in results if r.get('contenance_ca'))
        total = len(results)
        
        print(f"   HA rempli: {ha_filled}/{total} ({ha_filled/total*100:.1f}%)")
        print(f"   A rempli:  {a_filled}/{total} ({a_filled/total*100:.1f}%)")
        print(f"   CA rempli: {ca_filled}/{total} ({ca_filled/total*100:.1f}%)")
        
        if ha_filled > 0 or a_filled > 0 or ca_filled > 0:
            print("   ✅ Au moins une colonne contenance fonctionne!")
        else:
            print("   ❌ Aucune contenance extraite")
            
            # Debug: montrer toutes les clés disponibles
            print("\n🔍 Clés disponibles dans première propriété:")
            for key in first_result.keys():
                print(f"     {key}")
    else:
        print("   ❌ Aucun résultat!")

if __name__ == "__main__":
    test_contenance() 