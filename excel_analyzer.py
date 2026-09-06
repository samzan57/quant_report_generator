# excel_analyzer.py
import pandas as pd
import json
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL

client = Groq(api_key=GROQ_API_KEY)

def load_excel(filepath):
    """Charge toutes les feuilles du fichier Excel"""
    xl = pd.ExcelFile(filepath)
    sheets = {}
    for sheet in xl.sheet_names:
        # Lire directement avec header=0 pour garder les colonnes
        df = pd.read_excel(filepath, sheet_name=sheet, header=0)
        sheets[sheet] = df
    return sheets

def sheets_to_text(sheets):
    """Convertit les feuilles Excel en texte lisible par l'IA"""
    text = ""
    for name, df in sheets.items():
        text += f"\n=== Feuille: {name} ===\n"
        text += df.to_string(index=False)
        text += "\n"
    return text[:8000]  # Limite à 8000 caractères pour l'IA

def analyze_structure(filepath):
    """L'IA analyse et comprend la structure du fichier Excel"""
    print("Chargement du fichier Excel...")
    sheets = load_excel(filepath)
    raw_text = sheets_to_text(sheets)

    print("Analyse de la structure par l'IA...")
    prompt = f"""
Tu es un expert en finance de marché et en analyse quantitative.
Voici le contenu brut d'un fichier Excel financier :

{raw_text}

Analyse ce fichier et réponds UNIQUEMENT en JSON avec cette structure exacte :
{{
    "type_donnees": "type principal des données (ex: prix OHLCV, portefeuille, rendements...)",
    "colonnes_detectees": {{
        "date": "nom de la colonne date ou null",
        "open": "nom colonne open ou null",
        "high": "nom colonne high ou null",
        "low": "nom colonne low ou null",
        "close": "nom colonne close ou null",
        "volume": "nom colonne volume ou null",
        "autres": ["liste des autres colonnes importantes"]
    }},
    "actifs_detectes": ["liste des actifs financiers détectés"],
    "periode": "période couverte par les données",
    "qualite_donnees": "bonne / moyenne / mauvaise",
    "problemes_detectes": ["liste des problèmes éventuels"],
    "analyses_recommandees": ["liste des analyses quantitatives recommandées"],
    "resume": "résumé en 2-3 phrases de ce que contient ce fichier"
}}
Réponds UNIQUEMENT avec le JSON, aucun texte avant ou après.
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )

    raw = response.choices[0].message.content.strip()

    # Nettoyer si l'IA ajoute des backticks
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result = json.loads(raw)
    return result, sheets

def clean_and_structure(sheets, analysis):
    """Nettoie et restructure les données"""
    dfs = {}
    for name, df in sheets.items():
        df_clean = df.copy()

        # Convertir les colonnes numériques
        for col in df_clean.columns:
            try:
                df_clean[col] = pd.to_numeric(df_clean[col], errors='ignore')
            except:
                pass

        # Convertir et trier par date
        for col in df_clean.columns:
            if any(k in str(col).lower() for k in ['date', 'time']):
                try:
                    df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
                    df_clean = df_clean.dropna(subset=[col])
                    df_clean = df_clean.sort_values(col).reset_index(drop=True)
                    break
                except:
                    pass

        dfs[name] = df_clean
        print(f"  ✓ '{name}' : {len(df_clean)} lignes, colonnes numériques : {df_clean.select_dtypes(include=['number']).columns.tolist()}")

    return dfs

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        analysis, sheets = analyze_structure(filepath)
        print("\n=== ANALYSE DE L'IA ===")
        print(json.dumps(analysis, indent=2, ensure_ascii=False))
    else:
        print("Usage: python excel_analyzer.py <fichier.xlsx>")