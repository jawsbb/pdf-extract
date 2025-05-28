# 🖥️ Interface Graphique - Guide d'Utilisation

## 🚀 Lancement

```bash
python interface_gui.py
```

## 📋 Fonctionnalités de l'Interface

### ⚙️ Section Configuration
- **Mode Démo** : Simulation sans API OpenAI (activé par défaut)
- **Clé API OpenAI** : Saisie sécurisée de votre clé API
- **Bouton Sauvegarder** : Enregistre la configuration dans `.env`

### 📁 Section Fichiers PDF
- **Sélectionner PDFs** : Choisir des fichiers PDF depuis votre ordinateur
- **Utiliser PDFs de test** : Charger automatiquement les PDFs d'exemple
- **Effacer** : Vider la liste des fichiers sélectionnés
- **Liste des fichiers** : Affichage des PDFs à traiter

### 🚀 Section Traitement
- **Lancer l'extraction** : Démarre le processus d'extraction
- **Barre de progression** : Indicateur visuel du traitement en cours
- **Statut** : État actuel du processus

### 📊 Section Résultats
- **Zone de logs** : Affichage en temps réel des opérations
- **Ouvrir dossier output** : Accès direct au dossier des résultats
- **Voir CSV** : Visualisation du tableau des résultats
- **Effacer logs** : Nettoyer l'affichage des logs

## 🎯 Utilisation Rapide

### Mode Démo (Recommandé pour les tests)
1. ✅ Laissez "Mode Démo" coché
2. 📂 Cliquez "Utiliser PDFs de test"
3. 🚀 Cliquez "Lancer l'extraction"
4. 📊 Consultez les résultats dans les logs
5. 📄 Cliquez "Voir CSV" pour voir le tableau

### Mode Réel (Avec API OpenAI)
1. ❌ Décochez "Mode Démo"
2. 🔑 Saisissez votre clé API OpenAI
3. 💾 Cliquez "Sauvegarder"
4. 📂 Sélectionnez vos fichiers PDF
5. 🚀 Lancez l'extraction
6. 📊 Consultez les résultats

## 🖼️ Aperçu de l'Interface

```
┌─────────────────────────────────────────────────────────────┐
│ 🏠 Extracteur PDF de Propriétaires                         │
├─────────────────────────────────────────────────────────────┤
│ ⚙️ Configuration                                           │
│ ☑️ Mode Démo (simulation sans API)                        │
│ Clé API OpenAI: [******************] [💾 Sauvegarder]     │
├─────────────────────────────────────────────────────────────┤
│ 📁 Fichiers PDF                                           │
│ [📂 Sélectionner] [🧪 PDFs test] [🗑️ Effacer]           │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ test_proprietaires.pdf                                  │ │
│ │ proprietaires_paris.pdf                                 │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ 🚀 Traitement                                             │
│ [🚀 Lancer l'extraction] [████████████] Prêt              │
├─────────────────────────────────────────────────────────────┤
│ 📊 Résultats                                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Mode DÉMO activé - Simulation sans API                 │ │
│ │ 4 fichier(s) de test chargé(s)                         │ │
│ │ [START] Démarrage du traitement...                     │ │
│ │ [OK] Traitement terminé avec succès!                   │ │
│ └─────────────────────────────────────────────────────────┘ │
│ [📂 Ouvrir output] [📄 Voir CSV] [🗑️ Effacer logs]       │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Fonctionnalités Avancées

### 📄 Visualiseur CSV Intégré
- Tableau interactif avec toutes les colonnes
- Scrolling horizontal et vertical
- Ouverture dans une fenêtre séparée

### 📂 Gestion des Fichiers
- Copie automatique des PDFs dans le dossier `input/`
- Support du glisser-déposer (selon le système)
- Validation des formats de fichiers

### 🔄 Traitement Asynchrone
- Interface non bloquante pendant le traitement
- Logs en temps réel
- Barre de progression animée

## 🐛 Dépannage

### Interface ne se lance pas
```bash
# Vérifier les dépendances
pip install tkinter pillow pandas

# Relancer
python interface_gui.py
```

### Erreur "Module not found"
```bash
# S'assurer d'être dans le bon dossier
cd "vent d'est python"
python interface_gui.py
```

### Problème d'affichage
- L'interface s'adapte automatiquement à la taille d'écran
- Redimensionnable manuellement
- Compatible Windows, macOS, Linux

## 💡 Conseils d'Utilisation

1. **Commencez par le mode démo** pour vous familiariser
2. **Testez avec les PDFs d'exemple** avant vos vrais documents
3. **Surveillez les logs** pour comprendre le processus
4. **Sauvegardez votre clé API** pour éviter de la ressaisir
5. **Utilisez "Voir CSV"** pour vérifier les résultats rapidement

---

**🎉 Interface prête à l'emploi !** 