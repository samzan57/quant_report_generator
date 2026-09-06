# modules/black_scholes.py
import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq
import pandas as pd

# ── FORMULE BLACK-SCHOLES ─────────────────────────────────────

def d1(S, K, T, r, sigma):
    """
    Calcule d1 dans la formule Black-Scholes
    S : Prix actuel de l'actif
    K : Prix d'exercice (Strike)
    T : Temps jusqu'à maturité (en années)
    r : Taux sans risque
    sigma : Volatilité
    """
    return (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))

def d2(S, K, T, r, sigma):
    """Calcule d2 dans la formule Black-Scholes"""
    return d1(S, K, T, r, sigma) - sigma * np.sqrt(T)

def black_scholes_call(S, K, T, r, sigma):
    """
    Prix d'un Call européen par Black-Scholes
    C = S*N(d1) - K*e^(-rT)*N(d2)
    """
    if T <= 0:
        return max(S - K, 0)
    _d1 = d1(S, K, T, r, sigma)
    _d2 = d2(S, K, T, r, sigma)
    price = S * norm.cdf(_d1) - K * np.exp(-r * T) * norm.cdf(_d2)
    return float(price)

def black_scholes_put(S, K, T, r, sigma):
    """
    Prix d'un Put européen par Black-Scholes
    P = K*e^(-rT)*N(-d2) - S*N(-d1)
    """
    if T <= 0:
        return max(K - S, 0)
    _d1 = d1(S, K, T, r, sigma)
    _d2 = d2(S, K, T, r, sigma)
    price = K * np.exp(-r * T) * norm.cdf(-_d2) - S * norm.cdf(-_d1)
    return float(price)

def put_call_parity_check(S, K, T, r, sigma):
    """
    Vérifie la parité Put-Call :
    C - P = S - K*e^(-rT)
    """
    call = black_scholes_call(S, K, T, r, sigma)
    put = black_scholes_put(S, K, T, r, sigma)
    lhs = call - put
    rhs = S - K * np.exp(-r * T)
    error = abs(lhs - rhs)
    return {
        'call': round(call, 4),
        'put': round(put, 4),
        'lhs_C_minus_P': round(lhs, 4),
        'rhs_S_minus_PV_K': round(rhs, 4),
        'erreur': round(error, 8),
        'parite_verifiee': error < 1e-6
    }

# ── LES GREEKS ────────────────────────────────────────────────

def delta(S, K, T, r, sigma, option_type='call'):
    """
    Delta : Sensibilité du prix par rapport au prix de l'actif
    Delta Call = N(d1)
    Delta Put  = N(d1) - 1
    """
    if T <= 0:
        if option_type == 'call':
            return 1.0 if S > K else 0.0
        else:
            return -1.0 if S < K else 0.0
    _d1 = d1(S, K, T, r, sigma)
    if option_type == 'call':
        return float(norm.cdf(_d1))
    else:
        return float(norm.cdf(_d1) - 1)

def gamma(S, K, T, r, sigma):
    """
    Gamma : Sensibilité du Delta par rapport au prix de l'actif
    Gamma = N'(d1) / (S * sigma * sqrt(T))
    Identique pour Call et Put
    """
    if T <= 0:
        return 0.0
    _d1 = d1(S, K, T, r, sigma)
    return float(norm.pdf(_d1) / (S * sigma * np.sqrt(T)))

def vega(S, K, T, r, sigma):
    """
    Vega : Sensibilité par rapport à la volatilité
    Vega = S * N'(d1) * sqrt(T)
    Exprimé pour 1% de changement de volatilité
    Identique pour Call et Put
    """
    if T <= 0:
        return 0.0
    _d1 = d1(S, K, T, r, sigma)
    return float(S * norm.pdf(_d1) * np.sqrt(T) / 100)

def theta(S, K, T, r, sigma, option_type='call'):
    """
    Theta : Sensibilité par rapport au temps (time decay)
    Exprimé par jour calendaire
    """
    if T <= 0:
        return 0.0
    _d1 = d1(S, K, T, r, sigma)
    _d2 = d2(S, K, T, r, sigma)

    term1 = -(S * norm.pdf(_d1) * sigma) / (2 * np.sqrt(T))

    if option_type == 'call':
        term2 = -r * K * np.exp(-r * T) * norm.cdf(_d2)
        return float((term1 + term2) / 365)
    else:
        term2 = r * K * np.exp(-r * T) * norm.cdf(-_d2)
        return float((term1 + term2) / 365)

def rho(S, K, T, r, sigma, option_type='call'):
    """
    Rho : Sensibilité par rapport au taux sans risque
    Exprimé pour 1% de changement de taux
    """
    if T <= 0:
        return 0.0
    _d2 = d2(S, K, T, r, sigma)

    if option_type == 'call':
        return float(K * T * np.exp(-r * T) * norm.cdf(_d2) / 100)
    else:
        return float(-K * T * np.exp(-r * T) * norm.cdf(-_d2) / 100)

def vanna(S, K, T, r, sigma):
    """
    Vanna : Sensibilité du Delta par rapport à la volatilité
    Vanna = -N'(d1) * d2 / sigma
    """
    if T <= 0:
        return 0.0
    _d1 = d1(S, K, T, r, sigma)
    _d2 = d2(S, K, T, r, sigma)
    return float(-norm.pdf(_d1) * _d2 / sigma)

def volga(S, K, T, r, sigma):
    """
    Volga (Vomma) : Sensibilité du Vega par rapport à la volatilité
    Volga = Vega * d1 * d2 / sigma
    """
    if T <= 0:
        return 0.0
    _d1 = d1(S, K, T, r, sigma)
    _d2 = d2(S, K, T, r, sigma)
    _vega = vega(S, K, T, r, sigma) * 100
    return float(_vega * _d1 * _d2 / sigma)

def compute_all_greeks(S, K, T, r, sigma, option_type='call'):
    """Calcule tous les Greeks pour une option"""
    price = (black_scholes_call(S, K, T, r, sigma)
             if option_type == 'call'
             else black_scholes_put(S, K, T, r, sigma))

    moneyness = S / K
    if moneyness > 1.02:
        moneyness_label = 'In The Money (ITM)'
    elif moneyness < 0.98:
        moneyness_label = 'Out of The Money (OTM)'
    else:
        moneyness_label = 'At The Money (ATM)'

    return {
        'type': option_type.upper(),
        'prix': round(price, 4),
        'moneyness': round(moneyness, 4),
        'moneyness_label': moneyness_label,
        'delta': round(delta(S, K, T, r, sigma, option_type), 4),
        'gamma': round(gamma(S, K, T, r, sigma), 6),
        'vega': round(vega(S, K, T, r, sigma), 4),
        'theta': round(theta(S, K, T, r, sigma, option_type), 4),
        'rho': round(rho(S, K, T, r, sigma, option_type), 4),
        'vanna': round(vanna(S, K, T, r, sigma), 6),
        'volga': round(volga(S, K, T, r, sigma), 6),
        'parametres': {
            'S': S, 'K': K, 'T': T,
            'r': r, 'sigma': sigma
        }
    }

# ── VOLATILITÉ IMPLICITE ──────────────────────────────────────

def implied_volatility(market_price, S, K, T, r,
                       option_type='call', precision=1e-6):
    """
    Calcule la volatilité implicite par inversion numérique
    de Black-Scholes (méthode de Brent)
    """
    if T <= 0:
        return None

    intrinsic = max(S - K, 0) if option_type == 'call' else max(K - S, 0)
    if market_price <= intrinsic:
        return None

    def objective(sigma):
        if option_type == 'call':
            return black_scholes_call(S, K, T, r, sigma) - market_price
        else:
            return black_scholes_put(S, K, T, r, sigma) - market_price

    try:
        iv = brentq(objective, 1e-6, 10.0, xtol=precision)
        return float(iv)
    except:
        return None

def implied_volatility_surface(S, strikes, maturities, r,
                                option_type='call',
                                vol_base=0.20):
    """
    Génère une surface de volatilité implicite simulée
    avec smile et term structure
    """
    surface = []

    for T in maturities:
        row = []
        for K in strikes:
            moneyness = np.log(S / K)

            # Smile de volatilité (courbe en U)
            smile = vol_base + 0.5 * moneyness ** 2

            # Term structure (volatilité augmente avec le temps)
            term = smile * (1 + 0.1 * np.sqrt(T))

            # Skew (volatilité plus élevée pour les puts OTM)
            skew = term - 0.1 * moneyness

            vol = max(skew, 0.01)
            row.append(round(vol, 4))
        surface.append(row)

    return pd.DataFrame(
        surface,
        index=[f'{int(T*365)}j' for T in maturities],
        columns=[f'K={k:.0f}' for k in strikes]
    )

# ── ANALYSE COMPLÈTE D'UNE OPTION ────────────────────────────

def analyze_option(S, K, T, r, sigma, option_type='call'):
    """
    Analyse complète d'une option Black-Scholes
    avec interprétation des Greeks
    """
    greeks = compute_all_greeks(S, K, T, r, sigma, option_type)
    parity = put_call_parity_check(S, K, T, r, sigma)

    # Interprétations
    d = greeks['delta']
    g = greeks['gamma']
    v = greeks['vega']
    th = greeks['theta']

    interpretations = {
        'delta': (
            f"Pour +1€ sur le sous-jacent, "
            f"l'option gagne {abs(d):.4f}€"
        ),
        'gamma': (
            f"Le Delta change de {g:.6f} "
            f"pour chaque +1€ sur le sous-jacent"
        ),
        'vega': (
            f"Pour +1% de volatilité, "
            f"l'option gagne {abs(v):.4f}€"
        ),
        'theta': (
            f"L'option perd {abs(th):.4f}€ "
            f"chaque jour qui passe (time decay)"
        ),
        'rho': (
            f"Pour +1% de taux, "
            f"l'option {'gagne' if option_type == 'call' else 'perd'} "
            f"{abs(greeks['rho']):.4f}€"
        ),
    }

    # Probabilité d'exercice (approximation)
    _d2 = d2(S, K, T, r, sigma)
    prob_exercise = float(norm.cdf(_d2) if option_type == 'call'
                          else norm.cdf(-_d2))

    return {
        'greeks': greeks,
        'parity': parity,
        'interpretations': interpretations,
        'prob_exercise': round(prob_exercise * 100, 2),
        'break_even': round(
            S + greeks['prix'] if option_type == 'call'
            else S - greeks['prix'], 4
        ),
    }

def run_bs_analysis(prices, risk_free_rate=0.02):
    """
    Lance l'analyse Black-Scholes sur un actif réel
    en générant automatiquement plusieurs options
    """
    S = float(prices.iloc[-1])
    sigma = float(prices.pct_change().dropna().std() * np.sqrt(252))
    r = risk_free_rate

    # Générer des strikes autour du prix actuel
    strikes = [
        round(S * 0.80, 2),  # OTM Put / ITM Call
        round(S * 0.90, 2),  # OTM Put / ITM Call
        round(S * 0.95, 2),  # Légèrement OTM
        round(S * 1.00, 2),  # ATM
        round(S * 1.05, 2),  # Légèrement ITM
        round(S * 1.10, 2),  # OTM Call / ITM Put
        round(S * 1.20, 2),  # OTM Call / ITM Put
    ]

    # Maturités : 1 mois, 3 mois, 6 mois, 1 an
    maturities = {
        '1 mois': 1/12,
        '3 mois': 3/12,
        '6 mois': 6/12,
        '1 an': 1.0,
    }

    results = {
        'parametres': {
            'S': S,
            'sigma': round(sigma * 100, 2),
            'r': round(r * 100, 2),
        },
        'options': {},
        'surface_vol': None,
    }

    # Analyser ATM Call et Put pour chaque maturité
    print(f"    Sous-jacent : {S:.2f} | "
          f"Vol : {sigma*100:.1f}% | Taux : {r*100:.1f}%")

    for mat_name, T in maturities.items():
        K = round(S, 2)  # ATM
        call = analyze_option(S, K, T, r, sigma, 'call')
        put = analyze_option(S, K, T, r, sigma, 'put')

        results['options'][mat_name] = {
            'call': call,
            'put': put,
            'K': K,
            'T': T,
        }
        print(f"    {mat_name} ATM → "
              f"Call: {call['greeks']['prix']:.4f} | "
              f"Put: {put['greeks']['prix']:.4f} | "
              f"Delta Call: {call['greeks']['delta']:.4f}")

    # Surface de volatilité
    results['surface_vol'] = implied_volatility_surface(
        S, strikes,
        [1/12, 3/12, 6/12, 1.0],
        r, vol_base=sigma
    )

    # Analyse complète pour ATM 3 mois
    results['analyse_principale'] = {
        'call': analyze_option(S, round(S, 2), 3/12, r, sigma, 'call'),
        'put': analyze_option(S, round(S, 2), 3/12, r, sigma, 'put'),
    }

    return results