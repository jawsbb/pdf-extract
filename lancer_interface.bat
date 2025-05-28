@echo off
echo 🏠 Lancement de l'Interface Extracteur PDF
echo ==========================================
echo.

REM Vérifier si Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python n'est pas installé ou pas dans le PATH
    echo 💡 Installez Python depuis https://python.org
    pause
    exit /b 1
)

REM Vérifier si le fichier interface existe
if not exist "interface_gui.py" (
    echo ❌ Fichier interface_gui.py non trouvé
    echo 💡 Assurez-vous d'être dans le bon dossier
    pause
    exit /b 1
)

echo ✅ Python détecté
echo 🚀 Lancement de l'interface...
echo.

REM Lancer l'interface
python interface_gui.py

REM Si erreur, afficher un message
if errorlevel 1 (
    echo.
    echo ❌ Erreur lors du lancement
    echo 💡 Vérifiez les dépendances avec: pip install -r requirements.txt
    pause
) 