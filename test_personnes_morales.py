#!/usr/bin/env python3
"""
Test pour vérifier la gestion des personnes morales
(communes, entreprises, etc.)
"""

from pdf_extractor import PDFPropertyExtractor

def test_detection_personnes_morales():
    print("🧪 TEST DÉTECTION PERSONNES MORALES")
    print("=" * 50)
    
    # Simuler des données d'extraction avec différents cas
    test_owners = [
        # Cas 1: Personne physique normale
        {
            'nom': 'MARTIN',
            'prenom': 'JEAN PIERRE',
            'street_address': '15 RUE DE LA PAIX',
            'city': 'PARIS',
            'post_code': '75001'
        },
        
        # Cas 2: Commune bien extraite
        {
            'nom': 'COMMUNE DE BAR-LE-DUC',
            'prenom': '',
            'street_address': 'MAIRIE',
            'city': 'BAR-LE-DUC',
            'post_code': '55000'
        },
        
        # Cas 3: SCI mal extraite (nom dans prénom)
        {
            'nom': 'IMMOBILIER',
            'prenom': 'SCI DU CENTRE',
            'street_address': '10 AVENUE VICTOR HUGO',
            'city': 'LYON',
            'post_code': '69000'
        },
        
        # Cas 4: Société mal extraite (répartie sur nom+prénom)
        {
            'nom': 'SOCIÉTÉ',
            'prenom': 'ABC SARL',
            'street_address': '25 RUE GAMBETTA',
            'city': 'MARSEILLE',
            'post_code': '13000'
        },
        
        # Cas 5: Association
        {
            'nom': 'ASSOCIATION SPORTIVE DE NANCY',
            'prenom': 'MICHEL',  # Erreur d'extraction
            'street_address': '5 PLACE STANISLAS',
            'city': 'NANCY',
            'post_code': '54000'
        }
    ]
    
    print("📋 DONNÉES DE TEST AVANT CORRECTION:")
    for i, owner in enumerate(test_owners, 1):
        print(f"   {i}. Nom: '{owner['nom']}' | Prénom: '{owner['prenom']}'")
    
    # Tester la détection
    extractor = PDFPropertyExtractor()
    corrected_owners = extractor.detect_and_fix_legal_entities(test_owners)
    
    print(f"\n✅ DONNÉES APRÈS CORRECTION:")
    for i, owner in enumerate(corrected_owners, 1):
        nom = owner['nom']
        prenom = owner['prenom']
        is_legal = prenom == ''
        type_str = "🏢 PERSONNE MORALE" if is_legal else "👤 PERSONNE PHYSIQUE"
        print(f"   {i}. {type_str}")
        print(f"      Nom: '{nom}'")
        print(f"      Prénom: '{prenom}'")
        print()
    
    # Vérifications
    print("🔍 VÉRIFICATIONS:")
    
    # Cas 1: Doit rester personne physique
    assert corrected_owners[0]['prenom'] != '', "❌ Cas 1: Personne physique transformée à tort"
    print("   ✅ Cas 1: Personne physique préservée")
    
    # Cas 2: Doit rester personne morale
    assert corrected_owners[1]['prenom'] == '', "❌ Cas 2: Personne morale mal gérée"
    print("   ✅ Cas 2: Personne morale préservée")
    
    # Cas 3: Doit être corrigée en personne morale
    assert corrected_owners[2]['prenom'] == '', "❌ Cas 3: SCI non détectée"
    assert 'SCI' in corrected_owners[2]['nom'], "❌ Cas 3: Nom SCI non reconstruit"
    print("   ✅ Cas 3: SCI corrigée")
    
    # Cas 4: Doit être corrigée en personne morale
    assert corrected_owners[3]['prenom'] == '', "❌ Cas 4: SARL non détectée"
    assert 'SARL' in corrected_owners[3]['nom'], "❌ Cas 4: Nom SARL non reconstruit"
    print("   ✅ Cas 4: SARL corrigée")
    
    # Cas 5: Doit être corrigée en personne morale
    assert corrected_owners[4]['prenom'] == '', "❌ Cas 5: Association non détectée"
    print("   ✅ Cas 5: Association corrigée")
    
    print(f"\n🎉 TOUS LES TESTS PASSÉS!")
    print(f"📊 Résumé: {len([o for o in corrected_owners if o['prenom'] == ''])} personnes morales détectées")

def test_avec_pdf_reel():
    print(f"\n" + "=" * 50)
    print("🧪 TEST AVEC PDF RÉEL")
    print("=" * 50)
    
    # Chercher un PDF dans input/
    from pathlib import Path
    pdfs = list(Path("input").glob("*.pdf")) if Path("input").exists() else []
    
    if not pdfs:
        print("❌ Pas de PDF dans input/ pour test réel")
        return
    
    pdf_path = pdfs[0]
    print(f"📄 Test avec: {pdf_path.name}")
    
    extractor = PDFPropertyExtractor()
    
    # Test complet avec détection des personnes morales
    results = extractor.process_like_make(pdf_path)
    
    if not results:
        print("❌ Aucun résultat extrait")
        return
    
    print(f"✅ {len(results)} propriétés extraites")
    
    # Analyser les types de propriétaires
    personnes_physiques = 0
    personnes_morales = 0
    
    print(f"\n📊 ANALYSE DES PROPRIÉTAIRES:")
    for i, result in enumerate(results, 1):
        nom = result.get('nom', '')
        prenom = result.get('prenom', '')
        
        if prenom:
            personnes_physiques += 1
            type_str = "👤 PHYSIQUE"
        else:
            personnes_morales += 1
            type_str = "🏢 MORALE"
        
        print(f"   {i}. {type_str}: {nom} {prenom}".strip())
    
    print(f"\n📈 STATISTIQUES:")
    print(f"   👤 Personnes physiques: {personnes_physiques}")
    print(f"   🏢 Personnes morales: {personnes_morales}")
    print(f"   📊 Total: {len(results)}")

if __name__ == "__main__":
    test_detection_personnes_morales()
    test_avec_pdf_reel() 