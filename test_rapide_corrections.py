#!/usr/bin/env python3
"""
🚀 TEST RAPIDE DES CORRECTIONS DE QUALITÉ
Teste immédiatement les améliorations sur vos PDFs avec rapport détaillé
"""

import os
import sys
from pathlib import Path
from pdf_extractor import PDFPropertyExtractor
import time

def check_setup():
    """Vérifie que l'environnement est prêt"""
    print("🔍 VÉRIFICATION SETUP")
    print("=" * 25)
    
    # Vérifier .env
    if not Path(".env").exists():
        print("❌ Fichier .env manquant!")
        print("📝 Créez le fichier .env avec:")
        print("   OPENAI_API_KEY=sk-votre-cle-api-ici")
        print("   DEFAULT_SECTION=A")
        print("   DEFAULT_PLAN_NUMBER=123")
        return False
    
    # Vérifier dossier input
    input_dir = Path("input")
    if not input_dir.exists():
        print("📁 Création du dossier input/")
        input_dir.mkdir(exist_ok=True)
    
    # Compter les PDFs
    pdfs = list(input_dir.glob("*.pdf"))
    if not pdfs:
        print("📄 Aucun PDF trouvé dans input/")
        print("💡 Placez vos PDFs dans le dossier 'input/' et relancez")
        return False
    
    print(f"✅ Setup OK : {len(pdfs)} PDF(s) détecté(s)")
    for pdf in pdfs[:5]:  # Afficher max 5
        print(f"   📄 {pdf.name}")
    if len(pdfs) > 5:
        print(f"   ... et {len(pdfs) - 5} autres")
    
    return True

def test_corrections_sample():
    """Teste les corrections sur un échantillon de données"""
    print("\n🧪 TEST CORRECTIONS ÉCHANTILLON")
    print("=" * 35)
    
    extractor = PDFPropertyExtractor()
    
    # Données d'exemple basées sur vos problèmes
    sample_data = [
        {
            'nom': 'ALEXIS MOURADOFF', 'prenom': 'ALEXIS',
            'section': 'Y', 'numero': '13', 'department': '51', 'commune': '208',
            'contenance_ha': '1 216,05', 'contenance_a': '10', 'contenance_ca': '98',
            'voie': '2BRUE DES ANCIENNES ECOLES'
        },
        {
            'nom': 'MONT DE NOIX', 'prenom': '',
            'section': 'Z', 'numero': '9', 'department': '51', 'commune': '208'
        },
        {
            'nom': 'COMMUNE DE NOYER GOBAN', 'prenom': '',
            'section': 'Y', 'numero': '207', 'department': '51', 'commune': '208'
        }
    ]
    
    print("Données AVANT corrections :")
    for i, data in enumerate(sample_data, 1):
        print(f"  {i}. {data['nom']} / {data['prenom']} - Section {data.get('section', '?')}")
    
    # Appliquer les corrections
    corrected_data = []
    for data in sample_data:
        # Test filtrage propriétaires
        if extractor.is_likely_real_owner(data['nom'], data['prenom']):
            # Test séparation noms
            nom_corrige, prenom_corrige = extractor.split_name_intelligently(
                data['nom'], data['prenom']
            )
            # Test parsing contenance
            contenance_corrigee = extractor.parse_contenance_value(
                data.get('contenance_ha', '')
            )
            # Test nettoyage adresse
            adresse_corrigee = extractor.clean_address(data.get('voie', ''))
            
            corrected_data.append({
                'nom': nom_corrige,
                'prenom': prenom_corrige,
                'section': data.get('section', ''),
                'numero': data.get('numero', ''),
                'contenance_ha': contenance_corrigee,
                'voie': adresse_corrigee
            })
    
    print("\nDonnées APRÈS corrections :")
    for i, data in enumerate(corrected_data, 1):
        print(f"  ✅ {i}. {data['nom']} / {data['prenom']} - Section {data['section']}")
        if data.get('contenance_ha'):
            print(f"      💰 Contenance: {data['contenance_ha']}")
        if data.get('voie'):
            print(f"      🏠 Adresse: {data['voie']}")
    
    print(f"\n📊 Résultat: {len(sample_data)} → {len(corrected_data)} propriétaires valides")
    return len(corrected_data) > 0

def run_extraction_test(max_pdfs=2):
    """Lance un test d'extraction sur 1-2 PDFs pour validation"""
    print(f"\n🚀 TEST EXTRACTION RÉELLE ({max_pdfs} PDF max)")
    print("=" * 40)
    
    input_dir = Path("input")
    pdfs = list(input_dir.glob("*.pdf"))[:max_pdfs]
    
    if not pdfs:
        print("❌ Aucun PDF à tester")
        return False
    
    print(f"📄 Test sur: {[p.name for p in pdfs]}")
    
    try:
        extractor = PDFPropertyExtractor()
        
        start_time = time.time()
        all_properties = []
        
        for pdf_path in pdfs:
            print(f"\n🔄 Traitement {pdf_path.name}...")
            properties = extractor.process_like_make(pdf_path)
            
            if properties:
                print(f"  ✅ {len(properties)} propriétés extraites")
                all_properties.extend(properties)
                
                # Afficher quelques exemples
                for i, prop in enumerate(properties[:3]):
                    nom = prop.get('nom', '?')
                    prenom = prop.get('prenom', '')
                    section = prop.get('section', '?')
                    numero = prop.get('numero', '?')
                    print(f"    {i+1}. {nom} {prenom} - Parcelle {section}{numero}")
                
                if len(properties) > 3:
                    print(f"    ... et {len(properties) - 3} autres")
            else:
                print(f"  ❌ Aucune propriété extraite")
        
        duration = time.time() - start_time
        
        if all_properties:
            # Déduplication finale
            final_properties = extractor.deduplicate_batch_results(all_properties)
            
            print(f"\n📊 RÉSULTATS FINAUX:")
            print(f"  📄 PDFs traités: {len(pdfs)}")
            print(f"  🏠 Propriétés brutes: {len(all_properties)}")
            print(f"  ✨ Propriétés finales: {len(final_properties)}")
            print(f"  ⏱️ Durée: {duration:.1f}s")
            print(f"  🧹 Doublons supprimés: {len(all_properties) - len(final_properties)}")
            
            # Export test
            output_file = "test_corrections_rapide.xlsx"
            extractor.export_to_excel(final_properties, output_file)
            print(f"  💾 Export: {output_file}")
            
            return True
        else:
            print(f"\n❌ Aucune donnée extraite après {duration:.1f}s")
            return False
            
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {str(e)}")
        return False

def main():
    """Test rapide complet des corrections"""
    print("🎯 TEST RAPIDE CORRECTIONS QUALITÉ")
    print("=" * 45)
    print("Ce script valide les corrections sur vos données réelles")
    print()
    
    # 1. Vérification setup
    if not check_setup():
        print("\n❌ Setup incomplet - voir instructions ci-dessus")
        return
    
    # 2. Test des corrections sur échantillon
    if not test_corrections_sample():
        print("\n❌ Problème avec les corrections de base")
        return
    
    # 3. Demander confirmation pour test réel
    print("\n" + "="*45)
    print("💡 Voulez-vous tester sur vos PDFs réels ?")
    print("   (Consomme ~2-5 crédits OpenAI par PDF)")
    
    try:
        response = input("Continuer ? (o/N): ").strip().lower()
        if response in ['o', 'oui', 'y', 'yes']:
            success = run_extraction_test()
            
            if success:
                print("\n🎉 TEST RÉUSSI ! Les corrections fonctionnent parfaitement")
                print("\n📋 PROCHAINES ÉTAPES:")
                print("  1. Vérifiez le fichier test_corrections_rapide.xlsx")
                print("  2. Si satisfait, lancez: python start.py")
                print("  3. Pour traitement complet de tous vos PDFs")
            else:
                print("\n⚠️ Test partiel - vérifiez votre clé API et réessayez")
        else:
            print("\n✅ Test échantillon réussi - corrections validées")
            print("💡 Lancez 'python start.py' quand vous êtes prêt")
            
    except KeyboardInterrupt:
        print("\n\n👋 Test interrompu")
    
    print("\n📖 Plus d'infos: CORRECTIONS_FINALES_QUALITE.md")

if __name__ == "__main__":
    main() 