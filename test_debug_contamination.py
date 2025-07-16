#!/usr/bin/env python3
"""
🔍 SCRIPT DEBUG CONTAMINATION - Traçage étape par étape
OBJECTIF: Identifier précisément où et quand les données Paris (75) contaminent l'extraction
"""

import os
import sys
from pathlib import Path
import json
import logging

# Ajouter le répertoire du projet au path
sys.path.append(str(Path(__file__).parent))

from pdf_extractor import PDFPropertyExtractor

def setup_logging():
    """Configuration logging détaillé pour debug"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('debug_contamination.log')
        ]
    )

def debug_single_pdf_step_by_step(pdf_path: str):
    """
    🔍 TRAÇAGE COMPLET étape par étape d'UN SEUL PDF
    
    Objective: Identifier EXACTEMENT où apparaissent les données Paris (75)
    """
    print("="*80)
    print(f"🔍 DEBUG CONTAMINATION POUR: {pdf_path}")
    print("="*80)
    
    # Initialiser l'extracteur
    extractor = PDFPropertyExtractor("input", "output")
    pdf_path_obj = Path(pdf_path)
    
    # 🧹 ÉTAPE 1: NETTOYAGE CONTEXTE
    print("\n🧹 ÉTAPE 1: NETTOYAGE ANTI-CONTAMINATION")
    print("-" * 50)
    extractor.clean_extraction_context(pdf_path_obj)
    print("✅ Nettoyage terminé")
    
    # 📊 ÉTAPE 2: EXTRACTION TABLEAUX PDFPLUMBER
    print("\n📊 ÉTAPE 2: EXTRACTION TABLEAUX AVEC PDFPLUMBER")
    print("-" * 50)
    try:
        structured_data = extractor.extract_structured_data_with_pdfplumber(pdf_path_obj)
        
        print(f"📋 Propriétés bâties trouvées: {len(structured_data.get('prop_batie', []))}")
        print(f"📋 Propriétés non-bâties trouvées: {len(structured_data.get('non_batie', []))}")
        
        # Vérifier si Paris apparaît déjà dans les données pdfplumber
        all_pdfplumber_data = structured_data.get('prop_batie', []) + structured_data.get('non_batie', [])
        paris_in_pdfplumber = [item for item in all_pdfplumber_data if 'paris' in str(item).lower() or '75' in str(item)]
        
        if paris_in_pdfplumber:
            print("🚨 ALERTE: PARIS DÉTECTÉ DANS PDFPLUMBER!")
            for item in paris_in_pdfplumber:
                print(f"   - {item}")
        else:
            print("✅ Aucune trace de Paris dans pdfplumber")
            
    except Exception as e:
        print(f"❌ Erreur extraction pdfplumber: {e}")
        structured_data = {}
    
    # 🤖 ÉTAPE 3: EXTRACTION PROPRIÉTAIRES OPENAI
    print("\n🤖 ÉTAPE 3: EXTRACTION PROPRIÉTAIRES AVEC OPENAI")
    print("-" * 50)
    try:
        owners = extractor.extract_owners_make_style(pdf_path_obj)
        print(f"👤 Propriétaires extraits: {len(owners)}")
        
        # Analyser les départements trouvés
        departments = [owner.get('department', '') for owner in owners if owner.get('department')]
        unique_depts = set(departments)
        print(f"🏛️ Départements détectés: {unique_depts}")
        
        # Vérifier contamination Paris
        paris_owners = [owner for owner in owners if owner.get('department') == '75']
        if paris_owners:
            print(f"🚨 CONTAMINATION PARIS DÉTECTÉE: {len(paris_owners)} propriétaires")
            for i, owner in enumerate(paris_owners[:3]):  # Afficher les 3 premiers
                print(f"   {i+1}. {owner.get('nom', '')} {owner.get('prenom', '')} - {owner.get('department', '')}")
        else:
            print("✅ Aucune contamination Paris dans l'extraction OpenAI")
            
        # Sauvegarder extraction brute pour analyse
        with open('debug_owners_raw.json', 'w', encoding='utf-8') as f:
            json.dump(owners, f, indent=2, ensure_ascii=False)
        print("💾 Extraction sauvée dans: debug_owners_raw.json")
        
    except Exception as e:
        print(f"❌ Erreur extraction OpenAI: {e}")
        owners = []
    
    # 🧹 ÉTAPE 4: FILTRAGE NOMS PROPRIÉTAIRES
    print("\n🧹 ÉTAPE 4: FILTRAGE NOMS PROPRIÉTAIRES")
    print("-" * 50)
    try:
        filtered_owners = [owner for owner in owners if extractor.is_likely_real_owner(
            owner.get('nom', ''), owner.get('prenom', ''))]
        
        removed_count = len(owners) - len(filtered_owners)
        print(f"🗑️ Propriétaires filtrés: {removed_count}")
        print(f"✅ Propriétaires conservés: {len(filtered_owners)}")
        
        # Vérifier si Paris survit au filtrage
        paris_after_filter = [owner for owner in filtered_owners if owner.get('department') == '75']
        if paris_after_filter:
            print(f"🚨 PARIS SURVIT AU FILTRAGE: {len(paris_after_filter)} propriétaires")
        else:
            print("✅ Filtrage élimine Paris")
            
    except Exception as e:
        print(f"❌ Erreur filtrage: {e}")
        filtered_owners = owners
    
    # 🌍 ÉTAPE 5: FILTRAGE GÉOGRAPHIQUE
    print("\n🌍 ÉTAPE 5: FILTRAGE GÉOGRAPHIQUE")
    print("-" * 50)
    try:
        geo_filtered = extractor.filter_by_geographic_reference(filtered_owners)
        
        geo_removed = len(filtered_owners) - len(geo_filtered)
        print(f"🗑️ Lignes supprimées par filtrage géo: {geo_removed}")
        print(f"✅ Lignes conservées: {len(geo_filtered)}")
        
        # Analyser départements finaux
        final_depts = set(owner.get('department', '') for owner in geo_filtered if owner.get('department'))
        print(f"🏛️ Départements finaux: {final_depts}")
        
        # Vérifier si Paris persiste
        final_paris = [owner for owner in geo_filtered if owner.get('department') == '75']
        if final_paris:
            print(f"🚨 CONTAMINATION FINALE: {len(final_paris)} propriétaires Paris persistent!")
            print("🔍 DÉTAILS CONTAMINATION:")
            for owner in final_paris[:2]:
                print(f"   - {owner}")
        else:
            print("✅ Aucune contamination Paris finale")
        
        # Sauvegarder résultat final
        with open('debug_owners_final.json', 'w', encoding='utf-8') as f:
            json.dump(geo_filtered, f, indent=2, ensure_ascii=False)
        print("💾 Résultat final sauvé dans: debug_owners_final.json")
        
    except Exception as e:
        print(f"❌ Erreur filtrage géographique: {e}")
        geo_filtered = filtered_owners
    
    # 📈 RÉSUMÉ FINAL
    print("\n📈 RÉSUMÉ CONTAMINATION")
    print("-" * 50)
    print(f"📊 Propriétaires extraits: {len(owners)}")
    print(f"🧹 Après filtrage noms: {len(filtered_owners) if 'filtered_owners' in locals() else 'N/A'}")
    print(f"🌍 Après filtrage géo: {len(geo_filtered) if 'geo_filtered' in locals() else 'N/A'}")
    
    paris_stages = {
        "Extraction": len([o for o in owners if o.get('department') == '75']) if owners else 0,
        "Filtrage noms": len([o for o in filtered_owners if o.get('department') == '75']) if 'filtered_owners' in locals() else 0,
        "Filtrage géo": len([o for o in geo_filtered if o.get('department') == '75']) if 'geo_filtered' in locals() else 0
    }
    
    print(f"\n🚨 ÉVOLUTION CONTAMINATION PARIS:")
    for stage, count in paris_stages.items():
        if count > 0:
            print(f"   {stage}: {count} propriétaires Paris ❌")
        else:
            print(f"   {stage}: {count} propriétaires Paris ✅")
    
    return geo_filtered if 'geo_filtered' in locals() else []

def main():
    """Point d'entrée principal du script de debug"""
    setup_logging()
    
    if len(sys.argv) != 2:
        print("Usage: python test_debug_contamination.py <path_to_pdf>")
        print("Exemple: python test_debug_contamination.py input/ZY_28.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not Path(pdf_path).exists():
        print(f"❌ Fichier non trouvé: {pdf_path}")
        sys.exit(1)
    
    print(f"🚀 Lancement debug contamination pour: {pdf_path}")
    
    result = debug_single_pdf_step_by_step(pdf_path)
    
    print("\n✅ DEBUG TERMINÉ")
    print("📄 Logs détaillés disponibles dans: debug_contamination.log")
    print("📄 Données brutes dans: debug_owners_raw.json")
    print("📄 Données finales dans: debug_owners_final.json")

if __name__ == "__main__":
    main() 