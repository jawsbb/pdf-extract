#!/usr/bin/env python3
"""
Script de test pour l'extracteur PDF.
Crée un PDF de test et vérifie le fonctionnement du système.
"""

import os
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import tempfile

def create_test_pdf(output_path: str):
    """
    Crée un PDF de test avec des informations de propriétaires.
    
    Args:
        output_path: Chemin de sortie pour le PDF
    """
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Titre
    title = Paragraph("INFORMATIONS PROPRIÉTAIRES", styles['Title'])
    
    # Données de test
    data = [
        ['Nom', 'Prénom', 'Adresse', 'CP', 'Ville', 'N° Prop.', 'Dept', 'Commune', 'Droit'],
        ['DUPONT', 'JEAN', '1 RUE DES LILAS', '75010', 'PARIS', 'P001', '75', '001', 'Propriétaire'],
        ['MARTIN', 'MARIE', '15 AV DE LA PAIX', '69001', 'LYON', 'P002', '69', '001', 'Indivision'],
        ['BERNARD', 'PIERRE', '8 PLACE DU MARCHE', '13001', 'MARSEILLE', 'P003', '13', '001', 'Usufruitier']
    ]
    
    # Créer le tableau
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    # Construire le document
    story = [title, table]
    doc.build(story)
    
    print(f"✅ PDF de test créé: {output_path}")

def test_without_api():
    """
    Test du système sans appel API (simulation).
    """
    print("🧪 Test de l'extracteur sans API...")
    
    # Créer un PDF de test
    input_dir = Path("input")
    input_dir.mkdir(exist_ok=True)
    
    test_pdf_path = input_dir / "test_proprietaires.pdf"
    create_test_pdf(str(test_pdf_path))
    
    # Tester la conversion PDF vers image
    from pdf_extractor import PDFPropertyExtractor
    
    # Créer un extracteur factice (sans clé API)
    extractor = PDFPropertyExtractor("fake_api_key")
    
    # Test de conversion PDF vers image
    image_data = extractor.pdf_to_image(test_pdf_path)
    
    if image_data:
        print("✅ Conversion PDF → Image réussie")
        print(f"📏 Taille de l'image: {len(image_data)} bytes")
        
        # Sauvegarder l'image pour vérification
        with open("output/test_image.png", "wb") as f:
            f.write(image_data)
        print("💾 Image sauvegardée: output/test_image.png")
    else:
        print("❌ Échec de la conversion PDF → Image")
    
    # Test de génération d'ID parcellaire
    parcel_id = extractor.generate_parcel_id("75", "001")
    print(f"🆔 ID Parcellaire généré: {parcel_id}")
    
    print("✅ Tests de base terminés!")

if __name__ == "__main__":
    # Installer reportlab si nécessaire
    try:
        import reportlab
    except ImportError:
        print("📦 Installation de reportlab...")
        os.system("pip install reportlab")
    
    test_without_api() 