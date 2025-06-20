#!/usr/bin/env python3
"""
Test pour vérifier que les colonnes de contenance vides 
s'affichent bien comme vides dans le CSV final
"""

import pandas as pd
from pathlib import Path
from pdf_extractor import PDFPropertyExtractor

def test_contenance_vide():
    print("🧪 TEST CONTENANCE VIDE")
    print("=" * 40)
    
    # Simuler des données avec colonnes vides et non vides
    test_data = [
        {
            'department': '01',
            'commune': '001', 
            'prefixe': '302',
            'section': 'A',
            'numero': '123',
            'contenance_ha': '05',      # Non vide
            'contenance_a': '',         # Vide
            'contenance_ca': '123',     # Non vide
            'nom': 'DUPONT',
            'id': 'test123'
        },
        {
            'department': '01',
            'commune': '001',
            'prefixe': '303', 
            'section': 'B',
            'numero': '456',
            'contenance_ha': '',        # Vide
            'contenance_a': '',         # Vide  
            'contenance_ca': '',        # Vide
            'nom': 'MARTIN',
            'id': 'test456'
        },
        {
            'department': '01',
            'commune': '001',
            'prefixe': '304',
            'section': 'C', 
            'numero': '789',
            'contenance_ha': '02',      # Non vide
            'contenance_a': '15',       # Non vide
            'contenance_ca': '',        # Vide
            'nom': 'BERNARD',
            'id': 'test789'
        }
    ]
    
    print("📋 Données de test:")
    for i, data in enumerate(test_data, 1):
        print(f"   Propriété {i}:")
        print(f"     HA: '{data['contenance_ha']}'")
        print(f"     A:  '{data['contenance_a']}'") 
        print(f"     CA: '{data['contenance_ca']}'")
    
    # Tester l'export CSV
    extractor = PDFPropertyExtractor()
    
    print(f"\n💾 Export vers CSV...")
    csv_path = extractor.export_to_csv(test_data, "test_contenance_vide.csv")
    
    # Relire le CSV pour vérifier
    print(f"\n🔍 Vérification du CSV généré:")
    df = pd.read_csv(csv_path, sep=';', encoding='utf-8-sig')
    
    print(f"📊 Colonnes dans le CSV: {list(df.columns)}")
    
    # Vérifier les colonnes de contenance
    contenance_cols = ['Contenance HA', 'Contenance A', 'Contenance CA']
    
    for col in contenance_cols:
        if col in df.columns:
            print(f"\n✅ Colonne '{col}':")
            for i, val in enumerate(df[col]):
                if pd.isna(val) or val == '':
                    print(f"   Ligne {i+1}: VIDE ✅")
                else:
                    print(f"   Ligne {i+1}: '{val}'")
        else:
            print(f"❌ Colonne '{col}' manquante!")
    
    # Afficher quelques lignes du CSV brut
    print(f"\n📄 Aperçu du CSV brut:")
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        for i, line in enumerate(f):
            if i < 5:  # Afficher les 5 premières lignes
                print(f"   {line.strip()}")
    
    print(f"\n✅ Test terminé. Fichier CSV: {csv_path}")

if __name__ == "__main__":
    test_contenance_vide() 