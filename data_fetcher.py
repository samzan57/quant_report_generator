# data_fetcher.py
import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Catalogue d'actifs financiers orientés Quant
ASSETS_CATALOG = {
    "actions": {
        "Apple": "AAPL",
        "Microsoft": "MSFT",
        "Google": "GOOGL",
        "Amazon": "AMZN",
        "Tesla": "TSLA",
        "NVIDIA": "NVDA",
        "JPMorgan": "JPM",
        "Goldman Sachs": "GS",
        "BlackRock": "BLK",
        "Visa": "V",
        "General Dynamics": "GD",
        "KLA Corporation": "KLAC",
        "W.W. Grainger": "GWW",
        "NVR": "NVR",
        "SPXL": "SPXL",
        "META": "META",
        "JNJ": "JNJ", 
        "XOM": "XOM", 
        "UNH": "UNH", 
        "HD": "HD", 
        "LILAK": "LILAK", 
        "LILA": "LILA", 
        "JEF": "JEF", 
        "DEO": "DEO", 
        "NVR": "NVR", 
        "FWONK": "FWONK", 
        "LLYVA": "LLYVA", 
        "POOL": "POOL", 
        "LPX": "LPX", 
        "CHTR": "CHTR",
        "LLYVK": "LLYVK",
        "TMUS": "TMUS",
        "ALLY": "ALLY",
        "DPZ": "DPZ",
        "COF": "COF", 
        "AON": "AON",
        "MA": "MA",
        "STZ": "STZ", 
        "SIRI": "SIRI",
        "VRSN": "VRSN", 
        "KR": "KR", 
        "DVA": "DVA", 
        "CB": "CB", 
        "KHC": "KHC", 
        "MCO": "MCO", 
        "ORCL": "ORCL",  
        "OXY": "OXY", 
        "BAC": "BAC", 
        "KO": "KO", 
        "AXP": "AXP",
        "CVX": "CVX",
    },
    "indices": {
        "S&P 500": "^GSPC",
        "NASDAQ": "^IXIC",
        "Dow Jones": "^DJI",
        "CAC 40": "^FCHI",
        "DAX": "^GDAXI",
        "FTSE 100": "^FTSE",
        "Nikkei 225": "^N225",
    },
    "crypto": {
        "Bitcoin": "BTC-USD",
        "Ethereum": "ETH-USD",
        "Solana": "SOL-USD",
        "Ripple": "XRP-USD",
    },
    "etf": {
        "SPY (S&P 500 ETF)": "SPY",
        "QQQ (NASDAQ ETF)": "QQQ",
        "GLD (Gold ETF)": "GLD",
        "TLT (Bonds ETF)": "TLT",
        "VIX (Volatilité)": "^VIX",
    },
    "forex": {
        "EUR/USD": "EURUSD=X",
        "GBP/USD": "GBPUSD=X",
        "USD/JPY": "JPY=X",
        "USD/CHF": "CHF=X",
    },
    "matieres_premieres": {
        "Or": "GC=F",
        "Pétrole WTI": "CL=F",
        "Argent": "SI=F",
        "Gaz Naturel": "NG=F",
    }
}

PERIODS = {
    "1 mois": "1mo",
    "3 mois": "3mo",
    "6 mois": "6mo",
    "1 an": "1y",
    "2 ans": "2y",
    "5 ans": "5y",
    "10 ans": "10y",
    "Max": "max"
}

INTERVALS = {
    "Journalier": "1d",
    "Hebdomadaire": "1wk",
    "Mensuel": "1mo",
    "Horaire": "1h",
}

def fetch_single_asset(ticker, period="1y", interval="1d"):
    """Télécharge les données d'un seul actif"""
    try:
        data = yf.download(ticker, period=period,
                          interval=interval, progress=False,
                          auto_adjust=True)
        if data.empty:
            return None

        # Aplatir les colonnes multi-index
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [col[0] for col in data.columns]

        # Renommer proprement
        data.columns = [str(c).strip() for c in data.columns]
        data.reset_index(inplace=True)

        # Renommer la colonne date
        if 'Date' not in data.columns and 'Datetime' in data.columns:
            data.rename(columns={'Datetime': 'Date'}, inplace=True)

        print(f"  Colonnes : {list(data.columns)}")
        print(f"  Lignes : {len(data)}")
        return data
    except Exception as e:
        print(f"Erreur téléchargement {ticker}: {e}")
        return None

def fetch_multiple_assets(tickers_dict, period="1y", interval="1d"):
    """Télécharge plusieurs actifs et les met dans des feuilles séparées"""
    sheets = {}
    for name, ticker in tickers_dict.items():
        print(f"  Téléchargement : {name} ({ticker})...")
        data = fetch_single_asset(ticker, period, interval)
        if data is not None:
            sheets[name] = data
            print(f"  ✓ {name} : {len(data)} lignes")
        else:
            print(f"  ✗ {name} : échec")
    return sheets

def save_to_excel(sheets, filename):
    """Sauvegarde les données dans un fichier Excel"""
    filepath = os.path.join(DATA_DIR, filename)
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        for sheet_name, df in sheets.items():
            # Nettoyer le nom de feuille (max 31 caractères)
            clean_name = sheet_name[:31].replace('/', '-')
            df.to_excel(writer, sheet_name=clean_name, index=False)
    print(f"\n✅ Données sauvegardées : {filepath}")
    return filepath

def fetch_and_save(selection, period="1y", interval="1d", custom_ticker=None):
    """
    Fonction principale : télécharge et sauvegarde les données
    
    selection: dict {nom: ticker} ou string pour un seul actif
    custom_ticker: ticker personnalisé entré par l'utilisateur
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if custom_ticker:
        # Ticker personnalisé
        name = custom_ticker.upper()
        print(f"\n📡 Téléchargement : {name}...")
        data = fetch_single_asset(custom_ticker, period, interval)
        if data is None:
            raise ValueError(f"Impossible de télécharger {custom_ticker}")
        sheets = {name: data}
        filename = f"{name}_{period}_{timestamp}.xlsx"

    elif isinstance(selection, dict):
        # Plusieurs actifs
        print(f"\n📡 Téléchargement de {len(selection)} actifs...")
        sheets = fetch_multiple_assets(selection, period, interval)
        if not sheets:
            raise ValueError("Aucune donnée téléchargée")
        names = "_".join(list(selection.keys())[:2])
        filename = f"portfolio_{names}_{period}_{timestamp}.xlsx"

    else:
        raise ValueError("Sélection invalide")

    filepath = save_to_excel(sheets, filename)
    return filepath