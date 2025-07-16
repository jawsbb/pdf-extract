#!/usr/bin/env python3
"""
Test des corrections complètes anti-hallucinations et logging détaillé.
"""

import logging
import os
from pathlib import Path
from pdf_extractor import PDFPropertyExtractor

# Configuration du logging pour les tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_corrections.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def test_anti_hallucination_system():
    """Test du système anti-hallucinations."""
    logger.info("🧪 TEST: Système anti-hallucinations")
    
    extractor = PDFPropertyExtractor()
    
    # Test 1: Validation document mono-propriétaire
    text_mono = "TITULAIRE(S) DE DROIT(S) MARTIN Jean Propriétaire"
    owners_mono = [
        {"nom": "MARTIN", "prenom": "Jean", "droit_reel": "Propriétaire"},
        {"nom": "DUBOIS", "prenom": "Marie", "droit_reel": "Propriétaire"}  # Hallucination
    ]
    
    result = extractor.is_single_owner_document(text_mono, owners_mono)
    logger.info(f"   ✅ Mono-propriétaire: {result} (doit être False)")
    
    # Test 2: Validation document multi-propriétaires
    text_multi = "TITULAIRE(S) DE DROIT(S) MARTIN Jean TITULAIRE(S) DE DROIT(S) DUBOIS Marie"
    owners_multi = [
        {"nom": "MARTIN", "prenom": "Jean", "droit_reel": "Propriétaire"},
        {"nom": "DUBOIS", "prenom": "Marie", "droit_reel": "Propriétaire"}
    ]
    
    result = extractor.is_single_owner_document(text_multi, owners_multi)
    logger.info(f"   ✅ Multi-propriétaires: {result} (doit être True)")

def test_contamination_detection():
    """Test de détection des contaminations."""
    logger.info("🧪 TEST: Détection contaminations")
    
    extractor = PDFPropertyExtractor()
    
    # Propriétaires précédents
    previous_owners = [
        {"nom": "MARTIN", "prenom": "Jean", "numero_majic": "123456"},
        {"nom": "DUBOIS", "prenom": "Marie", "numero_majic": "789012"}
    ]
    
    # Propriétaires actuels avec contamination
    current_owners = [
        {"nom": "MARTIN", "prenom": "Jean", "numero_majic": "123456"},  # Contamination
        {"nom": "DURAND", "prenom": "Paul", "numero_majic": "345678"}   # Nouveau
    ]
    
    cleaned = extractor.detect_owner_contamination(current_owners, previous_owners)
    logger.info(f"   ✅ Nettoyage: {len(current_owners)} → {len(cleaned)} propriétaires")

def test_logging_detailed():
    """Test du logging détaillé."""
    logger.info("🧪 TEST: Logging détaillé")
    
    extractor = PDFPropertyExtractor()
    
    # Simuler un owner et une propriété
    owner = {
        "nom": "MARTIN",
        "prenom": "Jean",
        "department": "21",
        "commune": "026",
        "street_address": "12 RUE DE LA PAIX",
        "city": "DIJON",
        "post_code": "21000",
        "numero_proprietaire": "ABC123",
        "droit_reel": "Propriétaire"
    }
    
    prop = {
        "Sec": "A",
        "Préfixe": "000",
        "N° Plan": "1234",
        "Adresse": "Lieudit Les Vignes",
        "HA": "02",
        "A": "15",
        "CA": "50"
    }
    
    # Test génération ID avec logging
    unique_id = extractor.generate_id_with_openai_like_make(owner, prop)
    logger.info(f"   ✅ ID généré: {unique_id}")
    
    # Test fusion avec logging
    merged = extractor.merge_like_make(owner, prop, unique_id, "non_batie", "test.pdf")
    logger.info(f"   ✅ Fusion complète avec logging détaillé")

def test_id_structure():
    """Test de la structure des IDs générés."""
    logger.info("🧪 TEST: Structure IDs")
    
    extractor = PDFPropertyExtractor()
    
    # Test cas normal
    test_id = extractor.generate_unique_id("21", "026", "A", "1234", "000")
    logger.info(f"   ✅ ID normal: {test_id} (longueur: {len(test_id)})")
    
    # Test cas préfixe/section collés
    owner = {"department": "21", "commune": "026"}
    prop = {"Sec": "302A", "N° Plan": "1234", "Préfixe": ""}  # Section collée
    
    id_with_separation = extractor.generate_id_with_openai_like_make(owner, prop)
    logger.info(f"   ✅ ID avec séparation: {id_with_separation}")

def test_contenance_decomposition():
    """Test de la décomposition des contenances."""
    logger.info("🧪 TEST: Décomposition contenances")
    
    extractor = PDFPropertyExtractor()
    
    # Test différents formats
    test_cases = [
        "2 ha 15 a 50 ca",
        "0215050",
        "2,15,50",
        "2h15a50c",
        "invalide"
    ]
    
    for test_case in test_cases:
        result = extractor.parse_contenance_value(test_case)
        logger.info(f"   ✅ '{test_case}' → '{result}'")

def main():
    """Exécuter tous les tests."""
    logger.info("🚀 DÉBUT DES TESTS - Corrections complètes")
    
    try:
        test_anti_hallucination_system()
        test_contamination_detection()
        test_logging_detailed()
        test_id_structure()
        test_contenance_decomposition()
        
        logger.info("✅ TOUS LES TESTS TERMINÉS AVEC SUCCÈS")
        
    except Exception as e:
        logger.error(f"❌ ERREUR DANS LES TESTS: {e}")
        raise

if __name__ == "__main__":
    main() 