# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Clé API Groq — renseignée via .env (voir .env.example), jamais en dur ici
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY non défini — renseigne-le dans ton .env (voir .env.example).")

# Modèle Groq à utiliser
GROQ_MODEL = "llama-3.3-70b-versatile"

# Dossier de sortie des rapports
OUTPUT_DIR = "rapports_generés"

# Créer le dossier de sortie s'il n'existe pas
os.makedirs(OUTPUT_DIR, exist_ok=True)