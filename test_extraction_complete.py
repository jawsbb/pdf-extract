#!/usr/bin/env python3
"""
Script de test pour valider les améliorations d'extraction de propriétaires.
Test spécifique pour le problème d'extraction incomplète.
"""

import os
import sys
from pathlib import Path
from pdf_extractor import PDFPropertyExtractor

def test_extraction_complete():
    """
    Teste l'extraction complète de propriétaires après les améliorations.
    """
    print("🧪 TEST EXTRACTION COMPLÈTE - Après améliorations")
    print("=" * 60)
    
    # Initialiser l'extracteur
    try:
        extractor = PDFPropertyExtractor()
        print("✅ Extracteur initialisé")
    except Exception as e:
        print(f"❌ Erreur initialisation: {e}")
        return
    
    # Rechercher le fichier problématique mentionné
    pdf_files = extractor.list_pdf_files()
    target_file = None
    
    # Chercher le fichier "RP 11-06-2025 1049e.pdf" ou similaire
    for pdf_file in pdf_files:
        if "1049" in pdf_file.name or "RP" in pdf_file.name:
            target_file = pdf_file
            break
    
    if not target_file and pdf_files:
        # Prendre le premier fichier disponible pour le test
        target_file = pdf_files[0]
        print(f"📄 Fichier cible spécifique non trouvé, test avec: {target_file.name}")
    
    if not target_file:
        print("❌ Aucun fichier PDF trouvé dans le dossier input/")
        return
    
    print(f"🎯 Test avec: {target_file.name}")
    print("-" * 40)
    
    # TEST 1: Extraction des propriétaires style Make amélioré
    print("📋 TEST 1: Extraction propriétaires (prompt amélioré)")
    try:
        owners = extractor.extract_owners_make_style(target_file)
        print(f"✅ Propriétaires extraits: {len(owners)}")
        
        # Analyser les propriétaires extraits
        if owners:
            print("\n👥 PROPRIÉTAIRES DÉTECTÉS:")
            for i, owner in enumerate(owners, 1):
                nom = owner.get('nom', 'N/A')
                prenom = owner.get('prenom', 'N/A')
                droit = owner.get('droit_reel', 'N/A')
                print(f"   {i}. {nom} {prenom} - {droit}")
            
            # Vérifier s'il y a des signaux de multi-propriétaires
            family_names = set()
            droit_types = set()
            for owner in owners:
                if owner.get('nom'):
                    family_names.add(owner.get('nom', '').strip().upper())
                if owner.get('droit_reel'):
                    droit_types.add(owner.get('droit_reel', '').strip().upper())
            
            print(f"\n📊 ANALYSE:")
            print(f"   📛 {len(family_names)} noms de famille différents")
            print(f"   ⚖️ {len(droit_types)} types de droits: {list(droit_types)}")
            
            # Détecter les patterns usufruitier/nu-propriétaire
            critical_patterns = ['USUFRUITIER', 'NU-PROPRIÉTAIRE', 'NU-PROP', 'USUFRUIT']
            has_usufruit = any(pattern in ' '.join(droit_types) for pattern in critical_patterns)
            if has_usufruit:
                print("   🎯 PATTERN USUFRUITIER/NU-PROPRIÉTAIRE détecté")
                if len(owners) == 1:
                    print("   🚨 ALERTE: Un seul propriétaire mais pattern multi-propriétaires !")
                else:
                    print("   ✅ Extraction multi-propriétaires cohérente")
        else:
            print("❌ Aucun propriétaire extrait")
            
    except Exception as e:
        print(f"❌ Erreur extraction propriétaires: {e}")
    
    # TEST 2: Traitement complet style Make
    print("\n📋 TEST 2: Traitement complet style Make")
    try:
        properties = extractor.process_like_make(target_file)
        print(f"✅ Propriétés finales: {len(properties)}")
        
        if properties:
            # Analyser la distribution des propriétaires
            owner_distribution = {}
            for prop in properties:
                owner_key = f"{prop.get('nom', '')} {prop.get('prenom', '')}".strip()
                if owner_key:
                    if owner_key not in owner_distribution:
                        owner_distribution[owner_key] = 0
                    owner_distribution[owner_key] += 1
            
            print(f"\n👥 DISTRIBUTION DES PROPRIÉTAIRES:")
            for owner, count in owner_distribution.items():
                print(f"   {owner}: {count} propriété(s)")
            
            print(f"\n📊 RÉSUMÉ:")
            print(f"   👥 {len(owner_distribution)} propriétaires uniques")
            print(f"   🏠 {len(properties)} propriétés totales")
            print(f"   📈 Moyenne: {len(properties)/len(owner_distribution):.1f} propriétés/propriétaire")
            
    except Exception as e:
        print(f"❌ Erreur traitement complet: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 RECOMMANDATIONS:")
    print("1. Vérifiez les logs pour les alertes de validation")
    print("2. Si un seul propriétaire mais pattern usufruitier → vérifiez le PDF manuellement")
    print("3. Les améliorations devraient maintenant extraire TOUS les propriétaires")
    print("4. Le prompt amélioré insiste sur le scan exhaustif du document")

def main():
    """Point d'entrée principal."""
    test_extraction_complete()

if __name__ == "__main__":
    main() 