# 🚀 Guide de Déploiement - Streamlit Community Cloud

## Prérequis
- [ ] Compte GitHub
- [ ] Clé API OpenAI valide
- [ ] Code pushé sur GitHub (repo public ou privé)

## 📋 Étapes de Déploiement

### 1. Préparer le Repository GitHub

```bash
# Si pas encore fait, initialiser git et pousser sur GitHub
git add .
git commit -m "Préparation pour déploiement Streamlit"
git push origin master
```

### 2. Déployer sur Streamlit Community Cloud

1. **Aller sur [share.streamlit.io](https://share.streamlit.io)**
2. **Se connecter avec GitHub**
3. **Cliquer sur "New app"**
4. **Sélectionner :**
   - Repository : `jawsbb/pdf-extract`
   - Branch : `master`
   - Main file path : `streamlit_app.py`
5. **Cliquer sur "Deploy!"**

### 3. Configurer les Secrets

⚠️ **IMPORTANT** : Après le déploiement initial :

1. **Aller dans les paramètres de votre app**
2. **Section "Secrets" dans la sidebar**
3. **Coller ce contenu (remplacez par votre vraie clé API) :**

```toml
OPENAI_API_KEY = "sk-votre-vraie-cle-api-openai"
```

4. **Cliquer sur "Save"**
5. **L'app va redémarrer automatiquement**

## 🔗 Résultat

Votre app sera disponible sur une URL comme :
`https://votre-app-name.streamlit.app`

## 🔧 Maintenance

- **Mises à jour automatiques** : Chaque push sur `master` redéploie l'app
- **Logs** : Visibles dans l'interface Streamlit Cloud
- **Ressources** : 1GB RAM, CPU partagé (gratuit)

## 🚨 Sécurité

✅ **Ce qui est fait :**
- Secrets configurés dans Streamlit Cloud (non visibles publiquement)
- `.env` et `secrets.toml` dans `.gitignore`
- Gestion d'erreur si clé API manquante

❌ **À ne pas faire :**
- Ne jamais committer les vraies clés API
- Ne pas partager l'URL des secrets

## 📞 Support

Si problème de déploiement :
1. Vérifier les logs dans Streamlit Cloud
2. Vérifier que tous les fichiers sont bien pushés
3. Vérifier la configuration des secrets 