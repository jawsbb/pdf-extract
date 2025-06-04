#!/usr/bin/env python3
"""
Test du nouveau système de traitement par lots optimisé
"""

import os
import sys
from pathlib import Path
from pdf_extractor import PDFPropertyExtractor

def test_batch_processing():
    """Test du traitement par lots avec statistiques"""
    print("TEST TRAITEMENT PAR LOTS OPTIMISE")
    print("=" * 50)
    
    # Initialiser l'extracteur
    extractor = PDFPropertyExtractor("input", "output")
    
    # Vérifier le dossier input
    input_dir = Path("input")
    if not input_dir.exists():
        print("Erreur: Dossier 'input' introuvable")
        return
    
    # Lister tous les PDFs
    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        print("Erreur: Aucun PDF trouve dans 'input'")
        print("Veuillez ajouter plusieurs PDFs cadastraux pour tester le batch")
        return
    
    print(f"PDFs detectes: {len(pdf_files)}")
    for i, pdf in enumerate(pdf_files, 1):
        print(f"  {i}. {pdf.name}")
    
    print(f"\nDemarrage traitement par lots...")
    print("(Attention: necessite une cle OpenAI valide)")
    
    try:
        # Lancer le traitement par lots optimise
        extractor.run()
        
        # Verifier les resultats
        output_dir = Path("output")
        csv_files = list(output_dir.glob("*.csv"))
        
        if csv_files:
            latest_csv = max(csv_files, key=lambda f: f.stat().st_mtime)
            print(f"\nResultat genere: {latest_csv.name}")
            
            # Lire et analyser le CSV
            try:
                import pandas as pd
                df = pd.read_csv(latest_csv)
                
                print(f"STATISTIQUES FINALES:")
                print(f"  Lignes extraites: {len(df)}")
                print(f"  Colonnes: {len(df.columns)}")
                
                # Analyser les colonnes vides
                empty_stats = {}
                for col in df.columns:
                    empty_count = df[col].isna().sum() + (df[col] == '').sum()
                    total_count = len(df)
                    completion_rate = ((total_count - empty_count) / total_count) * 100
                    empty_stats[col] = completion_rate
                
                print(f"\nTAUX DE COMPLETION PAR COLONNE:")
                for col, rate in empty_stats.items():
                    status = "EXCELLENT" if rate >= 90 else "BON" if rate >= 70 else "MOYEN" if rate >= 50 else "FAIBLE"
                    print(f"  {col:<20}: {rate:5.1f}% [{status}]")
                
                # Moyenne globale
                avg_completion = sum(empty_stats.values()) / len(empty_stats)
                print(f"\nTAUX GLOBAL: {avg_completion:.1f}%")
                
                # Conseils selon les resultats
                if avg_completion >= 85:
                    print("🎉 EXCELLENT: Extraction tres reussie!")
                elif avg_completion >= 70:
                    print("✅ BON: Extraction satisfaisante")
                elif avg_completion >= 50:
                    print("⚠️ MOYEN: Extraction partielle, verifiez la qualite des PDFs")
                else:
                    print("❌ FAIBLE: Verifiez le format des PDFs et la cle API")
                
            except ImportError:
                print("Pandas non disponible pour l'analyse detaillee")
                print("Installez avec: pip install pandas")
        else:
            print("Aucun fichier CSV genere")
    
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_batch_processing()