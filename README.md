# 🏠 Extracteur de Propriétaires PDF

> **Application web moderne pour extraire automatiquement les informations de propriétaires depuis vos documents PDF**

![Interface](https://img.shields.io/badge/Interface-Streamlit-red)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![IA](https://img.shields.io/badge/IA-OpenAI-green)
![Production](https://img.shields.io/badge/Mode-Production-brightgreen)

## 🎯 **Qu'est-ce que c'est ?**

Cette application vous permet d'extraire automatiquement les informations de propriétaires (noms, adresses, contacts) depuis vos documents PDF en utilisant l'intelligence artificielle OpenAI.

### ✨ **Fonctionnalités principales**

- 📁 **Upload multiple** : Glissez-déposez plusieurs PDFs à la fois
- 🤖 **Extraction IA** : Reconnaissance automatique des données avec OpenAI
- 📊 **Visualisation** : Graphiques et tableaux des résultats
- 📥 **Export multiple** : CSV, Excel, JSON
- 🔄 **Temps réel** : Suivi du traitement en direct
- 🏢 **Mode Production** : Traitement IA réel inclus

## 🚀 **Démarrage Ultra-Rapide**

### 1. **Installation** (une seule fois)

```bash
# Cloner ou télécharger le projet
cd pdf-extract

# Installer les dépendances
pip install -r requirements.txt
```

### 2. **Configuration API** (une seule fois)

Modifiez le fichier `.env` avec votre clé API OpenAI :

```env
OPENAI_API_KEY=sk-votre-vraie-cle-api-ici
```

### 3. **Lancement** (à chaque utilisation)

```bash
# Méthode simple
python start.py

# OU directement
streamlit run streamlit_app.py
```

L'application s'ouvre automatiquement dans votre navigateur à l'adresse : `http://localhost:8501`

## 🏢 **Mode Production**

L'application fonctionne directement en **mode production** :

- ✅ **Extraction IA réelle** avec OpenAI
- ✅ **Pas de limitation** de fichiers
- ✅ **Résultats précis** et fiables
- ✅ **Coûts API inclus** côté serveur

## 📊 **Données Extraites**

L'application extrait automatiquement :

- 👤 **Identité** : Nom, prénom
- 🏠 **Adresse** : Adresse complète, code postal, ville
- 📞 **Contact** : Téléphone, email
- 🆔 **Références** : ID parcellaire, numéro de propriété
- 📄 **Source** : Fichier d'origine

## 🔧 **Configuration Serveur**

### 🔑 **Clé API OpenAI**

1. Créez un compte sur [platform.openai.com](https://platform.openai.com)
2. Générez une clé API
3. Modifiez le fichier `.env` :

```env
OPENAI_API_KEY=sk-votre-cle-api-ici
```

### 🚀 **Déploiement**

Pour déployer en production :

```bash
# Streamlit Cloud
streamlit run streamlit_app.py --server.port 8501

# Ou avec Docker
docker build -t pdf-extractor .
docker run -p 8501:8501 pdf-extractor
```

## 🛠️ **Dépannage**

### ❌ **Problèmes courants**

**L'application ne démarre pas :**
```bash
pip install --upgrade streamlit pandas python-dotenv
```

**Erreur de clé API :**
```bash
# Vérifiez le fichier .env
cat .env
```

**Port déjà utilisé :**
```bash
streamlit run streamlit_app.py --server.port 8502
```

### 📞 **Support**

- 📧 **Email** : support@votre-domaine.com
- 💬 **Chat** : Disponible dans l'application
- 📚 **Documentation** : [docs.votre-domaine.com](https://docs.votre-domaine.com)

## 🔒 **Sécurité & Confidentialité**

- 🔐 **Chiffrement** : Toutes les données sont chiffrées
- 🗑️ **Suppression** : Fichiers supprimés après traitement
- 🛡️ **Conformité** : RGPD compliant
- 🔑 **API** : Clé stockée côté serveur uniquement

## 📈 **Statistiques**

L'application suit automatiquement :
- Nombre de fichiers traités
- Propriétaires extraits
- Temps de traitement
- Taux de réussite

---

**🎯 Prêt en 30 secondes !** Configurez votre clé API et lancez `python start.py` 