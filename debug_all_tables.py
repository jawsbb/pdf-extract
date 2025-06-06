#!/usr/bin/env python3
"""
Script de diagnostic pour voir TOUS les tableaux dans un PDF
"""
import sys
import pdfplumber
from pathlib import Path

def debug_all_tables(pdf_file_path):
    """Debug tous les tableaux dans le PDF"""
    
    pdf_path = Path(pdf_file_path)
    print(f"🔍 Analyse COMPLÈTE du PDF: {pdf_path}")
    print("=" * 60)
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"📄 PDF: {len(pdf.pages)} page(s)")
            
            for page_num, page in enumerate(pdf.pages, 1):
                print(f"\n📄 PAGE {page_num}")
                print("-" * 40)
                
                # Extraire tous les tableaux
                tables = page.extract_tables()
                print(f"📋 Tableaux trouvés: {len(tables)}")
                
                for table_num, table in enumerate(tables, 1):
                    print(f"\n📊 TABLEAU {table_num} (Page {page_num})")
                    print(f"   Taille: {len(table)} lignes")
                    
                    # Afficher les premières lignes pour identifier le tableau
                    for i, row in enumerate(table[:5]):  # Max 5 premières lignes
                        if row:
                            print(f"   Ligne {i}: {row}")
                    
                    # Chercher spécifiquement des mentions de contenance
                    contenance_found = False
                    for row in table:
                        if row:
                            for cell in row:
                                if cell and ('contenance' in str(cell).lower() or 'HA' in str(cell) or 'CA' in str(cell)):
                                    if not contenance_found:
                                        print(f"   🎯 CONTENANCE DÉTECTÉE:")
                                        contenance_found = True
                                    print(f"      {row}")
                                    break
                    
                    if len(table) > 5:
                        print(f"   ... ({len(table) - 5} autres lignes)")
                    print()
                
                # Essayer aussi d'extraire le texte brut pour chercher "Contenance totale"
                text = page.extract_text()
                if text and 'contenance totale' in text.lower():
                    print("🎯 'Contenance totale' trouvé dans le texte de la page!")
                    # Extraire les lignes autour
                    lines = text.split('\n')
                    for i, line in enumerate(lines):
                        if 'contenance totale' in line.lower():
                            print(f"   Contexte autour de la ligne {i}:")
                            start = max(0, i-2)
                            end = min(len(lines), i+3)
                            for j in range(start, end):
                                marker = " -> " if j == i else "    "
                                print(f"{marker}{j}: {lines[j]}")
                            print()
                
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python debug_all_tables.py <chemin_vers_pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    debug_all_tables(pdf_path) 