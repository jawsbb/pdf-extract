#!/usr/bin/env python3
"""
Extracteur PDF Ultra-Simple
Interface minimaliste pour l'extraction de propriétaires depuis des PDFs
"""

import streamlit as st
import pandas as pd
import sys
import os
import tempfile
from io import BytesIO
import time
from dotenv import load_dotenv
from pathlib import Path

# Charger les variables d'environnement
load_dotenv()

# Configuration de la page
st.set_page_config(
    page_title="Extracteur PDF",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Import du module principal
sys.path.append('.')
try:
    from pdf_extractor import PDFPropertyExtractor
except ImportError:
    st.error("Module pdf_extractor non trouvé. Assurez-vous que le fichier pdf_extractor.py est présent.")
    st.stop()

# Configuration API côté serveur - Support Streamlit Secrets + variables d'environnement
try:
    # Essayer d'abord les secrets Streamlit (pour le déploiement)
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except (KeyError, FileNotFoundError):
    # Fallback sur les variables d'environnement (pour le développement local)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not OPENAI_API_KEY or OPENAI_API_KEY == "sk-votre-cle-api-ici":
    st.error("""
    🔑 **Clé API OpenAI non configurée**
    
    **Pour le développement local :**
    - Créez un fichier `.env` avec `OPENAI_API_KEY=votre-clé`
    
    **Pour le déploiement Streamlit Cloud :**
    - Configurez la clé dans les secrets de votre app sur share.streamlit.io
    """)
    st.stop()

os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

# CSS Ultra-Minimaliste
st.markdown("""
<style>
    /* Masquer les éléments Streamlit par défaut */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    
    /* FORCER LE FOND BLANC PARTOUT */
    .stApp, .main, .block-container, .element-container,
    div[data-testid="stVerticalBlock"], div[data-testid="stHorizontalBlock"],
    div[data-testid="column"], .stMarkdown, .stText {
        background: white !important;
        color: #1a1a1a !important;
    }
    
    /* Style principal */
    .stApp {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
    }
    
    .main .block-container {
        padding-top: 2rem !important;
        max-width: 600px;
        margin: 0 auto;
    }
    
    /* Titre principal */
    .title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 600;
        color: #1a1a1a !important;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
        background: white !important;
    }
    
    .subtitle {
        text-align: center;
        font-size: 1rem;
        color: #666 !important;
        margin-bottom: 3rem;
        background: white !important;
    }
    
    /* Zone d'upload */
    .upload-area {
        border: 2px dashed #ddd;
        border-radius: 12px;
        padding: 4rem 2rem;
        text-align: center;
        margin: 2rem 0;
        background: #fafafa !important;
        transition: all 0.2s ease;
    }
    
    .upload-area:hover {
        border-color: #999;
        background: #f5f5f5 !important;
    }
    
    .upload-text {
        font-size: 1.1rem;
        color: #333 !important;
        margin-bottom: 0.5rem;
        font-weight: 500;
        background: transparent !important;
    }
    
    .upload-subtext {
        font-size: 0.9rem;
        color: #666 !important;
        background: transparent !important;
    }
    
    /* Boutons principaux */
    .stButton > button {
        background: #1a1a1a !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 1rem 2rem !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
        width: 100% !important;
        margin: 2rem 0 !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
        background: #333 !important;
        color: white !important;
        transform: translateY(-1px);
    }
    
    /* Boutons de téléchargement */
    .stDownloadButton > button {
        background: #f8f9fa !important;
        color: #1a1a1a !important;
        border: 1px solid #ddd !important;
        border-radius: 6px !important;
        padding: 0.5rem 1rem !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        width: 100% !important;
        margin: 0.25rem 0 !important;
        transition: all 0.2s ease !important;
    }
    
    .stDownloadButton > button:hover {
        background: #e9ecef !important;
        color: #1a1a1a !important;
        border-color: #adb5bd !important;
    }
    
    /* Fichiers sélectionnés */
    .file-list {
        background: #f8f9fa !important;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #1a1a1a;
        color: #1a1a1a !important;
    }
    
    /* Métriques */
    .metric {
        text-align: center;
        margin: 1rem;
        padding: 1.5rem;
        background: white !important;
        border: 1px solid #eee;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .metric-number {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1a1a1a !important;
        margin-bottom: 0.25rem;
        background: white !important;
    }
    
    .metric-label {
        font-size: 0.8rem;
        color: #666 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 500;
        background: white !important;
    }
    
    /* CORRECTION COMPLÈTE DU TABLEAU */
    .stDataFrame {
        background: white !important;
        margin: 2rem 0;
        border: 1px solid #ddd !important;
        border-radius: 8px !important;
        overflow: hidden !important;
    }
    
    .stDataFrame > div {
        background: white !important;
    }
    
    .stDataFrame table {
        background: white !important;
        color: #1a1a1a !important;
        border-collapse: collapse;
        width: 100%;
        border: none !important;
    }
    
    .stDataFrame th {
        background: #f8f9fa !important;
        color: #1a1a1a !important;
        font-weight: 600 !important;
        border: 1px solid #dee2e6 !important;
        padding: 12px 8px !important;
        text-align: left !important;
    }
    
    .stDataFrame td {
        background: white !important;
        color: #1a1a1a !important;
        padding: 10px 8px !important;
        border: 1px solid #dee2e6 !important;
    }
    
    .stDataFrame tr {
        background: white !important;
    }
    
    .stDataFrame tbody tr:nth-child(even) {
        background: #f8f9fa !important;
    }
    
    .stDataFrame tbody tr:nth-child(odd) {
        background: white !important;
    }
    
    .stDataFrame tbody tr:hover {
        background: #e9ecef !important;
    }
    
    /* CORRECTION DES ÉLÉMENTS STREAMLIT SPÉCIFIQUES */
    div[data-testid="stDataFrame"] {
        background: white !important;
        border: 1px solid #ddd !important;
        border-radius: 8px !important;
    }
    
    div[data-testid="stDataFrame"] > div {
        background: white !important;
    }
    
    div[data-testid="stDataFrame"] table {
        background: white !important;
        border: none !important;
    }
    
    div[data-testid="stDataFrame"] th {
        background: #f8f9fa !important;
        color: #1a1a1a !important;
        border: 1px solid #dee2e6 !important;
        font-weight: 600 !important;
    }
    
    div[data-testid="stDataFrame"] td {
        background: white !important;
        color: #1a1a1a !important;
        border: 1px solid #dee2e6 !important;
    }
    
    div[data-testid="stDataFrame"] tbody tr:nth-child(even) {
        background: #f8f9fa !important;
    }
    
    div[data-testid="stDataFrame"] tbody tr:nth-child(odd) {
        background: white !important;
    }
    
    /* CORRECTION SPÉCIFIQUE POUR L'APERÇU DES DONNÉES */
    div[data-testid="stDataFrame"] div[data-testid="stDataFrameResizable"] {
        background: white !important;
        border: 1px solid #ddd !important;
        border-radius: 8px !important;
    }
    
    div[data-testid="stDataFrame"] div[data-testid="stDataFrameResizable"] > div {
        background: white !important;
    }
    
    div[data-testid="stDataFrame"] div[data-testid="stDataFrameResizable"] table {
        background: white !important;
        border-collapse: collapse !important;
    }
    
    div[data-testid="stDataFrame"] div[data-testid="stDataFrameResizable"] th {
        background: #f8f9fa !important;
        color: #1a1a1a !important;
        border: 1px solid #dee2e6 !important;
        font-weight: 600 !important;
        padding: 8px !important;
    }
    
    div[data-testid="stDataFrame"] div[data-testid="stDataFrameResizable"] td {
        background: white !important;
        color: #1a1a1a !important;
        border: 1px solid #dee2e6 !important;
        padding: 8px !important;
    }
    
    div[data-testid="stDataFrame"] div[data-testid="stDataFrameResizable"] tbody tr:nth-child(even) {
        background: #f8f9fa !important;
    }
    
    div[data-testid="stDataFrame"] div[data-testid="stDataFrameResizable"] tbody tr:nth-child(odd) {
        background: white !important;
    }
    
    /* FORCER LE TEXTE À ÊTRE VISIBLE DANS TOUS LES ÉLÉMENTS DU TABLEAU */
    .stDataFrame *, 
    div[data-testid="stDataFrame"] *,
    div[data-testid="stDataFrameResizable"] * {
        color: #1a1a1a !important;
    }
    
    /* FORCER TOUS LES ÉLÉMENTS DE TABLEAU À ÊTRE VISIBLES */
    .dataframe, .dataframe * {
        background: inherit !important;
        color: #1a1a1a !important;
        border: 1px solid #dee2e6 !important;
    }
    
    .dataframe th {
        background: #f8f9fa !important;
        color: #1a1a1a !important;
        font-weight: 600 !important;
    }
    
    .dataframe td {
        background: white !important;
        color: #1a1a1a !important;
    }
    
    /* CORRECTION POUR LES CELLULES SPÉCIFIQUES */
    .stDataFrame .data {
        background: white !important;
        color: #1a1a1a !important;
        border: 1px solid #dee2e6 !important;
    }
    
    .stDataFrame .blank {
        background: #f8f9fa !important;
        border: 1px solid #dee2e6 !important;
    }
    
    .stDataFrame .row_heading {
        background: #f8f9fa !important;
        color: #1a1a1a !important;
        font-weight: 600 !important;
        border: 1px solid #dee2e6 !important;
    }
    
    .stDataFrame .col_heading {
        background: #f8f9fa !important;
        color: #1a1a1a !important;
        font-weight: 600 !important;
        border: 1px solid #dee2e6 !important;
    }
    
    /* CORRECTION POUR LES ÉLÉMENTS AGRID/STREAMLIT */
    .ag-root-wrapper {
        background: white !important;
        border: 1px solid #ddd !important;
        border-radius: 8px !important;
    }
    
    .ag-root {
        background: white !important;
    }
    
    .ag-header {
        background: #f8f9fa !important;
    }
    
    .ag-header-cell {
        background: #f8f9fa !important;
        color: #1a1a1a !important;
        border: 1px solid #dee2e6 !important;
        font-weight: 600 !important;
    }
    
    .ag-cell {
        background: white !important;
        color: #1a1a1a !important;
        border: 1px solid #dee2e6 !important;
    }
    
    .ag-row {
        background: white !important;
    }
    
    .ag-row-even {
        background: #f8f9fa !important;
    }
    
    .ag-row-odd {
        background: white !important;
    }
    
    .ag-row:hover {
        background: #e9ecef !important;
    }
    
    /* FORCER TOUS LES CONTENEURS DE DONNÉES À ÊTRE VISIBLES */
    [data-testid="stDataFrame"] * {
        color: #1a1a1a !important;
    }
    
    [data-testid="stDataFrame"] th {
        background: #f8f9fa !important;
        border: 1px solid #dee2e6 !important;
    }
    
    [data-testid="stDataFrame"] td {
        background: white !important;
        border: 1px solid #dee2e6 !important;
    }
    
    /* RÈGLES SPÉCIFIQUES POUR FORCER LA VISIBILITÉ DU TEXTE */
    .stDataFrame span,
    .stDataFrame div,
    .stDataFrame p,
    div[data-testid="stDataFrame"] span,
    div[data-testid="stDataFrame"] div,
    div[data-testid="stDataFrame"] p,
    div[data-testid="stDataFrameResizable"] span,
    div[data-testid="stDataFrameResizable"] div,
    div[data-testid="stDataFrameResizable"] p {
        color: #1a1a1a !important;
        background: transparent !important;
    }
    
    /* Section de téléchargement */
    .download-section {
        margin: 2rem 0;
        padding: 1.5rem;
        background: white !important;
        border: 1px solid #eee;
        border-radius: 8px;
        text-align: center;
    }
    
    .download-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1a1a1a !important;
        margin-bottom: 1rem;
        background: white !important;
    }
    
    /* Messages */
    .success-message {
        background: #d4edda !important;
        color: #155724 !important;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        text-align: center;
        font-weight: 500;
        border: 1px solid #c3e6cb;
    }
    
    .warning-message {
        background: #fff3cd !important;
        color: #856404 !important;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        text-align: center;
        font-weight: 500;
        border: 1px solid #ffeaa7;
    }
    
    /* File uploader */
    .stFileUploader {
        background: white !important;
    }
    
    .stFileUploader > div {
        background: white !important;
    }
    
    .stFileUploader label {
        color: #1a1a1a !important;
        background: white !important;
    }
    
    .stFileUploader section {
        background: white !important;
        border: 2px dashed #ddd !important;
        border-radius: 8px !important;
    }
    
    .stFileUploader section > div {
        background: white !important;
        color: #1a1a1a !important;
    }
    
    /* Progress et Spinner */
    .stProgress {
        background: white !important;
    }
    
    .stProgress > div {
        background: white !important;
    }
    
    .stProgress > div > div {
        background: white !important;
        color: #1a1a1a !important;
    }
    
    .stProgress > div > div > div {
        background: #1a1a1a !important;
    }
    
    .stSpinner {
        background: white !important;
    }
    
    .stSpinner > div {
        background: white !important;
        color: #1a1a1a !important;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        margin-top: 4rem;
        padding-top: 2rem;
        border-top: 1px solid #eee;
        color: #666 !important;
        font-size: 0.8rem;
        background: white !important;
    }
    
    .footer a {
        color: #1a1a1a !important;
        text-decoration: none;
    }
    
    .footer a:hover {
        text-decoration: underline;
    }
    
    /* Instructions */
    .instructions {
        text-align: center;
        color: #666 !important;
        margin: 3rem 0;
        font-size: 1rem;
        line-height: 1.6;
        background: white !important;
    }
    
    .instructions p {
        color: #666 !important;
        background: white !important;
    }
    
    .instructions strong {
        color: #1a1a1a !important;
        background: white !important;
    }
    
    /* FORCER TOUS LES TEXTES À ÊTRE LISIBLES */
    * {
        box-sizing: border-box;
    }
    
    /* Exceptions pour conserver les couleurs spécifiques */
    .stButton > button,
    .success-message,
    .warning-message,
    .stDownloadButton > button {
        color: inherit !important;
    }
    
    /* Assurer la lisibilité de tous les éléments */
    p, span, div, h1, h2, h3, h4, h5, h6, label, li, td, th {
        color: #1a1a1a !important;
        background: inherit !important;
    }
    
    /* Correction spéciale pour les éléments Streamlit cachés */
    .stAlert, .stError, .stWarning, .stInfo, .stSuccess {
        background: white !important;
        color: #1a1a1a !important;
        border: 1px solid #ddd !important;
    }
    
    .stAlert > div, .stError > div, .stWarning > div, .stInfo > div, .stSuccess > div {
        background: white !important;
        color: #1a1a1a !important;
    }
</style>
""", unsafe_allow_html=True)

def process_files(uploaded_files):
    """Traite les fichiers uploadés et retourne les résultats"""
    try:
        # Initialisation de l'extracteur
        with st.spinner("Initialisation de l'extracteur IA..."):
            extractor = PDFPropertyExtractor()
        
        all_results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Traitement de chaque fichier
        for i, file in enumerate(uploaded_files):
            status_text.text(f"Traitement de {file.name}...")
            
            # Sauvegarde temporaire du fichier
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(file.getbuffer())
                tmp_file_path = tmp_file.name
            
            try:
                # Extraction des données
                results = extractor.process_single_pdf(Path(tmp_file_path))
                
                # Ajout du nom du fichier source
                for result in results:
                    result['fichier_source'] = file.name
                
                all_results.extend(results)
                
            except Exception as e:
                st.error(f"Erreur lors du traitement de {file.name}: {str(e)}")
            
            finally:
                # Nettoyage du fichier temporaire
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
            
            # Mise à jour de la barre de progression
            progress_bar.progress((i + 1) / len(uploaded_files))
        
        # Nettoyage de l'interface
        progress_bar.empty()
        status_text.empty()
        
        return all_results
        
    except Exception as e:
        st.error(f"Erreur lors de l'initialisation: {str(e)}")
        return []

def display_results(results):
    """Affiche les résultats de l'extraction"""
    if not results:
        st.markdown("""
        <div class="warning-message">
            Aucun propriétaire trouvé dans les fichiers traités
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Message de succès
    st.markdown("""
    <div class="success-message">
        Extraction terminée avec succès
    </div>
    """, unsafe_allow_html=True)
    
    # Métriques
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric">
            <div class="metric-number">{len(results)}</div>
            <div class="metric-label">Propriétaires</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        unique_files = len(set(r.get('fichier_source', '') for r in results))
        st.markdown(f"""
        <div class="metric">
            <div class="metric-number">{unique_files}</div>
            <div class="metric-label">Fichiers</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        unique_cities = len(set(r.get('city', '') for r in results if r.get('city')))
        st.markdown(f"""
        <div class="metric">
            <div class="metric-number">{unique_cities}</div>
            <div class="metric-label">Villes</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Préparation du DataFrame
    df = pd.DataFrame(results)
    
    # Mapping des colonnes pour l'affichage
    column_mapping = {
        'nom': 'Nom',
        'prenom': 'Prénom', 
        'adresse_proprietaire': 'Adresse Propriétaire',
        'city': 'Ville',
        'post_code': 'Code Postal',
        'droit_reel': 'Droit réel',
        'section': 'Section',
        'numero_plan': 'N° Plan',
        'street_address': 'Adresse Propriété',
        'contenance': 'Contenance',
        'HA': 'Hectares',
        'A': 'Ares',
        'CA': 'Centiares',
        'fichier_source': 'Fichier'
    }
    
    # Sélection et renommage des colonnes
    available_columns = [col for col in column_mapping.keys() if col in df.columns]
    df_display = df[available_columns].rename(columns=column_mapping)
    df_display = df_display.fillna('N/A')
    
    # Affichage du tableau
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    # Section de téléchargement
    st.markdown("""
    <div class="download-section">
        <div class="download-title">Télécharger les résultats</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    # CSV
    with col1:
        csv = df_display.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="CSV",
            data=csv,
            file_name="proprietaires.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    # Excel (avec gestion d'erreur)
    with col2:
        try:
            excel_buffer = BytesIO()
            df_display.to_excel(excel_buffer, index=False, engine='openpyxl')
            excel_buffer.seek(0)
            st.download_button(
                label="Excel",
                data=excel_buffer.getvalue(),
                file_name="proprietaires.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except ImportError:
            st.button("Excel (non disponible)", disabled=True, use_container_width=True)
    
    # JSON
    with col3:
        json_data = df_display.to_json(orient='records', indent=2, force_ascii=False)
        st.download_button(
            label="JSON",
            data=json_data,
            file_name="proprietaires.json",
            mime="application/json",
            use_container_width=True
        )

def main():
    """Interface principale"""
    
    # Titre et sous-titre
    st.markdown("""
    <div class="title">Extracteur PDF</div>
    <div class="subtitle">Extraction automatique de propriétaires depuis vos documents PDF</div>
    """, unsafe_allow_html=True)
    
    # Zone d'upload
    st.markdown("""
    <div class="upload-area">
        <div class="upload-text">Glissez vos fichiers PDF ici</div>
        <div class="upload-subtext">ou cliquez pour sélectionner</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Upload de fichiers
    uploaded_files = st.file_uploader(
        "Fichiers PDF",
        type="pdf",
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    
    if uploaded_files:
        # Affichage des fichiers sélectionnés
        st.markdown(f"""
        <div class="file-list">
            <strong>{len(uploaded_files)} fichier(s) sélectionné(s)</strong><br>
            {', '.join([f.name for f in uploaded_files])}
        </div>
        """, unsafe_allow_html=True)
        
        # Bouton de traitement
        if st.button("Extraire les propriétaires"):
            # Traitement des fichiers
            results = process_files(uploaded_files)
            
            if results:
                # Stockage des résultats dans la session
                st.session_state.results = results
                st.session_state.processed = True
            else:
                st.session_state.results = []
                st.session_state.processed = True
    
    # Affichage des résultats si disponibles
    if st.session_state.get('processed', False):
        results = st.session_state.get('results', [])
        display_results(results)
        
        # Bouton pour effacer les résultats
        if st.button("Nouvelle extraction"):
            if 'results' in st.session_state:
                del st.session_state.results
            if 'processed' in st.session_state:
                del st.session_state.processed
            st.rerun()
    
    elif not uploaded_files:
        # Instructions d'utilisation
        st.markdown("""
        <div class="instructions">
            <p><strong>Comment utiliser l'extracteur :</strong></p>
            <p>1. Sélectionnez vos fichiers PDF</p>
            <p>2. Cliquez sur "Extraire les propriétaires"</p>
            <p>3. Téléchargez vos résultats au format souhaité</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div class="footer">
        Développé avec l'intelligence artificielle OpenAI GPT-4o<br>
        © 2025 Level up - <a href="https://levelups.fr" target="_blank">levelups.fr</a>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 