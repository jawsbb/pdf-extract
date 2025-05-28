from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import sys
import uuid
from datetime import datetime
import threading
import time
import json

# Ajouter le répertoire parent au path pour importer pdf_extractor
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pdf_extractor import PDFPropertyExtractor

app = Flask(__name__)
CORS(app)  # Permettre les requêtes cross-origin depuis React

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Stockage en mémoire des tâches (en production, utiliser Redis/DB)
tasks = {}

class TaskStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"

@app.route('/api/health', methods=['GET'])
def health_check():
    """Vérification de l'état de l'API"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """Upload des fichiers PDF et démarrage du traitement"""
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'Aucun fichier fourni'}), 400
        
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'Aucun fichier sélectionné'}), 400
        
        # Vérifier que tous les fichiers sont des PDFs
        pdf_files = []
        for file in files:
            if file and file.filename.lower().endswith('.pdf'):
                pdf_files.append(file)
            else:
                return jsonify({'error': f'Le fichier {file.filename} n\'est pas un PDF'}), 400
        
        # Créer un ID de tâche unique
        task_id = str(uuid.uuid4())
        
        # Sauvegarder les fichiers
        saved_files = []
        for file in pdf_files:
            filename = f"{task_id}_{file.filename}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            saved_files.append(filepath)
        
        # Créer la tâche
        tasks[task_id] = {
            'id': task_id,
            'status': TaskStatus.PENDING,
            'files': saved_files,
            'total_files': len(saved_files),
            'processed_files': 0,
            'created_at': datetime.now().isoformat(),
            'results': [],
            'error': None,
            'output_file': None
        }
        
        # Démarrer le traitement en arrière-plan
        thread = threading.Thread(target=process_pdfs, args=(task_id,))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'task_id': task_id,
            'message': f'Traitement démarré pour {len(saved_files)} fichier(s)',
            'total_files': len(saved_files)
        })
        
    except Exception as e:
        return jsonify({'error': f'Erreur lors de l\'upload: {str(e)}'}), 500

@app.route('/api/status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """Récupérer le statut d'une tâche"""
    if task_id not in tasks:
        return jsonify({'error': 'Tâche non trouvée'}), 404
    
    task = tasks[task_id]
    return jsonify({
        'id': task['id'],
        'status': task['status'],
        'total_files': task['total_files'],
        'processed_files': task['processed_files'],
        'progress': (task['processed_files'] / task['total_files']) * 100 if task['total_files'] > 0 else 0,
        'created_at': task['created_at'],
        'results_count': len(task['results']),
        'error': task['error'],
        'has_output': task['output_file'] is not None
    })

@app.route('/api/download/<task_id>', methods=['GET'])
def download_results(task_id):
    """Télécharger le fichier CSV des résultats"""
    if task_id not in tasks:
        return jsonify({'error': 'Tâche non trouvée'}), 404
    
    task = tasks[task_id]
    if task['status'] != TaskStatus.COMPLETED or not task['output_file']:
        return jsonify({'error': 'Résultats non disponibles'}), 400
    
    if not os.path.exists(task['output_file']):
        return jsonify({'error': 'Fichier de résultats non trouvé'}), 404
    
    return send_file(
        task['output_file'],
        as_attachment=True,
        download_name=f'extraction_results_{task_id}.csv',
        mimetype='text/csv'
    )

@app.route('/api/results/<task_id>', methods=['GET'])
def get_results(task_id):
    """Récupérer les résultats détaillés d'une tâche"""
    if task_id not in tasks:
        return jsonify({'error': 'Tâche non trouvée'}), 404
    
    task = tasks[task_id]
    return jsonify({
        'id': task['id'],
        'status': task['status'],
        'results': task['results'],
        'total_files': task['total_files'],
        'processed_files': task['processed_files'],
        'error': task['error']
    })

def process_pdfs(task_id):
    """Traiter les PDFs en arrière-plan"""
    try:
        task = tasks[task_id]
        task['status'] = TaskStatus.PROCESSING
        
        # Initialiser l'extracteur
        extractor = PDFPropertyExtractor()
        
        all_results = []
        
        for i, pdf_path in enumerate(task['files']):
            try:
                # Traiter le PDF
                results = extractor.extract_from_pdf(pdf_path)
                all_results.extend(results)
                
                # Mettre à jour le progrès
                task['processed_files'] = i + 1
                task['results'] = all_results
                
            except Exception as e:
                print(f"Erreur lors du traitement de {pdf_path}: {e}")
                # Continuer avec les autres fichiers
                task['processed_files'] = i + 1
        
        # Sauvegarder les résultats en CSV
        if all_results:
            output_filename = f"results_{task_id}.csv"
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)
            extractor.save_to_csv(all_results, output_path)
            task['output_file'] = output_path
        
        task['status'] = TaskStatus.COMPLETED
        
        # Nettoyer les fichiers uploadés
        for file_path in task['files']:
            try:
                os.remove(file_path)
            except:
                pass
                
    except Exception as e:
        task['status'] = TaskStatus.ERROR
        task['error'] = str(e)
        print(f"Erreur lors du traitement de la tâche {task_id}: {e}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 