#!/bin/bash

echo "🏠 Lancement de l'Interface Extracteur PDF"
echo "=========================================="
echo

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "❌ Python n'est pas installé"
        echo "💡 Installez Python depuis https://python.org"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# Vérifier si le fichier interface existe
if [ ! -f "interface_gui.py" ]; then
    echo "❌ Fichier interface_gui.py non trouvé"
    echo "💡 Assurez-vous d'être dans le bon dossier"
    exit 1
fi

echo "✅ Python détecté ($PYTHON_CMD)"
echo "🚀 Lancement de l'interface..."
echo

# Lancer l'interface
$PYTHON_CMD interface_gui.py

# Vérifier le code de sortie
if [ $? -ne 0 ]; then
    echo
    echo "❌ Erreur lors du lancement"
    echo "💡 Vérifiez les dépendances avec: pip install -r requirements.txt"
    read -p "Appuyez sur Entrée pour continuer..."
fi 