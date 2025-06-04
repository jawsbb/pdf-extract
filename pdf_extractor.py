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
    
    def __init__(self, input_dir: str = "input", output_dir: str = "output"):
        """
        Initialise l'extracteur.
        
        Args:
            input_dir: Dossier contenant les PDFs
            output_dir: Dossier de sortie pour les résultats
        """
        # Charger les variables d'environnement
        load_dotenv()
        
        # Récupérer la clé API depuis les variables d'environnement
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("La clé API OpenAI n'est pas configurée. Veuillez définir OPENAI_API_KEY dans le fichier .env")
        
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

    def pdf_to_images(self, pdf_path: Path) -> List[bytes]:
        """
        Convertit toutes les pages d'un PDF en images PNG.
        
        Args:
            pdf_path: Chemin vers le fichier PDF
            
        Returns:
            Liste des bytes des images PNG ou liste vide en cas d'erreur
        """
        try:
            logger.info(f"Conversion de toutes les pages de {pdf_path.name} en images")
            
            # Ouvrir le PDF
            doc = fitz.open(pdf_path)
            
            if len(doc) == 0:
                logger.error(f"Le PDF {pdf_path.name} est vide")
                return []
            
            images = []
            
            # Traiter chaque page
            for page_num in range(len(doc)):
                try:
                    page = doc[page_num]
                    
                    # Convertir chaque page en image avec une résolution élevée
                    mat = fitz.Matrix(4.0, 4.0)  # Augmenté de 3.0 à 4.0 pour une qualité maximale
                    pix = page.get_pixmap(matrix=mat)
                    
                    # Convertir en PNG
                    img_data = pix.tobytes("png")
                    images.append(img_data)
                    
                    logger.info(f"Page {page_num + 1}/{len(doc)} convertie pour {pdf_path.name}")
                    
                except Exception as e:
                    logger.error(f"Erreur lors de la conversion de la page {page_num + 1} de {pdf_path.name}: {str(e)}")
                    continue
            
            doc.close()
            logger.info(f"Conversion réussie pour {pdf_path.name}: {len(images)} page(s) traitée(s)")
            return images
            
        except Exception as e:
            logger.error(f"Erreur lors de la conversion de {pdf_path.name}: {str(e)}")
            return []

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
            
            # Prompt simple et efficace - retour aux bases
            prompt = """
Analyze this French cadastral document and extract ALL property owner information you can see.

Look for:
- Owner names (nom/prénom)
- Property details (section, numero, contenance)
- Addresses and postal codes
- MAJIC codes (like M8BNF6)
- Department/commune codes
- Rights (droit réel like PP, US, NU)

Return JSON with this structure:
{
  "proprietes": [
    {
      "department": "",
      "commune": "",
      "prefixe": "",
      "section": "",
      "numero": "",
      "contenance": "",
      "droit_reel": "",
      "designation_parcelle": "",
      "nom": "",
      "prenom": "",
      "numero_majic": "",
      "voie": "",
      "post_code": "",
      "city": ""
    }
  ]
}

Extract ALL visible information. If something is not visible, use empty string "".
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
                max_tokens=3000,
                temperature=0.0
            )
            
            # Parser la réponse JSON
            response_text = response.choices[0].message.content.strip()
            
            # Nettoyer la réponse si elle contient des backticks
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            try:
                result = json.loads(response_text)
                if "proprietes" in result and result["proprietes"]:
                    logger.info(f"Extraction réussie pour {filename}: {len(result['proprietes'])} propriété(s) trouvé(s)")
                    return result
                else:
                    logger.warning(f"❌ Aucune propriété trouvée pour {filename}")
                    return None
            except json.JSONDecodeError as e:
                logger.error(f"Erreur de parsing JSON pour {filename}: {e}")
                logger.error(f"Réponse reçue: {response_text[:500]}...")
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction GPT-4o pour {filename}: {e}")
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

    def decompose_contenance(self, contenance: str) -> Dict[str, str]:
        """
        Décompose une contenance de 7 chiffres en hectares, ares et centiares.
        
        Args:
            contenance: Chaîne de 7 chiffres (ex: "0130221")
            
        Returns:
            Dictionnaire avec les clés HA, A, CA
        """
        if not contenance or contenance == "N/A" or len(contenance) != 7 or not contenance.isdigit():
            return {"HA": "N/A", "A": "N/A", "CA": "N/A"}
        
        # Décomposer selon le format : HHAACC
        ha = contenance[:2]  # 2 premiers chiffres (hectares)
        a = contenance[2:4]  # 2 suivants (ares)
        ca = contenance[4:7]  # 3 derniers (centiares)
        
        return {"HA": ha, "A": a, "CA": ca}

    def generate_unique_id(self, department: str, commune: str, section: str, numero: str, prefixe: str = "") -> str:
        """
        Génère un identifiant unique de 14 caractères selon les spécifications :
        Département (2) + Commune (3) + Section (5) + Numéro de plan (4)
        
        Args:
            department: Code département
            commune: Code commune
            section: Section cadastrale
            numero: Numéro de parcelle
            prefixe: Préfixe optionnel (ignoré dans cette version)
            
        Returns:
            ID unique formaté sur 14 caractères (ex: 25227000ZD0005)
        """
        # Département : 2 chiffres
        dept = str(department).zfill(2) if department and department != "N/A" else "00"
        
        # Commune : 3 chiffres
        comm = str(commune).zfill(3) if commune and commune != "N/A" else "000"
        
        # Section : 5 caractères avec zéros à gauche si nécessaire
        if section and section != "N/A":
            sect = str(section).strip()
            # Si la section fait moins de 5 caractères, compléter avec des zéros à gauche
            if len(sect) < 5:
                sect = sect.zfill(5)
            elif len(sect) > 5:
                # Si plus de 5 caractères, tronquer à 5
                sect = sect[:5]
        else:
            sect = "0000A"  # Section par défaut
        
        # Numéro de plan : 4 chiffres avec zéros à gauche
        if numero and numero != "N/A":
            num = str(numero).strip()
            # Enlever les caractères non numériques et prendre les chiffres
            num_clean = ''.join(filter(str.isdigit, num))
            if num_clean:
                num = num_clean.zfill(4)
                # Si plus de 4 chiffres, prendre les 4 derniers
                if len(num) > 4:
                    num = num[-4:]
            else:
                num = "0001"  # Numéro par défaut si pas de chiffres
        else:
            num = "0001"  # Numéro par défaut
        
        # Format final : DDCCCSSSSSNNNNN (14 caractères)
        unique_id = f"{dept}{comm}{sect}{num}"
        
        # Vérification de la longueur
        if len(unique_id) != 14:
            logger.warning(f"ID généré de longueur incorrecte ({len(unique_id)}): {unique_id}")
            # Ajuster si nécessaire
            if len(unique_id) < 14:
                unique_id = unique_id.ljust(14, '0')
            else:
                unique_id = unique_id[:14]
        
        return unique_id

    def process_single_pdf(self, pdf_path: Path) -> List[Dict]:
        """
        Traite un seul fichier PDF et retourne les informations extraites.
        VERSION SIMPLIFIÉE - suppression de toutes les couches complexes
        
        Args:
            pdf_path: Chemin vers le fichier PDF
            
        Returns:
            Liste des propriétaires avec leurs informations
        """
        logger.info(f"🔄 Traitement de {pdf_path.name}")
        
        # Convertir en images
        images = self.pdf_to_images(pdf_path)
        if not images:
            logger.error(f"❌ Échec de la conversion en images pour {pdf_path.name}")
            return []
        
        # Extraire les informations avec GPT-4o pour chaque page
        all_properties = []
        for page_num, image_data in enumerate(images, 1):
            logger.info(f"Extraction des données de la page {page_num}/{len(images)} pour {pdf_path.name}")
            extracted_data = self.extract_info_with_gpt4o(image_data, f"{pdf_path.name} (page {page_num})")
            if extracted_data and 'proprietes' in extracted_data:
                for prop in extracted_data['proprietes']:
                    # Générer l'ID unique
                    unique_id = self.generate_unique_id(
                        department=prop.get('department', '00'),
                        commune=prop.get('commune', '000'),
                        section=prop.get('section', 'A'),
                        numero=prop.get('numero', '0000'),
                        prefixe=prop.get('prefixe', '')
                    )
                    
                    # Ajouter l'ID unique et le fichier source
                    prop['id'] = unique_id
                    prop['fichier_source'] = pdf_path.name
                    
                    all_properties.append(prop)
        
        logger.info(f"✅ {pdf_path.name} traité avec succès - {len(all_properties)} propriété(s)")
        return all_properties

    def export_to_csv(self, all_properties: List[Dict], output_filename: str = "output.csv") -> None:
        """
        Exporte toutes les données vers un fichier CSV.
        
        Args:
            all_properties: Liste de toutes les propriétés
            output_filename: Nom du fichier de sortie
        """
        if not all_properties:
            logger.warning("Aucune donnée à exporter")
            return
        
        # Créer le DataFrame
        df = pd.DataFrame(all_properties)
        
        # Colonnes selon les spécifications du client
        columns_order = [
            'department', 'commune', 'prefixe', 'section', 'numero', 'contenance', 
            'droit_reel', 'designation_parcelle', 'nom', 'prenom', 'numero_majic', 
            'voie', 'post_code', 'city', 'id', 'fichier_source'
        ]
        
        # Renommer les colonnes pour plus de clarté
        column_mapping = {
            'department': 'Département',
            'commune': 'Commune', 
            'prefixe': 'Préfixe',
            'section': 'Section',
            'numero': 'Numéro',
            'contenance': 'Contenance',
            'droit_reel': 'Droit réel',
            'designation_parcelle': 'Designation Parcelle',
            'nom': 'Nom Propri',
            'prenom': 'Prénom Propri',
            'numero_majic': 'N°MAJIC',
            'voie': 'Voie',
            'post_code': 'CP',
            'city': 'Ville',
            'id': 'id',
            'fichier_source': 'Fichier source'
        }
        
        # Réorganiser et renommer
        df = df.reindex(columns=columns_order, fill_value='')
        df = df.rename(columns=column_mapping)
        
        # Exporter
        output_path = self.output_dir / output_filename
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        logger.info(f"📊 Données exportées vers {output_path}")
        logger.info(f"📈 Total: {len(all_properties)} propriété(s) dans {len(df['Fichier source'].unique())} fichier(s)")
        
        return output_path

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
        all_properties = []
        for pdf_file in pdf_files:
            properties = self.process_single_pdf(pdf_file)
            all_properties.extend(properties)
        
        # Exporter les résultats
        if all_properties:
            self.export_to_csv(all_properties)
            logger.info("✅ Extraction terminée avec succès!")
        else:
            logger.warning("❌ Aucune donnée extraite")


def main():
    """Fonction principale."""
    # Charger les variables d'environnement
    load_dotenv()
    
    # Créer et lancer l'extracteur
    extractor = PDFPropertyExtractor()
    extractor.run()


if __name__ == "__main__":
    main() 