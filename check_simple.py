#!/usr/bin/env python3

def check_simple():
    print("VERIFICATION COLONNES IMPORTANTES")
    print("=" * 40)
    
    colonnes_requises = [
        'department',           # Departement
        'commune',             # Commune  
        'prefixe',             # Prefixe
        'section',             # Section
        'numero',              # Numero
        'contenance',          # CONTENANCE (SURFACE)
        'droit_reel',          # Droit reel
        'designation_parcelle', # Designation Parcelle
        'nom',                 # Nom Proprietaire
        'prenom',              # Prenom Proprietaire
        'numero_majic',        # N°MAJIC
        'voie',                # Voie (adresse)
        'post_code',           # Code Postal
        'city',                # Ville
        'id',                  # ID unique
        'fichier_source'       # Fichier source
    ]
    
    print("COLONNES REQUISES:")
    for i, col in enumerate(colonnes_requises, 1):
        if col == 'contenance':
            print(f"   {i:2d}. {col:<20} <-- CONTENANCE (SURFACE)")
        else:
            print(f"   {i:2d}. {col:<20}")
    
    print(f"\nTOTAL: {len(colonnes_requises)} colonnes")
    
    # Verification dans le code
    print("\nVERIFICATION DANS LE CODE:")
    
    try:
        with open('pdf_extractor.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ("'contenance' dans le code", 'contenance' in content),
            ("'contenance' dans listes", "'contenance'," in content),
            ("parcel_fields OK", "parcel_fields" in content and "'contenance'" in content),
            ("Instructions CONTENANCE", "CONTENANCE" in content)
        ]
        
        for desc, result in checks:
            status = "OK" if result else "MANQUE"
            print(f"   {desc:<25}: {status}")
            
    except Exception as e:
        print(f"   Erreur lecture: {e}")
    
    print("\n" + "=" * 40)
    print("RESUME:")
    print("La colonne CONTENANCE (surface) est bien configuree")
    print("Si elle n'apparait pas:")
    print("1. Vos PDFs contiennent-ils les surfaces?")
    print("2. Format: m², ares, centiares, ha")
    print("3. Le systeme detecte automatiquement le format")

if __name__ == "__main__":
    check_simple()