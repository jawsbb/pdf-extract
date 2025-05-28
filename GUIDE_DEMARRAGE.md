# 🚀 Guide de Démarrage Rapide

## Installation Express

1. **Installer automatiquement** :
   ```bash
   python setup.py
   ```

2. **Configurer votre clé API** :
   - Éditez le fichier `.env`
   - Remplacez `your_openai_api_key_here` par votre vraie clé API OpenAI

## Utilisation

### 🧪 Test du Système
```bash
python demo_complete.py
```
Cette commande lance une démonstration complète avec des données fictives.

### 🏠 Extraction Réelle
1. Placez vos PDFs dans le dossier `input/`
2. Lancez :
   ```bash
   python pdf_extractor.py
   ```
3. Récupérez le fichier `output/output.csv`

## Structure des Fichiers

```
📁 input/          ← Placez vos PDFs ici
📁 output/         ← Résultats CSV ici
📄 .env            ← Configuration API
📄 pdf_extractor.py ← Script principal
```

## Résultat Attendu

Le fichier CSV contiendra :
- **Nom, Prénom** : Identité du propriétaire
- **Adresse, CP, Ville** : Localisation
- **Département, Commune** : Codes administratifs
- **Numéro MAJIC** : Identifiant propriétaire
- **Droit réel** : Type de propriété
- **ID Parcelle** : Identifiant généré automatiquement

## Support

- 📋 Consultez `README.md` pour la documentation complète
- 🐛 Vérifiez `extraction.log` en cas de problème
- 🧪 Testez avec `python test_extractor.py`

---
**Prêt à extraire ! 🎯** 