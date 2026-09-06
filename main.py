# main.py
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import os
from data_fetcher import (ASSETS_CATALOG, PERIODS, INTERVALS,
                           fetch_and_save)
from excel_analyzer import analyze_structure, clean_and_structure
from quant_calculator import run_full_analysis
from chart_generator import generate_all_charts
from report_generator import generate_report


class QuantApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Quant Report Generator")
        self.root.geometry("820x680")
        self.root.configure(bg='#0D1117')
        self.root.resizable(False, False)

        self.filepath = None
        self.selected_assets = {}
        self.setup_ui()

    def setup_ui(self):
        # Titre
        tk.Label(self.root, text="QUANT REPORT GENERATOR",
                 font=("Calibri", 22, "bold"),
                 fg='#00D4FF', bg='#0D1117').pack(pady=(20, 2))

        tk.Label(self.root,
                 text="Analyse quantitative automatisée — Powered by Groq AI & Yahoo Finance",
                 font=("Calibri", 10), fg='#8B949E',
                 bg='#0D1117').pack(pady=(0, 15))

        # Notebook (onglets)
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TNotebook", background='#0D1117', borderwidth=0)
        style.configure("TNotebook.Tab", background='#161B22',
                        foreground='#8B949E', padding=[15, 6],
                        font=("Calibri", 10, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", '#00D4FF')],
                  foreground=[("selected", '#0D1117')])

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(padx=20, fill='x')

        # Onglet 1 : Yahoo Finance
        self.tab_yahoo = tk.Frame(self.notebook, bg='#161B22')
        self.notebook.add(self.tab_yahoo, text="📡  Yahoo Finance")
        self.setup_yahoo_tab()

        # Onglet 2 : Fichier Excel local
        self.tab_file = tk.Frame(self.notebook, bg='#161B22')
        self.notebook.add(self.tab_file, text="📂  Fichier Excel Local")
        self.setup_file_tab()

        # Bouton générer
        self.generate_btn = tk.Button(
            self.root,
            text="⚡  GÉNÉRER LE RAPPORT",
            command=self.start_analysis,
            font=("Calibri", 13, "bold"),
            fg='#0D1117', bg='#00D4FF',
            relief='flat', cursor='hand2',
            padx=30, pady=10
        )
        self.generate_btn.pack(pady=12)

        # Barre de progression
        style.configure("TProgressbar", troughcolor='#161B22',
                        background='#00D4FF', thickness=4)
        self.progress = ttk.Progressbar(self.root, mode='indeterminate',
                                        length=780)
        self.progress.pack(padx=20, fill='x')

        # Console log
        log_frame = tk.Frame(self.root, bg='#0D1117')
        log_frame.pack(padx=20, pady=(10, 15), fill='both', expand=True)

        self.log_text = tk.Text(
            log_frame, font=("Consolas", 9),
            fg='#00FF88', bg='#161B22',
            relief='flat', height=10,
            state='disabled',
            highlightbackground='#21262D',
            highlightthickness=1
        )
        self.log_text.pack(side='left', fill='both', expand=True)

        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview,
                                 bg='#161B22')
        scrollbar.pack(side='right', fill='y')
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def setup_yahoo_tab(self):
        """Onglet Yahoo Finance"""
        main_frame = tk.Frame(self.tab_yahoo, bg='#161B22')
        main_frame.pack(padx=15, pady=10, fill='both')

        # Ligne 1 : Catégorie + Actif
        row1 = tk.Frame(main_frame, bg='#161B22')
        row1.pack(fill='x', pady=(0, 8))

        # Catégorie
        tk.Label(row1, text="Catégorie :", font=("Calibri", 10, "bold"),
                 fg='#8B949E', bg='#161B22').pack(side='left', padx=(0, 5))

        self.category_var = tk.StringVar(value="actions")
        categories = list(ASSETS_CATALOG.keys())
        cat_menu = ttk.Combobox(row1, textvariable=self.category_var,
                                values=categories, state='readonly', width=18,
                                font=("Calibri", 10))
        cat_menu.pack(side='left', padx=(0, 20))
        cat_menu.bind("<<ComboboxSelected>>", self.update_assets_list)

        # Actif
        tk.Label(row1, text="Actif :", font=("Calibri", 10, "bold"),
                 fg='#8B949E', bg='#161B22').pack(side='left', padx=(0, 5))

        self.asset_var = tk.StringVar()
        self.asset_menu = ttk.Combobox(row1, textvariable=self.asset_var,
                                       state='readonly', width=22,
                                       font=("Calibri", 10))
        self.asset_menu.pack(side='left', padx=(0, 15))

        add_btn = tk.Button(row1, text="+ Ajouter",
                            command=self.add_asset,
                            font=("Calibri", 9, "bold"),
                            fg='#0D1117', bg='#00D4FF',
                            relief='flat', cursor='hand2',
                            padx=10, pady=3)
        add_btn.pack(side='left')

        # Ligne 2 : Ticker personnalisé
        row2 = tk.Frame(main_frame, bg='#161B22')
        row2.pack(fill='x', pady=(0, 8))

        tk.Label(row2, text="Ticker personnalisé :",
                 font=("Calibri", 10, "bold"),
                 fg='#8B949E', bg='#161B22').pack(side='left', padx=(0, 5))

        self.custom_ticker = tk.Entry(row2, font=("Calibri", 10),
                                      bg='#0D1117', fg='white',
                                      insertbackground='white',
                                      relief='flat', width=15,
                                      highlightbackground='#00D4FF',
                                      highlightthickness=1)
        self.custom_ticker.pack(side='left', padx=(0, 10), ipady=4)
        self.custom_ticker.insert(0, "ex: AAPL, BTC-USD")

        add_custom_btn = tk.Button(row2, text="+ Ajouter",
                                   command=self.add_custom_asset,
                                   font=("Calibri", 9, "bold"),
                                   fg='#0D1117', bg='#00FF88',
                                   relief='flat', cursor='hand2',
                                   padx=10, pady=3)
        add_custom_btn.pack(side='left')

        # Ligne 3 : Période + Intervalle
        row3 = tk.Frame(main_frame, bg='#161B22')
        row3.pack(fill='x', pady=(0, 8))

        tk.Label(row3, text="Période :", font=("Calibri", 10, "bold"),
                 fg='#8B949E', bg='#161B22').pack(side='left', padx=(0, 5))

        self.period_var = tk.StringVar(value="1 an")
        period_menu = ttk.Combobox(row3, textvariable=self.period_var,
                                   values=list(PERIODS.keys()),
                                   state='readonly', width=12,
                                   font=("Calibri", 10))
        period_menu.pack(side='left', padx=(0, 20))

        tk.Label(row3, text="Intervalle :", font=("Calibri", 10, "bold"),
                 fg='#8B949E', bg='#161B22').pack(side='left', padx=(0, 5))

        self.interval_var = tk.StringVar(value="Journalier")
        interval_menu = ttk.Combobox(row3, textvariable=self.interval_var,
                                     values=list(INTERVALS.keys()),
                                     state='readonly', width=12,
                                     font=("Calibri", 10))
        interval_menu.pack(side='left')

        # Liste des actifs sélectionnés
        tk.Label(main_frame, text="Actifs sélectionnés :",
                 font=("Calibri", 10, "bold"),
                 fg='#8B949E', bg='#161B22').pack(anchor='w', pady=(5, 3))

        list_frame = tk.Frame(main_frame, bg='#161B22')
        list_frame.pack(fill='x')

        self.assets_listbox = tk.Listbox(
            list_frame, font=("Consolas", 9),
            fg='#00D4FF', bg='#0D1117',
            relief='flat', height=4,
            selectbackground='#21262D',
            highlightbackground='#21262D',
            highlightthickness=1
        )
        self.assets_listbox.pack(side='left', fill='x', expand=True)

        remove_btn = tk.Button(list_frame, text="✕ Retirer",
                               command=self.remove_asset,
                               font=("Calibri", 9),
                               fg='white', bg='#FF4444',
                               relief='flat', cursor='hand2',
                               padx=8, pady=3)
        remove_btn.pack(side='left', padx=(8, 0), anchor='n')

        # Initialiser la liste d'actifs
        self.update_assets_list()

    def setup_file_tab(self):
        """Onglet fichier Excel local"""
        frame = tk.Frame(self.tab_file, bg='#161B22')
        frame.pack(padx=15, pady=20, fill='x')

        tk.Label(frame,
                 text="Sélectionne un fichier Excel existant sur ton PC",
                 font=("Calibri", 11), fg='#8B949E',
                 bg='#161B22').pack(pady=(0, 15))

        file_row = tk.Frame(frame, bg='#161B22',
                            highlightbackground='#00D4FF',
                            highlightthickness=1)
        file_row.pack(fill='x')

        self.file_label = tk.Label(file_row,
                                   text="Aucun fichier sélectionné",
                                   font=("Calibri", 11),
                                   fg='#8B949E', bg='#161B22')
        self.file_label.pack(side='left', padx=15, pady=12)

        browse_btn = tk.Button(file_row, text="Parcourir",
                               command=self.browse_file,
                               font=("Calibri", 10, "bold"),
                               fg='#0D1117', bg='#00D4FF',
                               relief='flat', cursor='hand2',
                               padx=15, pady=5)
        browse_btn.pack(side='right', padx=10, pady=8)

    def update_assets_list(self, event=None):
        """Met à jour la liste des actifs selon la catégorie"""
        category = self.category_var.get()
        assets = list(ASSETS_CATALOG.get(category, {}).keys())
        self.asset_menu['values'] = assets
        if assets:
            self.asset_var.set(assets[0])

    def add_asset(self):
        """Ajoute un actif depuis le catalogue"""
        category = self.category_var.get()
        asset_name = self.asset_var.get()
        if not asset_name:
            return
        ticker = ASSETS_CATALOG[category][asset_name]
        if asset_name not in self.selected_assets:
            self.selected_assets[asset_name] = ticker
            self.assets_listbox.insert('end', f"  {asset_name} ({ticker})")
            self.log(f"+ Ajouté : {asset_name} ({ticker})")

    def add_custom_asset(self):
        """Ajoute un ticker personnalisé"""
        ticker = self.custom_ticker.get().strip()
        if not ticker or ticker == "ex: AAPL, BTC-USD":
            return
        ticker = ticker.upper()
        if ticker not in self.selected_assets.values():
            self.selected_assets[ticker] = ticker
            self.assets_listbox.insert('end', f"  {ticker}")
            self.log(f"+ Ajouté : {ticker}")
            self.custom_ticker.delete(0, 'end')

    def remove_asset(self):
        """Retire un actif de la sélection"""
        selection = self.assets_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        item = self.assets_listbox.get(idx)
        self.assets_listbox.delete(idx)
        keys = list(self.selected_assets.keys())
        if idx < len(keys):
            del self.selected_assets[keys[idx]]

    def browse_file(self):
        """Sélectionne un fichier Excel local"""
        filepath = filedialog.askopenfilename(
            title="Sélectionner un fichier Excel",
            filetypes=[("Fichiers Excel", "*.xlsx *.xls *.xlsm"),
                       ("Tous les fichiers", "*.*")]
        )
        if filepath:
            self.filepath = filepath
            filename = os.path.basename(filepath)
            self.file_label.config(text=filename, fg='#00D4FF')
            self.log(f"✓ Fichier sélectionné : {filename}")

    def log(self, message):
        """Affiche un message dans la console"""
        self.log_text.config(state='normal')
        self.log_text.insert('end', message + '\n')
        self.log_text.see('end')
        self.log_text.config(state='disabled')
        self.root.update()

    def start_analysis(self):
        """Lance l'analyse"""
        active_tab = self.notebook.index(self.notebook.select())

        if active_tab == 0:
            # Onglet Yahoo Finance
            if not self.selected_assets:
                messagebox.showerror(
                    "Erreur",
                    "Veuillez ajouter au moins un actif financier"
                )
                return
        else:
            # Onglet fichier local
            if not self.filepath:
                messagebox.showerror(
                    "Erreur",
                    "Veuillez sélectionner un fichier Excel"
                )
                return

        self.generate_btn.config(state='disabled')
        self.progress.start(10)
        self.log("\n🚀 Démarrage de l'analyse...")

        thread = threading.Thread(target=self.run_pipeline,
                                  args=(active_tab,))
        thread.daemon = True
        thread.start()

    def run_pipeline(self, active_tab):
        """Pipeline complet d'analyse"""
        try:
            # Étape 0 : Récupération des données si Yahoo Finance
            if active_tab == 0:
                self.log("📡 Étape 0/4 : Téléchargement Yahoo Finance...")
                period = PERIODS[self.period_var.get()]
                interval = INTERVALS[self.interval_var.get()]
                self.filepath = fetch_and_save(
                    self.selected_assets, period, interval
                )
                self.log(f"  ✓ Données sauvegardées dans /data")

            # Étape 1 : Analyse IA
            self.log("🤖 Étape 1/4 : Analyse de la structure par l'IA...")
            analysis, sheets = analyze_structure(self.filepath)
            self.log(f"  ✓ Type : {analysis.get('type_donnees', 'N/A')}")
            self.log(f"  ✓ Actifs : {', '.join(analysis.get('actifs_detectes', []))}")
            self.log(f"  ✓ Période : {analysis.get('periode', 'N/A')}")
            self.log(f"  ✓ Qualité : {analysis.get('qualite_donnees', 'N/A')}")

            # Étape 2 : Calculs quantitatifs
            self.log("\n📊 Étape 2/4 : Calculs quantitatifs...")
            clean_dfs = clean_and_structure(sheets, analysis)
            results = run_full_analysis(clean_dfs, analysis)
            self.log("  ✓ Métriques calculées (Sharpe, VaR, Drawdown...)")
            self.log("  ✓ Indicateurs techniques (RSI, MACD, BB...)")

            # Étape 3 : Graphiques
            self.log("\n📈 Étape 3/4 : Génération des graphiques...")
            chart_paths = generate_all_charts(results, analysis)
            self.log(f"  ✓ {len(chart_paths)} graphiques générés")

            # Étape 4 : Rapport PowerPoint
            self.log("\n📑 Étape 4/4 : Création du rapport PowerPoint...")
            report_path = generate_report(analysis, results, chart_paths)

            self.progress.stop()
            self.log(f"\n✅ RAPPORT GÉNÉRÉ AVEC SUCCÈS !")
            self.log(f"📁 Emplacement : {report_path}")

            self.root.after(0, lambda: messagebox.showinfo(
                "Succès !",
                f"Rapport généré avec succès !\n\nEmplacement :\n{report_path}"
            ))

        except Exception as e:
            self.progress.stop()
            self.log(f"\n❌ Erreur : {str(e)}")
            self.root.after(0, lambda: messagebox.showerror(
                "Erreur", f"Une erreur s'est produite :\n{str(e)}"
            ))
        finally:
            self.root.after(0, lambda: self.generate_btn.config(
                state='normal'))


if __name__ == "__main__":
    root = tk.Tk()
    app = QuantApp(root)
    root.mainloop()