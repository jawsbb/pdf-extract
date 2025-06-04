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
                    
                    # Convertir chaque page en image avec une résolution MAXIMALE
                    mat = fitz.Matrix(5.0, 5.0)  # ULTRA-HAUTE résolution pour extraction optimale
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
        EXTRACTION ULTRA-OPTIMISÉE pour extraire TOUTES les informations possibles.
        
        Args:
            image_data: Données de l'image en bytes
            filename: Nom du fichier pour le logging
            
        Returns:
            Dictionnaire contenant les informations extraites ou None en cas d'erreur
        """
        try:
            logger.info(f"🔍 Extraction ADAPTATIVE pour {filename}")
            
            # PHASE 1: DÉTECTION AUTOMATIQUE du format PDF
            format_info = self.detect_pdf_format(image_data)
            logger.info(f"📊 Format: {format_info.get('document_type')} | Époque: {format_info.get('format_era')} | Layout: {format_info.get('layout')}")
            
            # Encoder l'image en base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # PHASE 2: PROMPT ADAPTATIF selon le format détecté
            adapted_prompt = self.adapt_extraction_prompt(format_info)
            
            # PROMPT ADAPTATIF remplace l'ancien prompt fixe
            # (L'ancien prompt ultra-détaillé est maintenant dans adapt_extraction_prompt)
            logger.info(f"🎯 Utilisation stratégie: {format_info.get('extraction_strategy')}")
            
            # Fallback: si la détection échoue, utiliser le prompt ultra-détaillé original
            if not adapted_prompt:
                adapted_prompt = """
🎯 MISSION CRITIQUE: Tu es un expert en documents cadastraux français. Tu DOIS extraire TOUTES les informations visibles avec une précision maximale.

📋 STRATÉGIE D'EXTRACTION EXHAUSTIVE:

1️⃣ LOCALISATION (priorité absolue):
- Cherche en HAUT du document: codes comme "51179", "25227", "75001" 
- Format: DEPARTMENT(2 chiffres) + COMMUNE(3 chiffres)
- Exemples: "51179" = département 51, commune 179

2️⃣ PROPRIÉTAIRES (scan complet):
- Noms en MAJUSCULES: MARTIN, DUPONT, LAMBIN, etc.
- Prénoms: Jean, Marie, Didier Jean Guy, etc.
- Codes MAJIC: M8BNF6, MB43HC, P7QR92 (alphanumériques 6 caractères)

3️⃣ PARCELLES (détection fine):
- Sections: A, AB, ZY, 000ZD, etc.
- Numéros: 6, 0006, 123, 0123, etc.
- Contenance: 230040, 000150, 002300 (format chiffres)

4️⃣ ADRESSES (lecture complète):
- Voies: "1 RUE D AVAT", "15 AVENUE DE LA PAIX"
- Codes postaux: 51240, 75001, 13000
- Villes: COUPEVILLE, PARIS, MARSEILLE

5️⃣ DROITS RÉELS:
- PP = Pleine Propriété
- US = Usufruit  
- NU = Nue-propriété

📊 EXEMPLES CONCRETS DE DONNÉES RÉELLES:

EXEMPLE 1:
{
  "department": "51",
  "commune": "179", 
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

EXEMPLE 2:
{
  "department": "25",
  "commune": "227",
  "section": "000ZD",
  "numero": "0005",
  "contenance": "000150",
  "droit_reel": "PP",
  "designation_parcelle": "LE GRAND CHAMP",
  "nom": "MARTIN",
  "prenom": "PIERRE",
  "numero_majic": "MB43HC",
  "voie": "15 RUE DE LA PAIX",
  "post_code": "25000",
  "city": "BESANCON"
}

🔍 INSTRUCTIONS DE SCAN SYSTÉMATIQUE:

1. Commence par scanner TOUT LE HAUT du document pour les codes département/commune
2. Lit TOUS les noms en majuscules (ce sont les propriétaires)
3. Trouve TOUS les codes MAJIC (6 caractères alphanumériques)
4. Récupère TOUTES les adresses complètes
5. Identifie TOUTES les sections et numéros de parcelles
6. Collecte TOUTES les contenances (surfaces)

⚠️ RÈGLES STRICTES:
- Si tu vois une information partiellement, INCLUS-LA quand même
- Ne mets JAMAIS "N/A" - utilise "" si vraiment absent
- Scan CHAQUE ZONE du document méthodiquement
- IGNORE aucun détail, même petit
- Retourne TOUS les propriétaires trouvés

📤 FORMAT DE RÉPONSE OBLIGATOIRE:
{
  "proprietes": [
    {
      "department": "XX",
      "commune": "XXX",
      "prefixe": "",
      "section": "XXXX",
      "numero": "XXXX",
      "contenance": "XXXXXX",
      "droit_reel": "XX",
      "designation_parcelle": "LIEU-DIT",
      "nom": "NOM_PROPRIETAIRE",
      "prenom": "PRENOM_PROPRIETAIRE",
      "numero_majic": "XXXXXX",
      "voie": "ADRESSE_COMPLETE",
      "post_code": "XXXXX",
      "city": "VILLE"
    }
  ]
}

🎯 OBJECTIF: ZÉRO champ vide si l'info existe dans le document !
"""
            
            # PREMIÈRE PASSE: Extraction principale ultra-détaillée
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": adapted_prompt},
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
                max_tokens=4000,
                temperature=0.0
            )
            
            # Parser la réponse JSON
            response_text = response.choices[0].message.content.strip()
            
            # Nettoyer la réponse
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            try:
                main_result = json.loads(response_text)
                
                if "proprietes" in main_result and main_result["proprietes"]:
                    properties = main_result["proprietes"]
                    logger.info(f"✅ Extraction principale: {len(properties)} propriété(s) pour {filename}")
                    
                    # DEUXIÈME PASSE: Récupération des champs manquants
                    enhanced_properties = self.enhance_missing_fields(properties, base64_image, filename)
                    
                    if enhanced_properties:
                        logger.info(f"🚀 Extraction ULTRA-OPTIMISÉE terminée: {len(enhanced_properties)} propriété(s) pour {filename}")
                        return {"proprietes": enhanced_properties}
                    else:
                        return main_result
                else:
                    logger.warning(f"❌ Extraction principale sans résultat pour {filename}")
                    # PASSE DE SECOURS: Extraction d'urgence
                    return self.emergency_extraction(base64_image, filename)
                    
            except json.JSONDecodeError as e:
                logger.error(f"Erreur JSON pour {filename}: {e}")
                logger.error(f"Réponse: {response_text[:500]}...")
                # PASSE DE SECOURS en cas d'erreur JSON
                return self.emergency_extraction(base64_image, filename)
                
        except Exception as e:
            logger.error(f"Erreur extraction pour {filename}: {e}")
            return None

    def enhance_missing_fields(self, properties: List[Dict], base64_image: str, filename: str) -> List[Dict]:
        """
        DEUXIÈME PASSE: Amélioration ciblée des champs manquants.
        """
        try:
            # Analyser quels champs sont manquants
            missing_fields = {}
            critical_fields = ['department', 'commune', 'nom', 'prenom', 'section', 'numero']
            
            for prop in properties:
                for field in critical_fields:
                    if not prop.get(field) or prop.get(field) == "":
                        if field not in missing_fields:
                            missing_fields[field] = 0
                        missing_fields[field] += 1
            
            if not missing_fields:
                logger.info(f"✅ Tous les champs critiques présents pour {filename}")
                return properties
            
            logger.info(f"🔍 Récupération ciblée pour {filename}: {missing_fields}")
            
            # Prompt ciblé pour les champs manquants les plus critiques
            if 'department' in missing_fields or 'commune' in missing_fields:
                properties = self.extract_location_info(properties, base64_image, filename)
            
            if 'nom' in missing_fields or 'prenom' in missing_fields:
                properties = self.extract_owner_info(properties, base64_image, filename)
            
            return properties
            
        except Exception as e:
            logger.error(f"Erreur enhancement pour {filename}: {e}")
            return properties

    def extract_location_info(self, properties: List[Dict], base64_image: str, filename: str) -> List[Dict]:
        """Extraction ciblée des informations de localisation."""
        try:
            location_prompt = """
🎯 MISSION SPÉCIALISÉE: Trouve les codes département et commune dans ce document cadastral.

🔍 RECHERCHE INTENSIVE:
- Scan le HEADER du document
- Cherche des codes à 5 chiffres comme: 51179, 25227, 75001
- Format: 2 chiffres département + 3 chiffres commune
- Peut être écrit: 51 179, 51-179, ou 51179

Exemples typiques:
- "51179" → département: "51", commune: "179"
- "25227" → département: "25", commune: "227"
- "75001" → département: "75", commune: "001"

📤 RÉPONSE FORMAT:
{
  "location": {
    "department": "XX",
    "commune": "XXX"
  }
}

⚠️ CRUCIAL: Ces codes sont TOUJOURS dans l'en-tête du document !
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": location_prompt},
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
                max_tokens=500,
                temperature=0.0
            )
            
            location_text = response.choices[0].message.content.strip()
            if "```json" in location_text:
                location_text = location_text.split("```json")[1].split("```")[0].strip()
            
            location_data = json.loads(location_text)
            
            if "location" in location_data:
                dept = location_data["location"].get("department")
                commune = location_data["location"].get("commune")
                
                if dept or commune:
                    for prop in properties:
                        if not prop.get("department") and dept:
                            prop["department"] = dept
                        if not prop.get("commune") and commune:
                            prop["commune"] = commune
                    
                    logger.info(f"✅ Localisation récupérée: dept={dept}, commune={commune}")
            
        except Exception as e:
            logger.warning(f"Erreur extraction localisation: {e}")
        
        return properties

    def extract_owner_info(self, properties: List[Dict], base64_image: str, filename: str) -> List[Dict]:
        """Extraction ciblée des informations propriétaires."""
        try:
            owner_prompt = """
🎯 MISSION: Trouve TOUS les propriétaires dans ce document cadastral.

🔍 RECHERCHE SYSTÉMATIQUE:
- Noms en MAJUSCULES: MARTIN, DUPONT, LAMBIN, BERNARD, etc.
- Prénoms: Jean, Marie, Pierre, Didier Jean Guy, etc.
- Codes MAJIC: M8BNF6, MB43HC, P7QR92 (6 caractères alphanumériques)
- Adresses complètes: "1 RUE D AVAT", "15 AVENUE DE LA PAIX"

📤 FORMAT RÉPONSE:
{
  "owners": [
    {
      "nom": "NOM_MAJUSCULE",
      "prenom": "Prénom Complet",
      "numero_majic": "XXXXXX",
      "voie": "Adresse complète",
      "post_code": "XXXXX",
      "city": "VILLE"
    }
  ]
}

⚠️ Scan TOUT le document pour les propriétaires !
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": owner_prompt},
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
                max_tokens=2000,
                temperature=0.0
            )
            
            owner_text = response.choices[0].message.content.strip()
            if "```json" in owner_text:
                owner_text = owner_text.split("```json")[1].split("```")[0].strip()
            
            owner_data = json.loads(owner_text)
            
            if "owners" in owner_data and owner_data["owners"]:
                owners = owner_data["owners"]
                
                # Fusionner avec les propriétés existantes
                for i, prop in enumerate(properties):
                    if i < len(owners):
                        owner = owners[i]
                        for field in ['nom', 'prenom', 'numero_majic', 'voie', 'post_code', 'city']:
                            if not prop.get(field) and owner.get(field):
                                prop[field] = owner[field]
                
                logger.info(f"✅ Propriétaires récupérés: {len(owners)}")
        
        except Exception as e:
            logger.warning(f"Erreur extraction propriétaires: {e}")
        
        return properties

    def emergency_extraction(self, base64_image: str, filename: str) -> Optional[Dict]:
        """
        EXTRACTION D'URGENCE: Dernière tentative avec prompt ultra-simple.
        """
        try:
            logger.info(f"🚨 Extraction d'urgence pour {filename}")
            
            emergency_prompt = """
Regarde ce document cadastral français et trouve:
1. Tous les NOMS en MAJUSCULES
2. Tous les codes à 5 chiffres (département+commune)
3. Toutes les sections (lettres comme A, ZY)
4. Tous les numéros de parcelles

Retourne TOUT ce que tu vois en JSON:
{
  "proprietes": [
    {
      "department": "",
      "commune": "",
      "section": "",
      "numero": "",
      "nom": "",
      "prenom": "",
      "voie": "",
      "city": ""
    }
  ]
}
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": emergency_prompt},
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
                max_tokens=2000,
                temperature=0.1
            )
            
            emergency_text = response.choices[0].message.content.strip()
            if "```json" in emergency_text:
                emergency_text = emergency_text.split("```json")[1].split("```")[0].strip()
            
            result = json.loads(emergency_text)
            if "proprietes" in result and result["proprietes"]:
                logger.info(f"🆘 Extraction d'urgence réussie: {len(result['proprietes'])} propriété(s)")
                return result
            
        except Exception as e:
            logger.error(f"Échec extraction d'urgence pour {filename}: {e}")
        
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
        Traite un PDF MULTI-PAGES avec fusion intelligente des données.
        
        Args:
            pdf_path: Chemin vers le fichier PDF
            
        Returns:
            Liste des propriétaires avec leurs informations fusionnées
        """
        logger.info(f"🔄 Traitement MULTI-PAGES de {pdf_path.name}")
        
        # Convertir en images
        images = self.pdf_to_images(pdf_path)
        if not images:
            logger.error(f"❌ Échec de la conversion en images pour {pdf_path.name}")
            return []
        
        # PHASE 1: Extraction de TOUTES les pages
        all_page_data = []
        for page_num, image_data in enumerate(images, 1):
            logger.info(f"📄 Extraction page {page_num}/{len(images)} pour {pdf_path.name}")
            extracted_data = self.extract_info_with_gpt4o(image_data, f"{pdf_path.name} (page {page_num})")
            if extracted_data and 'proprietes' in extracted_data:
                all_page_data.extend(extracted_data['proprietes'])
                logger.info(f"✅ Page {page_num}: {len(extracted_data['proprietes'])} élément(s) extraits")
            else:
                logger.warning(f"⚠️ Page {page_num}: aucune donnée extraite")
        
        if not all_page_data:
            logger.error(f"❌ Aucune donnée extraite de {pdf_path.name}")
            return []
        
        logger.info(f"📊 Total éléments bruts extraits: {len(all_page_data)}")
        
        # PHASE 2: FUSION INTELLIGENTE multi-pages
        merged_properties = self.smart_merge_multi_page_data(all_page_data, pdf_path.name)
        
        # PHASE 3: Finalisation avec IDs uniques
        final_properties = []
        for prop in merged_properties:
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
            
            final_properties.append(prop)
        
        logger.info(f"🎉 {pdf_path.name} FUSIONNÉ avec succès - {len(final_properties)} propriété(s) complète(s)")
        return final_properties

    def detect_pdf_format(self, image_data: bytes) -> Dict:
        """
        DÉTECTE automatiquement le type/format du PDF cadastral.
        Chaque département/commune a son propre format !
        """
        detection_prompt = """
        Tu es un expert en documents cadastraux français. Analyse cette image et détermine :

        1. TYPE DE DOCUMENT :
           - Extrait cadastral (avec propriétaires)
           - Matrice cadastrale  
           - État de section
           - Plan cadastral
           - Autre

        2. FORMAT/ÉPOQUE :
           - Moderne (post-2010) - tableaux structurés, codes MAJIC
           - Intermédiaire (2000-2010) - semi-structuré
           - Ancien (pré-2000) - format libre

        3. MISE EN PAGE :
           - Une seule page avec tout
           - Multi-pages (info dispersée)
           - Tableau structuré
           - Texte libre

        4. INFORMATIONS VISIBLES :
           - Département/commune en en-tête
           - Codes MAJIC visibles (6 chars alphanumériques)
           - Parcelles avec sections/numéros
           - Propriétaires avec noms/prénoms
           - Adresses complètes

        Réponds en JSON :
        {
            "document_type": "extrait|matrice|section|plan|autre",
            "format_era": "moderne|intermediaire|ancien", 
            "layout": "single_page|multi_page|tableau|texte_libre",
            "visible_info": {
                "location_header": true/false,
                "majic_codes": true/false,
                "parcels_listed": true/false,
                "owners_listed": true/false,
                "addresses_present": true/false
            },
            "extraction_strategy": "complete|location_focus|parcel_focus|owner_focus|mixed"
        }
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": detection_prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64.b64encode(image_data).decode()}"}}
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            detection_result = json.loads(response.choices[0].message.content.strip())
            logger.info(f"🔍 Format détecté: {detection_result.get('document_type')} - {detection_result.get('format_era')} - Stratégie: {detection_result.get('extraction_strategy')}")
            return detection_result
            
        except Exception as e:
            logger.warning(f"⚠️ Échec détection format: {e}")
            # Format par défaut pour extraction maximale
            return {
                "document_type": "extrait",
                "format_era": "moderne", 
                "layout": "multi_page",
                "visible_info": {
                    "location_header": True,
                    "majic_codes": True,
                    "parcels_listed": True,
                    "owners_listed": True,
                    "addresses_present": True
                },
                "extraction_strategy": "complete"
            }

    def adapt_extraction_prompt(self, format_info: Dict) -> str:
        """
        ADAPTE le prompt d'extraction selon le format détecté.
        Chaque type de PDF nécessite une approche différente !
        """
        base_examples = """
🎯 EXEMPLES ULTRA-PRÉCIS avec TOUTES les colonnes importantes:

EXEMPLE DÉPARTEMENT 51:
{
  "department": "51",
  "commune": "179", 
  "prefixe": "",
  "section": "000ZE",
  "numero": "0025",
  "contenance": "001045",     ⬅️ CONTENANCE = SURFACE en m² (OBLIGATOIRE!)
  "droit_reel": "US",
  "designation_parcelle": "LES ROULLIERS",
  "nom": "LAMBIN",
  "prenom": "DIDIER JEAN GUY",
  "numero_majic": "M8BNF6",
  "voie": "1 RUE D AVAT",
  "post_code": "51240",
  "city": "COUPEVILLE"
}

EXEMPLE DÉPARTEMENT 25:
{
  "department": "25",
  "commune": "227",
  "prefixe": "",
  "section": "000ZD",
  "numero": "0005",
  "contenance": "000150",     ⬅️ SURFACE = 150m² (CHERCHE ça partout!)
  "droit_reel": "PP",
  "designation_parcelle": "LE GRAND CHAMP",
  "nom": "MARTIN",
  "prenom": "PIERRE",
  "numero_majic": "MB43HC",
  "voie": "15 RUE DE LA PAIX", 
  "post_code": "25000",
  "city": "BESANCON"
}
"""

        # Adaptations selon le format détecté
        if format_info.get('document_type') == 'matrice':
            specific_instructions = """
🎯 DOCUMENT TYPE: MATRICE CADASTRALE
- Focus sur les TABLES avec colonnes structurées
- Propriétaires souvent dans colonne de droite
- Parcelles dans colonnes de gauche
- ⭐ CONTENANCE dans colonne "Surface" ou "Cont." ou chiffres + m²
- Scan ligne par ligne méthodiquement
"""
        elif format_info.get('layout') == 'tableau':
            specific_instructions = """
🎯 FORMAT: TABLEAU STRUCTURÉ
- Identifie les EN-TÊTES de colonnes
- Cherche colonnes: "Surface", "Contenance", "m²", "ares", "ca"
- Lit chaque LIGNE du tableau
- Associe chaque valeur à sa colonne
- ⭐ CONTENANCE = valeurs numériques dans colonnes surface
- Attention aux cellules fusionnées
"""
        elif format_info.get('format_era') == 'ancien':
            specific_instructions = """
🎯 FORMAT: ANCIEN/LIBRE
- Scan TOUT le texte zone par zone
- Cherche les motifs : "NOM Prénom", codes, adresses
- Les infos peuvent être DISPERSÉES
- Utilise le contexte pour regrouper
"""
        else:
            specific_instructions = """
🎯 FORMAT: MODERNE/STANDARD
- Scan systématique de HAUT en BAS
- En-têtes pour département/commune
- Propriétaires en MAJUSCULES
- Codes MAJIC (6 caractères)
- ⭐ CONTENANCE = recherche "m²", "ares", "ca" + chiffres associés
- Sections format "000XX" ou "XX" + numéros parcelles
"""

        # Instructions spécifiques selon ce qui est visible
        if not format_info.get('visible_info', {}).get('majic_codes'):
            majic_note = "⚠️ CODES MAJIC probablement ABSENTS - concentre-toi sur noms/adresses"
        else:
            majic_note = "🎯 CODES MAJIC PRÉSENTS - scan tous les codes 6 caractères"

        if format_info.get('extraction_strategy') == 'location_focus':
            strategy_note = "🎯 PRIORITÉ: Département/Commune/Localisation"
        elif format_info.get('extraction_strategy') == 'owner_focus':
            strategy_note = "🎯 PRIORITÉ: Propriétaires/Noms/Adresses/MAJIC"
        elif format_info.get('extraction_strategy') == 'parcel_focus':
            strategy_note = "🎯 PRIORITÉ: Parcelles/Sections/Numéros/Contenances"
        else:
            strategy_note = "🎯 EXTRACTION COMPLÈTE de TOUTES les informations"

        # Prompt adaptatif final
        adapted_prompt = f"""
Tu es un EXPERT en extraction de données cadastrales françaises. Ce document a été analysé automatiquement.

{specific_instructions}

{strategy_note}
{majic_note}

{base_examples}

🔍 INSTRUCTIONS DE SCAN ADAPTATIF ULTRA-PRÉCIS:
1. Applique la stratégie détectée ci-dessus
2. Scan MÉTHODIQUEMENT selon le type de mise en page  
3. ⭐ CONTENANCE = SURFACE : Cherche PARTOUT les chiffres suivis de "m²", "ares", "ca" (centiares)
4. ⭐ SECTION + NUMÉRO : Formats "000ZE", "ZE", "003", toujours ensemble
5. ⭐ NOMS/PRÉNOMS : MAJUSCULES = nom, minuscules = prénom  
6. ⭐ CODES MAJIC : Exactement 6 caractères alphanumériques
7. ⭐ ADRESSES : Numéro + nom de rue + code postal + ville
8. Collecte TOUTES les informations visibles
9. Regroupe intelligemment les données dispersées
10. Ne laisse RIEN passer, même les valeurs partielles

⚠️ RÈGLES STRICTES:
- ADAPTE ta lecture au format détecté
- Si info partiellement visible, INCLUS-LA
- JAMAIS de "N/A" - utilise "" si vraiment absent
- IGNORE aucun détail même petit
- Retourne TOUS les propriétaires trouvés

📤 FORMAT RÉPONSE:
{{
  "proprietes": [
    {{
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
    }}
  ]
}}
"""
        return adapted_prompt

    def smart_merge_multi_page_data(self, all_page_data: List[Dict], filename: str) -> List[Dict]:
        """
        FUSION INTELLIGENTE des données multi-pages.
        Combine les informations dispersées sur plusieurs pages en propriétés complètes.
        """
        logger.info(f"🧠 Fusion intelligente de {len(all_page_data)} éléments pour {filename}")
        
        # Séparer les données par type d'information
        location_data = {}  # département/commune communs
        owners_data = []    # propriétaires avec infos complètes
        parcels_data = []   # parcelles avec sections/numéros
        mixed_data = []     # données mixtes
        
        # PHASE 1: Classification des données extraites
        for item in all_page_data:
            has_owner = bool(item.get('nom') or item.get('prenom'))
            has_parcel = bool(item.get('section') or item.get('numero'))
            has_location = bool(item.get('department') or item.get('commune'))
            
            if has_location and not location_data:
                # Stocker les infos de localisation (département/commune)
                location_data = {
                    'department': item.get('department', ''),
                    'commune': item.get('commune', ''),
                    'post_code': item.get('post_code', ''),
                    'city': item.get('city', '')
                }
                logger.info(f"📍 Localisation trouvée: {location_data}")
            
            if has_owner and has_parcel:
                # Données complètes
                mixed_data.append(item)
            elif has_owner:
                # Données propriétaire uniquement
                owners_data.append(item)
            elif has_parcel:
                # Données parcelle uniquement  
                parcels_data.append(item)
        
        logger.info(f"📋 Classification: {len(mixed_data)} complètes, {len(owners_data)} propriétaires, {len(parcels_data)} parcelles")
        
        # PHASE 2: Stratégie de fusion selon les données disponibles
        merged_properties = []
        
        if mixed_data:
            # Cas optimal: données déjà complètes
            for item in mixed_data:
                # Enrichir avec les infos de localisation si manquantes
                if not item.get('department') and location_data.get('department'):
                    item['department'] = location_data['department']
                if not item.get('commune') and location_data.get('commune'):
                    item['commune'] = location_data['commune']
                if not item.get('post_code') and location_data.get('post_code'):
                    item['post_code'] = location_data['post_code']
                if not item.get('city') and location_data.get('city'):
                    item['city'] = location_data['city']
                
                merged_properties.append(item)
                
        elif owners_data and parcels_data:
            # Fusion propriétaires + parcelles
            logger.info(f"🔗 Fusion {len(owners_data)} propriétaires avec {len(parcels_data)} parcelles")
            
            # Stratégie: croiser chaque propriétaire avec chaque parcelle
            for owner in owners_data:
                for parcel in parcels_data:
                    merged_prop = self.merge_owner_parcel(owner, parcel, location_data)
                    merged_properties.append(merged_prop)
                    
        elif owners_data:
            # Seulement des propriétaires - enrichir avec localisation
            for owner in owners_data:
                merged_prop = owner.copy()
                # Ajouter les infos de localisation
                for key, value in location_data.items():
                    if not merged_prop.get(key) and value:
                        merged_prop[key] = value
                merged_properties.append(merged_prop)
                
        elif parcels_data:
            # Seulement des parcelles - enrichir avec localisation  
            for parcel in parcels_data:
                merged_prop = parcel.copy()
                # Ajouter les infos de localisation
                for key, value in location_data.items():
                    if not merged_prop.get(key) and value:
                        merged_prop[key] = value
                merged_properties.append(merged_prop)
        
        else:
            # Cas de secours: utiliser toutes les données brutes
            merged_properties = all_page_data
        
        # PHASE 3: Nettoyage et déduplication
        cleaned_properties = self.clean_and_deduplicate(merged_properties, filename)
        
        logger.info(f"✨ Fusion terminée: {len(cleaned_properties)} propriété(s) finales")
        return cleaned_properties

    def merge_owner_parcel(self, owner: Dict, parcel: Dict, location: Dict) -> Dict:
        """
        Fusionne intelligemment les données propriétaire + parcelle + localisation.
        """
        merged = {}
        
        # Priorité aux données propriétaire pour les champs propriétaire
        owner_fields = ['nom', 'prenom', 'numero_majic', 'voie', 'post_code', 'city']
        for field in owner_fields:
            merged[field] = owner.get(field, '')
        
        # Priorité aux données parcelle pour les champs parcelle
        parcel_fields = ['section', 'numero', 'contenance', 'droit_reel', 'designation_parcelle', 'prefixe']
        for field in parcel_fields:
            merged[field] = parcel.get(field, '')
        
        # Utiliser les données de localisation pour les champs manquants
        location_fields = ['department', 'commune', 'post_code', 'city']
        for field in location_fields:
            if not merged.get(field) and location.get(field):
                merged[field] = location[field]
        
        # Si encore des champs manquants, essayer de les récupérer de l'autre source
        for field in ['department', 'commune']:
            if not merged.get(field):
                merged[field] = owner.get(field, parcel.get(field, ''))
        
        return merged

    def clean_and_deduplicate(self, properties: List[Dict], filename: str) -> List[Dict]:
        """
        Nettoie et déduplique les propriétés fusionnées.
        """
        if not properties:
            return []
        
        cleaned = []
        seen_combinations = set()
        
        for prop in properties:
            # Créer une clé unique basée sur les champs critiques
            key_fields = [
                prop.get('nom', ''),
                prop.get('prenom', ''),
                prop.get('section', ''),
                prop.get('numero', ''),
                prop.get('numero_majic', '')
            ]
            unique_key = '|'.join(str(f).strip() for f in key_fields)
            
            # Ignorer les entrées complètement vides
            if not any(key_fields) or unique_key == '||||':
                continue
            
            # Déduplication
            if unique_key not in seen_combinations:
                seen_combinations.add(unique_key)
                
                # Assurer que tous les champs requis existent
                required_fields = [
                    'department', 'commune', 'prefixe', 'section', 'numero', 
                    'contenance', 'droit_reel', 'designation_parcelle', 
                    'nom', 'prenom', 'numero_majic', 'voie', 'post_code', 'city'
                ]
                
                for field in required_fields:
                    if field not in prop:
                        prop[field] = ''
                
                cleaned.append(prop)
        
        logger.info(f"🧹 Nettoyage: {len(properties)} → {len(cleaned)} propriétés après déduplication")
        return cleaned

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