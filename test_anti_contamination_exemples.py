#!/usr/bin/env python3
"""
Test de validation : vérification que tous les exemples concrets ont été éliminés
"""

import os
import logging
from pathlib import Path
from pdf_extractor import PDFPropertyExtractor

def test_no_concrete_examples_in_code():
    """
    Vérifie que le code ne contient plus d'exemples concrets qui peuvent contaminer
    """
    print("🧪 TEST ANTI-CONTAMINATION : Vérification des exemples")
    print("=" * 60)
    
    # Lire le fichier principal
    with open("pdf_extractor.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Noms concrets qui ne doivent plus apparaître dans les prompts
    forbidden_names = [
        "DARTOIS", "MICHELINE", "FRÉDÉRIC", "CHRISTOPHE",
        "MARTIN", "PIERRE", "MARIE", "JEAN", "DIDIER",
        "BERNARD", "LAMBERT", "DUPONT", "DUMONT"
    ]
    
    found_issues = []
    
    for name in forbidden_names:
        # Chercher dans les prompts (lignes contenant des guillemets)
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if name in line and ('"' in line or "'" in line or "prompt" in line.lower()):
                # Vérifier si c'est dans un commentaire de correction (OK)
                if "❌ AVANT" in line or "✅ APRÈS" in line or "[NOM" in line or "[PRENOM" in line:
                    continue  # C'est un commentaire explicatif, OK
                    
                found_issues.append({
                    'line': i,
                    'name': name,
                    'content': line.strip()
                })
    
    # Vérifier que les placeholders sont présents
    required_placeholders = [
        "[NOM1]", "[NOM2]", "[PRENOM1]", "[PRENOM2]", 
        "[NOM_PROPRIETAIRE]", "[PRENOM_MULTIPLE]", "[PRENOM_SIMPLE]"
    ]
    
    missing_placeholders = []
    for placeholder in required_placeholders:
        if placeholder not in content:
            missing_placeholders.append(placeholder)
    
    # Rapport
    print(f"🔍 Noms concrets recherchés : {len(forbidden_names)}")
    print(f"❌ Problèmes trouvés : {len(found_issues)}")
    print(f"🏷️ Placeholders manquants : {len(missing_placeholders)}")
    
    if found_issues:
        print("\n🚨 EXEMPLES CONCRETS ENCORE PRÉSENTS :")
        for issue in found_issues:
            print(f"  Ligne {issue['line']}: '{issue['name']}' dans: {issue['content'][:100]}...")
    
    if missing_placeholders:
        print(f"\n⚠️ PLACEHOLDERS MANQUANTS : {missing_placeholders}")
    
    if not found_issues and not missing_placeholders:
        print("✅ PARFAIT ! Tous les exemples concrets ont été remplacés par des placeholders")
        return True
    else:
        print("❌ CORRECTION INCOMPLÈTE - Voir les problèmes ci-dessus")
        return False

def test_single_pdf_no_contamination():
    """
    Test un seul PDF pour vérifier qu'aucun nom fantôme n'apparaît
    """
    print("\n🧪 TEST PDF UNIQUE : Vérification absence de contamination")
    print("=" * 60)
    
    # Créer l'extracteur
    extractor = PDFPropertyExtractor("input", "output")
    
    # Lister les PDFs
    pdf_files = extractor.list_pdf_files()
    
    if not pdf_files:
        print("❌ Aucun PDF trouvé dans input/")
        return False
    
    # Traiter le premier PDF
    pdf_file = pdf_files[0]
    print(f"📄 Test avec : {pdf_file.name}")
    
    try:
        properties = extractor.process_like_make(pdf_file)
        
        if not properties:
            print("⚠️ Aucune propriété extraite")
            return True  # Pas de contamination si rien extrait
        
        # Vérifier absence de noms fantômes
        contaminated_names = []
        forbidden_names = [
            "DARTOIS", "MICHELINE", "FRÉDÉRIC", "CHRISTOPHE",
            "MARTIN", "PIERRE", "MARIE", "DIDIER", "BERNARD"
        ]
        
        for prop in properties:
            nom = str(prop.get('nom', '')).upper()
            prenom = str(prop.get('prenom', '')).upper()
            
            for forbidden in forbidden_names:
                if forbidden in nom or forbidden in prenom:
                    contaminated_names.append({
                        'nom': nom,
                        'prenom': prenom,
                        'forbidden': forbidden
                    })
        
        # Rapport
        print(f"📊 Propriétés extraites : {len(properties)}")
        print(f"🚨 Contaminations détectées : {len(contaminated_names)}")
        
        if contaminated_names:
            print("\n❌ NOMS FANTÔMES DÉTECTÉS :")
            for contamination in contaminated_names:
                print(f"  - {contamination['nom']} {contamination['prenom']} (contient '{contamination['forbidden']}')")
            return False
        else:
            print("✅ AUCUNE CONTAMINATION ! Tous les noms semblent légitimes")
            return True
            
    except Exception as e:
        print(f"❌ Erreur lors du test : {e}")
        return False

def main():
    """Test principal"""
    print("🚀 VALIDATION CORRECTION ANTI-CONTAMINATION")
    print("=" * 80)
    
    # Test 1: Code source
    code_ok = test_no_concrete_examples_in_code()
    
    # Test 2: PDF unique  
    pdf_ok = test_single_pdf_no_contamination()
    
    # Résultat final
    print("\n" + "=" * 80)
    if code_ok and pdf_ok:
        print("🎉 CORRECTION RÉUSSIE ! Anti-contamination opérationnelle")
        print("✅ Code source : Placeholders génériques installés")
        print("✅ Test PDF : Aucune contamination détectée")
    else:
        print("🚨 CORRECTION INCOMPLÈTE - Actions requises :")
        if not code_ok:
            print("❌ Code source : Encore des exemples concrets")
        if not pdf_ok:
            print("❌ Test PDF : Contamination détectée")

if __name__ == "__main__":
    main()