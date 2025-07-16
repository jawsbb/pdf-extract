#!/usr/bin/env python3
"""
Test rapide des corrections sur vos PDFs
Lance l'extraction avec le filtrage amélioré
"""

import os
from pathlib import Path
from pdf_extractor import PDFPropertyExtractor

def test_extraction_corrigee():
    print("🚀 TEST EXTRACTION AVEC CORRECTIONS")
    print("=" * 45)
    
    # Vérifier setup
    if not Path(".env").exists():
        print("❌ Fichier .env manquant!")
        print("Créez le fichier .env avec:")
        print("OPENAI_API_KEY=sk-votre-cle-api-ici")
        return
    
    pdfs = list(Path("input").glob("*.pdf")) if Path("input").exists() else []
    if not pdfs:
        print("❌ Pas de PDF dans le dossier input/")
        print("Placez vos PDFs dans le dossier 'input/'")
        return
    
    print(f"📄 {len(pdfs)} PDF(s) trouvé(s):")
    for pdf in pdfs[:3]:  # Afficher max 3
        print(f"   • {pdf.name}")
    if len(pdfs) > 3:
        print(f"   • ... et {len(pdfs)-3} autres")
    
    print(f"\n🎯 Test sur: {pdfs[0].name}")
    
    # Lancer l'extraction
    extractor = PDFPropertyExtractor()
    
    print("\n📊 EXTRACTION EN COURS...")
    print("-" * 30)
    
    try:
        # Test sur le premier PDF
        results = extractor.process_like_make(pdfs[0])
        
        print(f"\n✅ EXTRACTION TERMINÉE!")
        print(f"📈 Propriétés extraites: {len(results)}")
        
        if results:
            print(f"\n📋 APERÇU DES RÉSULTATS:")
            print("-" * 30)
            
            # Compter les propriétaires uniques
            proprietaires = set()
            for r in results:
                nom = r.get('nom', '')
                prenom = r.get('prenom', '')
                if nom or prenom:
                    proprietaires.add(f"{nom} {prenom}".strip())
            
            print(f"👤 Propriétaires uniques: {len(proprietaires)}")
            for prop in list(proprietaires)[:5]:  # Max 5
                print(f"   • {prop}")
            
            # Échantillon de données
            print(f"\n📄 Échantillon (première ligne):")
            first = results[0]
            print(f"   Propriétaire: {first.get('nom', '')} {first.get('prenom', '')}")
            print(f"   Parcelle: {first.get('section', '')}{first.get('numero', '')}")
            print(f"   Commune: {first.get('commune', '')}")
            print(f"   Désignation: {first.get('designation_parcelle', '')}")
            
            print(f"\n💾 Pour export complet, lancez: python start.py")
            
        else:
            print("⚠️ Aucune propriété extraite")
            print("Vérifiez votre clé API OpenAI dans .env")
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        print("Vérifiez votre clé API OpenAI")

if __name__ == "__main__":
    test_extraction_corrigee() 