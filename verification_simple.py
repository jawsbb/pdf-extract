#!/usr/bin/env python3
"""
Vérification simple que la correction fonctionne.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pdf_extractor import PDFPropertyExtractor

# Test simple
extractor = PDFPropertyExtractor()

print("🔍 VÉRIFICATION RAPIDE DE LA CORRECTION")
print("=" * 50)

# Test section A
result_A = extractor.generate_unique_id('25', '424', 'A', '90')
section_A = result_A[8:10]
print(f"Section A: {result_A} → section part: '{section_A}'")

# Test section B  
result_B = extractor.generate_unique_id('51', '179', 'B', '6')
section_B = result_B[8:10]
print(f"Section B: {result_B} → section part: '{section_B}'")

# Vérification
if section_A == "0A" and section_B == "0B":
    print("✅ CORRECTION RÉUSSIE ! Les zéros sont bien en PREMIÈRE position.")
else:
    print("❌ Problème persistant.")

print(f"✅ Section A: '{section_A}' (attendu: '0A')")
print(f"✅ Section B: '{section_B}' (attendu: '0B')") 