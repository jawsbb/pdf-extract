#!/usr/bin/env python3
"""
Démonstration complète du système d'extraction PDF.
Simule l'extraction avec des données fictives pour montrer le fonctionnement complet.
"""

import json
import pandas as pd
from pathlib import Path
from pdf_extractor import PDFPropertyExtractor
import logging

# Configuration du logging pour la démo
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DemoExtractor(PDFPropertyExtractor):
    """Version démo de l'extracteur qui simule les appels API."""
    
    def __init__(self):
        """Initialise l'extracteur démo sans clé API."""
        # Initialisation sans appel au parent pour éviter l'API OpenAI
        self.input_dir = Path("input")
        self.output_dir = Path("output")
        self.default_section = 'A'
        self.default_plan_number = 123
        
        # Créer les dossiers s'ils n'existent pas
        self.input_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info(f"Extracteur DÉMO initialisé - Input: {self.input_dir}, Output: {self.output_dir}")

    def extract_info_with_gpt4o(self, image_data: bytes, filename: str) -> dict:
        """
        Simule l'extraction GPT-4o avec des données fictives réalistes.
        
        Args:
            image_data: Données de l'image (non utilisées en démo)
            filename: Nom du fichier
            
        Returns:
            Dictionnaire avec des données fictives
        """
        logger.info(f"🤖 SIMULATION - Extraction GPT-4o pour {filename}")
        
        # Données fictives réalistes basées sur le nom du fichier
        if "test" in filename.lower():
            fake_data = {
                "owners": [
                    {
                        "nom": "DUPONT",
                        "prenom": "JEAN",
                        "street_address": "1 RUE DES LILAS",
                        "post_code": "75010",
                        "city": "PARIS",
                        "numero_proprietaire": "P001",
                        "department": "75",
                        "commune": "001",
                        "droit_reel": "Propriétaire"
                    },
                    {
                        "nom": "MARTIN",
                        "prenom": "MARIE",
                        "street_address": "15 AV DE LA PAIX",
                        "post_code": "69001",
                        "city": "LYON",
                        "numero_proprietaire": "P002",
                        "department": "69",
                        "commune": "001",
                        "droit_reel": "Indivision"
                    },
                    {
                        "nom": "BERNARD",
                        "prenom": "PIERRE",
                        "street_address": "8 PLACE DU MARCHE",
                        "post_code": "13001",
                        "city": "MARSEILLE",
                        "numero_proprietaire": "P003",
                        "department": "13",
                        "commune": "001",
                        "droit_reel": "Usufruitier"
                    }
                ]
            }
        else:
            # Données génériques pour d'autres fichiers
            fake_data = {
                "owners": [
                    {
                        "nom": "EXEMPLE",
                        "prenom": "DEMO",
                        "street_address": "123 RUE DE LA DEMO",
                        "post_code": "00000",
                        "city": "VILLE DEMO",
                        "numero_proprietaire": "DEMO001",
                        "department": "00",
                        "commune": "000",
                        "droit_reel": "Propriétaire"
                    }
                ]
            }
        
        logger.info(f"✅ SIMULATION - {len(fake_data['owners'])} propriétaire(s) 'extraits'")
        return fake_data

def create_additional_test_pdfs():
    """Crée des PDFs de test supplémentaires pour la démonstration."""
    from test_extractor import create_test_pdf
    
    input_dir = Path("input")
    
    # Créer différents types de PDFs de test
    test_files = [
        "proprietaires_paris.pdf",
        "proprietaires_lyon.pdf", 
        "proprietaires_marseille.pdf"
    ]
    
    for pdf_name in test_files:
        pdf_path = input_dir / pdf_name
        if not pdf_path.exists():
            create_test_pdf(str(pdf_path))
            logger.info(f"📄 PDF de test créé: {pdf_name}")

def run_complete_demo():
    """Lance une démonstration complète du système."""
    print("🎬 DÉMONSTRATION COMPLÈTE - Extracteur PDF de Propriétaires")
    print("=" * 60)
    
    # Créer des PDFs de test supplémentaires
    print("\n📄 Création de PDFs de test...")
    create_additional_test_pdfs()
    
    # Créer l'extracteur démo
    print("\n🤖 Initialisation de l'extracteur DÉMO...")
    extractor = DemoExtractor()
    
    # Lancer l'extraction
    print("\n🚀 Lancement de l'extraction (SIMULATION)...")
    extractor.run()
    
    # Afficher les résultats
    print("\n📊 Analyse des résultats...")
    output_file = Path("output/output.csv")
    
    if output_file.exists():
        df = pd.read_csv(output_file)
        print(f"✅ Fichier CSV créé avec {len(df)} entrée(s)")
        print(f"📁 Fichiers traités: {df['Fichier source'].nunique()}")
        print(f"🏠 Propriétaires uniques: {len(df)}")
        
        print("\n📋 Aperçu des données extraites:")
        print("-" * 40)
        for idx, row in df.head().iterrows():
            print(f"👤 {row['Nom']} {row['Prénom']}")
            print(f"   📍 {row['Adresse']}, {row['CP']} {row['Ville']}")
            print(f"   🆔 ID Parcelle: {row['ID Parcelle']}")
            print(f"   📄 Source: {row['Fichier source']}")
            print()
        
        print("💾 Fichier CSV complet disponible dans: output/output.csv")
    else:
        print("❌ Aucun fichier de sortie généré")
    
    print("\n🎉 Démonstration terminée!")
    print("\n💡 Pour utiliser avec de vrais PDFs:")
    print("   1. Ajoutez votre clé API OpenAI dans le fichier .env")
    print("   2. Placez vos PDFs dans le dossier input/")
    print("   3. Lancez: python pdf_extractor.py")

if __name__ == "__main__":
    run_complete_demo() 