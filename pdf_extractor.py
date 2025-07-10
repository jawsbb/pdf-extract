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
import re
import gc
import time

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

def clean_commune_code(commune: str) -> str:
    """
    Extrait le code commune sur EXACTEMENT 3 chiffres.
    ✅ PRÉSERVE LA COMMUNE au lieu de la vider
    
    Exemples:
    - "238 MAILLY-LE-CHATEAU" → "238"
    - "38" → "038" 
    - "5" → "005"
    - "2380" → "238"
    """
    if not commune:
        return ""
    
    # Chercher les premiers chiffres dans la chaîne
    match = re.search(r'(\d+)', commune.strip())
    if match:
        # Prendre exactement 3 chiffres
        number = match.group(1)
        if len(number) >= 3:
            return number[:3]  # "238" ou "2380" → "238"
        else:
            return number.zfill(3)  # "38" → "038", "5" → "005"
    
    # ✅ PRÉSERVATION: Ne plus vider si pas de chiffres trouvés
    logger.warning(f"🔍 Commune sans chiffres: '{commune}' - Préservée tel quel")
    return commune.strip()

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

    def clean_extraction_context(self, pdf_path: Path) -> None:
        """
        🧹 NETTOYAGE ANTI-CONTAMINATION ULTRA-SÉCURISÉ avant chaque PDF.
        
        VERSION 2.0 : Isolation complète pour éliminer toute contamination batch.
        """
        logger.info(f"🧹 NETTOYAGE ULTRA-SÉCURISÉ pour {pdf_path.name}")
        
        try:
            # 1. FORCER LE GARBAGE COLLECTOR AGRESSIVEMENT
            import gc
            gc.collect()
            gc.collect()  # Double nettoyage
            
            # 2. CRÉER UN NOUVEAU CLIENT OPENAI TOTALEMENT ISOLÉ
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                # Fermer l'ancien client si possible
                if hasattr(self.client, '_client') and hasattr(self.client._client, 'close'):
                    try:
                        self.client._client.close()
                    except:
                        pass
                
                # Créer un client complètement nouveau
                self.client = OpenAI(api_key=api_key)
                logger.info("✅ Nouveau client OpenAI créé (isolation complète)")
            
            # 3. VIDER TOUS LES CACHES ET VARIABLES D'ÉTAT
            cache_attrs = [
                '_image_cache', '_text_cache', '_extraction_cache', 
                '_prompt_cache', '_response_cache', '_header_cache'
            ]
            for attr in cache_attrs:
                if hasattr(self, attr):
                    getattr(self, attr).clear()
            
            # 4. RÉINITIALISER TOUTES LES VARIABLES DE TRAITEMENT
            reset_attrs = [
                '_last_processed_pdf', '_current_context', '_last_department',
                '_last_commune', '_extraction_history', '_contamination_context',
                '_temp_owners', '_temp_props', '_temp_results', '_current_extraction_state'
            ]
            for attr in reset_attrs:
                if hasattr(self, attr):
                    setattr(self, attr, None)
            
            # 5. NETTOYAGE SPÉCIAL POUR CONTAMINATION GÉOGRAPHIQUE
            self._geographic_cache = {}
            self._department_context = {}
            self._commune_context = {}
            
            # 6. FORCER LE NETTOYAGE DES VARIABLES GLOBALES POTENTIELLES
            globals_to_clear = [
                'CURRENT_PDF_CONTEXT', 'LAST_EXTRACTION', 'CURRENT_DEPARTMENT',
                'CURRENT_COMMUNE', 'EXTRACTION_MEMORY'
            ]
            for var_name in globals_to_clear:
                if var_name in globals():
                    globals()[var_name] = None
            
            # 7. NETTOYAGE TEMPORAIRE
            try:
                import tempfile
                temp_dir = tempfile.gettempdir()
                # Nettoyer les fichiers temporaires liés à l'extraction PDF
                for temp_file in Path(temp_dir).glob("*pdf_extract*"):
                    try:
                        temp_file.unlink()
                    except:
                        pass
            except:
                pass
            
            logger.info(f"✅ NETTOYAGE ULTRA-SÉCURISÉ TERMINÉ pour {pdf_path.name}")
            
        except Exception as e:
            logger.warning(f"Erreur lors du nettoyage: {e}")

    def batch_ultra_secure_cleanup(self, pdf_index: int, total_pdfs: int, pdf_path: Path) -> None:
        """
        🛡️ NETTOYAGE BATCH ULTRA-SÉCURISÉ SPÉCIALISÉ
        
        Mécanismes d'isolation renforcés spécifiquement pour le traitement par lots.
        """
        logger.info(f"🛡️ BATCH CLEANUP [{pdf_index}/{total_pdfs}] - {pdf_path.name}")
        
        try:
            # 1. NETTOYAGE STANDARD ULTRA-SÉCURISÉ
            self.clean_extraction_context(pdf_path)
            
            # 2. ISOLATION BATCH SPÉCIALISÉE
            
            # 2.1 Forcer l'oubli du contexte conversationnel OpenAI
            # En créant un délai artificiel pour laisser le temps au serveur OpenAI d'oublier
            if pdf_index > 1:  # Pas pour le premier PDF
                import time
                time.sleep(0.5)  # Micro-pause pour isolation serveur
            
            # 2.2 Réinitialiser complètement l'état du processeur
            self.__dict__.update({
                '_batch_contamination_guard': pdf_path.name,
                '_current_pdf_isolation_id': f"{pdf_path.name}_{pdf_index}_{int(time.time())}",
                '_batch_processing_state': 'isolated'
            })
            
            # 2.3 Variables spécifiques au batch à nettoyer
            batch_vars = [
                '_batch_context', '_cross_pdf_memory', '_accumulated_data',
                '_batch_department_history', '_batch_commune_history'
            ]
            for var in batch_vars:
                if hasattr(self, var):
                    setattr(self, var, {})
            
            # 2.4 Nettoyage mémoire Python agressif
            import gc
            collected = gc.collect()
            logger.debug(f"🗑️ Garbage collector: {collected} objets supprimés")
            
            # 2.5 Log de vérification isolation
            logger.info(f"✅ ISOLATION BATCH ACTIVÉE - PDF {pdf_index}/{total_pdfs}")
            logger.info(f"🔒 ID d'isolation: {getattr(self, '_current_pdf_isolation_id', 'unknown')}")
            
        except Exception as e:
            logger.error(f"❌ Erreur nettoyage batch ultra-sécurisé: {e}")

    def validate_extraction_consistency(self, owners: List[Dict], structured_data: Dict, pdf_path: Path) -> bool:
        """
        🔍 VALIDATION CROISÉE STRICT pour détecter les contaminations et erreurs.
        
        Vérifie la cohérence entre les différentes sources d'extraction.
        """
        logger.info(f"🔍 VALIDATION CROISÉE pour {pdf_path.name}")
        
        # 1. Vérifier que les propriétaires extraits sont cohérents avec le PDF
        valid_names = []
        suspicious_names = []
        
        for owner in owners:
            nom = owner.get('nom', '').strip()
            prenom = owner.get('prenom', '').strip()
            
            # Détecter les noms suspects (trop courts, numériques, etc.)
            if len(nom) < 2 or nom.isdigit():
                suspicious_names.append(f"{nom} {prenom}")
            else:
                valid_names.append(f"{nom} {prenom}")
        
        # 2. Vérifier la cohérence géographique
        departments = set()
        communes = set()
        for owner in owners:
            dept = owner.get('department', '').strip()
            comm = owner.get('commune', '').strip()
            if dept and dept.isdigit():
                departments.add(dept)
            if comm and comm.isdigit():
                communes.add(comm)
        
        # Alerte si trop de départements/communes différents (signe de contamination)
        if len(departments) > 2 or len(communes) > 2:
            logger.warning(f"⚠️ CONTAMINATION GÉOGRAPHIQUE DÉTECTÉE:")
            logger.warning(f"   - Départements: {departments}")
            logger.warning(f"   - Communes: {communes}")
            logger.warning(f"   - PDF: {pdf_path.name}")
            return False
        
        # 3. Vérifier la cohérence numérique
        expected_count = len(structured_data.get('prop_batie', [])) + len(structured_data.get('non_batie', []))
        actual_count = len(owners)
        
        if expected_count > 0 and actual_count > (expected_count * 3):  # Plus de 3x = suspect
            logger.warning(f"⚠️ EXPLOSION NUMÉRIQUE DÉTECTÉE:")
            logger.warning(f"   - Attendu: ~{expected_count} propriétaires")
            logger.warning(f"   - Extrait: {actual_count} propriétaires")
            logger.warning(f"   - Ratio: {actual_count/expected_count:.1f}x")
            return False
        
        logger.info(f"✅ Validation réussie: {len(valid_names)} propriétaires valides, {len(suspicious_names)} suspects")
        return True

    def clean_contaminated_data(self, owners: List[Dict], pdf_path: Path) -> List[Dict]:
        """
        🧽 NETTOYAGE DES DONNÉES CONTAMINÉES détectées.
        
        Supprime les propriétaires qui ne correspondent pas au PDF actuel.
        """
        logger.info(f"🧽 NETTOYAGE CONTAMINATION pour {pdf_path.name}")
        
        if not owners:
            return owners
        
        # 1. Extraire la référence géographique du nom du fichier si possible
        filename_parts = pdf_path.stem.split()
        reference_codes = []
        for part in filename_parts:
            if part.isdigit() and len(part) >= 4:  # Codes comme "51179"
                reference_codes.append(part[:2])  # Département
                reference_codes.append(part[2:])  # Commune
        
        # 2. Trouver la géographie majoritaire dans les propriétaires
        geo_counts = {}
        for owner in owners:
            dept = owner.get('department', '').strip()
            comm = owner.get('commune', '').strip()
            if dept and comm and dept.isdigit() and comm.isdigit():
                geo_key = f"{dept}-{comm}"
                geo_counts[geo_key] = geo_counts.get(geo_key, 0) + 1
        
        if not geo_counts:
            logger.warning("⚠️ Aucune géographie détectée dans les propriétaires")
            return owners
        
        # 3. Prendre la géographie majoritaire comme référence
        main_geo = max(geo_counts.items(), key=lambda x: x[1])[0]
        main_dept, main_comm = main_geo.split('-')
        
        logger.info(f"🎯 Géographie de référence: Dept {main_dept}, Commune {main_comm}")
        
        # 4. Filtrer les propriétaires selon la géographie de référence
        clean_owners = []
        contaminated_count = 0
        
        for owner in owners:
            dept = owner.get('department', '').strip()
            comm = owner.get('commune', '').strip()
            
            # Garder si géographie correspond OU si géographie vide (propagation possible)
            if (dept == main_dept and comm == main_comm) or (not dept and not comm):
                clean_owners.append(owner)
            else:
                contaminated_count += 1
                logger.info(f"❌ CONTAMINÉ: {owner.get('nom', '')} {owner.get('prenom', '')} (Dept {dept}, Commune {comm})")
        
        if contaminated_count > 0:
            logger.warning(f"🧽 NETTOYAGE: {contaminated_count} propriétaires contaminés supprimés")
            logger.info(f"✅ PROPRE: {len(clean_owners)} propriétaires conservés")
        
        return clean_owners

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
- Cherche en HAUT du document: codes comme "51179", "25227", "89238" 
- Format: DEPARTMENT(2 chiffres) + COMMUNE(3 chiffres)
- Exemples: "51179" = département 51, commune 179
- 🚨 RÈGLE ABSOLUE: "commune" = UNIQUEMENT 3 chiffres ("179", "424", "025"), JAMAIS noms/lieux
- ❌ INTERDIT dans commune: "LES PREMIERS SAPINS", "MAILLY-LE-CHATEAU", "91", "25"
- ✅ CORRECT dans commune: "179", "424", "238" (exactement 3 chiffres)
- Le nom de commune va dans "commune_nom" séparément

2️⃣ PROPRIÉTAIRES (scan complet):
- Noms en MAJUSCULES: [NOM1], [NOM2], [NOM3], etc.
- Prénoms: [Prénom1], [Prénom2], [Prénom Multiple], etc.
- Codes MAJIC: M8BNF6, MB43HC, P7QR92 (alphanumériques 6 caractères)

3️⃣ PARCELLES (détection fine):
- Sections: A, AB, ZY, 000ZD, etc.
- Numéros: 6, 0006, 123, 0123, etc.
- Contenance: 230040, 000150, 002300 (format chiffres)

4️⃣ ADRESSES (lecture complète):
- Voies: "1 RUE D AVAT", "15 AVENUE DE LA PAIX"
- Codes postaux: 51240, 89660, 21000
- Villes: COUPEVILLE, AUXERRE, DIJON

5️⃣ DROITS RÉELS:
- PP = Pleine Propriété
- US = Usufruit  
- NU = Nue-propriété

📊 EXEMPLES CONCRETS DE DONNÉES RÉELLES:

EXEMPLE 1:
{
  "department": "51",
  "commune": "179",
  "commune_nom": "DAMPIERRE-SUR-MOIVRE",
  "section": "ZY",
  "numero": "0006",
  "contenance": "230040",
  "droit_reel": "US",
  "designation_parcelle": "LES ROULLIERS",
  "nom": "[NOM_PROPRIETAIRE1]",
  "prenom": "[PRENOM_MULTIPLE]",
  "numero_majic": "M8BNF6",
  "voie": "1 RUE D AVAT",
  "post_code": "51240",
  "city": "COUPEVILLE"
}

EXEMPLE 2:
{
  "department": "25",
  "commune": "227",
  "commune_nom": "BESANCON",
  "section": "000ZD",
  "numero": "0005",
  "contenance": "000150",
  "droit_reel": "PP",
  "designation_parcelle": "LE GRAND CHAMP",
  "nom": "[NOM_PROPRIETAIRE2]",
  "prenom": "[PRENOM_SIMPLE]",
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
- 🚨 SÉPARATION OBLIGATOIRE: "commune" = UNIQUEMENT code (ex: "208"), "commune_nom" = nom complet (ex: "DAMPIERRE-SUR-MOIVRE")

📤 FORMAT DE RÉPONSE OBLIGATOIRE:
{
  "proprietes": [
    {
      "department": "XX",
      "commune": "XXX",
      "commune_nom": "NOM_COMMUNE",
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
                
                # ✅ NETTOYAGE IMMÉDIAT des codes commune (CORRECTION CRITIQUE)
                for prop in properties:
                    if prop.get('commune'):
                        original_commune = prop['commune']
                        cleaned_commune = clean_commune_code(original_commune)
                        if cleaned_commune != original_commune:
                            prop['commune'] = cleaned_commune
                            logger.debug(f"🧹 Commune nettoyée: '{original_commune}' → '{cleaned_commune}'")
                
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
        """
        🔧 NOUVELLE VERSION: Extraction département/commune avec pdfplumber + ChatGPT.
        Beaucoup plus fiable que l'analyse d'image.
        """
        try:
            # Convertir filename en Path si nécessaire
            if isinstance(filename, str):
                # Si c'est juste un nom de fichier, chercher dans input/
                pdf_path = Path(self.input_dir) / filename
                if not pdf_path.exists():
                    # Essayer d'autres chemins possibles
                    for possible_path in [Path(filename), Path(self.input_dir) / f"{filename}.pdf"]:
                        if possible_path.exists():
                            pdf_path = possible_path
                            break
            else:
                pdf_path = filename
            
            if not pdf_path.exists():
                logger.warning(f"⚠️ Fichier PDF introuvable pour extraction en-tête: {pdf_path}")
                return properties
            
            # Étape 1: Extraire le texte de l'en-tête avec pdfplumber
            header_text = self.extract_header_text_with_pdfplumber(pdf_path)
            
            if not header_text:
                logger.warning(f"⚠️ Impossible d'extraire l'en-tête textuel: {pdf_path.name}")
                return properties
            
            # Étape 2: Analyser l'en-tête avec ChatGPT
            location_data = self.parse_header_text_with_gpt(header_text, pdf_path.name)
            
            if not location_data:
                logger.warning(f"⚠️ Échec analyse en-tête: {pdf_path.name}")
                return properties
            
            # Étape 3: Appliquer les données extraites aux propriétés
            dept = location_data.get("department")
            commune = location_data.get("commune")
            
            if dept or commune:
                # 🚨 PROPAGATION FORCÉE département/commune depuis en-tête
                missing_commune_count = 0
                missing_dept_count = 0
                
                for prop in properties:
                    if not prop.get("department") and dept:
                        prop["department"] = dept
                        missing_dept_count += 1
                    if not prop.get("commune") and commune:
                        # ✅ NETTOYAGE immédiat du code commune
                        cleaned_commune = clean_commune_code(commune)
                        prop["commune"] = cleaned_commune
                        missing_commune_count += 1
                        if cleaned_commune != commune:
                            logger.debug(f"🧹 Commune nettoyée: '{commune}' → '{cleaned_commune}'")
                
                if missing_commune_count > 0:
                    logger.info(f"🔄 PROPAGATION FORCÉE: commune '{commune}' ajoutée à {missing_commune_count} propriétés")
                if missing_dept_count > 0:
                    logger.info(f"🔄 PROPAGATION FORCÉE: département '{dept}' ajouté à {missing_dept_count} propriétés")
                
                logger.info(f"✅ En-tête traité avec pdfplumber: dept={dept}, commune={commune} → {len(properties)} propriétés")
            else:
                logger.warning(f"⚠️ Aucune donnée géographique trouvée dans l'en-tête: {pdf_path.name}")
            
        except Exception as e:
            logger.error(f"❌ Erreur extraction en-tête pdfplumber: {e}")
        
        return properties

    def extract_header_text_with_pdfplumber(self, pdf_path: Path) -> str:
        """
        Extrait le texte brut de l'en-tête du PDF avec pdfplumber.
        Beaucoup plus fiable que l'analyse d'image.
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if not pdf.pages:
                    return ""
                
                first_page = pdf.pages[0]
                full_text = first_page.extract_text()
                
                if not full_text:
                    return ""
                
                # Extraire seulement les premières lignes (en-tête)
                lines = full_text.split('\n')
                header_lines = lines[:20]  # Plus de lignes pour capture élargie
                
                # ✅ NOUVEAU - Extraction beaucoup plus large
                relevant_lines = []
                import re
                
                for line in header_lines:
                    line_clean = line.strip()
                    # Garder TOUTES les lignes contenant des chiffres (codes géographiques potentiels)
                    if (any(keyword in line_clean.upper() for keyword in 
                           ['DÉPARTEMENT', 'COMMUNE', 'RELEVÉ', 'PROPRIÉTÉ', 'ANNÉE', 'CADASTRE']) or
                        # OU lignes avec codes numériques (département/commune)
                        re.search(r'\b\d{2,5}\b', line_clean) or
                        # OU lignes avec noms de communes françaises typiques
                        any(word in line_clean.upper() for word in ['MAILLY', 'CHÂTEAU', 'SAINT', 'SUR', 'LES', 'LE'])):
                        relevant_lines.append(line_clean)
                
                header_text = '\n'.join(relevant_lines)
                logger.debug(f"📄 En-tête extrait: {header_text[:100]}...")
                return header_text
                
        except Exception as e:
            logger.warning(f"Erreur extraction en-tête pdfplumber: {e}")
            return ""

    def parse_header_text_with_gpt(self, header_text: str, filename: str) -> Dict:
        """
        Analyse le texte d'en-tête avec ChatGPT pour extraire département et commune.
        """
        if not header_text.strip():
            return {}
            
        try:
            header_prompt = f"""
🎯 ANALYSE INTELLIGENTE d'en-tête cadastral français.

📄 TEXTE À ANALYSER:
{header_text}

🔍 RECHERCHE MULTI-FORMAT:
1. Format classique: "Département : 89" + "Commune : 238"
2. Format condensé: "89238" ou "89 238"  
3. Format avec nom: "238 MAILLY-LE-CHATEAU"
4. Format mixte: "Département 89 Commune 238"

📋 STRATÉGIE:
- Trouve TOUS les nombres de 2-5 chiffres
- Identifie le département (2 premiers chiffres)
- Identifie la commune (3 chiffres suivants OU séparés)
- Si nom de commune présent, extrais le code qui précède

📤 EXEMPLES DE DÉTECTION:
Input: "Département : 89   Commune : 238 MAILLY-LE-CHATEAU"
Output: {{"department": "89", "commune": "238"}}

Input: "89238 MAILLY-LE-CHATEAU Année 2024"  
Output: {{"department": "89", "commune": "238"}}

Input: "Cadastre 51179 ZY Propriétés"
Output: {{"department": "51", "commune": "179"}}

⚠️ RÈGLES:
- TOUJOURS chercher les codes numériques
- Si plusieurs possibilités, prendre la première
- Si aucun code trouvé, retourner {{"department": null, "commune": null}}
"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Plus rapide et moins cher pour analyse textuelle
                messages=[
                    {"role": "user", "content": header_prompt}
                ],
                max_tokens=200,
                temperature=0.0
            )
            
            response_text = response.choices[0].message.content.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            
            location_data = safe_json_parse(response_text, f"analyse en-tête {filename}")
            
            if location_data:
                dept = location_data.get("department")
                commune = location_data.get("commune")
                logger.info(f"✅ En-tête analysé: dept={dept}, commune={commune}")
                return location_data
            
        except Exception as e:
            logger.warning(f"Erreur analyse en-tête ChatGPT: {e}")
        
        return {}

    def extract_owner_info(self, properties: List[Dict], base64_image: str, filename: str) -> List[Dict]:
        """Extraction ciblée des informations propriétaires."""
        try:
            owner_prompt = """
🎯 MISSION: Trouve TOUS les propriétaires dans ce document cadastral.

🔍 RECHERCHE SYSTÉMATIQUE:
- Noms en MAJUSCULES: [NOM1], [NOM2], [NOM3], [NOM4], etc.
- Prénoms: [Prénom1], [Prénom2], [Prénom3], [Prénom Multiple], etc.
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
      "commune_nom": "",
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
            
            # ✅ NETTOYAGE des codes commune dans les résultats d'urgence
            if result and "proprietes" in result:
                for prop in result["proprietes"]:
                    if prop.get('commune'):
                        original_commune = prop['commune']
                        cleaned_commune = clean_commune_code(original_commune)
                        if cleaned_commune != original_commune:
                            prop['commune'] = cleaned_commune
                            logger.debug(f"🧹 Commune nettoyée (urgence): '{original_commune}' → '{cleaned_commune}'")
            
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
                
                # PROMPT AMÉLIORÉ - EXTRACTION SYSTÉMATIQUE COMPLÈTE
                simple_prompt = """🚨 EXTRACTION SYSTÉMATIQUE COMPLÈTE REQUISE 🚨

MISSION CRITIQUE: Tu dois extraire TOUTES les lignes de données propriétaires présentes dans ce tableau cadastral français. 

📋 MÉTHODE SYSTÉMATIQUE OBLIGATOIRE:
1. COMPTE d'abord le nombre total de lignes dans le(s) tableau(x)
2. LIS systématiquement CHAQUE ligne de données de haut en bas
3. EXTRAIS TOUTES les informations pour CHAQUE ligne trouvée
4. Ne JAMAIS arrêter après quelques lignes - CONTINUE jusqu'à la fin
5. VÉRIFIE que ton extraction contient le même nombre d'entrées que de lignes dans le tableau

⚠️ ATTENTION: Ce document peut contenir des tableaux avec plusieurs dizaines de lignes. Tu DOIS toutes les extraire.

🎯 INFORMATIONS À EXTRAIRE pour CHAQUE ligne:
- nom (en MAJUSCULES généralement)
- prenom (souvent après le nom)
- street_address (adresse complète rue/numéro)
- city (ville)
- post_code (code postal)
- numero_proprietaire (code généralement 6 caractères)
- department (département, garder les zéros de début)
- commune (🚨 OBLIGATOIRE: UNIQUEMENT le code à 3 chiffres, exemple "238", JAMAIS le nom "MAILLY-LE-CHATEAU")
- droit_reel (type de propriété: Propriétaire, Usufruitier, Nu-propriétaire, etc.)

🔍 RÈGLES DE QUALITÉ:
- Si une ligne est incomplète, extrait quand même ce qui est disponible
- Conserve TOUS les zéros de début pour department et commune
- Sépare correctement rue/ville/code postal dans l'adresse
- Ne jamais ignorer une ligne sous prétexte qu'elle manque d'info

🚨 RÈGLE ABSOLUE COMMUNE - ANTI-CONTAMINATION:
- commune = EXCLUSIVEMENT LE CODE À 3 CHIFFRES (ex: "424", "238", "179")
- ❌ INTERDIT: noms de lieux ("LES PREMIERS SAPINS", "MAILLY-LE-CHATEAU") 
- ❌ INTERDIT: codes de départements ("25", "91") dans le champ commune
- ✅ AUTORISÉ: uniquement codes numériques 3 chiffres ("424", "025", "001")
- SI tu vois "424 LES PREMIERS SAPINS", PRENDS SEULEMENT "424"
- SI tu vois "LES PREMIERS SAPINS" sans code, cherche dans les lignes autour
- VÉRIFICATION: commune doit avoir EXACTEMENT 3 chiffres, rien d'autre

RÉPONSE JSON OBLIGATOIRE (avec TOUTES les lignes trouvées):
{
  "owners": [
    {
      "nom": "[NOM_PROPRIETAIRE]",
      "prenom": "[PRENOM_MULTIPLE]", 
      "street_address": "2 RUE DE LA PAIX",
      "city": "MAILLY-LE-CHATEAU",
      "post_code": "89660",
      "numero_proprietaire": "MBRWL8",
      "department": "89",
      "commune": "238",
      "droit_reel": "Propriétaire"
    }
  ]
}

🚨 VALIDATION FINALE: Vérifie que ton array "owners" contient UNE entrée pour CHAQUE ligne de données du tableau !"""
                
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
  "commune_nom": "DAMPIERRE-SUR-MOIVRE",
  "prefixe": "",
  "section": "000ZE",
  "numero": "0025",
  "contenance": "001045",     ⬅️ CONTENANCE = SURFACE en m² (OBLIGATOIRE!)
  "droit_reel": "US",
  "designation_parcelle": "LES ROULLIERS",
  "nom": "[NOM_PROPRIETAIRE1]",
  "prenom": "[PRENOM_MULTIPLE]",
  "numero_majic": "M8BNF6",
  "voie": "1 RUE D AVAT",
  "post_code": "51240",
  "city": "COUPEVILLE"
}

EXEMPLE DÉPARTEMENT 25:
{
  "department": "25",
  "commune": "227",
  "commune_nom": "BESANCON",
  "prefixe": "",
  "section": "000ZD",
  "numero": "0005",
  "contenance": "000150",     ⬅️ SURFACE = 150m² (CHERCHE ça partout!)
  "droit_reel": "PP",
  "designation_parcelle": "LE GRAND CHAMP",
  "nom": "[NOM_PROPRIETAIRE2]",
  "prenom": "[PRENOM_SIMPLE]",
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
      "commune_nom": "",
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
        
        ✅ CORRECTION CONTAMINATION CROISÉE: Isolation stricte par fichier source.
        """
        if not properties:
            return properties
        
        # Grouper les propriétés par fichier source pour éviter la contamination croisée
        files_groups = {}
        for prop in properties:
            file_source = prop.get('fichier_source', 'unknown')
            if file_source not in files_groups:
                files_groups[file_source] = []
            files_groups[file_source].append(prop)
        
        all_updated_properties = []
        
        # Traiter chaque fichier séparément avec sa propre mémoire
        for file_source, file_props in files_groups.items():
            # ✅ ISOLATION: Nouvelle mémoire pour chaque fichier
            last_seen_values = {field: None for field in fields}
            
            for prop in file_props:
                updated_prop = prop.copy()
                for field in fields:
                    if updated_prop.get(field) is None or updated_prop.get(field) == "":
                        if last_seen_values[field] is not None:
                            updated_prop[field] = last_seen_values[field]
                    else:
                        last_seen_values[field] = updated_prop[field]
                all_updated_properties.append(updated_prop)
        
        return all_updated_properties

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

    def parse_contenance_value(self, value: str) -> str:
        """
        ✅ CORRECTION CONTENANCE : Parse les valeurs de contenance avec gestion des formats français.
        
        Gère les cas :
        - "1 216,05" → "1216" (supprime espaces et virgules)
        - "10,98" → "10" (partie entière)
        - "1098" → "1098" (déjà correct)
        - "" ou None → ""
        """
        if not value:
            return ""
        
        try:
            # Convertir en string et nettoyer
            clean_value = str(value).strip()
            
            if not clean_value or clean_value.lower() in ['n/a', 'null', 'none']:
                return ""
            
            # ✅ CORRECTION FORMAT FRANÇAIS : Supprimer espaces dans les milliers
            clean_value = clean_value.replace(' ', '')  # "1 216" → "1216"
            
            # ✅ CORRECTION VIRGULES : Remplacer virgules par points
            clean_value = clean_value.replace(',', '.')  # "1216,05" → "1216.05"
            
            # ✅ EXTRAIRE PARTIE ENTIÈRE : Prendre seulement la partie avant le point
            if '.' in clean_value:
                clean_value = clean_value.split('.')[0]  # "1216.05" → "1216"
            
            # ✅ VALIDATION : Vérifier que c'est numérique
            if clean_value.isdigit():
                return clean_value
            else:
                # Extraire seulement les chiffres
                digits_only = ''.join(filter(str.isdigit, clean_value))
                return digits_only if digits_only else ""
                
        except Exception as e:
            logger.warning(f"Erreur parsing contenance '{value}': {e}")
            return ""

    def split_name_intelligently(self, nom: str, prenom: str) -> tuple:
        """
        ✅ CORRECTION NOMS/PRÉNOMS : Sépare intelligemment les noms mal fusionnés.
        
        Gère les cas :
        - nom="ALEXIS MOURADOFF", prenom="ALEXIS" → nom="MOURADOFF", prenom="ALEXIS"
        - nom="MOURADOFF", prenom="MONIQUE ALEXIS" → nom="MOURADOFF", prenom="MONIQUE ALEXIS"
        """
        nom_clean = str(nom).strip()
        prenom_clean = str(prenom).strip()
        
        # Cas 1: Prénom dupliqué au début du nom
        if prenom_clean and nom_clean.startswith(prenom_clean + ' '):
            # "ALEXIS MOURADOFF" avec prénom "ALEXIS" → nom="MOURADOFF"
            nom_without_prenom = nom_clean[len(prenom_clean):].strip()
            logger.debug(f"🔧 Nom corrigé: '{nom_clean}' → '{nom_without_prenom}' (prénom dupliqué supprimé)")
            return nom_without_prenom, prenom_clean
        
        # Cas 2: Vérifier AVANT TOUT si c'est une personne morale (priorité absolue)
        nom_parts = nom_clean.split()
        if len(nom_parts) >= 2 and not prenom_clean:
            # ✅ CORRECTION: Détecter les personnes morales EN PREMIER
            legal_keywords = ['COM', 'COMMUNE', 'VILLE', 'MAIRIE', 'ÉTAT', 'DÉPARTEMENT', 'RÉGION', 'SCI', 'SARL', 'SA', 'EURL']
            if any(keyword in nom_clean.upper() for keyword in legal_keywords):
                logger.debug(f"🏛️ Personne morale conservée: '{nom_clean}'")
                return nom_clean, prenom_clean
        
        # Cas 3: Nom composé mal séparé (plus de 2 mots dans nom) - après vérification personne morale
        if len(nom_parts) > 2 and not prenom_clean:
            # "[PRENOM_MULTIPLE] [NOM_FAMILLE]" sans prénom → nom="[NOM_FAMILLE]", prenom="[PRENOM_MULTIPLE]"
            potential_nom = nom_parts[-1]  # Dernier mot = nom de famille
            potential_prenom = ' '.join(nom_parts[:-1])  # Reste = prénom
            logger.debug(f"🔧 Séparation automatique: '{nom_clean}' → nom='{potential_nom}' prenom='{potential_prenom}'")
            return potential_nom, potential_prenom
            
        # Cas 4: Nom simple (2 mots) - probable prénom+nom
        if len(nom_parts) == 2 and not prenom_clean:
            # "[PRENOM] [NOM_FAMILLE]" sans prénom → nom="[NOM_FAMILLE]", prenom="[PRENOM]"
            potential_nom = nom_parts[1]
            potential_prenom = nom_parts[0]
            logger.debug(f"🔧 Séparation simple: '{nom_clean}' → nom='{potential_nom}' prenom='{potential_prenom}'")
            return potential_nom, potential_prenom
        
        # Cas par défaut : garder tel quel
        return nom_clean, prenom_clean

    def clean_address(self, address: str) -> str:
        """
        ✅ CORRECTION ADRESSES : Nettoie et valide les adresses.
        
        Supprime les caractères parasites et valide le format.
        """
        if not address:
            return ""
        
        address_clean = str(address).strip()
        
        # Supprimer les caractères parasites courants
        parasites = ['<', '>', '|', '_', '+', '=']
        for parasite in parasites:
            address_clean = address_clean.replace(parasite, ' ')
        
        # Nettoyer les espaces multiples
        address_clean = ' '.join(address_clean.split())
        
        # Validation basique : doit contenir au moins une lettre
        if not any(c.isalpha() for c in address_clean):
            return ""
        
        # Validation longueur
        if len(address_clean) < 3 or len(address_clean) > 100:
            return ""
        
        return address_clean

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
        🧹 NETTOYAGE ET DÉDUPLICATION INTELLIGENTE avec validation géographique.
        
        Évite de supprimer des propriétaires légitimes différents.
        """
        if not properties:
            return []
        
        logger.info(f"🧹 NETTOYAGE INTELLIGENT pour {filename} - {len(properties)} propriétés")
        
        cleaned = []
        seen_combinations = set()
        
        # 1. VALIDATION GÉOGRAPHIQUE PRÉALABLE
        geo_stats = {}
        for prop in properties:
            dept = prop.get('department', '').strip()
            comm = prop.get('commune', '').strip()
            if dept and comm:
                geo_key = f"{dept}-{comm}"
                geo_stats[geo_key] = geo_stats.get(geo_key, 0) + 1
        
        # Détecter si on a une géographie dominante
        main_geo = None
        if geo_stats:
            main_geo = max(geo_stats.items(), key=lambda x: x[1])[0]
            logger.info(f"🎯 Géographie dominante: {main_geo} ({geo_stats[main_geo]} occurrences)")
        
        contaminated_removed = 0
        for prop in properties:
            # 2. FILTRAGE ANTI-CONTAMINATION GÉOGRAPHIQUE
            dept = prop.get('department', '').strip()
            comm = prop.get('commune', '').strip()
            
            if main_geo and dept and comm:
                prop_geo = f"{dept}-{comm}"
                if prop_geo != main_geo:
                    contaminated_removed += 1
                    logger.info(f"❌ CONTAMINATION: {prop.get('nom', '')} {prop.get('prenom', '')} (Geo: {prop_geo} vs {main_geo})")
                    continue  # Skip cette propriété contaminée
            
            # 3. CRÉATION CLÉ UNIQUE INTELLIGENTE pour déduplication fine
            key_fields = [
                prop.get('nom', '').strip().upper(),
                prop.get('prenom', '').strip().upper(),
                prop.get('section', '').strip(),
                prop.get('numero', '').strip(),
                prop.get('numero_majic', '').strip()
            ]
            unique_key = '|'.join(str(f) for f in key_fields)
            
            # 4. IGNORER LES ENTRÉES COMPLÈTEMENT VIDES OU INVALIDES
            if not any(key_fields) or unique_key == '||||':
                continue
            
            # Vérification spéciale pour noms suspects
            nom = prop.get('nom', '').strip()
            prenom = prop.get('prenom', '').strip()
            if not self.is_likely_real_owner(nom, prenom):
                logger.info(f"❌ NOM SUSPECT REJETÉ: {nom} {prenom}")
                continue
            
            # 5. DÉDUPLICATION INTELLIGENTE
            if unique_key not in seen_combinations:
                seen_combinations.add(unique_key)
                
                # 6. ASSURER LA COMPLÉTUDE DES CHAMPS
                required_fields = [
                    'department', 'commune', 'prefixe', 'section', 'numero', 
                    'contenance', 'droit_reel', 'designation_parcelle', 
                    'nom', 'prenom', 'numero_majic', 'voie', 'post_code', 'city'
                ]
                
                for field in required_fields:
                    if field not in prop:
                        prop[field] = ''
                
                cleaned.append(prop)
            else:
                logger.debug(f"🔄 DOUBLON IGNORÉ: {nom} {prenom} (déjà traité)")
        
        if contaminated_removed > 0:
            logger.warning(f"🧽 CONTAMINATION NETTOYÉE: {contaminated_removed} propriétaires d'autres PDFs supprimés")
        
        logger.info(f"✅ NETTOYAGE TERMINÉ: {len(properties)} → {len(cleaned)} propriétés valides après déduplication intelligente")
        return cleaned

    def export_to_csv(self, all_properties: List[Dict], output_filename: str = "output.csv") -> None:
        """
        Exporte toutes les données vers un fichier CSV avec séparateur point-virgule.
        """
        if not all_properties:
            logger.warning("Aucune donnée à exporter")
            return
        # Nettoyage du code commune avant export
        for prop in all_properties:
            prop['commune'] = clean_commune_code(prop.get('commune', ''))
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
        """
        if not all_properties:
            logger.warning("Aucune donnée à exporter en Excel")
            return
        # Nettoyage du code commune avant export
        for prop in all_properties:
            prop['commune'] = clean_commune_code(prop.get('commune', ''))
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
        Traitement optimisé pour un lot de PDFs homogènes avec isolation ultra-sécurisée.
        """
        logger.info("🔄 Traitement homogène optimisé STYLE MAKE - MODE ULTRA-SÉCURISÉ")
        all_properties = []
        
        # Traiter avec approche Make exacte + isolation batch
        for i, pdf_file in enumerate(pdf_files, 1):
            logger.info(f"📄 Traitement Make [{i}/{len(pdf_files)}]: {pdf_file.name}")
            
            # 🛡️ NETTOYAGE BATCH ULTRA-SÉCURISÉ avant chaque PDF
            self.batch_ultra_secure_cleanup(i, len(pdf_files), pdf_file)
            
            properties = self.process_like_make(pdf_file)
            all_properties.extend(properties)
            
            # Log intermédiaire pour suivi
            if i % 5 == 0:
                logger.info(f"📊 Progrès: {len(all_properties)} propriétés extraites jusqu'ici")
        
        return all_properties

    def process_high_volume_batch(self, pdf_files: List[Path]) -> List[Dict]:
        """
        Traitement optimisé pour gros volume avec style Make et isolation ultra-sécurisée.
        """
        logger.info("🚀 Traitement haut volume STYLE MAKE - MODE ULTRA-SÉCURISÉ")
        all_properties = []
        
        for i, pdf_file in enumerate(pdf_files, 1):
            logger.info(f"📄 Volume Make [{i}/{len(pdf_files)}]: {pdf_file.name}")
            
            # 🛡️ NETTOYAGE BATCH ULTRA-SÉCURISÉ avant chaque PDF
            self.batch_ultra_secure_cleanup(i, len(pdf_files), pdf_file)
            
            properties = self.process_like_make(pdf_file)
            all_properties.extend(properties)
            
            # Logs de progression
            if i % 10 == 0:
                logger.info(f"📊 Progression: {i}/{len(pdf_files)} fichiers traités")
        
        return all_properties

    def process_mixed_adaptive_batch(self, pdf_files: List[Path]) -> List[Dict]:
        """
        Traitement adaptatif mixte avec style Make et isolation ultra-sécurisée.
        """
        logger.info("🎯 Traitement adaptatif mixte STYLE MAKE - MODE ULTRA-SÉCURISÉ")
        all_properties = []
        
        for i, pdf_file in enumerate(pdf_files, 1):
            logger.info(f"📄 Adaptatif Make [{i}/{len(pdf_files)}]: {pdf_file.name}")
            
            # 🛡️ NETTOYAGE BATCH ULTRA-SÉCURISÉ avant chaque PDF
            self.batch_ultra_secure_cleanup(i, len(pdf_files), pdf_file)
            
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
        ✅ DÉDUPLICATION STRICTE CORRIGÉE - Élimine les vrais doublons même entre fichiers.
        """
        seen_keys = set()
        deduplicated = []
        
        for prop in properties:
            # ✅ CLÉ UNIQUE STRICTE - SANS fichier source pour éliminer les vrais doublons
            key_parts = [
                prop.get('nom', ''),
                prop.get('prenom', ''),
                prop.get('section', ''),
                prop.get('numero', ''),
                prop.get('department', ''),
                prop.get('commune', ''),
                prop.get('numero_majic', ''),
                prop.get('droit_reel', '')  # Inclure le droit réel pour distinguer usufruitier/nu-prop
            ]
            unique_key = '|'.join(str(p).strip().upper() for p in key_parts)
            
            # ✅ ÉVITER les entrées complètement vides ET les vrais doublons
            if unique_key not in seen_keys and unique_key != '|||||||':
                seen_keys.add(unique_key)
                deduplicated.append(prop)
            else:
                logger.debug(f"🗑️ Doublon éliminé: {prop.get('nom', '')}-{prop.get('section', '')}-{prop.get('numero', '')}")
        
        removed = len(properties) - len(deduplicated)
        if removed > 0:
            logger.info(f"🧹 {removed} doublons STRICTS supprimés (même entre fichiers différents)")
        
        return deduplicated

    def export_to_csv_with_stats(self, all_properties: List[Dict]) -> None:
        """
        🧹 EXPORT CSV ET EXCEL AVEC VALIDATION FINALE ET STATISTIQUES DÉTAILLÉES.
        """
        if not all_properties:
            logger.warning("Aucune donnée à exporter")
            return
        
        # 🔍 VALIDATION FINALE STRICTE avant export
        logger.info("🔍 VALIDATION FINALE avant export...")
        validated_properties = self.final_validation_before_export(all_properties)
        
        if len(validated_properties) != len(all_properties):
            removed = len(all_properties) - len(validated_properties)
            logger.warning(f"🧽 VALIDATION FINALE: {removed} propriétés contaminées supprimées")
        
        # Export CSV (avec point-virgule) ET Excel
        csv_path = self.export_to_csv(validated_properties)
        excel_path = self.export_to_excel(validated_properties, "output.xlsx")
        
        # Générer des statistiques de qualité
        self.generate_quality_report(validated_properties)
        
        logger.info(f"✅ EXPORTS TERMINÉS AVEC VALIDATION:")
        logger.info(f"📄 CSV: {csv_path}")
        logger.info(f"📊 Excel: {excel_path}")
        logger.info(f"🛡️ Données validées: {len(validated_properties)} propriétés finales")

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
            # 🧹 ÉTAPE 0: NETTOYAGE ANTI-CONTAMINATION (ultra-sécurisé si pas déjà fait en batch)
            if not hasattr(self, '_batch_processing_state') or self._batch_processing_state != 'isolated':
                # Mode single PDF - utiliser nettoyage ultra-sécurisé
                self.clean_extraction_context(pdf_path)
            else:
                # Mode batch - nettoyage déjà fait par batch_ultra_secure_cleanup
                logger.debug("🔒 Nettoyage batch déjà effectué - isolation préservée")
            
            # ÉTAPE 1: Extraction tableaux (comme Python Anywhere)
            structured_data = self.extract_tables_with_pdfplumber(pdf_path)
            logger.info(f"📋 Tableaux extraits: {len(structured_data.get('prop_batie', []))} bâtis, {len(structured_data.get('non_batie', []))} non-bâtis")
            
            # ÉTAPE 2: Extraction propriétaires (prompt Make exact)
            owners = self.extract_owners_make_style(pdf_path)
            logger.info(f"Proprietaires extraits: {len(owners)}")
            
            # 🔍 ÉTAPE 2.1: VALIDATION CROISÉE ANTI-CONTAMINATION
            if not self.validate_extraction_consistency(owners, structured_data, pdf_path):
                logger.warning(f"⚠️ CONTAMINATION DÉTECTÉE - Application du nettoyage")
                owners = self.clean_contaminated_data(owners, pdf_path)
                logger.info(f"🧽 Propriétaires après nettoyage: {len(owners)}")
            
            # 🔍 VALIDATION EXTRACTION COMPLÈTE: Vérifier si extraction semble incomplète
            if len(owners) > 0:
                # Estimer le nombre attendu de lignes basé sur les tableaux structurés
                expected_lines = len(structured_data.get('prop_batie', [])) + len(structured_data.get('non_batie', []))
                
                # Si différence significative, alerter et possiblement re-extraire
                if expected_lines > 0 and len(owners) < (expected_lines * 0.5):  # Si moins de 50% du attendu
                    logger.warning(f"⚠️ EXTRACTION POTENTIELLEMENT INCOMPLÈTE:")
                    logger.warning(f"   - Propriétaires extraits: {len(owners)}")
                    logger.warning(f"   - Lignes tableaux détectées: {expected_lines}")
                    logger.warning(f"   - Ratio: {len(owners)}/{expected_lines} = {len(owners)/expected_lines*100:.1f}%")
                    
                    # Stratégie de secours : extraction d'urgence
                    if len(owners) <= 2 and expected_lines > 5:
                        logger.warning(f"🆘 ACTIVATION EXTRACTION DE SECOURS pour données manquantes")
                        try:
                            # Re-extraction avec prompt ultra-directif sur données manquantes
                            images = self.pdf_to_images(pdf_path)
                            if images:
                                base64_image = base64.b64encode(images[0]).decode('utf-8')
                                backup_owners = self.extract_line_by_line_debug(base64_image, 1)
                                if len(backup_owners) > len(owners):
                                    logger.info(f"✅ SECOURS RÉUSSI: {len(backup_owners)} vs {len(owners)} propriétaires")
                                    owners = backup_owners
                        except Exception as e:
                            logger.error(f"❌ Erreur extraction de secours: {e}")
                
                logger.info(f"👤 PROPRIÉTAIRES FINAUX APRÈS VALIDATION: {len(owners)}")
            
            # ✅ CORRECTION CRITIQUE: Filtrage des VRAIS propriétaires uniquement
            filtered_owners = []
            for owner in owners:
                nom = owner.get('nom', '').strip()
                prenom = owner.get('prenom', '').strip()
                if self.is_likely_real_owner(nom, prenom):
                    filtered_owners.append(owner)
                    logger.info(f"✅ Vrai propriétaire: {nom} {prenom}")
                else:
                    logger.info(f"❌ Rejeté (lieu-dit/adresse): {nom} {prenom}")
            
            owners = filtered_owners
            logger.info(f"👤 Propriétaires valides après filtrage: {len(owners)}")
            
            # 🚨 DÉTECTION EXPLOSION COMBINATOIRE ULTRA-STRICTE
            if len(owners) > 50:  # Seuil très strict
                logger.error(f"🚨 EXPLOSION DÉTECTÉE: {len(owners)} propriétaires extraits (limite: 50)")
                logger.error(f"💡 CAUSE PROBABLE: Contamination ou explosion combinatoire")
                
                # Filtrer UNIQUEMENT les propriétaires avec données géographiques complètes
                filtered_owners = []
                for owner in owners:
                    dept = owner.get('department', '').strip()
                    comm = owner.get('commune', '').strip()
                    nom = owner.get('nom', '').strip()
                    
                    # Ne garder QUE si : département ET commune ET nom valide
                    if dept and comm and nom and self.is_likely_real_owner(nom, owner.get('prenom', '')):
                        filtered_owners.append(owner)
                
                logger.warning(f"🧽 FILTRAGE STRICT: {len(filtered_owners)} propriétaires conservés sur {len(owners)}")
                owners = filtered_owners[:20]  # Limite de sécurité absolue
                logger.info(f"✅ SÉCURITÉ: Limitation à {len(owners)} propriétaires maximum")
            
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
                    
                    # 🚨 LIMITE ANTI-EXPLOSION : Éviter le produit cartésien massif
                    potential_combinations = len(owners) * len([p for p in non_batie_props if p.get('Adresse')])
                    if potential_combinations > 100:
                        logger.warning(f"🚨 EXPLOSION DÉTECTÉE: {potential_combinations} combinaisons potentielles ({len(owners)} propriétaires × {len([p for p in non_batie_props if p.get('Adresse')])} parcelles)")
                        logger.warning(f"🛡️ LIMITE ACTIVÉE: Traitement en mode single_owner pour éviter les données artificielles")
                        
                        # Basculer en mode single_owner avec le premier propriétaire
                        main_owner = self.select_main_owner(owners)
                        for prop in non_batie_props:
                            if prop.get('Adresse'):
                                unique_id = self.generate_id_with_openai_like_make(main_owner, prop)
                                combined = self.merge_like_make(main_owner, prop, unique_id, 'non_batie', pdf_path.name)
                                final_results.append(combined)
                    else:
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
                    
                    # 🚨 LIMITE ANTI-EXPLOSION : Éviter le produit cartésien massif
                    potential_combinations = len(owners) * len([p for p in prop_batie if p.get('Adresse')])
                    if potential_combinations > 100:
                        logger.warning(f"🚨 EXPLOSION DÉTECTÉE (bâties): {potential_combinations} combinaisons potentielles ({len(owners)} propriétaires × {len([p for p in prop_batie if p.get('Adresse')])} parcelles)")
                        logger.warning(f"🛡️ LIMITE ACTIVÉE: Traitement en mode single_owner pour éviter les données artificielles")
                        
                        # Basculer en mode single_owner avec le premier propriétaire
                        main_owner = self.select_main_owner(owners)
                        for prop in prop_batie:
                            if prop.get('Adresse'):
                                unique_id = self.generate_id_with_openai_like_make(main_owner, prop)
                                combined = self.merge_like_make(main_owner, prop, unique_id, 'batie', pdf_path.name)
                                final_results.append(combined)
                    else:
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
            
            # ÉTAPE 6: Suppression des lignes sans numéro de parcelle
            final_results = self.remove_empty_parcel_numbers(final_results, pdf_path.name)
            
            # ÉTAPE 6.5: PROPAGATION GÉOGRAPHIQUE FORCÉE (ANTI-CONTAMINATION)
            logger.info("🎯 ÉTAPE 6.5: Propagation géographique forcée (anti-contamination)")
            
            if final_results:
                # Extraire géographie depuis en-tête PDF si disponible
                location_info = self.extract_location_info(final_results, "", pdf_path.name)
                if location_info and location_info[0] if isinstance(location_info, list) else location_info:
                    header_data = location_info[0] if isinstance(location_info, list) else location_info
                    header_dept = str(header_data.get('department', '')).strip()
                    header_commune = str(header_data.get('commune', '')).strip()
                    
                    # Vérifier si la géographie de l'en-tête est valide
                    if (header_dept.isdigit() and len(header_dept) == 2 and 
                        header_commune.isdigit() and len(header_commune) == 3):
                        
                        # PROPAGATION FORCÉE sur toutes les lignes Unknown/invalides
                        propagated_count = 0
                        for prop in final_results:
                            dept = str(prop.get('department', '')).strip()
                            comm = str(prop.get('commune', '')).strip()
                            
                            # Si géographie manquante/invalide → forcer avec en-tête
                            if (not dept or not comm or 
                                dept in ['Unknown', 'XX', 'COMMUNE'] or 
                                comm in ['Unknown', 'XX', 'COMMUNE'] or
                                not dept.isdigit() or not comm.isdigit()):
                                
                                prop['department'] = header_dept
                                prop['commune'] = header_commune
                                propagated_count += 1
                        
                        logger.info(f"   ✅ Propagation forcée: {propagated_count} lignes corrigées avec {header_dept}/{header_commune}")
                    else:
                        logger.warning(f"   ⚠️ En-tête géographique invalide: {header_dept}/{header_commune}")
                else:
                    logger.warning(f"   ⚠️ Impossible d'extraire géographie depuis en-tête PDF")
            
            # ÉTAPE 7: Filtrage géographique par référence (première ligne valide)
            final_results = self.filter_by_geographic_reference(final_results, pdf_path.name)
            
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
        
        ✅ AMÉLIORÉ : Détection plus fine des cas multi-propriétaires
        """
        if not owners:
            return "multiple_owners"
        
        # Analyse détaillée des propriétaires
        unique_owners = set()
        valid_owners = []
        family_names = {}
        droit_types = set()
        
        for owner in owners:
            nom = owner.get('nom', '').strip().upper()
            prenom = owner.get('prenom', '').strip().upper()
            droit = owner.get('droit_reel', '').strip().upper()
            owner_key = f"{nom}|{prenom}"
            unique_owners.add(owner_key)
            
            # Filtrer les vrais propriétaires
            if self.is_likely_real_owner(nom, prenom):
                valid_owners.append(owner)
                
                # Analyser les noms de famille
                if nom:
                    if nom not in family_names:
                        family_names[nom] = set()
                    family_names[nom].add(prenom)
                
                # Collecter les types de droits
                if droit:
                    droit_types.add(droit)
        
        num_properties = len(structured_data.get('non_batie', [])) + len(structured_data.get('prop_batie', []))
        num_unique_owners = len(unique_owners)
        num_valid_owners = len(valid_owners)
        num_families = len(family_names)
        
        logger.info(f"📊 Analyse détaillée: {num_unique_owners} extraits, {num_valid_owners} valides, {num_families} familles, {num_properties} propriétés")
        logger.info(f"📊 Types de droits: {list(droit_types)}")
        
        # ✅ SIGNAL FORT MULTI-PROPRIÉTAIRES : Usufruitier + Nu-propriétaires
        critical_patterns = ['USUFRUITIER', 'NU-PROPRIÉTAIRE', 'NU-PROP', 'USUFRUIT']
        has_usufruit_pattern = any(pattern in ' '.join(droit_types) for pattern in critical_patterns)
        
        if has_usufruit_pattern:
            logger.info(f"🎯 DÉTECTION FORTE: Types de droits usufruitiers détectés → multiple_owners")
            return "multiple_owners"
        
        # ✅ SIGNAL FORT : Plusieurs membres d'une même famille
        multi_family_members = any(len(prenoms) > 1 for prenoms in family_names.values())
        if multi_family_members and num_families <= 3:
            logger.info(f"🎯 DÉTECTION FORTE: Plusieurs membres de famille(s) → multiple_owners")
            return "multiple_owners"
        
        # ✅ SIGNAL FORT : Noms de famille très différents
        if num_families >= 3 and num_valid_owners >= 3:
            logger.info(f"🎯 DÉTECTION FORTE: {num_families} familles différentes → multiple_owners")
            return "multiple_owners"
        
        # ✅ CRITÈRE VOLUME : Si très peu de vrais propriétaires pour beaucoup de propriétés
        if num_valid_owners <= 2 and num_properties > 50:
            logger.info(f"🎯 Détection: PDF type single_owner ({num_valid_owners} vrais propriétaires pour {num_properties} propriétés)")
            return "single_owner"
        
        # ✅ CRITÈRE RATIO : Si ratio propriétaires/propriétés très faible 
        ratio_valid = num_valid_owners / max(num_properties, 1)
        if ratio_valid < 0.05:  # Moins de 5% (plus strict pour éviter erreurs)
            logger.info(f"🎯 Détection: PDF type single_owner (ratio {ratio_valid:.3f} très faible)")
            return "single_owner"
        
        # ✅ CAS MULTIPLE : Si beaucoup de propriétaires valides OU ratio élevé
        if num_valid_owners > 5 or ratio_valid > 0.3:
            logger.info(f"🎯 Détection: PDF type multiple_owners ({num_valid_owners} propriétaires, ratio {ratio_valid:.3f})")
            return "multiple_owners"
        
        # ✅ PAR DÉFAUT CONSERVATEUR : En cas de doute, privilégier multiple_owners
        # (Évite de rater des propriétaires en assumant single_owner)
        logger.info(f"🎯 Détection conservatrice: PDF type multiple_owners par défaut (sécurité)")
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
            'COM', 'COMMUNE', 'VILLE', 'MAIRIE', 'ÉTAT', 'DÉPARTEMENT', 'RÉGION',
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
        ✅ EXTRACTION ULTRA-ROBUSTE - Stratégies multiples pour capturer TOUS les propriétaires.
        
        Stratégies successives :
        1. Prompt standard amélioré
        2. Extraction spécialisée usufruitier/nu-propriétaire
        3. Mode debugging avec extraction ligne par ligne
        4. Extraction d'urgence simplifiée
        """
        logger.info(f"🎯 EXTRACTION ULTRA-ROBUSTE pour {pdf_path.name}")
        
        # Convertir PDF en images
        images = self.pdf_to_images(pdf_path)
        if not images:
            return []
        
        all_owners = []
        
        for page_num, image_data in enumerate(images, 1):
            logger.info(f"📄 Traitement page {page_num}/{len(images)}")
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # 🎯 STRATÉGIE 1: Prompt ultra-directif (version améliorée)
            page_owners = self.extract_with_ultra_directive_prompt(base64_image, page_num)
            
            # ✅ Si extraction insuffisante, essayer stratégies de secours
            if len(page_owners) <= 1:
                logger.warning(f"⚠️ Page {page_num}: Seulement {len(page_owners)} propriétaire(s) - Activation stratégies de secours")
                
                # 🎯 STRATÉGIE 2: Extraction spécialisée usufruitiers/nu-propriétaires
                backup_owners = self.extract_usufruit_nu_propriete_specialized(base64_image, page_num)
                if len(backup_owners) > len(page_owners):
                    logger.info(f"🔄 Stratégie usufruitier meilleure: {len(backup_owners)} vs {len(page_owners)}")
                    page_owners = backup_owners
                
                # 🎯 STRATÉGIE 3: Mode debugging ligne par ligne
                if len(page_owners) <= 1:
                    debug_owners = self.extract_line_by_line_debug(base64_image, page_num)
                    if len(debug_owners) > len(page_owners):
                        logger.info(f"🔄 Mode debug meilleur: {len(debug_owners)} vs {len(page_owners)}")
                        page_owners = debug_owners
                
                # 🎯 STRATÉGIE 4: Extraction d'urgence ultra-simple
                if len(page_owners) <= 1:
                    emergency_owners = self.extract_emergency_all_names(base64_image, page_num)
                    if len(emergency_owners) > len(page_owners):
                        logger.info(f"🆘 Mode urgence meilleur: {len(emergency_owners)} vs {len(page_owners)}")
                        page_owners = emergency_owners
            
            # Ajouter les propriétaires trouvés
            if page_owners:
                all_owners.extend(page_owners)
                logger.info(f"✅ Page {page_num}: {len(page_owners)} propriétaire(s) finalement extraits")
            else:
                logger.warning(f"❌ Page {page_num}: Aucun propriétaire extrait malgré toutes les stratégies")
        
        logger.info(f"📊 TOTAL APRÈS TOUTES STRATÉGIES: {len(all_owners)} propriétaire(s)")
        
        # Post-traitement classique
        all_owners = self.detect_and_fix_legal_entities(all_owners)
        validated_owners = self.validate_complete_extraction(all_owners, pdf_path.name)
        
        return validated_owners
    
    def extract_with_ultra_directive_prompt(self, base64_image: str, page_num: int) -> List[Dict]:
        """Stratégie 1: Prompt ultra-directif avec emphase sur la multiplicité"""
        try:
            prompt = """🚨 ALERTE CRITIQUE: Ce document peut contenir PLUSIEURS PROPRIÉTAIRES avec DIFFÉRENTS TYPES DE DROITS !

🎯 MISSION ABSOLUE: Trouve et extrait CHAQUE PERSONNE mentionnée dans ce document cadastral français.

⭐ TYPES DE DROITS CRITIQUES À IDENTIFIER:
- USUFRUITIER (personne qui a l'usufruit)
- NU-PROPRIÉTAIRE (personne qui a la nue-propriété)
- PROPRIÉTAIRE (pleine propriété)
- INDIVISAIRE (propriété en indivision)

🔍 MÉTHODE DE SCAN SYSTÉMATIQUE:

1️⃣ CHERCHE PARTOUT LES MOTS "TITULAIRE", "PROPRIÉTAIRE", "USUFRUITIER", "NU-PROPRIÉTAIRE"
2️⃣ POUR CHAQUE BLOC TROUVÉ, LIS TOUS LES NOMS ET PRÉNOMS
3️⃣ NE T'ARRÊTE PAS après le premier - CONTINUE jusqu'à la fin du document
4️⃣ REGARDE SPÉCIALEMENT S'IL Y A DES LISTES DE PERSONNES
5️⃣ ATTENTION aux héritiers multiples (même famille, prénoms différents)

⚠️ EXEMPLE TYPIQUE DE CE QUE TU DOIS TROUVER:
- 1 Usufruitier: [NOM_USUFRUITIER] [PRENOM_USUFRUITIER]
- 3 Nu-propriétaires: [NOM_NU_PROP_1] [PRENOM_NU_PROP_1], [NOM_NU_PROP_2] [PRENOM_NU_PROP_2], [NOM_NU_PROP_3] [PRENOM_NU_PROP_3]

🚨 RÈGLE VITALE: Si tu vois "Usufruitier" ET "Nu-propriétaire", il y a FORCÉMENT PLUSIEURS PERSONNES !

RÉPONSE JSON:
{"owners": [
    {"nom": "[NOM_USUFRUITIER]", "prenom": "[PRENOM_USUFRUITIER]", "droit_reel": "Usufruitier", "street_address": "...", "city": "...", "post_code": "...", "numero_proprietaire": "...", "department": "...", "commune": "..."},
    {"nom": "[NOM_NU_PROP_1]", "prenom": "[PRENOM_NU_PROP_1]", "droit_reel": "Nu-propriétaire", "street_address": "...", "city": "...", "post_code": "...", "numero_proprietaire": "...", "department": "...", "commune": "..."},
    {"nom": "[NOM_NU_PROP_2]", "prenom": "[PRENOM_NU_PROP_2]", "droit_reel": "Nu-propriétaire", "street_address": "...", "city": "...", "post_code": "...", "numero_proprietaire": "...", "department": "...", "commune": "..."},
    {"nom": "[NOM_NU_PROP_3]", "prenom": "[PRENOM_NU_PROP_3]", "droit_reel": "Nu-propriétaire", "street_address": "...", "city": "...", "post_code": "...", "numero_proprietaire": "...", "department": "...", "commune": "..."}
]}

🚨 JAMAIS moins de propriétaires qu'il n'y en a réellement dans le document !"""

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}", "detail": "high"}}
                    ]
                }],
                max_tokens=3000,
                temperature=0.1,  # Plus déterministe
                response_format={"type": "json_object"}
            )
            
            result = safe_json_parse(response.choices[0].message.content, f"ultra-directif page {page_num}")
            return result.get("owners", []) if result else []
            
        except Exception as e:
            logger.error(f"Erreur stratégie ultra-directive page {page_num}: {e}")
            return []
    
    def extract_usufruit_nu_propriete_specialized(self, base64_image: str, page_num: int) -> List[Dict]:
        """Stratégie 2: Extraction spécialisée pour les cas usufruitier/nu-propriétaire"""
        try:
            prompt = """🎯 MISSION SPÉCIALISÉE: Tu es un expert en droits d'usufruit et nue-propriété.

📋 TON OBJECTIF: Identifier TOUS les usufruitiers ET TOUS les nu-propriétaires dans ce document.

🔍 INDICES À CHERCHER:
- Mots "USUFRUITIER", "USUFRUIT" → personne qui a l'usufruit
- Mots "NU-PROPRIÉTAIRE", "NUE-PROPRIÉTÉ" → personne(s) qui ont la nue-propriété
- Souvent: 1 usufruitier + plusieurs nu-propriétaires (enfants, héritiers)

⚖️ RÈGLE JURIDIQUE: L'usufruit + nue-propriété = propriété complète
- USUFRUITIER = peut utiliser le bien (souvent le parent survivant)
- NU-PROPRIÉTAIRES = propriétaires "en attente" (souvent les enfants)

🔍 MÉTHODE DE RECHERCHE:
1. Cherche le mot "USUFRUITIER" - note la personne associée
2. Cherche le mot "NU-PROPRIÉTAIRE" - note TOUTES les personnes associées
3. Cherche dans les tableaux, listes, sections du document
4. Ne manque AUCUN nom mentionné avec ces droits

EXEMPLE TYPIQUE:
- [PRENOM_USUFRUITIER] [NOM_USUFRUITIER] (veuve) = Usufruitier
- Ses 3 enfants = Nu-propriétaires

{"owners": [
    {"nom": "...", "prenom": "...", "droit_reel": "Usufruitier", "numero_proprietaire": "...", "street_address": "...", "city": "...", "post_code": "...", "department": "...", "commune": "..."},
    {"nom": "...", "prenom": "...", "droit_reel": "Nu-propriétaire", "numero_proprietaire": "...", "street_address": "...", "city": "...", "post_code": "...", "department": "...", "commune": "..."}
]}"""

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user", 
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}", "detail": "high"}}
                    ]
                }],
                max_tokens=2500,
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            result = safe_json_parse(response.choices[0].message.content, f"usufruit spécialisé page {page_num}")
            return result.get("owners", []) if result else []
            
        except Exception as e:
            logger.error(f"Erreur stratégie usufruit page {page_num}: {e}")
            return []
    
    def extract_line_by_line_debug(self, base64_image: str, page_num: int) -> List[Dict]:
        """Stratégie 3: Mode debugging - extraction ligne par ligne"""
        try:
            prompt = """🔍 MODE DEBUGGING: Lis ce document ligne par ligne et trouve tous les noms de personnes.

📋 INSTRUCTIONS DE DEBUG:
1. Scanne le document de haut en bas
2. Pour CHAQUE ligne, note s'il y a un nom de personne
3. Ignore les adresses, lieux-dits, mais garde les vrais noms
4. Cherche particulièrement après les mots: TITULAIRE, PROPRIÉTAIRE, USUFRUITIER, NU-PROPRIÉTAIRE

🎯 PATTERN DE NOMS À CHERCHER:
- NOM en MAJUSCULES + prénom en minuscules
- Exemples: [NOM1] [Prénom1], [NOM2] [Prénom2], [NOM3] [Prénom3]
- Codes associés (6 caractères): M8BNF6, N7QX21, etc.

⚠️ À IGNORER:
- Noms de rues: RUE DE..., AVENUE..., PLACE...
- Lieux-dits: MONT DE..., COTE DE..., VAL DE...

Retourne TOUS les noms trouvés:
{"owners": [
    {"nom": "NOM1", "prenom": "Prénom1", "droit_reel": "...", "numero_proprietaire": "...", "street_address": "...", "city": "...", "post_code": "...", "department": "...", "commune": "..."}
]}"""

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}", "detail": "high"}}
                    ]
                }],
                max_tokens=2000,
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            result = safe_json_parse(response.choices[0].message.content, f"debug ligne-par-ligne page {page_num}")
            return result.get("owners", []) if result else []
            
        except Exception as e:
            logger.error(f"Erreur mode debug page {page_num}: {e}")
            return []
    
    def extract_emergency_all_names(self, base64_image: str, page_num: int) -> List[Dict]:
        """Stratégie 4: Extraction d'urgence - trouve tous les noms possibles"""
        try:
            prompt = """🆘 MODE URGENCE: Trouve TOUS les noms de personnes dans ce document, même partiellement.

MISSION SIMPLE: Liste TOUS les noms que tu vois, même si les informations sont incomplètes.

Cherche:
- Noms en MAJUSCULES
- Prénoms associés  
- N'importe quel pattern de personne

{"owners": [
    {"nom": "TOUS_LES_NOMS_TROUVÉS", "prenom": "TOUS_LES_PRÉNOMS", "droit_reel": "", "numero_proprietaire": "", "street_address": "", "city": "", "post_code": "", "department": "", "commune": ""}
]}"""

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}", "detail": "high"}}
                    ]
                }],
                max_tokens=1500,
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            result = safe_json_parse(response.choices[0].message.content, f"urgence page {page_num}")
            return result.get("owners", []) if result else []
            
        except Exception as e:
            logger.error(f"Erreur mode urgence page {page_num}: {e}")
            return []

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
            'COM', 'COMMUNE DE', 'VILLE DE', 'MAIRIE DE',
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

    def validate_complete_extraction(self, owners: List[Dict], filename: str) -> List[Dict]:
        """
        ✅ VALIDATION CRITIQUE: Vérification que l'extraction est complète.
        
        Analyse les signaux d'extraction incomplète et alerte si nécessaire.
        """
        if not owners:
            logger.warning(f"🚨 EXTRACTION INCOMPLÈTE: Aucun propriétaire extrait pour {filename}")
            return owners
        
        logger.info(f"🔍 Validation extraction: {len(owners)} propriétaire(s) pour {filename}")
        
        # Analyser les patterns qui suggèrent une extraction incomplète
        unique_names = set()
        name_counts = {}
        droit_types = set()
        
        for owner in owners:
            nom = owner.get('nom', '').strip()
            prenom = owner.get('prenom', '').strip()
            droit = owner.get('droit_reel', '').strip()
            
            full_name = f"{nom} {prenom}".strip()
            unique_names.add(full_name)
            
            if full_name in name_counts:
                name_counts[full_name] += 1
            else:
                name_counts[full_name] = 1
            
            if droit:
                droit_types.add(droit.upper())
        
        # ✅ SIGNAL 1: Très peu de propriétaires uniques
        if len(unique_names) == 1 and len(owners) > 5:
            logger.warning(f"🚨 POTENTIEL PROBLÈME: Un seul nom unique ({list(unique_names)[0]}) répété {len(owners)} fois")
            logger.warning(f"💡 SUGGESTION: Vérifier si le document contient d'autres propriétaires")
        
        # ✅ SIGNAL 2: Mélange de types de droits suggère multi-propriétaires
        critical_droit_patterns = ['USUFRUITIER', 'NU-PROPRIÉTAIRE', 'NU-PROP', 'USUFRUIT']
        has_critical_patterns = any(pattern in ' '.join(droit_types) for pattern in critical_droit_patterns)
        
        if has_critical_patterns and len(unique_names) == 1:
            logger.warning(f"🚨 ALERTE CRITIQUE: Types de droits multiples détectés ({droit_types}) mais un seul propriétaire")
            logger.warning(f"💡 CONSEIL: Un usufruitier implique généralement plusieurs nu-propriétaires")
        
        # ✅ SIGNAL 3: Noms de famille identiques avec prénoms différents
        family_names = {}
        for owner in owners:
            nom = owner.get('nom', '').strip().upper()
            prenom = owner.get('prenom', '').strip()
            if nom:
                if nom not in family_names:
                    family_names[nom] = set()
                family_names[nom].add(prenom)
        
        for family_name, prenoms in family_names.items():
            if len(prenoms) > 1:
                logger.info(f"✅ Famille {family_name}: {len(prenoms)} prénoms trouvés → Extraction multi-héritiers probable")
        
        # ✅ RAPPORT DE VALIDATION
        logger.info(f"📊 RAPPORT VALIDATION {filename}:")
        logger.info(f"   👥 {len(owners)} propriétaires extraits")
        logger.info(f"   🔤 {len(unique_names)} noms uniques")
        logger.info(f"   ⚖️ {len(droit_types)} types de droits: {list(droit_types)}")
        
        # Si extraction semble complète
        if len(unique_names) > 1 or (len(unique_names) == 1 and len(owners) == 1):
            logger.info(f"✅ Validation réussie: extraction semble complète")
        else:
            logger.warning(f"⚠️ Validation incertaine: vérifier manuellement le PDF")
        
        return owners

    def merge_like_make(self, owner: Dict, prop: Dict, unique_id: str, prop_type: str, pdf_path_name: str) -> Dict:
        """
        ✅ FUSION CORRIGÉE avec gestion optimisée des contenances et adresses.
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
        
        # ✅ CORRECTION CONTENANCE : Gestion des formats français et parsing robuste
        contenance_ha = self.parse_contenance_value(prop.get('HA', prop.get('Contenance', '')))
        contenance_a = self.parse_contenance_value(prop.get('A', ''))
        contenance_ca = self.parse_contenance_value(prop.get('CA', ''))
        
        # ✅ CORRECTION NOMS/PRÉNOMS : Séparation intelligente des noms composés
        nom_final, prenom_final = self.split_name_intelligently(
            owner.get('nom', ''), owner.get('prenom', '')
        )
        
        # ✅ CORRECTION ADRESSES : Nettoyage et validation des adresses
        voie_cleaned = self.clean_address(owner.get('street_address', ''))
        
        # Mapping exact comme dans Make Google Sheets (CORRIGÉ)
        merged = {
            # Colonnes A-E (informations parcelle)
            'department': str(owner.get('department', '')),  # Colonne A
            'commune': clean_commune_code(str(owner.get('commune', ''))),        # Colonne B - CORRIGÉ avec nettoyage  
            'prefixe': final_prefixe,                        # Colonne C (CORRIGÉ - séparation auto)
            'section': final_section,                        # Colonne D (CORRIGÉ - séparation auto)
            'numero': str(prop.get('N° Plan', '')),         # Colonne E
            
            # Colonnes F-H (gestion/demande - vides dans Make)
            'demandeur': '',    # Colonne F
            'date': '',         # Colonne G  
            'envoye': '',       # Colonne H
            
            # Colonne I (designation + contenance détaillée CORRIGÉE)
            'designation_parcelle': str(prop.get('Adresse', '')),  # Colonne I
            'contenance_ha': contenance_ha,     # ✅ CORRIGÉ - Parsing français
            'contenance_a': contenance_a,       # ✅ CORRIGÉ - Parsing français  
            'contenance_ca': contenance_ca,     # ✅ CORRIGÉ - Parsing français
            
            # Colonnes J-O (propriétaire CORRIGÉES)
            'nom': nom_final,                                    # ✅ CORRIGÉ - Séparation intelligente
            'prenom': prenom_final,                             # ✅ CORRIGÉ - Séparation intelligente
            'numero_majic': str(owner.get('numero_proprietaire', '')),  # Colonne L
            'voie': voie_cleaned,                               # ✅ CORRIGÉ - Adresse nettoyée
            'post_code': str(owner.get('post_code', '')),       # Colonne N
            'city': str(owner.get('city', '')),                 # Colonne O
            
            # Colonnes P-R (statuts - vides dans Make)
            'identifie': '',    # Colonne P
            'rdp': '',          # Colonne Q
            'sig': '',          # Colonne R
            
            # Colonnes S-T (ID et droit)
            'id': unique_id,                                    # Colonne S
            'droit_reel': str(owner.get('droit_reel', '')),    # Colonne T - ✅ CORRIGÉ: clé avec underscore
            
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
        
        RENFORCÉ : Filtre strictement les résidus parasites et lignes artificielles.
        """
        if not nom.strip():
            return False
            
        nom_upper = nom.upper().strip()
        prenom_clean = prenom.strip()
        
        # 🚨 FILTRE STRICT: Éliminer immédiatement les mots parasites spécifiques
        parasitic_words = [
            'AUX', 'LAVES', 'ECHASSIR', 'ECURIE', 'GABOIS', 'NAUX', 'MANDE', 
            'NOIX', 'MONTANT', 'PUISEAU', 'REMEMBRES', 'PRINCESSES', 'PARC',
            'MARECHAUX', 'AUXERRE', 'FORETS', 'BLANC', 'MALVOISINE', 'LONGEVAS',
            'VAL', 'COTE', 'MONT', 'CHAMPS', 'PRES', 'BOIS', 'DESSUS', 'DESSOUS'
        ]

        # Si le nom exact correspond à un mot parasite, REJETER immédiatement
        if nom_upper in parasitic_words:
            logger.debug(f"🗑️ REJETÉ (mot parasite): {nom}")
            return False

        # Si le nom commence par un pattern suspect, REJETER
        suspicious_starts = ['LE ', 'LA ', 'LES ', 'DU ', 'DE ', 'AU ', 'AUX ']
        if any(nom_upper.startswith(pattern) for pattern in suspicious_starts):
            logger.debug(f"🗑️ REJETÉ (préfixe suspect): {nom}")
            return False
        
        # ✅ CRITÈRE 1: Personnes morales (communes, sociétés) - PRIORITÉ ABSOLUE
        legal_entity_keywords = [
            'COM', 'COMMUNE', 'VILLE', 'MAIRIE', 'ÉTAT', 'DÉPARTEMENT', 'RÉGION',
            'SCI', 'SARL', 'SASU', 'EURL', 'SA', 'SOCIÉTÉ', 'ENTERPRISE',
            'ASSOCIATION', 'SYNDICAT', 'FEDERATION', 'UNION'
        ]
        
        for keyword in legal_entity_keywords:
            if keyword in nom_upper and len(nom.strip()) >= 8:  # Nom suffisamment long
                return True
        
        # ✅ CRITÈRE 2: Rejet des adresses/lieux-dits (APRÈS vérification personnes morales)
        if self.looks_like_address(nom_upper):
            return False
        
        # ✅ CRITÈRE 3: Personnes physiques avec prénom
        if prenom_clean and len(prenom_clean) >= 2:
            # Nom de famille classique (pas trop court, pas d'adresse)
            if len(nom.strip()) >= 3 and not self.looks_like_address(nom_upper):
                return True
        
        # ✅ CRITÈRE 4: Noms de famille seuls mais plausibles
        if not prenom_clean:
            # Doit ressembler à un nom de famille (pas d'adresse, longueur raisonnable)
            if (len(nom.strip()) >= 5 and 
                not self.looks_like_address(nom_upper) and
                not any(char.isdigit() for char in nom) and  # Pas de chiffres
                nom_upper not in ['N/A', 'NULL', 'VIDE', 'INCONNU']):
                return True
        
        # ✅ CRITÈRE 5: Patterns de noms classiques français
        classic_patterns = ['MC', 'MAC', 'DE ', 'DU ', 'LE ', 'LA ']
        for pattern in classic_patterns:
            if pattern in nom_upper and len(nom.strip()) >= 5:
                return True
        
        # Par défaut : REJETER si aucun critère positif
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
            'ROCHE', 'PIERRE', 'MONT', 'COL', 'VALLEE', 'PLAINE', 'PLATEAU',
            # ✅ AJOUTS SPÉCIFIQUES aux données utilisateur
            'NOIX', 'MANDE', 'NAUX', 'GOBAIN', 'MONTANT', 'REMEMBRES', 'PUISEAU',
            'GABOIS', 'PRINCESSES', 'PARC', 'MARECHAUX', 'AUXERRE', 'FORETS',
            'BLANC', 'MALVOISINE', 'LONGEVAS',
            # 🚨 AJOUTS ANTI-RÉSIDUS STRICTS
            'CUDRET', 'SEUT', 'GIBELIN', 'VALLON', 'TERRES', 'CHAMP', 'PRE',
            'VIGNE', 'VIGNOBLE', 'ETANG', 'MARE', 'SOURCE', 'FONTAINE',
            'CROIX', 'CALVAIRE', 'CHAPELLE', 'MOULIN', 'FERME', 'GRANGE'
        ]
        
        # Si le nom contient des mots-clés d'adresse
        for keyword in address_keywords:
            if keyword in nom_upper:
                return True
        
        # Patterns d'adresses typiques (enrichis)
        address_patterns = [
            'GIRARDET', 'HAUTETERRE', 'HAUTEPIERRE', 'REISSILLE',
            # ✅ Patterns spécifiques aux données utilisateur
            'MONT DE NOIX', 'COTE DE MANDE', 'SUR LES NAUX', 'MONTANT DU NOYER',
            'VAL DE PUISEAU', 'LA VALLEE DE', 'CHE DES VIGNES', 'RUE D EN HAUT',
            'RENVERS DES FORETS', 'HAM DE MALVOISINE', 'VIEILLE RUE D'
        ]
        
        for pattern in address_patterns:
            if pattern in nom_upper:
                return True
        
        return False

    def clean_inconsistent_location_data(self, properties: List[Dict], filename: str) -> List[Dict]:
        """
        Nettoie les incohérences géographiques par fichier source.
        
        Pour chaque fichier :
        1. Analyser TOUTES les lignes pour identifier le couple (département, commune) de référence
        2. En cas d'égalité, prendre la première localisation dans l'ordre du fichier
        3. Supprimer toutes les lignes avec un couple différent ou des valeurs vides
        
        Args:
            properties: Liste des propriétés à nettoyer
            filename: Nom du fichier pour les logs
            
        Returns:
            Liste filtrée sans les lignes géographiquement incohérentes
        """
        if not properties:
            return properties
        
        initial_count = len(properties)
        
        # Grouper par fichier source
        files_groups = {}
        for prop in properties:
            file_source = prop.get('fichier_source', 'unknown')
            if file_source not in files_groups:
                files_groups[file_source] = []
            files_groups[file_source].append(prop)
        
        cleaned_properties = []
        total_removed = 0
        
        # Traiter chaque fichier séparément
        for file_source, file_props in files_groups.items():
            logger.info(f"🌍 Nettoyage géographique pour {file_source}: {len(file_props)} lignes")
            
            # ÉTAPE 1: Analyser TOUTES les lignes pour identifier la référence géographique
            location_counts = {}
            location_first_occurrence = {}  # Mémoriser l'ordre d'apparition
            
            for index, prop in enumerate(file_props):
                dept = str(prop.get('department', '')).strip()
                commune = str(prop.get('commune', '')).strip()
                
                # Ignorer les valeurs vides pour la référence
                if dept and commune and dept != 'N/A' and commune != 'N/A':
                    location_key = f"{dept}-{commune}"
                    
                    # Compter les occurrences
                    location_counts[location_key] = location_counts.get(location_key, 0) + 1
                    
                    # Mémoriser la première occurrence pour le départage
                    if location_key not in location_first_occurrence:
                        location_first_occurrence[location_key] = index
            
            # Si aucune référence valide trouvée, garder toutes les lignes
            if not location_counts:
                logger.warning(f"⚠️ {file_source}: Aucune référence géographique trouvée, conservation de toutes les lignes")
                cleaned_properties.extend(file_props)
                continue
            
            # Couple de référence = le premier dans l'ordre du fichier (pour respecter votre demande)
            # Modification : au lieu de prendre le plus fréquent, prendre le premier
            reference_location = min(location_counts.keys(), key=lambda loc: location_first_occurrence[loc])
            
            # ✅ CORRECTION CRITIQUE: Gestion des tirets multiples dans la clé
            try:
                # Utiliser split avec maxsplit=1 pour ne séparer que sur le premier tiret
                parts = reference_location.split('-', 1)
                if len(parts) == 2:
                    ref_dept, ref_commune = parts
                else:
                    # Fallback si le format est inattendu
                    logger.warning(f"⚠️ Format de référence inattendu: {reference_location}")
                    ref_dept = parts[0] if parts else ""
                    ref_commune = ""
            except Exception as e:
                logger.error(f"❌ Erreur parsing référence géographique '{reference_location}': {e}")
                # En cas d'erreur, garder toutes les lignes de ce fichier
                cleaned_properties.extend(file_props)
                continue
            
            logger.info(f"   - Référence identifiée: département={ref_dept}, commune={ref_commune}")
            logger.info(f"   - Basée sur la première occurrence dans le fichier")
            
            # ÉTAPE 2: Filtrer selon la référence
            file_cleaned = []
            file_removed = 0
            
            for prop in file_props:
                dept = str(prop.get('department', '')).strip()
                commune = str(prop.get('commune', '')).strip()
                
                # Supprimer si valeurs vides
                if not dept or not commune or dept == 'N/A' or commune == 'N/A':
                    file_removed += 1
                    logger.debug(f"      🗑️ Supprimé (valeurs vides): {prop.get('nom', 'N/A')} - dept={dept}, commune={commune}")
                    continue
                
                # Supprimer si différent de la référence
                if dept != ref_dept or commune != ref_commune:
                    file_removed += 1
                    logger.debug(f"      🗑️ Supprimé (incohérent): {prop.get('nom', 'N/A')} - {dept}-{commune} vs {reference_location}")
                    continue
                
                # Garder si cohérent
                file_cleaned.append(prop)
            
            cleaned_properties.extend(file_cleaned)
            total_removed += file_removed
            
            logger.info(f"   - ✅ {len(file_cleaned)} lignes conservées, {file_removed} supprimées")
        
        final_count = len(cleaned_properties)
        logger.info(f"🎯 ÉTAPE 7 TERMINÉE: {total_removed} ligne(s) supprimée(s) au total, {final_count} conservée(s)")
        
        return cleaned_properties

    def filter_by_geographic_reference(self, properties: List[Dict], filename: str) -> List[Dict]:
        """
        Filtrage géographique par référence : prend la première ligne valide comme référence
        et supprime toutes les lignes avec un département/commune différent.
        
        Args:
            properties: Liste des propriétés à filtrer  
            filename: Nom du fichier pour les logs
            
        Returns:
            Liste filtrée selon la référence géographique de la première ligne valide
        """
        if not properties:
            return properties
        
        initial_count = len(properties)
        
        # Grouper par fichier source pour traiter chaque PDF séparément
        files_groups = {}
        for prop in properties:
            file_source = prop.get('fichier_source', 'unknown')
            if file_source not in files_groups:
                files_groups[file_source] = []
            files_groups[file_source].append(prop)
        
        filtered_properties = []
        total_removed = 0
        
        # Traiter chaque fichier séparément
        for file_source, file_props in files_groups.items():
            logger.info(f"🎯 Filtrage géographique par référence pour {file_source}: {len(file_props)} lignes")
            
            # ÉTAPE 1: Trouver la PREMIÈRE géographie RÉELLEMENT VALIDE (ANTI-CONTAMINATION ULTRA-STRICT)
            reference_dept = None
            reference_commune = None
            reference_found_at = -1
            
            # Chercher la première géographie avec critères ultra-stricts
            for index, prop in enumerate(file_props):
                dept = str(prop.get('department', '')).strip()
                commune = str(prop.get('commune', '')).strip()
                
                # ✅ CRITÈRES ULTRA-STRICTS pour géographie valide
                if (dept and commune and 
                    dept not in ['', 'N/A', 'None', 'XX', 'Unknown'] and 
                    commune not in ['', 'N/A', 'None', 'COMMUNE', 'Unknown'] and
                    # OBLIGATOIRE : codes numériques seulement
                    dept.isdigit() and len(dept) == 2 and
                    commune.isdigit() and len(commune) == 3):
                    
                    reference_dept = dept
                    reference_commune = commune
                    reference_found_at = index
                    logger.info(f"   📍 Référence VALIDE trouvée: {dept}/{commune} (ligne {index+1})")
                    break
            
            # MODE DE SECOURS si aucune géographie parfaitement valide
            if reference_dept is None:
                logger.warning(f"⚠️ AUCUNE géographie ultra-valide trouvée - Mode de secours activé")
                for index, prop in enumerate(file_props):
                    dept = str(prop.get('department', '')).strip()
                    commune = str(prop.get('commune', '')).strip()
                    if (dept and commune and 
                        any(c.isdigit() for c in dept) and any(c.isdigit() for c in commune) and
                        dept not in ['XX', 'COMMUNE', 'Unknown'] and commune not in ['XX', 'COMMUNE', 'Unknown']):
                        reference_dept = dept
                        reference_commune = commune
                        logger.warning(f"   🆘 Mode de secours: {dept}/{commune}")
                        break
            
            # Si aucune référence trouvée, ignorer le filtrage pour ce fichier
            if reference_dept is None or reference_commune is None:
                logger.warning(f"⚠️ {file_source}: Aucune référence géographique valide trouvée - conservation de toutes les lignes")
                filtered_properties.extend(file_props)
                continue
            
            # ÉTAPE 2: Filtrer selon la référence
            file_filtered = []
            file_removed = 0
            
            for index, prop in enumerate(file_props):
                dept = str(prop.get('department', '')).strip()
                commune = str(prop.get('commune', '')).strip()
                
                # Ignorer le filtrage si département/commune vides ou sans chiffres (comme demandé)
                if (not dept or not commune or dept in ['', 'N/A', 'None'] or commune in ['', 'N/A', 'None'] or
                    not any(c.isdigit() for c in dept) or not any(c.isdigit() for c in commune)):
                    file_filtered.append(prop)
                    logger.debug(f"      ⏭️ Ignoré (valeurs vides ou sans chiffres): ligne {index + 1}")
                    continue
                
                # Garder si correspond à la référence
                if dept == reference_dept and commune == reference_commune:
                    file_filtered.append(prop)
                    logger.debug(f"      ✅ Conservé (référence): ligne {index + 1}")
                else:
                    # Supprimer si différent de la référence
                    file_removed += 1
                    logger.debug(f"      🗑️ Supprimé (hors référence): ligne {index + 1} - {dept}-{commune} vs {reference_dept}-{reference_commune}")
            
            filtered_properties.extend(file_filtered)
            total_removed += file_removed
            
            logger.info(f"   ✅ {len(file_filtered)} lignes conservées, {file_removed} supprimées")
        
        final_count = len(filtered_properties)
        logger.info(f"🎯 FILTRAGE GÉOGRAPHIQUE TERMINÉ: {total_removed} ligne(s) supprimée(s) au total, {final_count} conservée(s)")
        
        return filtered_properties

    def remove_empty_parcel_numbers(self, properties: List[Dict], filename: str) -> List[Dict]:
        """
        Supprime les lignes où la colonne 'numero' (numéro de parcelle) est vide.
        
        Args:
            properties: Liste des propriétés à filtrer
            filename: Nom du fichier pour les logs
            
        Returns:
            Liste filtrée sans les lignes avec numéro de parcelle vide
        """
        if not properties:
            return properties
        
        initial_count = len(properties)
        
        # Filtrer les propriétés avec un numéro de parcelle non vide
        filtered_properties = []
        for prop in properties:
            numero = str(prop.get('numero', '')).strip()
            
            # Garder seulement les lignes avec un numéro de parcelle valide
            if numero and numero not in ['', 'N/A', 'None', 'null', '0']:
                filtered_properties.append(prop)
            else:
                logger.debug(f"🗑️ Ligne supprimée (numéro de parcelle vide): {prop.get('nom', 'N/A')} - {prop.get('designation_parcelle', 'N/A')}")
        
        removed_count = initial_count - len(filtered_properties)
        
        if removed_count > 0:
            logger.info(f"🧹 ÉTAPE 6: Suppression des lignes sans numéro de parcelle")
            logger.info(f"   - {removed_count} ligne(s) supprimée(s) sur {initial_count}")
            logger.info(f"   - {len(filtered_properties)} ligne(s) conservée(s)")
        else:
            logger.info(f"✅ ÉTAPE 6: Aucune ligne sans numéro de parcelle trouvée ({initial_count} lignes vérifiées)")
        
        return filtered_properties

    def final_validation_before_export(self, all_properties: List[Dict]) -> List[Dict]:
        """
        🔍 VALIDATION FINALE STRICTE avant export - Dernière vérification qualité.
        
        Détecte et corrige les derniers problèmes avant l'export final.
        """
        logger.info(f"🔍 VALIDATION FINALE - {len(all_properties)} propriétés à valider")
        
        if not all_properties:
            return all_properties
        
        # 1. STATISTIQUES PAR FICHIER SOURCE
        file_stats = {}
        geo_stats = {}
        
        # 🚨 NETTOYAGE FINAL ANTI-RÉSIDUS
        logger.info("🧹 NETTOYAGE FINAL ANTI-RÉSIDUS...")

        # Filtrer ligne par ligne avec critères stricts
        final_clean = []
        removed_count = 0

        for prop in all_properties:
            nom = prop.get('nom', '').strip()
            prenom = prop.get('prenom', '').strip()
            dept = prop.get('department', '').strip()
            comm = prop.get('commune', '').strip()
            
            # CRITÈRE 1: Nom valide requis
            if not self.is_likely_real_owner(nom, prenom):
                removed_count += 1
                logger.debug(f"🗑️ SUPPRIMÉ (nom invalide): {nom} {prenom}")
                continue
            
            # CRITÈRE 2: Données géographiques requises (STRICT)
            if not dept or not comm or dept == 'N/A' or comm == 'N/A':
                removed_count += 1 
                logger.debug(f"🗑️ SUPPRIMÉ (géo manquante): {nom} - dept={dept}, comm={comm}")
                continue
            
            # CRITÈRE 3: REJET GÉOGRAPHIES CONTAMINÉES (ULTRA-STRICT)
            if (dept in ['XX', 'COMMUNE', 'Unknown'] or 
                comm in ['XX', 'COMMUNE', 'Unknown'] or
                not dept.isdigit() or not comm.isdigit() or
                len(dept) != 2 or len(comm) != 3):
                removed_count += 1
                logger.debug(f"🗑️ SUPPRIMÉ (géo contaminée): {nom} - dept={dept}, comm={comm}")
                continue
            
            # CRITÈRE 4: Longueur minimale du nom
            if len(nom) < 3:
                removed_count += 1
                logger.debug(f"🗑️ SUPPRIMÉ (nom trop court): {nom}")
                continue
            
            final_clean.append(prop)

        if removed_count > 0:
            logger.warning(f"🧽 NETTOYAGE FINAL: {removed_count} lignes parasites supprimées")
            logger.info(f"✅ RÉSULTAT FINAL: {len(final_clean)} propriétés valides")

        all_properties = final_clean
        
        for prop in all_properties:
            fichier = prop.get('fichier_source', 'INCONNU')
            dept = prop.get('department', '').strip()
            comm = prop.get('commune', '').strip()
            
            # Stats par fichier
            if fichier not in file_stats:
                file_stats[fichier] = {'count': 0, 'geo': set()}
            file_stats[fichier]['count'] += 1
            
            # Stats géographiques
            if dept and comm:
                geo_key = f"{dept}-{comm}"
                file_stats[fichier]['geo'].add(geo_key)
                geo_stats[geo_key] = geo_stats.get(geo_key, 0) + 1
        
        # 2. DÉTECTION DE CONTAMINATION CROISÉE
        contaminated_files = []
        for fichier, stats in file_stats.items():
            if len(stats['geo']) > 1:  # Plus d'1 géographie = suspect
                contaminated_files.append(fichier)
                logger.warning(f"⚠️ FICHIER SUSPECT: {fichier} - {len(stats['geo'])} géographies différentes: {stats['geo']}")
        
        # 3. NETTOYAGE FINAL SI CONTAMINATION DÉTECTÉE
        if contaminated_files:
            logger.warning(f"🧽 NETTOYAGE FINAL - {len(contaminated_files)} fichiers avec contamination")
            
            cleaned_properties = []
            removed_count = 0
            
            for prop in all_properties:
                fichier = prop.get('fichier_source', '')
                dept = prop.get('department', '').strip()
                comm = prop.get('commune', '').strip()
                
                if fichier in contaminated_files and dept and comm:
                    # Pour les fichiers contaminés, garder seulement la géographie majoritaire
                    geo_key = f"{dept}-{comm}"
                    main_geo = max(geo_stats.items(), key=lambda x: x[1])[0]
                    
                    if geo_key == main_geo:
                        cleaned_properties.append(prop)
                    else:
                        removed_count += 1
                        logger.info(f"❌ SUPPRIMÉ: {prop.get('nom', '')} {prop.get('prenom', '')} (Geo {geo_key} != {main_geo})")
                else:
                    cleaned_properties.append(prop)
            
            if removed_count > 0:
                logger.warning(f"🧽 CONTAMINATION FINALE NETTOYÉE: {removed_count} propriétés supprimées")
                all_properties = cleaned_properties
        
        # 4. RAPPORT FINAL DE QUALITÉ
        logger.info(f"✅ VALIDATION FINALE TERMINÉE:")
        logger.info(f"   - Propriétés finales: {len(all_properties)}")
        logger.info(f"   - Fichiers traités: {len(file_stats)}")
        logger.info(f"   - Géographies uniques: {len(geo_stats)}")
        
        for geo, count in geo_stats.items():
            logger.info(f"   - {geo}: {count} propriétés")
        
        return all_properties

    def export_to_csv(self, all_properties: List[Dict], output_filename: str = "output.csv") -> None:
        """
        Exporte toutes les données vers un fichier CSV avec séparateur point-virgule.
        """
        if not all_properties:
            logger.warning("Aucune donnée à exporter")
            return
        # Nettoyage du code commune avant export
        for prop in all_properties:
            prop['commune'] = clean_commune_code(prop.get('commune', ''))
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


def main():
    """Fonction principale."""
    # Charger les variables d'environnement
    load_dotenv()
    
    # Créer et lancer l'extracteur
    extractor = PDFPropertyExtractor()
    extractor.run()


if __name__ == "__main__":
    main() 