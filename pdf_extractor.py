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
                    mat = fitz.Matrix(3.0, 3.0)  # Augmenté de 2.0 à 3.0 pour une meilleure qualité
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
            
            # Prompt simple et efficace inspiré de Make.com
            prompt = """
In the following image, you will find information of owners such as nom, prenom, adresse, droit reel, numero proprietaire, department and commune. If there are any leading zero's before commune or deparment, keep it as it is. Format the address as street address, city and post code. If city or postcode is not available, just leave it blank. There can be one or multiple owners. I want to extract all of them and return them in json format.

output example:

{
  "proprietes": [
    {
      "department": "51",
      "commune": "179", 
      "prefixe": "",
      "section": "ZY",
      "numero": "0006",
      "contenance": "230040",
      "droit_reel": "US",
      "designation_parcelle": "LES ROULLIERS",
      "nom": "LAMBIN",
      "prenom": "DIDIER JEAN GUY",
      "numero_majic": "M8BNF6",
      "voie": "1 RUE D AVAT",
      "post_code": "51240",
      "city": "COUPEVILLE"
    }
  ]
}

Extract all owners and properties. If information is not available, leave it blank or use "N/A".
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
                max_tokens=2500,
                temperature=0.1
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
                
                # Tentative de récupération avec extraction simplifiée
                logger.info(f"Tentative de récupération pour {filename}")
                return self.fallback_extraction(image_data, filename)
                
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction GPT-4o pour {filename}: {e}")
            return None

    def fallback_extraction(self, image_data: bytes, filename: str) -> Optional[Dict]:
        """Extraction de secours avec prompt simplifié"""
        try:
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Prompt simplifié pour la récupération
            simple_prompt = """
Extract property owners from this French cadastral document.

Return JSON format:
{
  "proprietes": [
    {
      "department": "dept code",
      "commune": "commune code",
      "section": "section",
      "numero": "number",
      "contenance": "surface",
      "droit_reel": "PP/US/NU",
      "designation_parcelle": "place name",
      "nom": "last name",
      "prenom": "first name", 
      "numero_majic": "MAJIC code",
      "voie": "address",
      "post_code": "postal code",
      "city": "city"
    }
  ]
}

Extract all visible information. Use "N/A" if not available.
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": simple_prompt},
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
                max_tokens=1500,
                temperature=0.1
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Nettoyage du JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].strip()
            
            result = json.loads(response_text)
            if "proprietes" in result and result["proprietes"]:
                # Compléter les champs manquants avec "N/A"
                for prop in result["proprietes"]:
                    for field in ["department", "commune", "prefixe", "section", "numero", "contenance", 
                                "droit_reel", "designation_parcelle", "nom", "prenom", "numero_majic", 
                                "voie", "post_code", "city"]:
                        if field not in prop:
                            prop[field] = "N/A"
                
                logger.info(f"✅ Récupération réussie pour {filename}: {len(result['proprietes'])} propriété(s)")
                return result
            else:
                logger.warning(f"❌ Récupération échouée pour {filename}")
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération pour {filename}: {e}")
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

    def improve_extracted_data(self, properties: List[Dict], filename: str) -> List[Dict]:
        """
        Améliore intelligemment les données extraites en comblant les manques.
        
        Args:
            properties: Liste des propriétés extraites
            filename: Nom du fichier pour le contexte
            
        Returns:
            Liste des propriétés améliorées
        """
        if not properties:
            return []
        
        improved = []
        
        # Analyser les données pour trouver des patterns communs
        common_dept = None
        common_commune = None
        
        # Chercher les valeurs les plus fréquentes non-N/A
        depts = [p.get('department') for p in properties if p.get('department') and p.get('department') != 'N/A']
        communes = [p.get('commune') for p in properties if p.get('commune') and p.get('commune') != 'N/A']
        
        if depts:
            common_dept = max(set(depts), key=depts.count)
        if communes:
            common_commune = max(set(communes), key=communes.count)
        
        # Si pas de dept/commune trouvés, essayer de déduire depuis les codes postaux
        if not common_dept:
            postcodes = [p.get('post_code') for p in properties if p.get('post_code') and p.get('post_code') != 'N/A']
            if postcodes:
                # Extraire le département depuis le code postal (2 premiers chiffres)
                for pc in postcodes:
                    if len(str(pc)) >= 2 and str(pc)[:2].isdigit():
                        dept_from_pc = str(pc)[:2]
                        if not common_dept:
                            common_dept = dept_from_pc
                            logger.info(f"Département déduit du code postal {pc}: {dept_from_pc}")
                            break
        
        # Si toujours pas de département, essayer des heuristiques basées sur le filename
        if not common_dept:
            # Recherche de patterns dans le nom de fichier (ex: ZY 6 -> peut-être section ZY)
            if 'ZY' in filename.upper():
                # Heuristique : fichiers ZY souvent dans certains départements
                # On peut essayer 51 (Marne) qui apparaît souvent avec ZY
                common_dept = '51'
                logger.info(f"Département deviné depuis filename {filename}: 51 (heuristique ZY)")
        
        logger.info(f"Amélioration pour {filename} - Dept commun: {common_dept}, Commune commune: {common_commune}")
        
        for prop in properties:
            improved_prop = prop.copy()
            
            # Améliorer département/commune si manquants
            if improved_prop.get('department') == 'N/A' and common_dept:
                improved_prop['department'] = common_dept
                
            if improved_prop.get('commune') == 'N/A' and common_commune:
                improved_prop['commune'] = common_commune
            
            # Nettoyer et normaliser les numéros de parcelles
            numero = improved_prop.get('numero', 'N/A')
            if numero and numero != 'N/A':
                # Enlever les espaces et normaliser
                numero_clean = str(numero).replace(' ', '').strip()
                if numero_clean.isdigit():
                    improved_prop['numero'] = numero_clean.zfill(4)
            
            # Nettoyer la contenance (enlever les espaces, normaliser)
            contenance = improved_prop.get('contenance', 'N/A')
            if contenance and contenance != 'N/A':
                # Enlever tous les espaces
                contenance_clean = str(contenance).replace(' ', '').strip()
                
                # Convertir "23 HA 40 A" en format numérique
                if 'HA' in str(contenance).upper():
                    try:
                        parts = str(contenance).upper().replace('A', '').replace('HA', '').strip().split()
                        if len(parts) >= 2:
                            ha = int(parts[0]) if parts[0].isdigit() else 0
                            a = int(parts[1]) if parts[1].isdigit() else 0
                            # Format: HHAAAA (2 chiffres HA + 4 chiffres A)
                            improved_prop['contenance'] = f"{ha:02d}{a:04d}0"
                    except:
                        # Si échec, garder la version nettoyée
                        improved_prop['contenance'] = contenance_clean
                else:
                    # Juste nettoyer les espaces
                    improved_prop['contenance'] = contenance_clean
            
            # Normaliser les droits réels
            droit = str(improved_prop.get('droit_reel', 'N/A')).upper()
            if 'PROPRIET' in droit and droit != 'PP':
                improved_prop['droit_reel'] = 'PP'
            elif 'USUFRUIT' in droit and droit != 'US':
                improved_prop['droit_reel'] = 'US'
            elif 'NU-PROPRIET' in droit or 'NUE-PROPRIET' in droit:
                improved_prop['droit_reel'] = 'NU'
            
            # Nettoyer les codes postaux (enlever espaces)
            if 'post_code' in improved_prop and improved_prop['post_code']:
                pc = str(improved_prop['post_code']).replace(' ', '').strip()
                if pc.isdigit() and len(pc) == 5:
                    improved_prop['post_code'] = pc
            
            # Ignorer les propriétés complètement vides (que des N/A)
            essential_fields = ['nom', 'prenom', 'section']
            if all(improved_prop.get(field) in ['N/A', None, ''] for field in essential_fields):
                logger.warning(f"Propriété ignorée car trop incomplète dans {filename}")
                continue
            
            improved.append(improved_prop)
        
        logger.info(f"Amélioration terminée: {len(properties)} → {len(improved)} propriété(s) pour {filename}")
        return improved

    def conservative_na_recovery(self, properties: List[Dict], filename: str) -> List[Dict]:
        """
        Récupération conservatrice des N/A - SEULEMENT si très confiant.
        Préserve la précision en étant très prudent.
        """
        if not properties:
            return []
        
        logger.info(f"🔍 Récupération conservatrice pour {filename}")
        
        # Analyser les patterns CONFIRMÉS uniquement
        confirmed_depts = [p.get('department') for p in properties 
                          if p.get('department') and p.get('department') != 'N/A']
        confirmed_communes = [p.get('commune') for p in properties 
                             if p.get('commune') and p.get('commune') != 'N/A']
        
        best_dept = None
        best_commune = None
        
        # Récupération département
        if confirmed_depts:
            # Seulement si >60% des propriétés ont le même département
            dept_counts = {}
            for d in confirmed_depts:
                dept_counts[d] = dept_counts.get(d, 0) + 1
            total_props = len([p for p in properties if p.get('nom') != 'N/A'])
            if total_props > 0:
                most_common_dept, count = max(dept_counts.items(), key=lambda x: x[1])
                if count > total_props * 0.6:  # 60% minimum
                    best_dept = most_common_dept
                    logger.info(f"✅ Département dominant détecté: {best_dept} ({count}/{total_props})")
        
        # Récupération commune
        if confirmed_communes:
            commune_counts = {}
            for c in confirmed_communes:
                commune_counts[c] = commune_counts.get(c, 0) + 1
            if commune_counts:
                most_common_commune, count = max(commune_counts.items(), key=lambda x: x[1])
                if count >= 2:  # Au moins 2 occurrences
                    best_commune = most_common_commune
                    logger.info(f"✅ Commune dominante détectée: {best_commune} ({count} occurrences)")
        
        # Récupération PRUDENTE depuis codes postaux (seulement si pas de département/commune trouvé)
        if not best_dept or not best_commune:
            postcodes = [p.get('post_code') for p in properties 
                        if p.get('post_code') and p.get('post_code') != 'N/A']
            if len(postcodes) >= 2:
                pc_info = {}
                for pc in postcodes:
                    if len(str(pc)) >= 2 and str(pc)[:2].isdigit():
                        dept = str(pc)[:2]
                        pc_info[dept] = pc_info.get(dept, 0) + 1
                
                if pc_info and not best_dept:
                    most_common_pc_dept, count = max(pc_info.items(), key=lambda x: x[1])
                    if count >= 2:  # Au moins 2 occurrences identiques
                        best_dept = most_common_pc_dept
                        logger.info(f"✅ Département déduit PRUDEMMENT des CP: {best_dept} ({count} occurrences)")
        
        # Application conservatrice
        recovered = []
        dept_applied = 0
        commune_applied = 0
        
        for prop in properties:
            new_prop = prop.copy()
            
            # Application SEULEMENT si très confiant ET c'est un vrai propriétaire
            if new_prop.get('nom') != 'N/A' and new_prop.get('prenom') != 'N/A':
                
                # Appliquer département
                if new_prop.get('department') == 'N/A' and best_dept:
                    new_prop['department'] = best_dept
                    dept_applied += 1
                
                # Appliquer commune (seulement si on a déjà un département valide)
                if (new_prop.get('commune') == 'N/A' and best_commune and 
                    new_prop.get('department') != 'N/A'):
                    new_prop['commune'] = best_commune
                    commune_applied += 1
            
            recovered.append(new_prop)
        
        if dept_applied > 0 or commune_applied > 0:
            logger.info(f"✅ Appliqué: {dept_applied} département(s), {commune_applied} commune(s)")
        else:
            logger.info(f"⚠️  Aucune récupération appliquée - précision préservée")
        
        return recovered

    def process_single_pdf(self, pdf_path: Path) -> List[Dict]:
        """
        Traite un seul fichier PDF et retourne les informations extraites.
        
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
        all_page_data = []
        for page_num, image_data in enumerate(images, 1):
            logger.info(f"Extraction des données de la page {page_num}/{len(images)} pour {pdf_path.name}")
            extracted_data = self.extract_info_with_gpt4o(image_data, f"{pdf_path.name} (page {page_num})")
            if extracted_data and 'proprietes' in extracted_data:
                # Ajouter le numéro de page à chaque propriété pour le suivi
                for prop in extracted_data['proprietes']:
                    prop['_source_page'] = page_num
                all_page_data.append({
                    'page': page_num,
                    'data': extracted_data['proprietes']
                })
            elif extracted_data is None:
                logger.warning(f"❌ Échec de l'extraction pour la page {page_num} de {pdf_path.name}")
        
        if not all_page_data:
            logger.error(f"❌ Aucune donnée extraite pour {pdf_path.name}")
            return []
        
        # Combiner intelligemment les données des pages
        combined_properties = self.combine_multi_page_data(all_page_data, pdf_path.name)
        
        # Améliorer les données extraites
        improved_properties = self.improve_extracted_data(combined_properties, pdf_path.name)
        
        # Récupérer la récupération conservatrice
        recovered_properties = self.conservative_na_recovery(improved_properties, pdf_path.name)
        
        # Traiter chaque propriété combinée
        processed_properties = []
        for property_data in recovered_properties:
            # Générer l'ID unique avec les nouvelles colonnes
            unique_id = self.generate_unique_id(
                department=property_data.get('department', '00'),
                commune=property_data.get('commune', '000'),
                section=property_data.get('section', 'A'),
                numero=property_data.get('numero', '0000'),
                prefixe=property_data.get('prefixe', '')
            )
            
            # Ajouter l'ID unique et le fichier source
            property_data['id'] = unique_id
            property_data['fichier_source'] = pdf_path.name
            
            # Nettoyer les champs techniques
            property_data.pop('_source_page', None)
            
            processed_properties.append(property_data)
        
        logger.info(f"✅ {pdf_path.name} traité avec succès - {len(processed_properties)} propriété(s)")
        return processed_properties

    def combine_multi_page_data(self, all_page_data: List[Dict], filename: str) -> List[Dict]:
        """
        Combine intelligemment les données de plusieurs pages.
        
        Args:
            all_page_data: Liste des données extraites par page
            filename: Nom du fichier pour le logging
            
        Returns:
            Liste des propriétés combinées
        """
        if len(all_page_data) == 1:
            # Une seule page, retourner directement
            return all_page_data[0]['data']
        
        # Analyser le contenu de chaque page
        owner_pages = []  # Pages avec principalement des infos propriétaires
        property_pages = []  # Pages avec principalement des infos parcelles
        complete_pages = []  # Pages avec infos complètes
        
        for page_info in all_page_data:
            page_num = page_info['page']
            properties = page_info['data']
            
            # Analyser chaque propriété de la page
            owner_info_count = 0
            property_info_count = 0
            complete_count = 0
            
            for prop in properties:
                has_owner_info = self.has_complete_owner_info(prop)
                has_property_info = self.has_complete_property_info(prop)
                
                if has_owner_info and has_property_info:
                    complete_count += 1
                elif has_owner_info:
                    owner_info_count += 1
                elif has_property_info:
                    property_info_count += 1
            
            # Classifier la page
            if complete_count > 0:
                complete_pages.append(page_info)
                logger.info(f"Page {page_num} de {filename}: {complete_count} propriété(s) complète(s)")
            elif owner_info_count > property_info_count:
                owner_pages.append(page_info)
                logger.info(f"Page {page_num} de {filename}: principalement des infos propriétaires ({owner_info_count})")
            elif property_info_count > owner_info_count:
                property_pages.append(page_info)
                logger.info(f"Page {page_num} de {filename}: principalement des infos parcelles ({property_info_count})")
            else:
                complete_pages.append(page_info)
                logger.info(f"Page {page_num} de {filename}: contenu mixte")
        
        # Stratégie de combinaison
        if complete_pages:
            # Si on a des pages complètes, les utiliser en priorité
            combined = []
            for page_info in complete_pages:
                combined.extend(page_info['data'])
            
            # Ajouter les données des autres pages si elles apportent des infos supplémentaires
            if owner_pages or property_pages:
                combined.extend(self.merge_incomplete_pages(owner_pages, property_pages, filename))
            
            return combined
        
        elif owner_pages and property_pages:
            # Combiner les pages d'infos propriétaires avec les pages d'infos parcelles
            logger.info(f"Combinaison des pages séparées pour {filename}")
            return self.merge_incomplete_pages(owner_pages, property_pages, filename)
        
        else:
            # Fallback : combiner toutes les données
            combined = []
            for page_info in all_page_data:
                combined.extend(page_info['data'])
            return combined

    def has_complete_owner_info(self, prop: Dict) -> bool:
        """Vérifie si une propriété a des informations complètes sur le propriétaire."""
        required_fields = ['nom', 'prenom']
        optional_fields = ['voie', 'post_code', 'city', 'numero_majic']
        
        # Au moins les champs requis
        has_required = all(prop.get(field, 'N/A') not in ['N/A', '', None] for field in required_fields)
        
        # Au moins un champ optionnel
        has_optional = any(prop.get(field, 'N/A') not in ['N/A', '', None] for field in optional_fields)
        
        return has_required and has_optional

    def has_complete_property_info(self, prop: Dict) -> bool:
        """Vérifie si une propriété a des informations complètes sur la parcelle."""
        required_fields = ['section', 'numero']
        optional_fields = ['department', 'commune', 'contenance', 'designation_parcelle']
        
        # Au moins les champs requis
        has_required = all(prop.get(field, 'N/A') not in ['N/A', '', None] for field in required_fields)
        
        # Au moins un champ optionnel
        has_optional = any(prop.get(field, 'N/A') not in ['N/A', '', None] for field in optional_fields)
        
        return has_required and has_optional

    def merge_incomplete_pages(self, owner_pages: List[Dict], property_pages: List[Dict], filename: str) -> List[Dict]:
        """
        Fusionne les pages avec infos propriétaires et les pages avec infos parcelles.
        
        Args:
            owner_pages: Pages avec infos propriétaires
            property_pages: Pages avec infos parcelles
            filename: Nom du fichier pour le logging
            
        Returns:
            Liste des propriétés fusionnées
        """
        if not owner_pages or not property_pages:
            # Si on n'a qu'un type, retourner tout
            all_data = []
            for page_info in owner_pages + property_pages:
                all_data.extend(page_info['data'])
            return all_data
        
        # Extraire les données
        owners = []
        properties = []
        
        for page_info in owner_pages:
            owners.extend(page_info['data'])
        
        for page_info in property_pages:
            properties.extend(page_info['data'])
        
        logger.info(f"Fusion de {len(owners)} propriétaire(s) avec {len(properties)} parcelle(s) pour {filename}")
        
        # Stratégie de fusion
        merged = []
        
        if len(owners) == 1 and len(properties) >= 1:
            # Un propriétaire, plusieurs parcelles
            owner = owners[0]
            for prop in properties:
                merged_prop = self.merge_owner_and_property(owner, prop)
                merged.append(merged_prop)
        
        elif len(owners) >= 1 and len(properties) == 1:
            # Plusieurs propriétaires, une parcelle (rare mais possible)
            prop = properties[0]
            for owner in owners:
                merged_prop = self.merge_owner_and_property(owner, prop)
                merged.append(merged_prop)
        
        elif len(owners) == len(properties):
            # Même nombre, fusion 1:1
            for i in range(len(owners)):
                merged_prop = self.merge_owner_and_property(owners[i], properties[i])
                merged.append(merged_prop)
        
        else:
            # Cas complexe : essayer de faire correspondre intelligemment
            logger.warning(f"Cas complexe de fusion pour {filename}: {len(owners)} propriétaires, {len(properties)} parcelles")
            
            # Stratégie : chaque propriétaire avec chaque parcelle
            for owner in owners:
                for prop in properties:
                    merged_prop = self.merge_owner_and_property(owner, prop)
                    merged.append(merged_prop)
        
        logger.info(f"Fusion terminée: {len(merged)} propriété(s) créée(s)")
        return merged

    def merge_owner_and_property(self, owner: Dict, prop: Dict) -> Dict:
        """
        Fusionne les informations d'un propriétaire avec celles d'une propriété.
        
        Args:
            owner: Données du propriétaire
            prop: Données de la propriété
            
        Returns:
            Propriété fusionnée
        """
        merged = {}
        
        # Priorité aux infos propriétaire pour les champs propriétaire
        owner_fields = ['nom', 'prenom', 'adresse_proprietaire', 'post_code', 'city', 'numero_proprietaire']
        for field in owner_fields:
            merged[field] = owner.get(field, prop.get(field, 'N/A'))
        
        # Priorité aux infos propriété pour les champs propriété
        property_fields = ['section', 'numero_plan', 'street_address', 'contenance', 'droit_reel', 'department', 'commune', 'HA', 'A', 'CA']
        for field in property_fields:
            merged[field] = prop.get(field, owner.get(field, 'N/A'))
        
        # Garder la source de page pour le debug
        merged['_source_page'] = f"{owner.get('_source_page', '?')},{prop.get('_source_page', '?')}"
        
        return merged

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
        
        # Réorganiser les colonnes selon les spécifications
        columns_order = [
            'nom', 'prenom', 'adresse_proprietaire', 'post_code', 'city',
            'department', 'commune', 'numero_proprietaire', 'droit_reel',
            'section', 'numero_plan', 'street_address',
            'contenance', 'HA', 'A', 'CA', 'id_parcelle', 'fichier_source'
        ]
        
        # Renommer les colonnes pour plus de clarté
        column_mapping = {
            'nom': 'Nom',
            'prenom': 'Prénom',
            'adresse_proprietaire': 'Adresse Propriétaire',
            'post_code': 'CP',
            'city': 'Ville',
            'department': 'Département',
            'commune': 'Commune',
            'numero_proprietaire': 'Numéro MAJIC',
            'droit_reel': 'Droit réel',
            'section': 'Section',
            'numero_plan': 'N° Plan',
            'street_address': 'Adresse Propriété',
            'contenance': 'Contenance',
            'HA': 'Hectares',
            'A': 'Ares',
            'CA': 'Centiares',
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
        logger.info(f"📈 Total: {len(all_properties)} propriété(s) dans {len(df['Fichier source'].unique())} fichier(s)")

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