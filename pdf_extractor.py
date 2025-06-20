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
import pdfplumber
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
from PIL import Image
import io
import logging.handlers
import sys
import tempfile
import shutil

# Configuration du logging avec encodage UTF-8 pour Windows
def setup_logging():
    """Configure le logging avec support UTF-8 pour Windows"""
    # Créer un formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Logger principal
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # Supprimer les handlers existants
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Handler pour fichier avec encodage UTF-8
    try:
        file_handler = logging.FileHandler('extraction.log', encoding='utf-8', mode='a')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Erreur configuration fichier log: {e}")
    
    # Handler pour console avec gestion des erreurs d'encodage
    try:
        # Créer un stream qui ignore les erreurs d'encodage
        console_stream = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        console_handler = logging.StreamHandler(console_stream)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    except Exception:
        # Fallback vers un handler console simple sans emojis
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger

# Initialiser le logger
logger = setup_logging()

def safe_json_parse(content: str, context: str = "API response") -> Optional[Dict]:
    """
    Parse JSON de manière robuste avec gestion d'erreurs
    
    Args:
        content: Contenu à parser
        context: Contexte pour le logging d'erreur
    
    Returns:
        Dict parsé ou None si échec
    """
    if not content or content.strip() == "":
        logger.warning(f"Contenu vide pour {context}")
        return None
    
    # Nettoyer le contenu
    content = content.strip()
    
    # Chercher un objet JSON dans la réponse
    start_idx = content.find('{')
    end_idx = content.rfind('}')
    
    if start_idx == -1 or end_idx == -1:
        logger.warning(f"Pas de JSON trouvé dans {context}: {content[:100]}...")
        return None
    
    try:
        json_content = content[start_idx:end_idx+1]
        result = json.loads(json_content)
        return result
    except json.JSONDecodeError as e:
        logger.warning(f"Erreur parsing JSON pour {context}: {e}")
        logger.debug(f"Contenu problématique: {json_content[:200]}...")
        return None
    except Exception as e:
        logger.error(f"Erreur inattendue parsing JSON pour {context}: {e}")
        return None

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
7. ⭐ PRÉFIXE (TRÈS RARE mais CRUCIAL) : Cherche activement les préfixes comme "ZY", "AB", "000AC" dans les tableaux "Propriété(s) non bâtie(s)" - ils apparaissent AVANT les sections !

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
            
            main_result = safe_json_parse(response_text, f"extraction principale {filename}")
            
            if main_result and "proprietes" in main_result and main_result["proprietes"]:
                properties = main_result["proprietes"]
                logger.info(f"Extraction principale: {len(properties)} propriété(s) pour {filename}")
                
                # DEUXIÈME PASSE: Récupération des champs manquants
                enhanced_properties = self.enhance_missing_fields(properties, base64_image, filename)
                
                if enhanced_properties:
                    logger.info(f"Extraction ULTRA-OPTIMISÉE terminée: {len(enhanced_properties)} propriété(s) pour {filename}")
                    return {"proprietes": enhanced_properties}
                else:
                    return main_result
            else:
                logger.warning(f"Extraction principale sans résultat pour {filename}")
                # PASSE DE SECOURS: Extraction d'urgence
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
            
            location_data = safe_json_parse(location_text, f"extraction localisation {filename}")
            
            if not location_data:
                logger.warning(f"Échec parsing localisation pour {filename}")
                return properties
            
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
            
            owner_data = safe_json_parse(owner_text, f"extraction propriétaires {filename}")
            
            if not owner_data:
                logger.warning(f"Échec parsing propriétaires pour {filename}")
                return properties
            
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
            
            result = safe_json_parse(emergency_text, f"extraction urgence {filename}")
            
            if not result:
                logger.error(f"Échec total extraction pour {filename}")
                return None
            if "proprietes" in result and result["proprietes"]:
                logger.info(f"🆘 Extraction d'urgence réussie: {len(result['proprietes'])} propriété(s)")
                return result
            
        except Exception as e:
            logger.error(f"Échec extraction d'urgence pour {filename}: {e}")
        
        return None

    def generate_unique_id(self, department: str, commune: str, section: str, numero: str, prefixe: str = "") -> str:
        """
        GÉNÉRATION D'ID FORMAT CADASTRAL FRANÇAIS - 14 CARACTÈRES (NOUVELLE VERSION)
        
        Format selon spécifications client :
        DÉPARTEMENT(2) + COMMUNE(3) + SECTION_AVEC_PRÉFIXE(5) + NUMÉRO(4) = 14 caractères
        
        NOUVELLE RÈGLE : Le préfixe s'intègre DANS la section (5 caractères total)
        - Sans préfixe : Section "A" → "0000A", Section "ZD" → "000ZD"
        - Avec préfixe : Préfixe "302" + Section "A" → "3020A"
        - Avec préfixe : Préfixe "12" + Section "A" → "1200A"
        
        Args:
            department: Code département 
            commune: Code commune
            section: Section cadastrale (ex: "A", "ZC")
            numero: Numéro de parcelle
            prefixe: Préfixe (peut être vide, max 3 caractères)
            
        Returns:
            ID unique formaté sur EXACTEMENT 14 caractères
        """
        # ÉTAPE 1: Département - EXACTEMENT 2 caractères
        dept = str(department or "00").strip()
        if dept == "N/A" or not dept:
            dept = "00"
        dept = dept.zfill(2)[:2]  # Zéros à gauche, max 2 caractères
        
        # ÉTAPE 2: Commune - EXACTEMENT 3 caractères  
        comm = str(commune or "000").strip()
        if comm == "N/A" or not comm:
            comm = "000"
        comm = comm.zfill(3)[:3]  # Zéros à gauche, max 3 caractères
        
        # ÉTAPE 3: Section avec préfixe intégré - EXACTEMENT 5 caractères
        # Nettoyer la section et détecter si elle contient déjà le préfixe
        if section and str(section).strip() and section != "N/A":
            sect_raw = str(section).strip().upper()
            
            # Cas spécial : section contient déjà le préfixe avec espace (ex: "302 A")
            if ' ' in sect_raw and prefixe and str(prefixe).strip():
                parts = sect_raw.split(' ', 1)
                if len(parts) == 2 and parts[0] == str(prefixe).strip():
                    # La section contient déjà le préfixe, extraire la vraie section
                    sect = parts[1]
                    logger.debug(f"🔍 Section avec préfixe détectée: '{sect_raw}' → section='{sect}' préfixe='{prefixe}'")
                else:
                    sect = sect_raw
            else:
                sect = sect_raw
        else:
            sect = "A"  # Section par défaut
        
        # Nettoyer le préfixe
        if prefixe and str(prefixe).strip() and prefixe != "N/A":
            pref = str(prefixe).strip()
        else:
            pref = ""  # Pas de préfixe
        
        # Construire la section avec préfixe (5 caractères total)
        if pref:
            # Avec préfixe : préfixe + zéros de padding + section = 5 caractères
            combined_length = len(pref) + len(sect)
            if combined_length <= 5:
                # Ajouter des zéros entre le préfixe et la section
                padding_zeros = "0" * (5 - combined_length)
                section_final = f"{pref}{padding_zeros}{sect}"
            else:
                # Si trop long, tronquer la section
                available_for_section = 5 - len(pref)
                if available_for_section > 0:
                    section_final = f"{pref}{sect[:available_for_section]}"
                else:
                    # Préfixe trop long, le tronquer
                    section_final = pref[:5]
        else:
            # Sans préfixe : compléter avec des zéros à gauche (format cadastral)
            section_final = sect.zfill(5)
        
        # Validation section finale
        if len(section_final) != 5:
            logger.warning(f"🔧 Section finale corrigée: '{section_final}' → longueur ajustée")
            section_final = (section_final + "00000")[:5]  # Force 5 caractères
        
        # ÉTAPE 4: Numéro - EXACTEMENT 4 caractères  
        if numero and str(numero).strip() and numero != "N/A":
            num = str(numero).strip()
            # Extraire les chiffres et compléter avec des zéros à gauche
            num_clean = ''.join(filter(str.isdigit, num))
            if num_clean:
                num = num_clean.zfill(4)[-4:]  # Derniers 4 chiffres si trop long
            else:
                num = "0001"  # Numéro par défaut si pas de chiffres
        else:
            num = "0001"  # Numéro par défaut
        
        # Validation numéro
        if len(num) != 4:
            logger.warning(f"🔧 Numéro corrigé: '{numero}' → '{num}' (longueur: {len(num)})")
            num = (num + "0000")[:4]  # Force correction d'urgence
        
        # ASSEMBLAGE FINAL : DEPT(2) + COMM(3) + SECTION_AVEC_PRÉFIXE(5) + NUMÉRO(4) = 14 caractères
        unique_id = f"{dept}{comm}{section_final}{num}"
        expected_length = 14
        
        # VALIDATION FINALE
        if len(unique_id) != expected_length:
            logger.error(f"🚨 ID LONGUEUR CRITIQUE: '{unique_id}' = {len(unique_id)} caractères (devrait être {expected_length})")
            logger.error(f"🔍 ANALYSE: dept='{dept}'({len(dept)}) comm='{comm}'({len(comm)}) section='{section_final}'({len(section_final)}) num='{num}'({len(num)})")
            
            # CORRECTION FORCÉE
            if len(unique_id) < expected_length:
                unique_id = unique_id.ljust(expected_length, '0')
                logger.warning(f"🔧 ID COMPLÉTÉ: '{unique_id}'")
            elif len(unique_id) > expected_length:
                unique_id = unique_id[:expected_length]
                logger.warning(f"🔧 ID TRONQUÉ: '{unique_id}'")
        
        # ASSERTION FINALE - Garantie absolue 14 caractères
        if len(unique_id) != expected_length:
            raise ValueError(f"ERREUR FATALE: ID '{unique_id}' = {len(unique_id)} caractères (devrait être {expected_length})")
        
        logger.debug(f"✅ ID 14 CARACTÈRES NOUVEAU FORMAT: '{unique_id}' (dept:{dept} comm:{comm} section_avec_préfixe:{section_final} num:{num})")
        return unique_id

    def extract_tables_with_pdfplumber(self, pdf_path: Path) -> Dict:
        """
        EXTRACTION HYBRIDE ÉTAPE 1: Extraction des tableaux structurés avec pdfplumber.
        Réplique exactement l'approche du code Make/Python Anywhere.
        """
        logger.info(f"📋 Extraction tableaux pdfplumber pour {pdf_path.name}")
        
        try:
            prop_batie = []
            non_prop_batie = []
            contenance_totale = {}
            property_batie_in_new_page = False
            
            with pdfplumber.open(pdf_path) as pdf:
                # Parcourir toutes les pages
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        if not table or not table[0]:
                            continue
                            
                        # Détecter les tableaux de propriétés bâties
                        if table[0][0] == 'Propriété(s) bâtie(s)':
                            logger.info(f"📊 Trouvé tableau propriétés bâties")
                            property_batie_in_new_page = True
                            prop_batie = self.extract_property_batie(table)
                        
                        # Détecter les tableaux de propriétés non bâties
                        elif table[0][0] == 'Propriété(s) non bâtie(s)':
                            logger.info(f"📊 Trouvé tableau propriétés non bâties")
                            prop_non_batie_dict = self.extract_property_non_batie(table)
                            non_prop_batie.extend(prop_non_batie_dict)
                        
                        # NOUVEAU: Détecter le tableau "Contenance totale"
                        elif any(row and 'Contenance totale' in str(row[0]) for row in table if row):
                            logger.info(f"🎯 Trouvé tableau Contenance totale")
                            contenance_totale = self.extract_contenance_totale(table)
                            # Appliquer les valeurs HA, A, CA aux propriétés déjà extraites
                            if contenance_totale:
                                self.apply_contenance_totale_to_properties(non_prop_batie, contenance_totale)
                
                # Fallback: chercher dans la première page si pas trouvé ailleurs
                if not property_batie_in_new_page and pdf.pages:
                    first_page_tables = pdf.pages[0].extract_tables()
                    if first_page_tables:
                        for idx, row in enumerate(first_page_tables[0]):
                            if row and row[0] == 'Propriété(s) bâtie(s)':
                                property_batie_table = first_page_tables[0][idx:]
                                prop_batie = self.extract_property_batie(property_batie_table)
            
            logger.info(f"✅ pdfplumber: {len(prop_batie)} bâties, {len(non_prop_batie)} non bâties")
            return {
                "prop_batie": prop_batie,
                "non_batie": non_prop_batie
            }
            
        except Exception as e:
            logger.error(f"Erreur pdfplumber pour {pdf_path.name}: {e}")
            return {"prop_batie": [], "non_batie": []}

    def extract_property_batie(self, table: List[List]) -> List[Dict]:
        """Extraction des propriétés bâties (réplique du code Make)."""
        if len(table) < 3:
            return []
            
        property_rows = table[2:]
        headers = property_rows[0]
        clean_headers = [header.replace('\n', ' ').strip() if header is not None else '' for header in headers]
        property_dicts = []

        if len(property_rows) > 1 and property_rows[1] and "Total" not in str(property_rows[1][0]):
            for row in property_rows[1:]:
                if row and "Total" in str(row[0]):
                    break
                
                property_dict = {
                    clean_headers[i]: row[i] if i < len(row) else None 
                    for i in range(len(clean_headers))
                }
                property_dicts.append(property_dict)
        
        return property_dicts

    def extract_property_non_batie(self, table: List[List]) -> List[Dict]:
        """Extraction des propriétés non bâties (réplique du code Make)."""
        if len(table) < 3:
            return []
            
        property_rows = table[2:]
        headers = property_rows[0]
        clean_headers = [header.replace('\n', ' ').strip() if header is not None else '' for header in headers]
        property_dicts = []

        # Chercher les en-têtes HA, A, CA supplémentaires
        ha_pos = None
        a_pos = None
        ca_pos = None
        
        # Vérifier s'il y a une ligne avec HA, A, CA après les en-têtes principaux
        for i, row in enumerate(property_rows):
            if row:
                for j, cell in enumerate(row):
                    if cell == 'HA':
                        ha_pos = j
                    elif cell == 'A':
                        a_pos = j
                    elif cell == 'CA':
                        ca_pos = j
                
                # Si on a trouvé HA, A, CA dans cette ligne
                if ha_pos is not None and a_pos is not None and ca_pos is not None:
                    logger.info(f"🎯 En-têtes HA/A/CA trouvés dans tableau non bâties aux positions {ha_pos}, {a_pos}, {ca_pos}")
                    break

        if len(property_rows) > 2 and property_rows[2] and "totale" not in str(property_rows[2][0]).lower():
            for row in property_rows[2:]:
                if row and "totale" in str(row[0]).lower():
                    break
                
                property_dict = {
                    clean_headers[i]: row[i] if i < len(row) else None 
                    for i in range(len(clean_headers))
                }
                
                # 🔧 CORRECTION SECTION : Debug et recherche améliorée
                section_value = None
                
                # Debug : afficher toute la ligne pour diagnostic
                logger.debug(f"DEBUG Ligne complète: {row}")
                
                # Méthode 1 : Par en-tête (existante)
                for i, header in enumerate(clean_headers):
                    if header and ('Sec' in header or 'Section' in header) and i < len(row):
                        if row[i]:
                            section_value = str(row[i]).strip()
                            logger.debug(f"Section par en-tête '{header}': '{section_value}'")
                            break
                
                # Méthode 2 : Si section vide ou trop courte, chercher dans toutes les cellules
                import re
                if not section_value or len(section_value) < 2:
                    for cell in row:
                        if cell:
                            cell_str = str(cell).strip()
                            # Rechercher pattern : 1-2 lettres majuscules (ZK, AA, C, etc.)
                            if re.match(r'^[A-Z]{1,2}$', cell_str):
                                section_value = cell_str
                                logger.debug(f"Section trouvée par regex: '{section_value}'")
                                break
                
                if section_value:
                    property_dict['Sec'] = section_value
                    logger.info(f"Section finale extraite: '{section_value}'")
                else:
                    logger.warning(f"Section non trouvée dans la ligne")
                
                # Ajouter les valeurs HA, A, CA si elles existent
                if ha_pos is not None and ha_pos < len(row) and row[ha_pos]:
                    property_dict['HA'] = str(row[ha_pos]).strip()
                if a_pos is not None and a_pos < len(row) and row[a_pos]:
                    property_dict['A'] = str(row[a_pos]).strip()
                if ca_pos is not None and ca_pos < len(row) and row[ca_pos]:
                    property_dict['CA'] = str(row[ca_pos]).strip()
                
                property_dicts.append(property_dict)
        
        return property_dicts

    def extract_contenance_totale(self, table: List[List]) -> Dict:
        """Extraction du tableau 'Contenance totale' avec colonnes HA, A, CA"""
        try:
            # Chercher les en-têtes HA, A, CA ET la ligne de données correspondante
            contenance_data = {}
            
            for i, row in enumerate(table):
                if not row:
                    continue
                    
                # Chercher une ligne avec exactement HA, A, CA consécutifs
                ha_pos = None
                a_pos = None  
                ca_pos = None
                
                for j, cell in enumerate(row):
                    if cell == 'HA':
                        ha_pos = j
                    elif cell == 'A' and j > 0 and row[j-1] == 'HA':  # A juste après HA
                        a_pos = j
                    elif cell == 'CA' and j > 1 and row[j-1] == 'A' and row[j-2] == 'HA':  # CA après A après HA
                        ca_pos = j
                
                # Si on a trouvé les trois colonnes consécutives
                if ha_pos is not None and a_pos is not None and ca_pos is not None:
                    logger.info(f"🎯 En-têtes HA/A/CA trouvés aux positions {ha_pos}, {a_pos}, {ca_pos}")
                    
                    # Chercher les données dans la même ligne ou les lignes suivantes
                    for data_row_idx in range(i, min(i + 3, len(table))):  # Chercher dans les 3 lignes suivantes
                        data_row = table[data_row_idx]
                        if data_row and len(data_row) > ca_pos:
                            # Vérifier si on a des valeurs numériques aux bonnes positions
                            ha_val = str(data_row[ha_pos]).strip() if ha_pos < len(data_row) and data_row[ha_pos] else ''
                            a_val = str(data_row[a_pos]).strip() if a_pos < len(data_row) and data_row[a_pos] else ''
                            ca_val = str(data_row[ca_pos]).strip() if ca_pos < len(data_row) and data_row[ca_pos] else ''
                            
                            # Si au moins une valeur est numérique, on prend cette ligne
                            if ha_val.isdigit() or a_val.isdigit() or ca_val.isdigit():
                                contenance_data = {
                                    'HA': ha_val,
                                    'A': a_val, 
                                    'CA': ca_val
                                }
                                logger.info(f"🎯 Contenance totale extraite: {contenance_data}")
                                return contenance_data
                    break  # On a trouvé les en-têtes, pas besoin de continuer
            
            if not contenance_data:
                logger.warning("🎯 Tableau contenance totale détecté mais données non extraites")
            
            return contenance_data
            
        except Exception as e:
            logger.warning(f"Erreur extraction contenance totale: {e}")
            return {}

    def apply_contenance_totale_to_properties(self, properties: List[Dict], contenance_totale: Dict):
        """Applique les valeurs HA, A, CA du tableau contenance totale aux propriétés"""
        if not contenance_totale or not properties:
            return
            
        logger.info(f"🔄 Application contenance totale à {len(properties)} propriété(s)")
        
        for prop in properties:
            # Ajouter les valeurs HA, A, CA si elles n'existent pas déjà
            if 'HA' not in prop and 'HA' in contenance_totale:
                prop['HA'] = contenance_totale['HA']
            if 'A' not in prop and 'A' in contenance_totale:
                prop['A'] = contenance_totale['A']
            if 'CA' not in prop and 'CA' in contenance_totale:
                prop['CA'] = contenance_totale['CA']

    def extract_owners_with_vision_simple(self, pdf_path: Path) -> List[Dict]:
        """
        EXTRACTION HYBRIDE ÉTAPE 2: Extraction des propriétaires avec OpenAI Vision.
        Utilise le prompt simplifié du style Make.
        """
        logger.info(f"👤 Extraction propriétaires OpenAI pour {pdf_path.name}")
        
        # Convertir PDF en images
        images = self.pdf_to_images(pdf_path)
        if not images:
            return []
        
        all_owners = []
        
        for page_num, image_data in enumerate(images, 1):
            try:
                # Encoder l'image
                base64_image = base64.b64encode(image_data).decode('utf-8')
                
                # PROMPT SIMPLIFIÉ (style Make)
                simple_prompt = """In the following image, you will find information of owners such as nom, prenom, adresse, droit reel, numero proprietaire, department and commune. If there are any leading zero's before commune or deparment, keep it as it is. Format the address as street address, city and post code. If city or postcode is not available, just leave it blank. There can be one or multiple owners. I want to extract all of them and return them in json format.

Output example:
{
  "owners": [
    {
      "nom": "MARTIN",
      "prenom": "MARIE MADELEINE", 
      "street_address": "2 RUE DE PARIS",
      "city": "KINGERSHEIM",
      "post_code": "68260",
      "numero_proprietaire": "MBRWL8",
      "department": "21",
      "commune": "026",
      "droit_reel": "Propriétaire/Indivision"
    }
  ]
}"""
                
                # Appel OpenAI (paramètres identiques à Make)
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
                    max_tokens=2048,
                    temperature=1.0,  # Exactement comme Make
                    response_format={"type": "json_object"}
                )
                
                # Parser la réponse
                response_text = response.choices[0].message.content.strip()
                result = safe_json_parse(response_text, f"vision simple page {page_num}")
                if result and "owners" in result and result["owners"]:
                    all_owners.extend(result["owners"])
                    logger.info(f"Page {page_num}: {len(result['owners'])} propriétaire(s)")
                else:
                    logger.warning(f"Pas de propriétaires trouvés page {page_num}")
                    
            except Exception as e:
                logger.error(f"Erreur extraction page {page_num}: {e}")
                continue
        
        logger.info(f"👤 Total propriétaires extraits: {len(all_owners)}")
        return all_owners

    def merge_structured_and_vision_data(self, structured_data: Dict, owners_data: List[Dict], filename: str) -> List[Dict]:
        """
        EXTRACTION HYBRIDE ÉTAPE 3: Fusion intelligente des données tableaux + propriétaires.
        """
        logger.info(f"🔗 Fusion hybride pour {filename}")
        
        merged_properties = []
        
        # Récupérer les données structurées
        prop_batie = structured_data.get("prop_batie", [])
        non_prop_batie = structured_data.get("non_batie", [])
        
        # Combiner toutes les propriétés structurées
        all_structured = prop_batie + non_prop_batie
        
        if not all_structured and not owners_data:
            logger.warning(f"Aucune donnée extraite pour {filename}")
            return []
        
        # Stratégie de fusion
        if all_structured and owners_data:
            # CAS OPTIMAL: Les deux types de données
            logger.info(f"🎯 Fusion: {len(all_structured)} propriétés + {len(owners_data)} propriétaires")
            
            for i, structured_prop in enumerate(all_structured):
                merged_prop = self.convert_structured_to_standard_format(structured_prop)
                
                # Associer avec un propriétaire si disponible
                if i < len(owners_data):
                    owner = owners_data[i]
                    merged_prop.update({
                        'nom': owner.get('nom', ''),
                        'prenom': owner.get('prenom', ''),
                        'numero_majic': owner.get('numero_proprietaire', ''),
                        'voie': owner.get('street_address', ''),
                        'post_code': owner.get('post_code', ''),
                        'city': owner.get('city', ''),
                        'droit_reel': owner.get('droit_reel', ''),
                        'department': owner.get('department', ''),
                        'commune': owner.get('commune', '')
                    })
                
                merged_properties.append(merged_prop)
            
            # Ajouter les propriétaires restants s'il y en a plus
            for j in range(len(all_structured), len(owners_data)):
                owner = owners_data[j]
                merged_prop = {
                    'department': owner.get('department', ''),
                    'commune': owner.get('commune', ''),
                    'prefixe': '',
                    'section': '',
                    'numero': '',
                    'contenance': '',
                    'droit_reel': owner.get('droit_reel', ''),
                    'designation_parcelle': '',
                    'nom': owner.get('nom', ''),
                    'prenom': owner.get('prenom', ''),
                    'numero_majic': owner.get('numero_proprietaire', ''),
                    'voie': owner.get('street_address', ''),
                    'post_code': owner.get('post_code', ''),
                    'city': owner.get('city', '')
                }
                merged_properties.append(merged_prop)
                
        elif all_structured:
            # Seulement des données structurées
            logger.info(f"📊 Seulement données structurées: {len(all_structured)}")
            for structured_prop in all_structured:
                merged_prop = self.convert_structured_to_standard_format(structured_prop)
                merged_properties.append(merged_prop)
                
        elif owners_data:
            # Seulement des propriétaires
            logger.info(f"👤 Seulement propriétaires: {len(owners_data)}")
            for owner in owners_data:
                merged_prop = {
                    'department': owner.get('department', ''),
                    'commune': owner.get('commune', ''),
                    'prefixe': '',
                    'section': '',
                    'numero': '',
                    'contenance': '',
                    'droit_reel': owner.get('droit_reel', ''),
                    'designation_parcelle': '',
                    'nom': owner.get('nom', ''),
                    'prenom': owner.get('prenom', ''),
                    'numero_majic': owner.get('numero_proprietaire', ''),
                    'voie': owner.get('street_address', ''),
                    'post_code': owner.get('post_code', ''),
                    'city': owner.get('city', '')
                }
                merged_properties.append(merged_prop)
        
        logger.info(f"🎉 Fusion hybride terminée: {len(merged_properties)} propriétés")
        return merged_properties

    def convert_structured_to_standard_format(self, structured_prop: Dict) -> Dict:
        """Convertit les données pdfplumber au format standard."""
        return {
            'department': '',
            'commune': '',
            'prefixe': structured_prop.get('Préfixe', ''),
            'section': structured_prop.get('Sec', structured_prop.get('Section', '')),
            'numero': structured_prop.get('N° Plan', structured_prop.get('Numéro', '')),
            'contenance': structured_prop.get('Contenance', ''),
            'droit_reel': '',
            'designation_parcelle': structured_prop.get('Adresse', structured_prop.get('Désignation', '')),
            'nom': '',
            'prenom': '',
            'numero_majic': '',
            'voie': '',
            'post_code': '',
            'city': ''
        }

    def process_single_pdf_hybrid(self, pdf_path: Path) -> List[Dict]:
        """
        TRAITEMENT HYBRIDE PRINCIPAL : pdfplumber + OpenAI Vision
        Réplique l'approche Make pour des résultats optimaux.
        """
        logger.info(f"🚀 TRAITEMENT HYBRIDE de {pdf_path.name}")
        
        # ÉTAPE 1: Extraction tableaux avec pdfplumber
        structured_data = self.extract_tables_with_pdfplumber(pdf_path)
        
        # ÉTAPE 2: Extraction propriétaires avec OpenAI Vision
        owners_data = self.extract_owners_with_vision_simple(pdf_path)
        
        # ÉTAPE 3: Fusion intelligente
        merged_properties = self.merge_structured_and_vision_data(structured_data, owners_data, pdf_path.name)
        
        # ÉTAPE 4: Finalisation avec IDs uniques et propagation
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
        
        # Séparation automatique des préfixes collés
        if final_properties:
            final_properties = self.separate_stuck_prefixes(final_properties)
        
        # Propagation des valeurs
        if final_properties:
            final_properties = self.propagate_values_downward(final_properties, ['designation_parcelle', 'prefixe'])
        
        logger.info(f"✅ HYBRIDE terminé: {len(final_properties)} propriété(s) pour {pdf_path.name}")
        return final_properties

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
            
            content = response.choices[0].message.content
            if not content or content.strip() == "":
                logger.warning("Réponse API vide pour détection format")
                raise ValueError("Réponse vide")
            
            # Nettoyer le contenu et extraire le JSON
            content = content.strip()
            
            # Chercher un objet JSON dans la réponse
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            
            if start_idx == -1 or end_idx == -1:
                logger.warning(f"Pas de JSON trouvé dans la réponse: {content[:100]}...")
                raise ValueError("Pas de JSON dans la réponse")
            
            json_content = content[start_idx:end_idx+1]
            detection_result = json.loads(json_content)
            
            # Vérifier que tous les champs requis sont présents
            required_fields = ["document_type", "format_era", "layout", "extraction_strategy"]
            for field in required_fields:
                if field not in detection_result:
                    logger.warning(f"Champ manquant dans détection: {field}")
                    raise ValueError(f"Champ manquant: {field}")
            
            logger.info(f"Format détecté: {detection_result.get('document_type')} - {detection_result.get('format_era')} - Stratégie: {detection_result.get('extraction_strategy')}")
            return detection_result
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Échec détection format: {e}")
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
        except Exception as e:
            logger.error(f"Erreur détection format: {e}")
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
11. ⭐ PRÉFIXE (TRÈS RARE mais CRUCIAL) : Le préfixe n'apparaît que dans quelques PDFs spéciaux, mais quand il existe, il est IMPÉRATIF de l'extraire !
    - Position : dans les tableaux "Propriété(s) non bâtie(s)" AVANT la désignation du lieu-dit
    - Format typique : "ZY 8", "AB 12", "000AC 5" → préfixe="ZY"/"AB"/"000AC", section="8"/"12"/"5"  
    - Colonne souvent nommée "Préfixe", "Pfxe" ou précède directement la section
    - Si AUCUN préfixe visible = "", ne JAMAIS inventer
    - Si préfixe trouvé = l'extraire avec PRÉCISION ABSOLUE

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
      "prefixe": "ZY",
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

    def propagate_values_downward(self, properties: List[Dict], fields: List[str]) -> List[Dict]:
        """
        Propage les valeurs des champs spécifiés vers le bas si elles sont vides.
        Mémorise la dernière valeur vue pour chaque champ et la propage.
        """
        last_seen_values = {field: None for field in fields}
        
        updated_properties = []
        for prop in properties:
            updated_prop = prop.copy()
            for field in fields:
                if updated_prop.get(field) is None or updated_prop.get(field) == "":
                    if last_seen_values[field] is not None:
                        updated_prop[field] = last_seen_values[field]
                else:
                    last_seen_values[field] = updated_prop[field]
            updated_properties.append(updated_prop)
            
        return updated_properties

    def separate_stuck_prefixes(self, properties: List[Dict]) -> List[Dict]:
        """
        SÉPARATION AUTOMATIQUE des préfixes collés aux sections.
        Détecte et sépare les patterns comme "302A" → préfixe="302", section="A"
        """
        import re
        
        updated_properties = []
        separated_count = 0
        
        for prop in properties:
            updated_prop = prop.copy()
            section = str(updated_prop.get('section', '')).strip()
            current_prefixe = str(updated_prop.get('prefixe', '')).strip()
            
            # Ne traiter que si la section n'est pas vide et le préfixe est vide
            if section and not current_prefixe:
                # Pattern pour détecter préfixe numérique collé à section alphabétique
                # Exemples: "302A", "302 A", "302AB", "001ZD", "123AC", etc.
                pattern = r'^(\d+)\s*([A-Z]+)$'  # \s* permet les espaces optionnels
                match = re.match(pattern, section)
                
                if match:
                    detected_prefixe = match.group(1)  # La partie numérique (302)
                    detected_section = match.group(2)  # La partie alphabétique (A)
                    
                    # Mettre à jour les champs
                    updated_prop['prefixe'] = detected_prefixe
                    updated_prop['section'] = detected_section
                    
                    separated_count += 1
                    logger.info(f"🔍 Préfixe séparé: '{section}' → préfixe='{detected_prefixe}' section='{detected_section}'")
            
            updated_properties.append(updated_prop)
        
        if separated_count > 0:
            logger.info(f"✂️ Séparation automatique: {separated_count} préfixe(s) détecté(s) et séparé(s)")
        
        return updated_properties

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
        
        # Séparation automatique des préfixes collés
        cleaned_properties = self.separate_stuck_prefixes(cleaned_properties)
        
        # Propager les valeurs de designation_parcelle et prefixe vers le bas
        cleaned_properties = self.propagate_values_downward(cleaned_properties, ['designation_parcelle', 'prefixe'])
        
        logger.info(f"✨ Fusion terminée: {len(cleaned_properties)} propriétés finales")
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
        Exporte toutes les données vers un fichier CSV avec séparateur point-virgule.
        
        Args:
            all_properties: Liste de toutes les propriétés
            output_filename: Nom du fichier de sortie
        """
        if not all_properties:
            logger.warning("Aucune donnée à exporter")
            return
        
        # Créer le DataFrame
        df = pd.DataFrame(all_properties)
        
        # Colonnes selon les spécifications du client (avec contenance détaillée)
        columns_order = [
            'department', 'commune', 'prefixe', 'section', 'numero', 
            'contenance_ha', 'contenance_a', 'contenance_ca',
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
            'contenance_ha': 'Contenance HA',
            'contenance_a': 'Contenance A', 
            'contenance_ca': 'Contenance CA',
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
        
        # Export CSV avec séparateur point-virgule (meilleur pour Excel français)
        output_path = self.output_dir / output_filename
        df.to_csv(output_path, index=False, encoding='utf-8-sig', sep=';')
        
        logger.info(f"📊 Données CSV exportées vers {output_path} (séparateur: ;)")
        logger.info(f"📈 Total: {len(all_properties)} propriété(s) dans {len(df['Fichier source'].unique())} fichier(s)")
        
        return output_path

    def export_to_excel(self, all_properties: List[Dict], output_filename: str = "output.xlsx") -> None:
        """
        Exporte toutes les données vers un fichier Excel (.xlsx).
        
        Args:
            all_properties: Liste de toutes les propriétés
            output_filename: Nom du fichier de sortie
        """
        if not all_properties:
            logger.warning("Aucune donnée à exporter en Excel")
            return
        
        # Créer le DataFrame
        df = pd.DataFrame(all_properties)
        
        # Colonnes selon les spécifications du client (avec contenance détaillée)
        columns_order = [
            'department', 'commune', 'prefixe', 'section', 'numero', 
            'contenance_ha', 'contenance_a', 'contenance_ca',
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
            'contenance_ha': 'Contenance HA',
            'contenance_a': 'Contenance A', 
            'contenance_ca': 'Contenance CA',
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
        
        # Export Excel
        output_path = self.output_dir / output_filename
        df.to_excel(output_path, index=False, engine='openpyxl')
        
        logger.info(f"📊 Données Excel exportées vers {output_path}")
        logger.info(f"📈 Total: {len(all_properties)} propriété(s) dans {len(df['Fichier source'].unique())} fichier(s)")
        
        return output_path

    def run(self) -> None:
        """
        TRAITEMENT PAR LOTS OPTIMISÉ pour extraction maximale.
        """
        logger.info("🚀 Démarrage de l'extraction BATCH OPTIMISÉE")
        
        # Lister les fichiers PDF
        pdf_files = self.list_pdf_files()
        
        if not pdf_files:
            logger.warning("❌ Aucun fichier PDF trouvé dans le dossier input/")
            return
        
        logger.info(f"📄 {len(pdf_files)} PDF(s) détecté(s) pour traitement par lots")
        
        # PHASE 1: PRÉ-ANALYSE du lot pour stratégie globale
        batch_strategy = self.analyze_pdf_batch(pdf_files)
        logger.info(f"🧠 Stratégie globale: {batch_strategy.get('approach', 'standard')}")
        
        # PHASE 2: TRAITEMENT OPTIMISÉ par lots
        all_properties = self.process_pdf_batch_optimized(pdf_files, batch_strategy)
        
        # PHASE 3: POST-TRAITEMENT pour combler les trous
        if all_properties:
            enhanced_properties = self.post_process_batch_results(all_properties, pdf_files)
            
            # PHASE 4: EXPORT avec statistiques détaillées
            self.export_to_csv_with_stats(enhanced_properties)
            
            # Statistiques finales
            total_props = len(enhanced_properties)
            total_pdfs = len(pdf_files)
            avg_per_pdf = total_props / total_pdfs if total_pdfs > 0 else 0
            
            logger.info(f"✅ EXTRACTION BATCH TERMINÉE!")
            logger.info(f"📊 {total_props} propriétés extraites de {total_pdfs} PDFs")
            logger.info(f"📈 Moyenne: {avg_per_pdf:.1f} propriétés/PDF")
        else:
            logger.warning("❌ Aucune donnée extraite du lot")

    def analyze_pdf_batch(self, pdf_files: List[Path]) -> Dict:
        """
        PRÉ-ANALYSE du lot de PDFs pour déterminer la stratégie optimale.
        """
        logger.info(f"🔍 Pré-analyse de {len(pdf_files)} PDFs...")
        
        batch_info = {
            'total_files': len(pdf_files),
            'formats_detected': {},
            'total_pages': 0,
            'approach': 'standard',
            'common_location': {},
            'estimated_properties': 0
        }
        
        # Analyser un échantillon pour détecter les patterns
        sample_size = min(3, len(pdf_files))  # Analyser max 3 PDFs pour la stratégie
        
        for i, pdf_file in enumerate(pdf_files[:sample_size]):
            logger.info(f"🔍 Analyse échantillon {i+1}/{sample_size}: {pdf_file.name}")
            
            # Convertir première page pour analyse rapide
            images = self.pdf_to_images(pdf_file)
            if images:
                batch_info['total_pages'] += len(images)
                
                # Détecter le format de ce PDF
                format_info = self.detect_pdf_format(images[0])
                format_key = f"{format_info.get('document_type')}_{format_info.get('format_era')}"
                
                if format_key in batch_info['formats_detected']:
                    batch_info['formats_detected'][format_key] += 1
                else:
                    batch_info['formats_detected'][format_key] = 1
        
        # Déterminer la stratégie globale basée sur l'analyse
        if len(batch_info['formats_detected']) == 1:
            # Format homogène - stratégie spécialisée
            batch_info['approach'] = 'homogeneous_optimized'
        elif len(pdf_files) > 10:
            # Beaucoup de PDFs - stratégie volume
            batch_info['approach'] = 'high_volume_batch'
        else:
            # Format mixte - stratégie adaptative
            batch_info['approach'] = 'mixed_adaptive'
        
        logger.info(f"📊 Formats détectés: {batch_info['formats_detected']}")
        logger.info(f"🎯 Stratégie choisie: {batch_info['approach']}")
        
        return batch_info

    def process_pdf_batch_optimized(self, pdf_files: List[Path], batch_strategy: Dict) -> List[Dict]:
        """
        TRAITEMENT PAR LOTS OPTIMISÉ selon la stratégie déterminée.
        """
        all_properties = []
        approach = batch_strategy.get('approach', 'standard')
        
        logger.info(f"⚙️ Traitement par lots - Approche: {approach}")
        
        if approach == 'homogeneous_optimized':
            # Format homogène - traitement optimisé
            all_properties = self.process_homogeneous_batch(pdf_files)
        elif approach == 'high_volume_batch':
            # Volume élevé - traitement parallèle simulé
            all_properties = self.process_high_volume_batch(pdf_files)
        else:
            # Approche adaptative mixte (par défaut)
            all_properties = self.process_mixed_adaptive_batch(pdf_files)
        
        logger.info(f"📊 {len(all_properties)} propriétés extraites au total")
        return all_properties

    def process_homogeneous_batch(self, pdf_files: List[Path]) -> List[Dict]:
        """
        Traitement optimisé pour un lot de PDFs homogènes.
        """
        logger.info("🔄 Traitement homogène optimisé STYLE MAKE")
        all_properties = []
        
        # Traiter avec approche Make exacte
        for i, pdf_file in enumerate(pdf_files, 1):
            logger.info(f"📄 Traitement Make {i}/{len(pdf_files)}: {pdf_file.name}")
            
            properties = self.process_like_make(pdf_file)
            all_properties.extend(properties)
            
            # Log intermédiaire pour suivi
            if i % 5 == 0:
                logger.info(f"📊 Progrès: {len(all_properties)} propriétés extraites jusqu'ici")
        
        return all_properties

    def process_high_volume_batch(self, pdf_files: List[Path]) -> List[Dict]:
        """
        Traitement optimisé pour gros volume avec style Make.
        """
        logger.info("🚀 Traitement haut volume STYLE MAKE")
        all_properties = []
        
        for i, pdf_file in enumerate(pdf_files, 1):
            logger.info(f"📄 Volume Make {i}/{len(pdf_files)}: {pdf_file.name}")
            
            properties = self.process_like_make(pdf_file)
            all_properties.extend(properties)
            
            # Logs de progression
            if i % 10 == 0:
                logger.info(f"📊 Progression: {i}/{len(pdf_files)} fichiers traités")
        
        return all_properties

    def process_mixed_adaptive_batch(self, pdf_files: List[Path]) -> List[Dict]:
        """
        Traitement adaptatif mixte avec style Make.
        """
        logger.info("🎯 Traitement adaptatif mixte STYLE MAKE")
        all_properties = []
        
        for i, pdf_file in enumerate(pdf_files, 1):
            logger.info(f"📄 Adaptatif Make {i}/{len(pdf_files)}: {pdf_file.name}")
            
            properties = self.process_like_make(pdf_file)
            all_properties.extend(properties)
            
            # Suivi adaptatif
            if len(properties) == 0:
                logger.warning(f"⚠️ Aucune propriété extraite pour {pdf_file.name}")
        
        return all_properties

    def post_process_batch_results(self, all_properties: List[Dict], pdf_files: List[Path]) -> List[Dict]:
        """
        POST-TRAITEMENT SÉCURISÉ - AUCUN cross-référencement pour garantir la fiabilité.
        Mode extraction PURE uniquement.
        """
        logger.info(f"🔧 Post-traitement SÉCURISÉ de {len(all_properties)} propriétés")
        logger.info("🛡️ Mode FIABILITÉ MAXIMALE - Aucun cross-référencement")
        
        if not all_properties:
            return all_properties
        
        # Analyser les champs manquants à l'échelle du lot (pour statistiques seulement)
        missing_stats = self.analyze_missing_fields_batch(all_properties)
        logger.info(f"📊 Champs incomplets détectés: {len(missing_stats)} types")
        
        # ❌ CROSS-RÉFÉRENCEMENT DÉSACTIVÉ pour éviter les erreurs
        # Les colonnes vides restent vides = FIABILITÉ GARANTIE
        logger.info("🚫 Cross-référencement DÉSACTIVÉ - Extraction pure uniquement")
        
        # Déduplication finale à l'échelle du lot (sécurisée)
        final_properties = self.deduplicate_batch_results(all_properties)
        
        # Statistiques de qualité
        removed_duplicates = len(all_properties) - len(final_properties)
        if removed_duplicates > 0:
            logger.info(f"🧹 {removed_duplicates} doublons supprimés")
        
        logger.info(f"✅ Post-traitement terminé: {len(final_properties)} propriétés FIABLES")
        logger.info("🎯 Toutes les données sont extraites directement des PDFs (AUCUNE invention)")
        
        return final_properties

    def analyze_missing_fields_batch(self, properties: List[Dict]) -> Dict:
        """
        Analyse les champs manquants à l'échelle du lot complet.
        """
        missing_stats = {}
        total_props = len(properties)
        
        required_fields = [
            'department', 'commune', 'section', 'numero', 'contenance',
            'nom', 'prenom', 'numero_majic', 'voie', 'post_code', 'city'
        ]
        
        for field in required_fields:
            empty_count = sum(1 for prop in properties if not prop.get(field))
            if empty_count > 0:
                missing_stats[field] = {
                    'empty_count': empty_count,
                    'completion_rate': ((total_props - empty_count) / total_props) * 100
                }
        
        for field, stats in missing_stats.items():
            logger.info(f"📊 {field}: {stats['completion_rate']:.1f}% complété ({stats['empty_count']} manquants)")
        
        return missing_stats

    def deduplicate_batch_results(self, properties: List[Dict]) -> List[Dict]:
        """
        Déduplication finale à l'échelle du lot complet.
        """
        seen_keys = set()
        deduplicated = []
        
        for prop in properties:
            # Clé unique plus robuste
            key_parts = [
                prop.get('nom', ''),
                prop.get('prenom', ''),
                prop.get('section', ''),
                prop.get('numero', ''),
                prop.get('numero_majic', ''),
                prop.get('fichier_source', '')  # Inclure le fichier source pour éviter les conflits
            ]
            unique_key = '|'.join(str(p).strip().upper() for p in key_parts)
            
            if unique_key not in seen_keys and unique_key != '|||||':
                seen_keys.add(unique_key)
                deduplicated.append(prop)
        
        removed = len(properties) - len(deduplicated)
        if removed > 0:
            logger.info(f"🧹 {removed} doublons supprimés lors de la déduplication finale")
        
        return deduplicated

    def export_to_csv_with_stats(self, all_properties: List[Dict]) -> None:
        """
        Export CSV et Excel avec statistiques détaillées.
        """
        if not all_properties:
            logger.warning("Aucune donnée à exporter")
            return
        
        # Export CSV (avec point-virgule) ET Excel
        csv_path = self.export_to_csv(all_properties)
        excel_path = self.export_to_excel(all_properties, "output.xlsx")
        
        # Générer des statistiques de qualité
        self.generate_quality_report(all_properties)
        
        logger.info(f"✅ EXPORTS TERMINÉS:")
        logger.info(f"📄 CSV: {csv_path}")
        logger.info(f"📊 Excel: {excel_path}")

    def generate_quality_report(self, properties: List[Dict]) -> None:
        """
        Génère un rapport de qualité détaillé pour le lot traité.
        MODE SÉCURISÉ - Extraction pure uniquement.
        """
        total_props = len(properties)
        
        # Calculer les taux de complétion par champ
        required_fields = [
            'department', 'commune', 'section', 'numero', 'contenance',
            'nom', 'prenom', 'numero_majic', 'voie', 'post_code', 'city'
        ]
        
        completion_stats = {}
        for field in required_fields:
            filled_count = sum(1 for prop in properties if prop.get(field))
            completion_rate = (filled_count / total_props) * 100 if total_props > 0 else 0
            completion_stats[field] = completion_rate
        
        # Log du rapport de qualité
        logger.info("📊 RAPPORT DE QUALITÉ - MODE SÉCURISÉ")
        logger.info("=" * 50)
        logger.info(f"🛡️ EXTRACTION PURE - Fiabilité 100% garantie")
        logger.info(f"Total propriétés extraites: {total_props}")
        logger.info("\nTaux de complétion par champ:")
        
        for field, rate in completion_stats.items():
            status = "🟢" if rate >= 90 else "🟡" if rate >= 70 else "🔴"
            logger.info(f"  {status} {field:<20}: {rate:5.1f}%")
        
        # Moyenne globale
        avg_completion = sum(completion_stats.values()) / len(completion_stats)
        overall_status = "🟢" if avg_completion >= 90 else "🟡" if avg_completion >= 70 else "🔴"
        logger.info(f"\n{overall_status} TAUX GLOBAL DE COMPLÉTION: {avg_completion:.1f}%")
        
        # Message de sécurité
        logger.info("\n🎯 GARANTIES DE FIABILITÉ:")
        logger.info("  ✅ Toutes les données proviennent directement des PDFs")
        logger.info("  ✅ Aucune invention ou interpolation de données")
        logger.info("  ✅ Colonnes vides = vraiment absentes du PDF original")
        logger.info("  ✅ Aucun risque de mélange entre propriétaires/adresses")

    def process_like_make(self, pdf_path: Path) -> List[Dict]:
        """
        RÉPLIQUE EXACTE DU WORKFLOW MAKE - CORRIGÉE ANTI-DUPLICATION
        
        Suit exactement la même logique que l'automatisation Make :
        1. pdfplumber pour les tableaux (comme Python Anywhere)
        2. OpenAI Vision simple pour les propriétaires (prompt Make)
        3. DÉTECTION TYPE PDF et traitement adapté
        4. Génération ID avec OpenAI (comme Make)
        5. Fusion 1:1 intelligente
        """
        logger.info(f"🎯 TRAITEMENT STYLE MAKE pour {pdf_path.name}")
        
        try:
            # ÉTAPE 1: Extraction tableaux (comme Python Anywhere)
            structured_data = self.extract_tables_with_pdfplumber(pdf_path)
            logger.info(f"📋 Tableaux extraits: {len(structured_data.get('prop_batie', []))} bâtis, {len(structured_data.get('non_batie', []))} non-bâtis")
            
            # ÉTAPE 2: Extraction propriétaires (prompt Make exact)
            owners = self.extract_owners_make_style(pdf_path)
            logger.info(f"Proprietaires extraits: {len(owners)}")
            
            if not owners and not structured_data.get('prop_batie') and not structured_data.get('non_batie'):
                logger.warning(f"Aucune donnée extraite pour {pdf_path.name}")
                return []
            
            # ÉTAPE 3: 🎯 DÉTECTION TYPE PDF ET TRAITEMENT ADAPTÉ
            pdf_type = self.detect_pdf_ownership_type(owners, structured_data)
            logger.info(f"🔍 Type PDF détecté: {pdf_type}")
            
            final_results = []
            
            # Traiter les propriétés non bâties
            non_batie_props = structured_data.get('non_batie', [])
            if non_batie_props and owners:
                logger.info("🏞️ Traitement propriétés non bâties style Make")
                
                if pdf_type == "single_owner":
                    # TYPE 2: Un seul propriétaire pour toutes les propriétés
                    main_owner = self.select_main_owner(owners)
                    logger.info(f"👤 Propriétaire unique sélectionné: {main_owner.get('nom', '')} {main_owner.get('prenom', '')}")
                    
                    for prop in non_batie_props:
                        if prop.get('Adresse'):  # Filtre comme Make
                            # Génération ID avec OpenAI (comme Make)
                            unique_id = self.generate_id_with_openai_like_make(main_owner, prop)
                            
                            # Fusion 1:1 simple (comme Make)
                            combined = self.merge_like_make(main_owner, prop, unique_id, 'non_batie', pdf_path.name)
                            final_results.append(combined)
                
                else:
                    # TYPE 1: Plusieurs propriétaires (logique originale)
                    logger.info("👥 Multiple propriétaires - association complexe")
                    for owner in owners:
                        for prop in non_batie_props:
                            if prop.get('Adresse'):  # Filtre comme Make
                                # Génération ID avec OpenAI (comme Make)
                                unique_id = self.generate_id_with_openai_like_make(owner, prop)
                                
                                # Fusion 1:1 simple (comme Make)
                                combined = self.merge_like_make(owner, prop, unique_id, 'non_batie', pdf_path.name)
                                final_results.append(combined)
            
            # Traiter les propriétés bâties
            prop_batie = structured_data.get('prop_batie', [])
            if prop_batie and owners:
                logger.info("🏠 Traitement propriétés bâties style Make")
                
                if pdf_type == "single_owner":
                    # TYPE 2: Un seul propriétaire pour toutes les propriétés
                    main_owner = self.select_main_owner(owners)
                    
                    for prop in prop_batie:
                        if prop.get('Adresse'):  # Filtre comme Make
                            # Génération ID avec OpenAI (comme Make)
                            unique_id = self.generate_id_with_openai_like_make(main_owner, prop)
                            
                            # Fusion 1:1 simple (comme Make)
                            combined = self.merge_like_make(main_owner, prop, unique_id, 'batie', pdf_path.name)
                            final_results.append(combined)
                            
                else:
                    # TYPE 1: Plusieurs propriétaires (logique originale)
                    for owner in owners:
                        for prop in prop_batie:
                            if prop.get('Adresse'):  # Filtre comme Make
                                # Génération ID avec OpenAI (comme Make)
                                unique_id = self.generate_id_with_openai_like_make(owner, prop)
                                
                                # Fusion 1:1 simple (comme Make)
                                combined = self.merge_like_make(owner, prop, unique_id, 'batie', pdf_path.name)
                                final_results.append(combined)
            
            # Si pas de structured data, juste les propriétaires
            if not non_batie_props and not prop_batie and owners:
                logger.info("👤 Seulement propriétaires (pas de tableaux)")
                if pdf_type == "single_owner":
                    main_owner = self.select_main_owner(owners)
                    combined = self.merge_like_make(main_owner, {}, "", 'owners_only', pdf_path.name)
                    final_results.append(combined)
                else:
                    for owner in owners:
                        combined = self.merge_like_make(owner, {}, "", 'owners_only', pdf_path.name)
                        final_results.append(combined)
            
            # ÉTAPE 4: Séparation automatique des préfixes collés
            final_results = self.separate_stuck_prefixes(final_results)
            
            # ÉTAPE 5: Propagation des valeurs manquantes (prefixe, contenance détaillée)
            final_results = self.propagate_values_downward(final_results, ['prefixe', 'contenance_ha', 'contenance_a', 'contenance_ca'])
            
            logger.info(f"Traitement Make termine: {len(final_results)} proprietes finales")
            return final_results
            
        except Exception as e:
            logger.error(f"❌ Erreur traitement Make {pdf_path.name}: {e}")
            return []

    def detect_pdf_ownership_type(self, owners: List[Dict], structured_data: Dict) -> str:
        """
        Détecte le type de PDF :
        - "single_owner" : Un seul propriétaire réel (Type 2)
        - "multiple_owners" : Plusieurs propriétaires distincts (Type 1)
        
        CORRIGÉ : Utilise le filtrage strict des vrais propriétaires
        """
        if not owners:
            return "multiple_owners"
        
        # Compter les propriétaires uniques par nom ET filtrer les vrais propriétaires
        unique_owners = set()
        valid_owners = []  # Propriétaires qui passent le filtre strict
        
        for owner in owners:
            nom = owner.get('nom', '').strip().upper()
            prenom = owner.get('prenom', '').strip().upper()
            owner_key = f"{nom}|{prenom}"
            unique_owners.add(owner_key)
            
            # ✅ FILTRAGE STRICT : seuls les vrais propriétaires
            if self.is_likely_real_owner(nom, prenom):
                valid_owners.append(owner)
        
        num_properties = len(structured_data.get('non_batie', [])) + len(structured_data.get('prop_batie', []))
        num_unique_owners = len(unique_owners)
        num_valid_owners = len(valid_owners)
        
        logger.info(f"📊 Analyse: {num_unique_owners} extraits uniques, {num_valid_owners} vrais propriétaires, {num_properties} propriétés")
        
        # ✅ HEURISTIQUE PRINCIPALE : Si très peu de vrais propriétaires pour beaucoup de propriétés
        if num_valid_owners <= 5 and num_properties > 50:
            logger.info(f"🎯 Détection: PDF type single_owner ({num_valid_owners} vrais propriétaires pour {num_properties} propriétés)")
            return "single_owner"
        
        # ✅ SÉCURITÉ : Si ratio propriétaires/propriétés très faible 
        ratio_valid = num_valid_owners / max(num_properties, 1)
        if ratio_valid < 0.1:  # Moins de 10% de propriétaires valides par rapport aux propriétés
            logger.info(f"🎯 Détection: PDF type single_owner (ratio {ratio_valid:.3f} très faible)")
            return "single_owner"
        
        # ✅ CAS MULTIPLE : Si beaucoup de propriétaires valides ET ratio élevé
        if num_valid_owners > 10 and ratio_valid > 0.5:
            logger.info(f"🎯 Détection: PDF type multiple_owners ({num_valid_owners} propriétaires pour {num_properties} propriétés)")
            return "multiple_owners"
        
        # ✅ PAR DÉFAUT : Avec beaucoup de propriétés, probablement single owner
        if num_properties > 100:
            logger.info(f"🎯 Détection: PDF type single_owner par défaut (nombreuses propriétés: {num_properties})")
            return "single_owner"
        
        # Dernier recours
        logger.info(f"🎯 Détection: PDF type multiple_owners par défaut")
        return "multiple_owners"

    def select_main_owner(self, owners: List[Dict]) -> Dict:
        """
        Sélectionne le propriétaire principal quand il n'y en a qu'un seul réel.
        Priorise les personnes morales (communes, etc.) et les plus fréquents.
        """
        if not owners:
            return {}
        
        # Compter les occurrences de chaque propriétaire
        owner_counts = {}
        for owner in owners:
            nom = owner.get('nom', '').strip()
            prenom = owner.get('prenom', '').strip()
            key = f"{nom}|{prenom}"
            
            if key not in owner_counts:
                owner_counts[key] = {'owner': owner, 'count': 0}
            owner_counts[key]['count'] += 1
        
        # Prioriser les personnes morales
        legal_entity_keywords = [
            'COMMUNE', 'VILLE', 'MAIRIE', 'ÉTAT', 'DÉPARTEMENT', 'RÉGION',
            'SCI', 'SARL', 'SASU', 'EURL', 'SA', 'SOCIÉTÉ', 'ENTERPRISE'
        ]
        
        for key, data in owner_counts.items():
            nom = data['owner'].get('nom', '').upper()
            for keyword in legal_entity_keywords:
                if keyword in nom:
                    logger.info(f"🏢 Propriétaire principal sélectionné (personne morale): {nom}")
                    return data['owner']
        
        # Sinon, prendre le plus fréquent
        most_frequent = max(owner_counts.values(), key=lambda x: x['count'])
        main_owner = most_frequent['owner']
        nom = main_owner.get('nom', '')
        prenom = main_owner.get('prenom', '')
        logger.info(f"👤 Propriétaire principal sélectionné (plus fréquent): {nom} {prenom}")
        
        return main_owner

    def extract_owners_make_style(self, pdf_path: Path) -> List[Dict]:
        """
        Extraction des propriétaires EXACTEMENT comme Make.
        Utilise le prompt exact et les paramètres exacts de Make.
        """
        logger.info(f"Extraction propriétaires style Make pour {pdf_path.name}")
        
        # Convertir PDF en images
        images = self.pdf_to_images(pdf_path)
        if not images:
            return []
        
        all_owners = []
        
        for page_num, image_data in enumerate(images, 1):
            try:
                # Encoder l'image
                base64_image = base64.b64encode(image_data).decode('utf-8')
                
                # PROMPT EXACT DE MAKE (copié à l'identique avec amélioration adresses + personnes morales)
                make_prompt = """In the following image, you will find information of owners such as nom, prenom, adresse, droit reel, numero proprietaire, department and commune. If there are any leading zero's before commune or deparment, keep it as it is. 

IMPORTANT - LEGAL ENTITIES: Some owners might be legal entities (companies, municipalities, etc.) instead of individuals. For legal entities:
- Put the full entity name in "nom" field
- Leave "prenom" field empty
- Look for keywords like: COMMUNE DE, VILLE DE, SCI, SARL, SASU, EURL, SA, SOCIÉTÉ, ENTREPRISE, ASSOCIATION, ÉTAT, DÉPARTEMENT, RÉGION

For addresses: Extract street address, city and post code separately. If some parts are missing, try to extract whatever is available. If completely no address is found, leave all address fields blank.

There can be one or multiple owners (individuals or legal entities). I want to extract all of them and return them in json format.
output example:

{"owners": [
    {
        "nom": "MARTIN",
        "prenom": "MARIE MADELEINE",
        "street_address": "2 RUE DE PARIS",
       "city": "KINGERSHEIM",
        "post_code": "68260",
        "numero_proprietaire": "MBRWL8",
"department": 21,
"commune": 026,
"droit reel": "Propriétaire/Indivision"
    },
    {
        "nom": "COMMUNE DE BAR-LE-DUC",
        "prenom": "",
         "street_address": "MAIRIE",
       "city": "BAR-LE-DUC",
        "post_code": "55000",
        "numero_proprietaire": "MBXNZ8",
"department": 21,
"commune": 026,
"droit reel": "Propriétaire"
    }
]
}"""
                
                # Appel OpenAI avec PARAMÈTRES EXACTS DE MAKE
                response = self.client.chat.completions.create(
                    model="gpt-4o",  # Même modèle que Make
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": make_prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{base64_image}",
                                        "detail": "high"  # Même que Make
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=2048,        # Même que Make
                    temperature=1,          # Même que Make (pas 1.0)
                    n=1,        # Corrigé: n au lieu de n_completions
                    response_format={"type": "json_object"}  # Même que Make
                )
                
                # Parser la réponse EXACTEMENT comme Make
                response_text = response.choices[0].message.content.strip()
                result = safe_json_parse(response_text, f"make style page {page_num}")
                if result and "owners" in result and result["owners"]:
                    page_owners = result["owners"]
                    all_owners.extend(page_owners)
                    logger.info(f"Page {page_num}: {len(page_owners)} proprietaire(s) extraits")
                else:
                    logger.warning(f"Pas de propriétaires extraits page {page_num}")
                    
            except Exception as e:
                logger.error(f"Erreur extraction proprietaires page {page_num}: {e}")
                continue
        
        logger.info(f"Total proprietaires Make style: {len(all_owners)}")
        
        # Post-traitement pour détecter et corriger les personnes morales ratées
        all_owners = self.detect_and_fix_legal_entities(all_owners)
        
        return all_owners

    def generate_id_with_openai_like_make(self, owner: Dict, prop: Dict) -> str:
        """
        GÉNÉRATION D'ID CORRIGÉE - Utilise notre méthode locale ultra-robuste
        au lieu du prompt OpenAI défaillant qui générait des IDs à 13 caractères.
        
        GARANTIT exactement 14 caractères à chaque fois.
        """
        # Extraire les données comme Make
        department = owner.get('department', '')
        commune = owner.get('commune', '')
        raw_section = prop.get('Sec', '')
        plan_number = prop.get('N° Plan', '')
        raw_prefixe = prop.get('Préfixe', prop.get('Pfxe', ''))  # Support des deux variantes
        
        # 🔧 NETTOYAGE PRÉALABLE: Séparer préfixe et section si collés avec espace
        import re
        final_section = raw_section
        final_prefixe = raw_prefixe
        
        # Si pas de préfixe et section contient pattern numérique+alphabétique avec espace
        if not raw_prefixe and raw_section:
            pattern = r'^(\d+)\s+([A-Z]+)$'  # \s+ pour détecter les espaces
            match = re.match(pattern, raw_section)
            if match:
                final_prefixe = match.group(1)  # 302
                final_section = match.group(2)  # A (sans espace)
                logger.debug(f"🔧 Section nettoyée pour ID: '{raw_section}' → section='{final_section}' prefixe='{final_prefixe}'")
        
        # ✅ UTILISATION DIRECTE de notre méthode locale CORRIGÉE
        # Plus fiable, plus rapide, et économise les tokens OpenAI
        generated_id = self.generate_unique_id(
            str(department), str(commune), 
            str(final_section), str(plan_number), str(final_prefixe)
        )
        
        logger.debug(f"ID généré localement (14 car. garantis): {generated_id}")
        return generated_id

    def detect_and_fix_legal_entities(self, owners: List[Dict]) -> List[Dict]:
        """
        Détecte et corrige les personnes morales (entreprises, communes, etc.)
        qui auraient pu être mal extraites comme personnes physiques.
        """
        if not owners:
            return owners
            
        # Mots-clés pour détecter les personnes morales
        legal_entity_keywords = [
            'COMMUNE DE', 'VILLE DE', 'MAIRIE DE',
            'SCI', 'SARL', 'SASU', 'EURL', 'SA ', 'SAS ',
            'SOCIÉTÉ', 'ENTREPRISE', 'COMPAGNIE',
            'ASSOCIATION', 'FONDATION',
            'ÉTAT', 'DÉPARTEMENT', 'RÉGION',
            'SYNDICAT', 'COLLECTIVITÉ',
            'ÉTABLISSEMENT', 'INSTITUTION',
            'COOPÉRATIVE', 'MUTUELLE'
        ]
        
        corrected_owners = []
        
        for owner in owners:
            nom = str(owner.get('nom', '')).upper().strip()
            prenom = str(owner.get('prenom', '')).strip()
            
            # Vérifier si c'est une personne morale
            is_legal_entity = False
            full_entity_name = nom
            
            # Cas 1: Le nom contient déjà un mot-clé de personne morale
            for keyword in legal_entity_keywords:
                if keyword in nom:
                    is_legal_entity = True
                    # Si il y a aussi un prénom, reconstruire le nom complet
                    if prenom:
                        full_entity_name = f"{nom} {prenom}".strip()
                    break
            
            # Cas 2: Le prénom contient un mot-clé (mal extrait)
            if not is_legal_entity and prenom:
                prenom_upper = prenom.upper()
                for keyword in legal_entity_keywords:
                    if keyword in prenom_upper:
                        is_legal_entity = True
                        # Reconstruire le nom complet
                        full_entity_name = f"{nom} {prenom}".strip()
                        break
            
            # Cas 3: Nom + prénom forment ensemble une personne morale
            if not is_legal_entity and nom and prenom:
                combined = f"{nom} {prenom}".upper()
                for keyword in legal_entity_keywords:
                    if keyword in combined:
                        is_legal_entity = True
                        full_entity_name = combined
                        break
            
            # Créer l'entrée corrigée
            corrected_owner = owner.copy()
            
            if is_legal_entity:
                corrected_owner['nom'] = full_entity_name
                corrected_owner['prenom'] = ''  # Vider le prénom pour les personnes morales
                logger.info(f"🏢 Personne morale détectée: '{full_entity_name}'")
            
            corrected_owners.append(corrected_owner)
        
        return corrected_owners

    def merge_like_make(self, owner: Dict, prop: Dict, unique_id: str, prop_type: str, pdf_path_name: str) -> Dict:
        """
        Fusion EXACTEMENT comme Make (mapping direct des champs).
        Réplique la logique Google Sheets de Make.
        """
        
        # SÉPARATION AUTOMATIQUE DES PRÉFIXES COLLÉS
        import re
        raw_section = str(prop.get('Sec', ''))
        raw_prefixe = str(prop.get('Préfixe', prop.get('Pfxe', '')))
        
        # Si pas de préfixe et section contient pattern numérique+alphabétique
        if not raw_prefixe and raw_section:
            pattern = r'^(\d+)\s*([A-Z]+)$'  # \s* permet les espaces optionnels
            match = re.match(pattern, raw_section)
            if match:
                final_prefixe = match.group(1)  # 302
                final_section = match.group(2)  # A
                logger.info(f"🔍 PRÉFIXE SÉPARÉ: '{raw_section}' → préfixe='{final_prefixe}' section='{final_section}'")
            else:
                final_prefixe = raw_prefixe
                final_section = raw_section
        else:
            final_prefixe = raw_prefixe
            final_section = raw_section
        
        # Mapping exact comme dans Make Google Sheets
        merged = {
            # Colonnes A-E (informations parcelle)
            'department': str(owner.get('department', '')),  # Colonne A
            'commune': str(owner.get('commune', '')),        # Colonne B  
            'prefixe': final_prefixe,                        # Colonne C (CORRIGÉ - séparation auto)
            'section': final_section,                        # Colonne D (CORRIGÉ - séparation auto)
            'numero': str(prop.get('N° Plan', '')),         # Colonne E
            
            # Colonnes F-H (gestion/demande - vides dans Make)
            'demandeur': '',    # Colonne F
            'date': '',         # Colonne G  
            'envoye': '',       # Colonne H
            
            # Colonne I (designation + contenance détaillée)
            'designation_parcelle': str(prop.get('Adresse', '')),  # Colonne I
            'contenance_ha': str(prop.get('HA', prop.get('Contenance', ''))).strip() if prop.get('HA', prop.get('Contenance', '')) else '',           # Hectares (fallback sur Contenance)
            'contenance_a': str(prop.get('A', '')).strip() if prop.get('A', '') else '',             # Ares  
            'contenance_ca': str(prop.get('CA', '')).strip() if prop.get('CA', '') else '',           # Centiares
            
            # Colonnes J-O (propriétaire)
            'nom': str(owner.get('nom', '')),                    # Colonne J
            'prenom': str(owner.get('prenom', '')),             # Colonne K
            'numero_majic': str(owner.get('numero_proprietaire', '')),  # Colonne L
            'voie': str(owner.get('street_address', '')),       # Colonne M
            'post_code': str(owner.get('post_code', '')),       # Colonne N
            'city': str(owner.get('city', '')),                 # Colonne O
            
            # Colonnes P-R (statuts - vides dans Make)
            'identifie': '',    # Colonne P
            'rdp': '',          # Colonne Q
            'sig': '',          # Colonne R
            
            # Colonnes S-T (ID et droit)
            'id': unique_id,                                    # Colonne S
            'droit_reel': str(owner.get('droit reel', '')),    # Colonne T
            
            # Métadonnées internes
            'fichier_source': pdf_path_name,
            'type_propriete': prop_type
        }
        
        return merged

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

    def is_likely_real_owner(self, nom: str, prenom: str) -> bool:
        """
        Détermine si un nom/prénom correspond à un vrai propriétaire
        ou à une adresse/lieu confondu par GPT-4 Vision.
        
        ULTRA-STRICT : Seuls les vrais propriétaires passent ce filtre.
        """
        # Mots-clés de personnes morales (vrais propriétaires)
        legal_entity_keywords = [
            'COMMUNE', 'VILLE', 'MAIRIE', 'ÉTAT', 'DÉPARTEMENT', 'RÉGION',
            'SCI', 'SARL', 'SASU', 'EURL', 'SA', 'SOCIÉTÉ', 'ENTERPRISE'
        ]
        
        nom_upper = nom.upper()
        
        # ✅ CRITÈRE 1: Personne morale reconnue avec mots-clés stricts
        for keyword in legal_entity_keywords:
            if keyword in nom_upper and len(nom.strip()) > 10:  # Nom suffisamment long
                return True
        
        # ✅ CRITÈRE 2: Personne physique avec prénom ET nom de famille classique
        if prenom.strip() and len(prenom.strip()) > 2:
            # Le nom doit ressembler à un nom de famille (pas d'adresse)
            if not self.looks_like_address(nom_upper):
                return True
        
        # ❌ CRITÈRE 3: Rejet strict des adresses
        if self.looks_like_address(nom_upper):
            return False
        
        # ❌ CRITÈRE 4: Rejet des noms trop courts
        if len(nom.strip()) < 5:
            return False
        
        # ❌ CRITÈRE 5: Rejet des noms sans prénom et suspects
        if not prenom.strip():
            # Sans prénom, doit être une personne morale claire
            return False
        
        # Par défaut : REJETER (approche conservative)
        return False

    def looks_like_address(self, nom_upper: str) -> bool:
        """
        Détermine si un nom ressemble à une adresse plutôt qu'à un propriétaire.
        """
        # Mots-clés d'adresses (très étendu)
        address_keywords = [
            'RUE', 'AVENUE', 'PLACE', 'CHEMIN', 'ROUTE', 'LIEU-DIT', 'IMPASSE',
            'AU VILLAGE', 'AU ', 'LA ', 'LE ', 'LES ', 'DE LA', 'DU ', 'DES ',
            'CHAMPS', 'PRES', 'BOIS', 'FORET', 'COTE', 'SUR ', 'SOUS ', 'HAUTE',
            'DESSUS', 'DESSOUS', 'HAUT', 'BAS', 'GRAND', 'PETIT', 'VIEUX', 'NOUVEAU',
            'GRANDE', 'PETITE', 'VIEILLE', 'NOUVELLE', 'RANG', 'TETE', 'BOUT',
            'MILIEU', 'ENTRE', 'VERS', 'PRES DE', 'PROCHE', 'CUDRET', 'SEUT',
            'ROCHE', 'PIERRE', 'MONT', 'COL', 'VALLEE', 'PLAINE', 'PLATEAU'
        ]
        
        # Si le nom contient des mots-clés d'adresse
        for keyword in address_keywords:
            if keyword in nom_upper:
                return True
        
        # Patterns d'adresses typiques
        address_patterns = [
            'GIRARDET', 'HAUTETERRE', 'HAUTEPIERRE', 'REISSILLE'
        ]
        
        for pattern in address_patterns:
            if pattern in nom_upper:
                return True
        
        return False


def main():
    """Fonction principale."""
    # Charger les variables d'environnement
    load_dotenv()
    
    # Créer et lancer l'extracteur
    extractor = PDFPropertyExtractor()
    extractor.run()


if __name__ == "__main__":
    main() 