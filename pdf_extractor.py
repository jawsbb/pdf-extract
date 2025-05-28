#!/usr/bin/env python3
"""
Script d'extraction automatique d'informations de propriétaires depuis des PDFs.

Auteur: Assistant IA
Date: 2025
"""

import os
import json
import logging
import base64
from pathlib import Path
from typing import List, Dict, Optional
import fitz  # PyMuPDF
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
from PIL import Image
import io

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PDFPropertyExtractor:
    """Classe principale pour l'extraction d'informations de propriétaires depuis des PDFs."""
    
    def __init__(self, api_key: str, input_dir: str = "input", output_dir: str = "output"):
        """
        Initialise l'extracteur.
        
        Args:
            api_key: Clé API OpenAI
            input_dir: Dossier contenant les PDFs
            output_dir: Dossier de sortie pour les résultats
        """
        self.client = OpenAI(api_key=api_key)
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.default_section = os.getenv('DEFAULT_SECTION', 'A')
        self.default_plan_number = int(os.getenv('DEFAULT_PLAN_NUMBER', '123'))
        
        # Créer les dossiers s'ils n'existent pas
        self.input_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info(f"Extracteur initialisé - Input: {self.input_dir}, Output: {self.output_dir}")

    def list_pdf_files(self) -> List[Path]:
        """
        Liste tous les fichiers PDF dans le dossier input.
        
        Returns:
            Liste des chemins vers les fichiers PDF
        """
        pdf_files = list(self.input_dir.glob("*.pdf"))
        logger.info(f"Trouvé {len(pdf_files)} fichier(s) PDF dans {self.input_dir}")
        return pdf_files

    def pdf_to_image(self, pdf_path: Path) -> Optional[bytes]:
        """
        Convertit la première page d'un PDF en image PNG.
        
        Args:
            pdf_path: Chemin vers le fichier PDF
            
        Returns:
            Bytes de l'image PNG ou None en cas d'erreur
        """
        try:
            logger.info(f"Conversion de la première page de {pdf_path.name} en image")
            
            # Ouvrir le PDF
            doc = fitz.open(pdf_path)
            
            if len(doc) == 0:
                logger.error(f"Le PDF {pdf_path.name} est vide")
                return None
            
            # Récupérer la première page
            page = doc[0]
            
            # Convertir en image avec une résolution élevée
            mat = fitz.Matrix(2.0, 2.0)  # Zoom x2 pour une meilleure qualité
            pix = page.get_pixmap(matrix=mat)
            
            # Convertir en PNG
            img_data = pix.tobytes("png")
            
            doc.close()
            logger.info(f"Conversion réussie pour {pdf_path.name}")
            return img_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la conversion de {pdf_path.name}: {str(e)}")
            return None

    def extract_info_with_gpt4o(self, image_data: bytes, filename: str) -> Optional[Dict]:
        """
        Utilise GPT-4o pour extraire les informations de propriétaires depuis l'image.
        
        Args:
            image_data: Données de l'image en bytes
            filename: Nom du fichier pour le logging
            
        Returns:
            Dictionnaire contenant les informations extraites ou None en cas d'erreur
        """
        try:
            logger.info(f"Extraction des informations avec GPT-4o pour {filename}")
            
            # Encoder l'image en base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Prompt détaillé pour l'extraction
            prompt = """
            Analyse cette image qui contient des informations de propriétaires immobiliers.
            
            Extrait TOUTES les informations de propriétaires visibles et retourne un JSON avec la structure suivante :
            
            {
              "owners": [
                {
                  "nom": "NOM_FAMILLE",
                  "prenom": "PRENOM",
                  "street_address": "ADRESSE_COMPLETE_RUE",
                  "post_code": "CODE_POSTAL",
                  "city": "VILLE",
                  "numero_proprietaire": "NUMERO_PROPRIETAIRE",
                  "department": "DEPARTEMENT_2_CHIFFRES",
                  "commune": "COMMUNE_3_CHIFFRES",
                  "droit_reel": "TYPE_DROIT_REEL"
                }
              ]
            }
            
            INSTRUCTIONS IMPORTANTES :
            - Extrait TOUS les propriétaires visibles dans l'image
            - Garde les zéros initiaux pour département et commune (ex: "01", "001")
            - Pour le droit réel, utilise les termes exacts trouvés (Propriétaire, Indivision, Usufruitier, etc.)
            - Si une information n'est pas visible, utilise "N/A"
            - Assure-toi que le JSON est valide
            - Ne retourne QUE le JSON, sans texte supplémentaire
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.1
            )
            
            # Parser la réponse JSON
            response_text = response.choices[0].message.content.strip()
            
            # Nettoyer la réponse si elle contient des backticks
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            result = json.loads(response_text)
            logger.info(f"Extraction réussie pour {filename}: {len(result.get('owners', []))} propriétaire(s) trouvé(s)")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de parsing JSON pour {filename}: {str(e)}")
            logger.error(f"Réponse reçue: {response_text}")
            return None
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction GPT-4o pour {filename}: {str(e)}")
            return None

    def generate_parcel_id(self, department: str, commune: str, section: str = None, plan_number: int = None) -> str:
        """
        Génère un identifiant parcellaire selon la formule spécifiée.
        
        Args:
            department: Code département (2 chiffres)
            commune: Code commune (3 chiffres)
            section: Section (5 caractères, optionnel)
            plan_number: Numéro de plan (4 chiffres, optionnel)
            
        Returns:
            Identifiant parcellaire formaté
        """
        # Utiliser les valeurs par défaut si non fournies
        if section is None:
            section = self.default_section
        if plan_number is None:
            plan_number = self.default_plan_number
        
        # Formater selon les règles
        dept_formatted = department.zfill(2)
        commune_formatted = commune.zfill(3)
        section_formatted = str(section).ljust(5, '0')[:5]
        plan_formatted = str(plan_number).zfill(4)
        
        parcel_id = f"{dept_formatted}{commune_formatted}{section_formatted}{plan_formatted}"
        return parcel_id

    def process_single_pdf(self, pdf_path: Path) -> List[Dict]:
        """
        Traite un seul fichier PDF et retourne les informations extraites.
        
        Args:
            pdf_path: Chemin vers le fichier PDF
            
        Returns:
            Liste des propriétaires avec leurs informations
        """
        logger.info(f"🔄 Traitement de {pdf_path.name}")
        
        # Convertir en image
        image_data = self.pdf_to_image(pdf_path)
        if image_data is None:
            logger.error(f"❌ Échec de la conversion en image pour {pdf_path.name}")
            return []
        
        # Extraire les informations avec GPT-4o
        extracted_data = self.extract_info_with_gpt4o(image_data, pdf_path.name)
        if extracted_data is None:
            logger.error(f"❌ Échec de l'extraction pour {pdf_path.name}")
            return []
        
        # Traiter chaque propriétaire
        processed_owners = []
        for owner in extracted_data.get('owners', []):
            # Générer l'ID parcellaire
            parcel_id = self.generate_parcel_id(
                department=owner.get('department', '00'),
                commune=owner.get('commune', '000')
            )
            
            # Ajouter l'ID parcellaire aux données
            owner['id_parcelle'] = parcel_id
            owner['fichier_source'] = pdf_path.name
            
            processed_owners.append(owner)
        
        logger.info(f"✅ {pdf_path.name} traité avec succès - {len(processed_owners)} propriétaire(s)")
        return processed_owners

    def export_to_csv(self, all_owners: List[Dict], output_filename: str = "output.csv") -> None:
        """
        Exporte toutes les données vers un fichier CSV.
        
        Args:
            all_owners: Liste de tous les propriétaires
            output_filename: Nom du fichier de sortie
        """
        if not all_owners:
            logger.warning("Aucune donnée à exporter")
            return
        
        # Créer le DataFrame
        df = pd.DataFrame(all_owners)
        
        # Réorganiser les colonnes selon les spécifications
        columns_order = [
            'nom', 'prenom', 'street_address', 'post_code', 'city',
            'department', 'commune', 'numero_proprietaire', 'droit_reel',
            'id_parcelle', 'fichier_source'
        ]
        
        # Renommer les colonnes pour plus de clarté
        column_mapping = {
            'nom': 'Nom',
            'prenom': 'Prénom',
            'street_address': 'Adresse',
            'post_code': 'CP',
            'city': 'Ville',
            'department': 'Département',
            'commune': 'Commune',
            'numero_proprietaire': 'Numéro MAJIC',
            'droit_reel': 'Droit réel',
            'id_parcelle': 'ID Parcelle',
            'fichier_source': 'Fichier source'
        }
        
        # Réorganiser et renommer
        df = df.reindex(columns=columns_order, fill_value='N/A')
        df = df.rename(columns=column_mapping)
        
        # Exporter
        output_path = self.output_dir / output_filename
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        logger.info(f"📊 Données exportées vers {output_path}")
        logger.info(f"📈 Total: {len(all_owners)} propriétaire(s) dans {len(df['Fichier source'].unique())} fichier(s)")

    def run(self) -> None:
        """
        Lance le processus complet d'extraction.
        """
        logger.info("🚀 Démarrage de l'extraction automatique")
        
        # Lister les fichiers PDF
        pdf_files = self.list_pdf_files()
        
        if not pdf_files:
            logger.warning("❌ Aucun fichier PDF trouvé dans le dossier input/")
            return
        
        # Traiter tous les fichiers
        all_owners = []
        for pdf_file in pdf_files:
            owners = self.process_single_pdf(pdf_file)
            all_owners.extend(owners)
        
        # Exporter les résultats
        if all_owners:
            self.export_to_csv(all_owners)
            logger.info("✅ Extraction terminée avec succès!")
        else:
            logger.warning("❌ Aucune donnée extraite")


def main():
    """Fonction principale."""
    # Charger les variables d'environnement
    load_dotenv()
    
    # Récupérer la clé API
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.error("❌ OPENAI_API_KEY non trouvée dans les variables d'environnement")
        logger.info("💡 Créez un fichier .env avec votre clé API OpenAI")
        return
    
    # Créer et lancer l'extracteur
    extractor = PDFPropertyExtractor(api_key)
    extractor.run()


if __name__ == "__main__":
    main() 