#!/usr/bin/env python3
"""
Application Streamlit pour l'extraction d'informations de propriétaires depuis des PDFs cadastraux français.

Version simplifiée - retour aux bases pour une meilleure qualité d'extraction.
"""

import streamlit as st
import os
import tempfile
import pandas as pd
from pathlib import Path
import logging
from pdf_extractor import PDFPropertyExtractor

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration de la page
st.set_page_config(
    page_title="Extracteur PDF Cadastral",
    page_icon="📋",
    layout="wide"
)

def get_api_key():
    """Récupère la clé API OpenAI depuis les secrets Streamlit ou les variables d'environnement."""
    try:
        # Essayer d'abord les secrets Streamlit
        return st.secrets["OPENAI_API_KEY"]
    except:
        # Fallback sur les variables d'environnement
        return os.getenv("OPENAI_API_KEY")

def initialize_extractor(temp_dir):
    """Initialize the PDF extractor with API key."""
    api_key = get_api_key()
    if not api_key:
        st.error("❌ Clé API OpenAI non configurée. Veuillez configurer OPENAI_API_KEY.")
        st.stop()
    
    # Set the environment variable for the extractor
    os.environ['OPENAI_API_KEY'] = api_key
    
    return PDFPropertyExtractor(
        input_dir=str(temp_dir / "input"),
        output_dir=str(temp_dir / "output")
    )

def main():
    st.title("📋 Extracteur PDF Cadastral Français")
    st.markdown("### Version Simplifiée - Extraction de Qualité")
    
    st.markdown("""
    **Nouvelle structure de colonnes :**
    `Département | Commune | Préfixe | Section | Numéro | Contenance | Droit réel | Designation Parcelle | Nom Propri | Prénom Propri | N°MAJIC | Voie | CP | Ville | id`
    """)
    
    # Upload des fichiers
    uploaded_files = st.file_uploader(
        "Sélectionnez vos fichiers PDF cadastraux",
        type=['pdf'],
        accept_multiple_files=True,
        help="Vous pouvez sélectionner plusieurs fichiers PDF à traiter en une fois."
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} fichier(s) sélectionné(s)")
        
        if st.button("🚀 Lancer l'extraction", type="primary"):
            with st.spinner("Extraction en cours..."):
                # Créer un répertoire temporaire
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    input_dir = temp_path / "input"
                    output_dir = temp_path / "output"
                    input_dir.mkdir()
                    output_dir.mkdir()
                    
                    # Sauvegarder les fichiers uploadés
                    saved_files = []
                    for uploaded_file in uploaded_files:
                        file_path = input_dir / uploaded_file.name
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        saved_files.append(file_path)
                        st.info(f"📄 {uploaded_file.name} sauvegardé")
                    
                    try:
                        # Initialiser l'extracteur
                        extractor = initialize_extractor(temp_path)
                        
                        # Traitement
                        st.info("🔄 Traitement des fichiers PDF...")
                        all_properties = []
                        
                        # Barre de progression
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        for i, pdf_file in enumerate(saved_files):
                            status_text.text(f"Traitement de {pdf_file.name}...")
                            progress_bar.progress((i + 1) / len(saved_files))
                            
                            properties = extractor.process_single_pdf(pdf_file)
                            all_properties.extend(properties)
                            
                            st.success(f"✅ {pdf_file.name}: {len(properties)} propriété(s) extraite(s)")
                        
                        if all_properties:
                            # Export vers CSV
                            st.info("📊 Export des données...")
                            output_path = extractor.export_to_csv(all_properties, "extraction_results.csv")
                            
                            # Affichage des résultats
                            st.success(f"🎉 Extraction terminée ! {len(all_properties)} propriété(s) au total")
                            
                            # Aperçu des données
                            df = pd.DataFrame(all_properties)
                            
                            # Réorganiser les colonnes pour l'affichage
                            display_columns = [
                                'department', 'commune', 'prefixe', 'section', 'numero', 
                                'contenance', 'droit_reel', 'designation_parcelle', 
                                'nom', 'prenom', 'numero_majic', 'voie', 'post_code', 'city', 'id'
                            ]
                            
                            df_display = df.reindex(columns=display_columns, fill_value='')
                            
                            st.markdown("### 📊 Aperçu des données extraites")
                            st.dataframe(df_display, use_container_width=True)
                            
                            # Statistiques
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total propriétés", len(all_properties))
                            with col2:
                                unique_owners = len(df[df['nom'].notna()]['nom'].unique())
                                st.metric("Propriétaires uniques", unique_owners)
                            with col3:
                                files_processed = len(df['fichier_source'].unique())
                                st.metric("Fichiers traités", files_processed)
                            
                            # Téléchargement du CSV
                            with open(output_path, 'rb') as f:
                                csv_data = f.read()
                            
                            st.download_button(
                                label="📥 Télécharger le CSV",
                                data=csv_data,
                                file_name="extraction_cadastrale.csv",
                                mime="text/csv",
                                type="primary"
                            )
                            
                            # Analyse de qualité
                            st.markdown("### 📈 Analyse de qualité")
                            
                            quality_metrics = {}
                            essential_fields = ['nom', 'prenom', 'section', 'numero']
                            
                            for field in essential_fields:
                                non_empty = len(df[df[field].notna() & (df[field] != '')])
                                percentage = (non_empty / len(df)) * 100
                                quality_metrics[field] = percentage
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                for field, percentage in quality_metrics.items():
                                    st.metric(f"Complétude {field}", f"{percentage:.1f}%")
                            
                            with col2:
                                # Détection des champs vides
                                empty_count = 0
                                for _, row in df.iterrows():
                                    for field in essential_fields:
                                        if pd.isna(row[field]) or row[field] == '':
                                            empty_count += 1
                                
                                st.metric("Champs vides détectés", empty_count)
                        
                        else:
                            st.error("❌ Aucune donnée n'a pu être extraite des fichiers PDF.")
                    
                    except Exception as e:
                        st.error(f"❌ Erreur lors du traitement : {str(e)}")
                        logger.error(f"Erreur: {e}")
    
    else:
        st.info("👆 Veuillez sélectionner un ou plusieurs fichiers PDF pour commencer.")
    
    # Informations
    with st.expander("ℹ️ Informations"):
        st.markdown("""
        ### Comment utiliser cette application
        
        1. **Sélectionnez vos fichiers PDF** cadastraux français
        2. **Cliquez sur "Lancer l'extraction"** pour démarrer le processus
        3. **Consultez les résultats** dans le tableau et téléchargez le CSV
        
        ### Colonnes extraites
        - **Département** : Code département (2 chiffres)
        - **Commune** : Code commune (3 chiffres)  
        - **Préfixe** : Préfixe de section
        - **Section** : Section cadastrale
        - **Numéro** : Numéro de parcelle
        - **Contenance** : Surface de la parcelle
        - **Droit réel** : Type de droit (PP, US, NU)
        - **Designation Parcelle** : Nom/lieu-dit de la parcelle
        - **Nom Propri** : Nom du propriétaire
        - **Prénom Propri** : Prénom du propriétaire
        - **N°MAJIC** : Code MAJIC du propriétaire
        - **Voie** : Adresse du propriétaire
        - **CP** : Code postal
        - **Ville** : Ville
        - **id** : Identifiant unique (14 caractères)
        
        ### Version simplifiée
        Cette version se concentre sur l'extraction de base pour une meilleure qualité des données.
        Moins de post-traitement = meilleure précision.
        """)

if __name__ == "__main__":
    main() 