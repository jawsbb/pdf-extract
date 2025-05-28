# 🚀 Guide de Déploiement - Extracteur PDF en Ligne

## 📋 Vue d'ensemble

Votre application est maintenant prête pour le déploiement ! Vous avez :
- **Backend** : API Flask avec traitement asynchrone
- **Frontend** : Interface React moderne avec Tailwind CSS
- **Architecture** : Séparation frontend/backend pour scalabilité

## 🎯 Options de Déploiement

### 1. **OPTION RAPIDE : Streamlit Cloud (Recommandée pour débuter)**

**Avantages :** Gratuit, simple, parfait pour prototypage
**Inconvénients :** Interface moins personnalisable

```bash
# Créer une version Streamlit
pip install streamlit streamlit-dropzone
```

### 2. **OPTION MODERNE : Vercel + Railway**

**Frontend (Vercel) :** Gratuit, CDN mondial, déploiement automatique
**Backend (Railway) :** $5/mois, base de données incluse

### 3. **OPTION COMPLÈTE : Heroku**

**Avantages :** Tout-en-un, facile à configurer
**Coût :** ~$7/mois par dyno

### 4. **OPTION PROFESSIONNELLE : AWS/Google Cloud**

**Avantages :** Scalabilité maximale, contrôle total
**Complexité :** Plus technique, coût variable

## 🚀 Déploiement Recommandé : Vercel + Railway

### Étape 1 : Préparer le Backend (Railway)

1. **Créer un compte sur Railway.app**
2. **Connecter votre repository GitHub**
3. **Configurer les variables d'environnement :**

```env
OPENAI_API_KEY=votre_clé_openai
FLASK_ENV=production
PORT=5000
```

4. **Créer `backend/Procfile` :**

```
web: python app.py
```

5. **Mettre à jour `backend/app.py` pour la production :**

```python
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
```

### Étape 2 : Préparer le Frontend (Vercel)

1. **Créer un compte sur Vercel.com**
2. **Connecter votre repository GitHub**
3. **Configurer les variables d'environnement :**

```env
REACT_APP_API_URL=https://votre-backend.railway.app
```

4. **Build automatique :** Vercel détecte React automatiquement

### Étape 3 : Configuration CORS

Mettre à jour `backend/app.py` :

```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["https://votre-frontend.vercel.app"])
```

## 🔧 Alternative : Déploiement Local avec Ngrok

Pour tester rapidement en ligne sans hébergement :

```bash
# Installer ngrok
npm install -g ngrok

# Terminal 1 : Backend
cd backend
python app.py

# Terminal 2 : Frontend  
cd frontend
npm start

# Terminal 3 : Exposer en ligne
ngrok http 3000
```

## 📦 Déploiement Streamlit (Option Simple)

Créer `streamlit_app.py` :

```python
import streamlit as st
import sys
import os
sys.path.append('.')
from pdf_extractor import PDFPropertyExtractor

st.set_page_config(
    page_title="Extracteur PDF",
    page_icon="📄",
    layout="wide"
)

st.title("🏠 Extracteur de Propriétaires PDF")
st.markdown("Uploadez vos PDFs et extrayez automatiquement les informations")

uploaded_files = st.file_uploader(
    "Choisissez vos fichiers PDF",
    type="pdf",
    accept_multiple_files=True
)

if uploaded_files:
    if st.button("Extraire les données"):
        with st.spinner("Traitement en cours..."):
            extractor = PDFPropertyExtractor()
            all_results = []
            
            progress_bar = st.progress(0)
            for i, file in enumerate(uploaded_files):
                # Sauvegarder temporairement
                with open(f"temp_{file.name}", "wb") as f:
                    f.write(file.getbuffer())
                
                # Traiter
                results = extractor.extract_from_pdf(f"temp_{file.name}")
                all_results.extend(results)
                
                # Nettoyer
                os.remove(f"temp_{file.name}")
                
                progress_bar.progress((i + 1) / len(uploaded_files))
            
            if all_results:
                st.success(f"✅ {len(all_results)} propriétaire(s) extrait(s)")
                
                # Afficher les résultats
                df = pd.DataFrame(all_results)
                st.dataframe(df)
                
                # Téléchargement CSV
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Télécharger CSV",
                    csv,
                    "extraction_results.csv",
                    "text/csv"
                )
```

Déployer sur Streamlit Cloud :
1. Push sur GitHub
2. Aller sur share.streamlit.io
3. Connecter le repository
4. Ajouter les secrets (OPENAI_API_KEY)

## 🌐 URLs de Déploiement

Après déploiement, vous aurez :

- **Frontend :** `https://votre-app.vercel.app`
- **Backend :** `https://votre-api.railway.app`
- **Streamlit :** `https://votre-app.streamlit.app`

## 🔒 Sécurité et Configuration

### Variables d'environnement requises :

**Backend :**
```env
OPENAI_API_KEY=sk-...
FLASK_ENV=production
CORS_ORIGINS=https://votre-frontend.vercel.app
```

**Frontend :**
```env
REACT_APP_API_URL=https://votre-backend.railway.app
```

### Limites de fichiers :

```python
# Dans app.py
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max
```

## 📊 Monitoring et Logs

### Railway (Backend) :
- Logs automatiques dans le dashboard
- Métriques de performance
- Alertes par email

### Vercel (Frontend) :
- Analytics intégrés
- Monitoring des erreurs
- Déploiements automatiques

## 💰 Coûts Estimés

| Service | Gratuit | Payant |
|---------|---------|---------|
| **Vercel** | 100GB/mois | $20/mois (Pro) |
| **Railway** | $5 crédit/mois | $5/mois + usage |
| **Streamlit** | Illimité | - |
| **Heroku** | - | $7/mois/dyno |

## 🚀 Commandes de Déploiement

```bash
# 1. Préparer le projet
git add .
git commit -m "Prêt pour déploiement"
git push origin main

# 2. Frontend (Vercel)
# - Connecter GitHub sur vercel.com
# - Déploiement automatique

# 3. Backend (Railway)  
# - Connecter GitHub sur railway.app
# - Ajouter variables d'environnement
# - Déploiement automatique

# 4. Tester
curl https://votre-backend.railway.app/api/health
```

## 🎉 Prochaines Étapes

1. **Déployer** avec l'option choisie
2. **Tester** avec de vrais PDFs
3. **Partager** l'URL avec vos utilisateurs
4. **Monitorer** les performances
5. **Améliorer** selon les retours

Votre extracteur PDF est maintenant prêt pour le monde ! 🌍 