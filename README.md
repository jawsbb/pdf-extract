# 🏠 Extracteur de Propriétaires PDF

Application web moderne pour extraire automatiquement les informations de propriétaires depuis des documents PDF en utilisant l'intelligence artificielle.

## 🚀 Fonctionnalités

- ✅ **Upload multiple** de fichiers PDF
- 🤖 **Extraction IA** automatique avec OpenAI
- 🎭 **Mode démo** intégré (sans API)
- 📊 **Visualisations** automatiques
- 📥 **Export** CSV/Excel/JSON
- 📱 **Interface responsive** moderne
- ⚡ **Traitement asynchrone** avec progress bars

## 🎯 3 Interfaces Disponibles

### 1. 📱 Streamlit (Recommandé)
Interface simple et efficace, parfaite pour débuter.
```bash
streamlit run streamlit_app.py
```

### 2. ⚛️ React + Flask (Moderne)
Interface ultra-moderne avec animations et API REST.
```bash
python start_web.py
```

### 3. 🔧 API Backend (Développeurs)
API REST complète pour intégrations.
```bash
cd backend && python app.py
```

## ⚡ Démarrage Rapide

### Installation
```bash
# Cloner le repository
git clone https://github.com/jawsbb/pdf-extract.git
cd pdf-extract

# Installer les dépendances
pip install -r requirements_streamlit.txt
```

### Lancement
```bash
# Option 1: Interface Streamlit
streamlit run streamlit_app.py

# Option 2: Menu interactif
python start_web.py
```

### Configuration OpenAI (Optionnel)
```bash
# Créer un fichier .env
echo "OPENAI_API_KEY=sk-votre_clé_ici" > .env
```

## 🌐 Déploiement

### Streamlit Cloud (Gratuit)
1. Push sur GitHub
2. Connecter sur [share.streamlit.io](https://share.streamlit.io)
3. Ajouter `OPENAI_API_KEY` dans les secrets
4. Déploiement automatique !

### Vercel + Railway
- **Frontend** : Déployer `frontend/` sur Vercel
- **Backend** : Déployer `backend/` sur Railway

## 📁 Structure du Projet

```
📁 pdf-extract/
├── 📱 streamlit_app.py          # Interface Streamlit
├── 🚀 start_web.py              # Lanceur multi-interface
├── 🔧 pdf_extractor.py          # Module d'extraction principal
├── 📚 DEMARRAGE_WEB.md          # Guide de démarrage
├── 🌐 deploy.md                 # Guide de déploiement
├── 
├── 🔧 backend/
│   ├── app.py                   # API Flask REST
│   ├── requirements.txt         # Dépendances backend
│   └── ...
├── 
├── ⚛️ frontend/
│   ├── src/App.tsx              # Interface React
│   ├── package.json             # Dépendances React
│   └── ...
└── 
└── 📄 requirements_streamlit.txt # Dépendances Streamlit
```

## 🔑 Configuration

### Mode Démo
- ✅ Aucune configuration requise
- 🎭 Résultats simulés réalistes
- 🎯 Parfait pour tester

### Mode Réel (OpenAI)
- 🤖 Extraction IA véritable
- 💰 Coût : ~$0.02-0.05 par PDF
- 🔑 Clé API OpenAI requise

## 📊 Données Extraites

- 👤 **Nom et prénom** du propriétaire
- 🏠 **Adresse** complète
- 🏙️ **Ville et code postal**
- 📞 **Téléphone** (si disponible)
- 📧 **Email** (si disponible)
- 🗺️ **Identifiant parcellaire**
- 📄 **Fichier source**

## 🛠️ Technologies

- **Backend** : Python, Flask, OpenAI API
- **Frontend** : React, TypeScript, Tailwind CSS
- **Interface** : Streamlit
- **Déploiement** : Streamlit Cloud, Vercel, Railway

## 📈 Performances

- ⚡ **Traitement** : 1-3 secondes par PDF
- 📊 **Précision** : 90-95% avec OpenAI
- 🔄 **Lots** : Jusqu'à 100 PDFs simultanés
- 💾 **Formats** : Export CSV, Excel, JSON

## 🤝 Contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commit (`git commit -am 'Ajouter nouvelle fonctionnalité'`)
4. Push (`git push origin feature/nouvelle-fonctionnalite`)
5. Créer une Pull Request

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🆘 Support

- 📚 **Documentation** : Voir les fichiers `.md` du projet
- 🐛 **Issues** : [GitHub Issues](https://github.com/jawsbb/pdf-extract/issues)
- 💬 **Discussions** : [GitHub Discussions](https://github.com/jawsbb/pdf-extract/discussions)

## 🎉 Démo en Ligne

🌐 **Streamlit Cloud** : [Lien vers l'application](https://votre-app.streamlit.app) (après déploiement)

---

*Développé avec ❤️ - De l'interface desktop à l'application web moderne !* 