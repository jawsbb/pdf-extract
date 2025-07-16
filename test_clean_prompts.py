#!/usr/bin/env python3
"""
Script de vérification des corrections anti-contamination des prompts
Vérifie que tous les exemples concrets ont été supprimés des prompts OpenAI
"""

import re
from pathlib import Path

def check_for_contaminating_examples():
    """Vérifier que tous les exemples contaminants ont été supprimés"""
    print("🧹 VÉRIFICATION ANTI-CONTAMINATION DES PROMPTS")
    print("=" * 60)
    
    # Lire le fichier pdf_extractor.py
    pdf_extractor_path = Path("pdf_extractor.py")
    if not pdf_extractor_path.exists():
        print("❌ Fichier pdf_extractor.py non trouvé")
        return False
    
    with open(pdf_extractor_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Noms contaminants connus
    contaminating_names = [
        'DARTOIS', 'MICHELINE', 'FRÉDÉRIC', 'CHRISTOPHE',
        'MARTIN', 'PIERRE', 'MARIE', 'DUMONT', 'BERNARD',
        'LAMBIN', 'DIDIER', 'JEAN', 'DUBOIS', 'LAMBERT',
        'COUPEVILLE', 'AUXERRE', 'DIJON', 'BESANCON',
        'DAMPIERRE-SUR-MOIVRE', 'MAILLY-LE-CHATEAU'
    ]
    
    # Adresses contaminantes
    contaminating_addresses = [
        'RUE D AVAT', 'RUE DE LA PAIX', 'AVENUE DE LA PAIX',
        'M8BNF6', 'MB43HC', 'P7QR92', 'MBRWL8'
    ]
    
    # Codes postaux/villes contaminants
    contaminating_codes = [
        '51240', '89660', '21000', '25000'
    ]
    
    all_contaminants = contaminating_names + contaminating_addresses + contaminating_codes
    
    print("🔍 Recherche des contaminants dans les prompts...")
    found_contaminants = []
    
    # Chercher les contaminants dans le contenu
    for contaminant in all_contaminants:
        # Chercher dans les chaînes de prompt (entre guillemets triple)
        if contaminant in content:
            # Vérifier que ce n'est pas dans un commentaire ou une zone non-prompt
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if contaminant in line and ('"""' in content[:content.find(line)] or 'prompt' in line.lower()):
                    found_contaminants.append((contaminant, i, line.strip()))
    
    if found_contaminants:
        print(f"❌ CONTAMINANTS TROUVÉS: {len(found_contaminants)}")
        for contaminant, line_num, line in found_contaminants[:10]:  # Limite à 10 pour la lisibilité
            print(f"   Ligne {line_num}: {contaminant} dans '{line[:80]}...'")
        return False
    else:
        print("✅ AUCUN CONTAMINANT TROUVÉ - Prompts nettoyés avec succès!")
        return True

def check_placeholder_patterns():
    """Vérifier que les placeholders génériques sont présents"""
    print("\n🔧 VÉRIFICATION DES PLACEHOLDERS GÉNÉRIQUES")
    print("=" * 60)
    
    pdf_extractor_path = Path("pdf_extractor.py")
    with open(pdf_extractor_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Patterns de placeholders attendus
    expected_placeholders = [
        r'\[NOM_PROPRIETAIRE\]', r'\[PRENOM\]', r'\[AUTRE_NOM\]',
        r'\[CODE_MAJIC\]', r'\[ADRESSE\]', r'\[VILLE\]',
        r'\[DEPT\]', r'\[COMMUNE\]', r'\[SECTION\]'
    ]
    
    found_placeholders = []
    
    for pattern in expected_placeholders:
        matches = re.findall(pattern, content)
        if matches:
            found_placeholders.extend(matches)
    
    if found_placeholders:
        print(f"✅ PLACEHOLDERS GÉNÉRIQUES TROUVÉS: {len(set(found_placeholders))}")
        unique_placeholders = set(found_placeholders)
        for placeholder in sorted(unique_placeholders)[:10]:
            print(f"   ✓ {placeholder}")
        return True
    else:
        print("❌ AUCUN PLACEHOLDER GÉNÉRIQUE TROUVÉ")
        return False

def main():
    """Test principal"""
    print("🚀 TEST NETTOYAGE ANTI-CONTAMINATION DES PROMPTS")
    print("=" * 70)
    
    # Test 1: Vérifier l'absence de contaminants
    clean_check = check_for_contaminating_examples()
    
    # Test 2: Vérifier la présence de placeholders
    placeholder_check = check_placeholder_patterns()
    
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 70)
    
    if clean_check and placeholder_check:
        print("✅ TOUS LES TESTS RÉUSSIS")
        print("✅ Prompts nettoyés et placeholders en place")
        print("✅ Risque de contamination éliminé")
        return True
    else:
        print("❌ ÉCHECS DÉTECTÉS")
        if not clean_check:
            print("❌ Des contaminants subsistent dans les prompts")
        if not placeholder_check:
            print("❌ Placeholders génériques manquants")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)