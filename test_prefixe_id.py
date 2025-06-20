#!/usr/bin/env python3
"""
Test pour vérifier la nouvelle génération d'ID avec préfixe intégré
"""

from pdf_extractor import PDFPropertyExtractor

def test_generation_id_avec_prefixe():
    print("🧪 TEST GÉNÉRATION ID AVEC PRÉFIXE")
    print("=" * 60)
    
    extractor = PDFPropertyExtractor()
    
    # Cas de test selon les spécifications
    test_cases = [
        # Format: (department, commune, section, numero, prefixe, id_attendu, description)
        ("21", "026", "A", "123", "302", "210263020A0123", "Exemple donné par l'utilisateur"),
        ("21", "026", "ZD", "5", "", "21026000ZD0005", "Sans préfixe, section 2 caractères"),
        ("25", "227", "ZD", "5", "", "25227000ZD0005", "Exemple de référence donné"),
        ("01", "001", "C", "74", "", "010010000C0074", "Sans préfixe, section 1 caractère"),
        ("12", "345", "B", "77", "302", "123453020B0077", "Avec préfixe, section 1 caractère"),
        ("12", "345", "ZA", "52", "480", "12345480ZA0052", "Avec préfixe, section 2 caractères"),
        ("12", "345", "ZC", "111", "480", "12345480ZC0111", "Avec préfixe, section 2 caractères"),
        ("01", "002", "A", "50", "12", "010021200A0050", "Préfixe 2 caractères"),
        ("01", "003", "B", "60", "1", "010031000B0060", "Préfixe 1 caractère"),
    ]
    
    print("📋 TESTS DE GÉNÉRATION D'ID:")
    print()
    
    for i, (dept, comm, sect, num, pref, expected, desc) in enumerate(test_cases, 1):
        print(f"Test {i}: {desc}")
        print(f"   Entrée: dept={dept}, comm={comm}, section={sect}, numero={num}, prefixe='{pref}'")
        
        # Générer l'ID
        generated_id = extractor.generate_unique_id(dept, comm, sect, num, pref)
        
        print(f"   Généré:  {generated_id}")
        print(f"   Attendu: {expected}")
        
        # Vérification
        if generated_id == expected:
            print(f"   ✅ SUCCÈS")
        else:
            print(f"   ❌ ÉCHEC")
            
        # Vérification longueur
        if len(generated_id) == 14:
            print(f"   ✅ Longueur: 14 caractères")
        else:
            print(f"   ❌ Longueur: {len(generated_id)} caractères (devrait être 14)")
        
        print()
    
    print("🔍 ANALYSE DES COMPOSANTS:")
    print()
    
    # Test détaillé d'un cas complexe
    dept, comm, sect, num, pref = "21", "026", "A", "123", "302"
    generated_id = extractor.generate_unique_id(dept, comm, sect, num, pref)
    
    print(f"Exemple détaillé: dept={dept}, comm={comm}, section={sect}, numero={num}, prefixe={pref}")
    print(f"ID généré: {generated_id}")
    print(f"Décomposition:")
    print(f"   Département: '{generated_id[0:2]}'  (positions 0-1)")
    print(f"   Commune:     '{generated_id[2:5]}'  (positions 2-4)")
    print(f"   Section:     '{generated_id[5:10]}' (positions 5-9, avec préfixe)")
    print(f"   Numéro:      '{generated_id[10:14]}' (positions 10-13)")
    print()
    
    # Test cas limites
    print("🚨 TESTS CAS LIMITES:")
    print()
    
    edge_cases = [
        ("", "", "", "", "", "Description: Tout vide"),
        ("1", "1", "A", "1", "", "Description: Valeurs minimales"),
        ("999", "999", "ABCDEF", "9999", "9999", "Description: Valeurs trop longues"),
    ]
    
    for dept, comm, sect, num, pref, desc in edge_cases:
        print(f"{desc}")
        print(f"   Entrée: dept='{dept}', comm='{comm}', section='{sect}', numero='{num}', prefixe='{pref}'")
        try:
            generated_id = extractor.generate_unique_id(dept, comm, sect, num, pref)
            print(f"   Résultat: {generated_id} (longueur: {len(generated_id)})")
            if len(generated_id) == 14:
                print(f"   ✅ Longueur correcte")
            else:
                print(f"   ❌ Longueur incorrecte")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        print()

def test_avec_pdf_reel():
    print("=" * 60)
    print("🧪 TEST AVEC PDF RÉEL")
    print("=" * 60)
    
    from pathlib import Path
    pdfs = list(Path("input").glob("*.pdf")) if Path("input").exists() else []
    
    if not pdfs:
        print("❌ Pas de PDF dans input/ pour test réel")
        return
    
    pdf_path = pdfs[0]
    print(f"📄 Test avec: {pdf_path.name}")
    
    extractor = PDFPropertyExtractor()
    
    # Traitement complet avec nouvelle génération d'ID
    results = extractor.process_like_make(pdf_path)
    
    if not results:
        print("❌ Aucun résultat extrait")
        return
    
    print(f"✅ {len(results)} propriétés extraites")
    
    print(f"\n📊 ANALYSE DES IDs GÉNÉRÉS:")
    for i, result in enumerate(results[:5], 1):  # Afficher les 5 premiers
        id_val = result.get('id', '')
        prefixe = result.get('prefixe', '')
        section = result.get('section', '')
        
        print(f"   {i}. ID: {id_val}")
        print(f"      Préfixe: '{prefixe}'")
        print(f"      Section: '{section}'")
        
        if len(id_val) == 14:
            # Décomposer l'ID
            dept = id_val[0:2]
            comm = id_val[2:5]
            sect_avec_pref = id_val[5:10]
            num = id_val[10:14]
            
            print(f"      Décomposition: {dept}|{comm}|{sect_avec_pref}|{num}")
            
            if prefixe and prefixe in sect_avec_pref:
                print(f"      ✅ Préfixe '{prefixe}' intégré dans section")
            elif not prefixe:
                print(f"      ✅ Pas de préfixe (normal)")
            else:
                print(f"      ⚠️ Préfixe '{prefixe}' non trouvé dans section '{sect_avec_pref}'")
        else:
            print(f"      ❌ Longueur incorrecte: {len(id_val)} caractères")
        print()

if __name__ == "__main__":
    test_generation_id_avec_prefixe()
    test_avec_pdf_reel() 