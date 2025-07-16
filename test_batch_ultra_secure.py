#!/usr/bin/env python3
"""
Test du Mode Batch Ultra-Sécurisé pour éliminer la contamination entre PDFs
"""

import os
import logging
from pathlib import Path
from pdf_extractor import PDFPropertyExtractor

def test_batch_ultra_secure():
    """
    Test du mode batch ultra-sécurisé avec surveillance de la contamination
    """
    print("🚀 TEST BATCH ULTRA-SÉCURISÉ")
    print("=" * 50)
    
    # Configuration
    input_dir = "input"
    output_dir = "output"
    
    # Créer l'extracteur
    extractor = PDFPropertyExtractor(input_dir, output_dir)
    
    # Lister les PDFs disponibles
    pdf_files = extractor.list_pdf_files()
    
    if not pdf_files:
        print("❌ Aucun PDF trouvé dans le dossier input/")
        return
    
    print(f"📁 {len(pdf_files)} PDF(s) trouvé(s):")
    for i, pdf in enumerate(pdf_files, 1):
        print(f"   {i}. {pdf.name}")
    
    # Limiter à 5 PDFs max pour le test
    test_files = pdf_files[:5]
    print(f"\n🧪 Test avec {len(test_files)} PDF(s)")
    
    # Test avec le mode ultra-sécurisé
    print("\n🛡️ DÉMARRAGE MODE BATCH ULTRA-SÉCURISÉ")
    print("-" * 50)
    
    try:
        # Analyser le batch
        batch_strategy = extractor.analyze_pdf_batch(test_files)
        print(f"📊 Stratégie batch: {batch_strategy.get('approach', 'standard')}")
        
        # Traitement avec mode ultra-sécurisé
        all_properties = extractor.process_pdf_batch_optimized(test_files, batch_strategy)
        
        print(f"\n✅ TRAITEMENT TERMINÉ")
        print(f"📊 Total extractions: {len(all_properties)}")
        
        # Analyse de contamination
        print("\n🔍 ANALYSE CONTAMINATION:")
        departments = set()
        communes = set()
        
        for prop in all_properties:
            dept = prop.get('department', '').strip()
            comm = prop.get('commune', '').strip()
            if dept:
                departments.add(dept)
            if comm:
                communes.add(comm)
        
        print(f"   Départements uniques: {sorted(departments)}")
        print(f"   Communes uniques: {sorted(communes)}")
        
        # Vérifier la contamination
        contamination_detected = False
        
        # Vérifier les départements suspects (Paris = 75, Lyon = 69)
        suspect_depts = {'75', '69'}
        found_suspect = departments.intersection(suspect_depts)
        if found_suspect:
            print(f"⚠️ CONTAMINATION DÉTECTÉE - Départements suspects: {found_suspect}")
            contamination_detected = True
        
        # Vérifier les communes vides ou incorrectes
        empty_communes = sum(1 for prop in all_properties if not prop.get('commune', '').strip())
        if empty_communes > len(all_properties) * 0.3:  # Plus de 30% vides
            print(f"⚠️ CONTAMINATION DÉTECTÉE - {empty_communes} communes vides sur {len(all_properties)}")
            contamination_detected = True
        
        if not contamination_detected:
            print("✅ AUCUNE CONTAMINATION DÉTECTÉE - Mode ultra-sécurisé efficace")
        
        # Post-traitement sécurisé
        print("\n🔧 POST-TRAITEMENT SÉCURISÉ...")
        final_properties = extractor.post_process_batch_results(all_properties, test_files)
        
        # Export avec validation
        print("\n💾 EXPORT AVEC VALIDATION...")
        extractor.export_to_csv_with_stats(final_properties)
        
        print("\n🎯 TEST BATCH ULTRA-SÉCURISÉ TERMINÉ")
        print(f"✅ Propriétés finales: {len(final_properties)}")
        
    except Exception as e:
        print(f"❌ Erreur durant le test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_batch_ultra_secure() 