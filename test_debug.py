#!/usr/bin/env python3
"""
Script de debug pour tester l'extraction Make
"""

import os
import sys
from pathlib import Path
from pdf_extractor import PDFPropertyExtractor
import logging

# Configuration logging pour debug
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_extraction_debug():
    """Test debug de l'extraction Make"""
    print("🔍 TEST DEBUG EXTRACTION MAKE")
    print("=" * 50)
    
    # Vérifier la clé API
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY non configurée")
        return
    else:
        print(f"✅ API Key configurée: {api_key[:10]}...")
    
    # Initialiser l'extracteur
    try:
        extractor = PDFPropertyExtractor("input", "output")
        print("✅ Extracteur initialisé")
    except Exception as e:
        print(f"❌ Erreur initialisation: {e}")
        return
    
    # Chercher des PDFs
    input_dir = Path("input")
    if not input_dir.exists():
        print("❌ Dossier 'input' introuvable")
        return
    
    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        print("❌ Aucun PDF trouvé dans 'input/'")
        return
    
    print(f"📁 {len(pdf_files)} PDF(s) trouvé(s)")
    
    # Tester sur le premier PDF
    test_pdf = pdf_files[0]
    print(f"🧪 Test sur: {test_pdf.name}")
    print("-" * 30)
    
    # Test 1: pdfplumber
    print("📋 TEST 1: Extraction tableaux pdfplumber")
    try:
        structured = extractor.extract_tables_with_pdfplumber(test_pdf)
        print(f"  📊 Prop bâties: {len(structured.get('prop_batie', []))}")
        print(f"  📊 Prop non bâties: {len(structured.get('non_batie', []))}")
        
        if structured.get('prop_batie'):
            print(f"  🔍 Exemple bâti: {structured['prop_batie'][0]}")
        if structured.get('non_batie'):
            print(f"  🔍 Exemple non bâti: {structured['non_batie'][0]}")
            
    except Exception as e:
        print(f"  ❌ Erreur pdfplumber: {e}")
    
    print()
    
    # Test 2: OpenAI Vision
    print("👤 TEST 2: Extraction propriétaires OpenAI")
    try:
        owners = extractor.extract_owners_make_style(test_pdf)
        print(f"  👥 Propriétaires trouvés: {len(owners)}")
        
        if owners:
            print(f"  🔍 Premier propriétaire: {owners[0]}")
            
    except Exception as e:
        print(f"  ❌ Erreur OpenAI: {e}")
    
    print()
    
    # Test 3: Méthode complète
    print("🎯 TEST 3: Méthode Make complète")
    try:
        result = extractor.process_like_make(test_pdf)
        print(f"  🎉 Résultat final: {len(result)} propriétés")
        
        if result:
            print(f"  🔍 Première propriété: {result[0]}")
            
    except Exception as e:
        print(f"  ❌ Erreur méthode Make: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("🏁 Test debug terminé")

if __name__ == "__main__":
    test_extraction_debug() 