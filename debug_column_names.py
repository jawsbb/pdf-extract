#!/usr/bin/env python3
"""
Script de diagnostic pour identifier les vrais noms de colonnes pdfplumber
"""
import sys
import tempfile
from pathlib import Path
from pdf_extractor import PDFPropertyExtractor

def debug_column_names(pdf_file_path):
    """Debug les noms de colonnes extraites par pdfplumber"""
    
    # Créer un répertoire temporaire
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Initialiser l'extracteur
        extractor = PDFPropertyExtractor(input_dir=str(temp_path), output_dir=str(temp_path))
        
        print(f"🔍 Analyse du PDF: {pdf_file_path}")
        print("=" * 50)
        
        try:
            # Extraire les tableaux avec pdfplumber
            structured = extractor.extract_tables_with_pdfplumber(pdf_file_path)
            
            print(f"📋 Propriétés bâties trouvées: {len(structured.get('prop_batie', []))}")
            print(f"📋 Propriétés non bâties trouvées: {len(structured.get('non_batie', []))}")
            print()
            
            # Analyser les propriétés bâties
            if structured.get('prop_batie'):
                print("🏠 COLONNES PROPRIÉTÉS BÂTIES:")
                print("-" * 30)
                first_batie = structured['prop_batie'][0]
                for key, value in first_batie.items():
                    print(f"  '{key}': '{value}'")
                print()
            
            # Analyser les propriétés non bâties  
            if structured.get('non_batie'):
                print("🌿 COLONNES PROPRIÉTÉS NON BÂTIES:")
                print("-" * 30)
                first_non_batie = structured['non_batie'][0]
                for key, value in first_non_batie.items():
                    print(f"  '{key}': '{value}'")
                print()
            
            # Chercher spécifiquement les colonnes contenance
            all_props = structured.get('prop_batie', []) + structured.get('non_batie', [])
            contenance_keys = []
            
            for prop in all_props:
                for key in prop.keys():
                    if any(word in key.lower() for word in ['ha', 'are', 'ca', 'contenance', 'surface']):
                        if key not in contenance_keys:
                            contenance_keys.append(key)
            
            if contenance_keys:
                print("🎯 COLONNES LIÉES À LA CONTENANCE:")
                print("-" * 30)
                for key in contenance_keys:
                    print(f"  '{key}'")
                print()
            
            print("🔧 MAPPING ACTUEL DANS LE CODE:")
            print("-" * 30)
            print("  Code cherche: 'HA', 'A', 'CA'")
            print(f"  PDF contient: {list(first_batie.keys() if structured.get('prop_batie') else first_non_batie.keys() if structured.get('non_batie') else [])}")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'analyse: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python debug_column_names.py <chemin_vers_pdf>")
        sys.exit(1)
    
    pdf_path = Path(sys.argv[1])
    debug_column_names(pdf_path) 