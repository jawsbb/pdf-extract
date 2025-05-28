#!/usr/bin/env python3
"""
Interface graphique pour l'extracteur PDF de propriétaires.
Permet de tester facilement le système avec une interface utilisateur simple.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import sys
from pathlib import Path
import pandas as pd
from PIL import Image, ImageTk
import io

# Import du module principal
try:
    from pdf_extractor import PDFPropertyExtractor
    from demo_complete import DemoExtractor
except ImportError as e:
    print(f"Erreur d'import: {e}")
    sys.exit(1)

class PDFExtractorGUI:
    """Interface graphique pour l'extracteur PDF."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🏠 Extracteur PDF de Propriétaires")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')
        
        # Variables
        self.selected_files = []
        self.api_key = tk.StringVar()
        self.demo_mode = tk.BooleanVar(value=True)
        self.processing = False
        
        self.setup_ui()
        self.load_config()
    
    def setup_ui(self):
        """Configure l'interface utilisateur."""
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configuration de la grille
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Titre
        title_label = ttk.Label(main_frame, text="🏠 Extracteur PDF de Propriétaires", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Section Configuration
        config_frame = ttk.LabelFrame(main_frame, text="⚙️ Configuration", padding="10")
        config_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)
        
        # Mode démo
        ttk.Checkbutton(config_frame, text="Mode Démo (simulation sans API)", 
                       variable=self.demo_mode, command=self.toggle_demo_mode).grid(
                       row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Clé API
        ttk.Label(config_frame, text="Clé API OpenAI:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        self.api_entry = ttk.Entry(config_frame, textvariable=self.api_key, show="*", width=50)
        self.api_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Button(config_frame, text="💾 Sauvegarder", 
                  command=self.save_config).grid(row=1, column=2)
        
        # Section Fichiers
        files_frame = ttk.LabelFrame(main_frame, text="📁 Fichiers PDF", padding="10")
        files_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        files_frame.columnconfigure(0, weight=1)
        
        # Boutons de fichiers
        buttons_frame = ttk.Frame(files_frame)
        buttons_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(buttons_frame, text="📂 Sélectionner PDFs", 
                  command=self.select_files).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(buttons_frame, text="🧪 Utiliser PDFs de test", 
                  command=self.use_test_files).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(buttons_frame, text="🗑️ Effacer", 
                  command=self.clear_files).pack(side=tk.LEFT)
        
        # Liste des fichiers
        self.files_listbox = tk.Listbox(files_frame, height=4)
        self.files_listbox.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Scrollbar pour la liste
        files_scrollbar = ttk.Scrollbar(files_frame, orient=tk.VERTICAL, command=self.files_listbox.yview)
        files_scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.files_listbox.configure(yscrollcommand=files_scrollbar.set)
        
        # Section Traitement
        process_frame = ttk.LabelFrame(main_frame, text="🚀 Traitement", padding="10")
        process_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Bouton de traitement
        self.process_button = ttk.Button(process_frame, text="🚀 Lancer l'extraction", 
                                        command=self.start_processing, style='Accent.TButton')
        self.process_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Barre de progression
        self.progress = ttk.Progressbar(process_frame, mode='indeterminate')
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Statut
        self.status_label = ttk.Label(process_frame, text="Prêt")
        self.status_label.pack(side=tk.RIGHT)
        
        # Section Résultats
        results_frame = ttk.LabelFrame(main_frame, text="📊 Résultats", padding="10")
        results_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Zone de texte pour les logs
        self.log_text = scrolledtext.ScrolledText(results_frame, height=10, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Boutons de résultats
        results_buttons = ttk.Frame(results_frame)
        results_buttons.grid(row=1, column=0, sticky=tk.W)
        
        ttk.Button(results_buttons, text="📂 Ouvrir dossier output", 
                  command=self.open_output_folder).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(results_buttons, text="📄 Voir CSV", 
                  command=self.view_csv).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(results_buttons, text="🗑️ Effacer logs", 
                  command=self.clear_logs).pack(side=tk.LEFT)
        
        # Initialiser l'état
        self.toggle_demo_mode()
    
    def toggle_demo_mode(self):
        """Active/désactive le mode démo."""
        if self.demo_mode.get():
            self.api_entry.configure(state='disabled')
            self.log("Mode DÉMO activé - Simulation sans API")
        else:
            self.api_entry.configure(state='normal')
            self.log("Mode RÉEL activé - API OpenAI requise")
    
    def load_config(self):
        """Charge la configuration depuis le fichier .env."""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.getenv('OPENAI_API_KEY', '')
            if api_key and api_key != 'your_openai_api_key_here':
                self.api_key.set(api_key)
                self.demo_mode.set(False)
                self.toggle_demo_mode()
        except Exception as e:
            self.log(f"Impossible de charger la config: {e}")
    
    def save_config(self):
        """Sauvegarde la clé API dans le fichier .env."""
        try:
            env_content = f"OPENAI_API_KEY={self.api_key.get()}\n"
            env_content += "DEFAULT_SECTION=A\n"
            env_content += "DEFAULT_PLAN_NUMBER=123\n"
            
            with open('.env', 'w') as f:
                f.write(env_content)
            
            messagebox.showinfo("Succès", "Configuration sauvegardée dans .env")
            self.log("Configuration sauvegardée")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de sauvegarder: {e}")
    
    def select_files(self):
        """Sélectionne des fichiers PDF."""
        files = filedialog.askopenfilenames(
            title="Sélectionner des fichiers PDF",
            filetypes=[("Fichiers PDF", "*.pdf"), ("Tous les fichiers", "*.*")]
        )
        
        if files:
            self.selected_files = list(files)
            self.update_files_list()
            self.log(f"{len(files)} fichier(s) sélectionné(s)")
    
    def use_test_files(self):
        """Utilise les fichiers PDF de test."""
        input_dir = Path("input")
        if input_dir.exists():
            test_files = list(input_dir.glob("*.pdf"))
            if test_files:
                self.selected_files = [str(f) for f in test_files]
                self.update_files_list()
                self.log(f"{len(test_files)} fichier(s) de test chargé(s)")
            else:
                messagebox.showwarning("Attention", "Aucun fichier PDF trouvé dans input/")
        else:
            messagebox.showwarning("Attention", "Dossier input/ non trouvé")
    
    def clear_files(self):
        """Efface la liste des fichiers."""
        self.selected_files = []
        self.update_files_list()
        self.log("Liste des fichiers effacée")
    
    def update_files_list(self):
        """Met à jour l'affichage de la liste des fichiers."""
        self.files_listbox.delete(0, tk.END)
        for file_path in self.selected_files:
            filename = Path(file_path).name
            self.files_listbox.insert(tk.END, filename)
    
    def log(self, message):
        """Ajoute un message aux logs."""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_logs(self):
        """Efface les logs."""
        self.log_text.delete(1.0, tk.END)
    
    def start_processing(self):
        """Lance le traitement en arrière-plan."""
        if self.processing:
            return
        
        if not self.selected_files:
            messagebox.showwarning("Attention", "Veuillez sélectionner des fichiers PDF")
            return
        
        if not self.demo_mode.get() and not self.api_key.get():
            messagebox.showwarning("Attention", "Veuillez entrer votre clé API OpenAI")
            return
        
        # Lancer le traitement dans un thread séparé
        self.processing = True
        self.process_button.configure(state='disabled', text="⏳ Traitement en cours...")
        self.progress.start()
        
        thread = threading.Thread(target=self.process_files)
        thread.daemon = True
        thread.start()
    
    def process_files(self):
        """Traite les fichiers PDF."""
        try:
            self.log("🚀 Démarrage du traitement...")
            
            # Copier les fichiers dans input/ si nécessaire
            input_dir = Path("input")
            input_dir.mkdir(exist_ok=True)
            
            copied_files = []
            for file_path in self.selected_files:
                src_path = Path(file_path)
                dst_path = input_dir / src_path.name
                
                if src_path != dst_path:
                    import shutil
                    shutil.copy2(src_path, dst_path)
                    self.log(f"📄 Copié: {src_path.name}")
                
                copied_files.append(dst_path)
            
            # Créer l'extracteur
            if self.demo_mode.get():
                self.log("🤖 Mode DÉMO - Simulation activée")
                extractor = DemoExtractor()
            else:
                self.log("🔑 Mode RÉEL - Utilisation de l'API OpenAI")
                extractor = PDFPropertyExtractor(self.api_key.get())
            
            # Traitement
            self.log("⚙️ Traitement des fichiers...")
            
            # Rediriger les logs de l'extracteur vers l'interface
            import logging
            
            class GUILogHandler(logging.Handler):
                def __init__(self, gui):
                    super().__init__()
                    self.gui = gui
                
                def emit(self, record):
                    msg = self.format(record)
                    # Nettoyer les emojis problématiques pour Windows
                    msg = msg.replace('🚀', '[START]').replace('✅', '[OK]').replace('❌', '[ERROR]')
                    msg = msg.replace('🔄', '[PROCESS]').replace('📊', '[EXPORT]').replace('📈', '[STATS]')
                    self.gui.log(msg)
            
            # Ajouter le handler GUI
            gui_handler = GUILogHandler(self)
            logging.getLogger('pdf_extractor').addHandler(gui_handler)
            logging.getLogger('demo_complete').addHandler(gui_handler)
            
            # Lancer l'extraction
            extractor.run()
            
            self.log("✅ Traitement terminé avec succès!")
            
            # Afficher les résultats
            self.show_results()
            
        except Exception as e:
            self.log(f"❌ Erreur: {str(e)}")
            messagebox.showerror("Erreur", f"Erreur lors du traitement:\n{str(e)}")
        
        finally:
            # Réactiver l'interface
            self.root.after(0, self.finish_processing)
    
    def finish_processing(self):
        """Termine le traitement et réactive l'interface."""
        self.processing = False
        self.process_button.configure(state='normal', text="🚀 Lancer l'extraction")
        self.progress.stop()
        self.status_label.configure(text="Terminé")
    
    def show_results(self):
        """Affiche un résumé des résultats."""
        output_file = Path("output/output.csv")
        if output_file.exists():
            try:
                df = pd.read_csv(output_file)
                self.log(f"📊 Résultats: {len(df)} propriétaire(s) dans {df['Fichier source'].nunique()} fichier(s)")
                self.log(f"📁 Fichier CSV: {output_file}")
            except Exception as e:
                self.log(f"Erreur lecture CSV: {e}")
        else:
            self.log("❌ Aucun fichier de résultat généré")
    
    def open_output_folder(self):
        """Ouvre le dossier output."""
        output_dir = Path("output")
        if output_dir.exists():
            if sys.platform == "win32":
                os.startfile(output_dir)
            elif sys.platform == "darwin":
                os.system(f"open {output_dir}")
            else:
                os.system(f"xdg-open {output_dir}")
        else:
            messagebox.showwarning("Attention", "Dossier output/ non trouvé")
    
    def view_csv(self):
        """Affiche le contenu du CSV dans une nouvelle fenêtre."""
        output_file = Path("output/output.csv")
        if not output_file.exists():
            messagebox.showwarning("Attention", "Aucun fichier CSV trouvé")
            return
        
        try:
            df = pd.read_csv(output_file)
            
            # Nouvelle fenêtre
            csv_window = tk.Toplevel(self.root)
            csv_window.title("📄 Résultats CSV")
            csv_window.geometry("1000x400")
            
            # Treeview pour afficher le tableau
            tree_frame = ttk.Frame(csv_window, padding="10")
            tree_frame.pack(fill=tk.BOTH, expand=True)
            
            tree = ttk.Treeview(tree_frame, columns=list(df.columns), show='headings')
            
            # Configurer les colonnes
            for col in df.columns:
                tree.heading(col, text=col)
                tree.column(col, width=100)
            
            # Ajouter les données
            for _, row in df.iterrows():
                tree.insert('', tk.END, values=list(row))
            
            # Scrollbars
            v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
            h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=tree.xview)
            tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
            
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'afficher le CSV:\n{str(e)}")

def main():
    """Lance l'interface graphique."""
    root = tk.Tk()
    app = PDFExtractorGUI(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Interface fermée par l'utilisateur")

if __name__ == "__main__":
    main() 