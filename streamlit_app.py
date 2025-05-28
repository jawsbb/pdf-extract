import streamlit as st
import pandas as pd
import sys
import os
import tempfile
import zipfile
from io import BytesIO
import time

# Configuration de la page
st.set_page_config(
    page_title="Extracteur PDF - Propriétaires",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import du module principal
sys.path.append('.')
try:
    from pdf_extractor import PDFPropertyExtractor
except ImportError:
    st.error("❌ Module pdf_extractor non trouvé. Assurez-vous que le fichier pdf_extractor.py est présent.")
    st.stop()

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .upload-section {
        border: 2px dashed #667eea;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
    }
    .results-section {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

def generate_demo_results(filename):
    """Générer des résultats de démonstration"""
    import random
    
    demo_data = [
        {
            "nom": "MARTIN",
            "prenom": "Jean",
            "adresse": "123 Rue de la Paix, 75001 Paris",
            "code_postal": "75001",
            "ville": "Paris",
            "telephone": "01.23.45.67.89",
            "email": "jean.martin@email.com",
            "id_parcellaire": "75001AB0123",
            "source_fichier": filename
        },
        {
            "nom": "DUBOIS",
            "prenom": "Marie",
            "adresse": "456 Avenue des Champs, 69000 Lyon",
            "code_postal": "69000",
            "ville": "Lyon",
            "telephone": "04.56.78.90.12",
            "email": "marie.dubois@email.com",
            "id_parcellaire": "69000CD0456",
            "source_fichier": filename
        }
    ]
    
    # Retourner 1-2 résultats aléatoirement
    return random.sample(demo_data, random.randint(1, 2))

def display_results(results, demo_mode):
    """Afficher les résultats finaux"""
    
    if not results:
        st.warning("⚠️ Aucun propriétaire trouvé dans les fichiers traités")
        return
    
    st.header("📊 Résultats de l'extraction")
    
    # Métriques
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Propriétaires trouvés", len(results))
    with col2:
        unique_files = len(set(r.get('source_fichier', '') for r in results))
        st.metric("Fichiers avec résultats", unique_files)
    with col3:
        unique_cities = len(set(r.get('ville', '') for r in results if r.get('ville')))
        st.metric("Villes différentes", unique_cities)
    with col4:
        with_email = sum(1 for r in results if r.get('email'))
        st.metric("Avec email", with_email)
    
    # Tableau des résultats
    df = pd.DataFrame(results)
    
    # Réorganiser les colonnes
    column_order = ['nom', 'prenom', 'adresse', 'ville', 'code_postal', 'telephone', 'email', 'id_parcellaire', 'source_fichier']
    df = df.reindex(columns=[col for col in column_order if col in df.columns])
    
    st.subheader("📋 Tableau détaillé")
    st.dataframe(df, use_container_width=True)
    
    # Analyses
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Répartition par ville")
        if 'ville' in df.columns:
            city_counts = df['ville'].value_counts()
            st.bar_chart(city_counts)
    
    with col2:
        st.subheader("📁 Répartition par fichier")
        if 'source_fichier' in df.columns:
            file_counts = df['source_fichier'].value_counts()
            st.bar_chart(file_counts)
    
    # Export
    st.subheader("📥 Export des données")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # CSV
        csv = df.to_csv(index=False)
        st.download_button(
            label="📄 Télécharger CSV",
            data=csv,
            file_name=f"extraction_proprietaires_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # Excel
        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_buffer.seek(0)
        
        st.download_button(
            label="📊 Télécharger Excel",
            data=excel_buffer.getvalue(),
            file_name=f"extraction_proprietaires_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    with col3:
        # JSON
        json_data = df.to_json(orient='records', indent=2)
        st.download_button(
            label="🔧 Télécharger JSON",
            data=json_data,
            file_name=f"extraction_proprietaires_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
    
    if demo_mode:
        st.info("🎭 **Mode démo** : Ces résultats sont simulés. Configurez votre clé API OpenAI pour un traitement réel.")

def process_files(files, demo_mode, batch_size, include_debug):
    """Traiter les fichiers PDF"""
    
    # Initialisation
    if not demo_mode:
        try:
            extractor = PDFPropertyExtractor()
        except Exception as e:
            st.error(f"❌ Erreur d'initialisation : {e}")
            return
    
    all_results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Conteneur pour les résultats en temps réel
    results_container = st.container()
    
    # Traitement par lots
    for batch_start in range(0, len(files), batch_size):
        batch_files = files[batch_start:batch_start + batch_size]
        
        for i, file in enumerate(batch_files):
            current_file_index = batch_start + i
            progress = (current_file_index + 1) / len(files)
            
            status_text.text(f"📄 Traitement de {file.name}... ({current_file_index + 1}/{len(files)})")
            progress_bar.progress(progress)
            
            try:
                if demo_mode:
                    # Simulation pour le mode démo
                    time.sleep(1)  # Simulation du temps de traitement
                    results = generate_demo_results(file.name)
                else:
                    # Traitement réel
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                        tmp_file.write(file.getbuffer())
                        tmp_file_path = tmp_file.name
                    
                    results = extractor.extract_from_pdf(tmp_file_path)
                    os.unlink(tmp_file_path)  # Nettoyer le fichier temporaire
                
                all_results.extend(results)
                
                # Affichage en temps réel
                if results:
                    with results_container:
                        st.success(f"✅ {file.name}: {len(results)} propriétaire(s) trouvé(s)")
                        if include_debug:
                            with st.expander(f"Détails - {file.name}"):
                                st.json(results)
                else:
                    with results_container:
                        st.warning(f"⚠️ {file.name}: Aucun propriétaire trouvé")
                        
            except Exception as e:
                with results_container:
                    st.error(f"❌ Erreur avec {file.name}: {str(e)}")
                if include_debug:
                    st.exception(e)
    
    # Finalisation
    progress_bar.progress(1.0)
    status_text.text("✅ Traitement terminé !")
    
    # Mise à jour des statistiques
    st.session_state.total_processed += len(files)
    st.session_state.total_extracted += len(all_results)
    
    # Affichage des résultats finaux
    display_results(all_results, demo_mode)

# Header principal
st.markdown("""
<div class="main-header">
    <h1>🏠 Extracteur de Propriétaires PDF</h1>
    <p>Extrayez automatiquement les informations de propriétaires depuis vos documents PDF</p>
</div>
""", unsafe_allow_html=True)

# Sidebar avec informations
with st.sidebar:
    st.header("ℹ️ Informations")
    st.markdown("""
    **Fonctionnalités :**
    - ✅ Upload multiple de PDFs
    - 🤖 Extraction IA automatique
    - 📊 Visualisation des résultats
    - 📥 Export CSV
    - 🔄 Traitement en temps réel
    
    **Formats supportés :**
    - PDF uniquement
    - Taille max : 200MB par fichier
    """)
    
    st.header("🔧 Configuration")
    
    # Mode démo
    demo_mode = st.checkbox("Mode démo (sans API OpenAI)", value=True)
    
    if not demo_mode:
        api_key = st.text_input("Clé API OpenAI", type="password", help="Votre clé API OpenAI pour l'extraction réelle")
        if api_key:
            os.environ['OPENAI_API_KEY'] = api_key
    
    st.header("📈 Statistiques")
    if 'total_processed' not in st.session_state:
        st.session_state.total_processed = 0
    if 'total_extracted' not in st.session_state:
        st.session_state.total_extracted = 0
    
    st.metric("Fichiers traités", st.session_state.total_processed)
    st.metric("Propriétaires extraits", st.session_state.total_extracted)

# Section principale
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📁 Upload des fichiers PDF")
    
    uploaded_files = st.file_uploader(
        "Choisissez vos fichiers PDF",
        type="pdf",
        accept_multiple_files=True,
        help="Vous pouvez sélectionner plusieurs fichiers PDF à la fois"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} fichier(s) sélectionné(s)")
        
        # Affichage des fichiers
        with st.expander("📋 Détails des fichiers", expanded=True):
            for i, file in enumerate(uploaded_files):
                col_file, col_size = st.columns([3, 1])
                with col_file:
                    st.write(f"📄 {file.name}")
                with col_size:
                    st.write(f"{file.size / 1024 / 1024:.2f} MB")

with col2:
    st.header("⚙️ Options de traitement")
    
    if uploaded_files:
        # Options avancées
        with st.expander("🔧 Paramètres avancés"):
            batch_size = st.slider("Taille des lots", 1, 10, 5, help="Nombre de fichiers traités simultanément")
            include_debug = st.checkbox("Inclure les logs de debug", help="Afficher les détails du traitement")
        
        # Bouton de traitement
        if st.button("🚀 Lancer l'extraction", type="primary", use_container_width=True):
            if demo_mode:
                st.info("🎭 Mode démo activé - Simulation du traitement")
            
            # Traitement des fichiers
            process_files(uploaded_files, demo_mode, batch_size, include_debug)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    🏠 Extracteur de Propriétaires PDF - Développé avec ❤️ et Streamlit<br>
    <small>Version 1.0 - Traitement automatisé par IA</small>
</div>
""", unsafe_allow_html=True) 