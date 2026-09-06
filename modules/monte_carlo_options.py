# modules/monte_carlo_options.py
import numpy as np
import pandas as pd
from modules.black_scholes import black_scholes_call, black_scholes_put

# ── SIMULATION GBM DE BASE ────────────────────────────────────

def simulate_paths(S, r, sigma, T, n_simulations=10000, n_steps=252):
    """
    Simule des trajectoires de prix par GBM
    dS = S*(r*dt + sigma*dW)
    """
    dt = T / n_steps
    paths = np.zeros((n_steps + 1, n_simulations))
    paths[0] = S

    for t in range(1, n_steps + 1):
        Z = np.random.standard_normal(n_simulations)
        paths[t] = paths[t-1] * np.exp(
            (r - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z
        )

    return paths

def simulate_paths_antithetic(S, r, sigma, T,
                               n_simulations=10000, n_steps=252):
    """
    Simule des trajectoires avec variables antithétiques
    (réduction de variance)
    """
    dt = T / n_steps
    half = n_simulations // 2
    paths = np.zeros((n_steps + 1, n_simulations))
    paths[0] = S

    for t in range(1, n_steps + 1):
        Z = np.random.standard_normal(half)
        Z_full = np.concatenate([Z, -Z])  # Variables antithétiques
        paths[t] = paths[t-1] * np.exp(
            (r - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z_full
        )

    return paths

# ── OPTIONS VANILLE ───────────────────────────────────────────

def mc_european_call(S, K, T, r, sigma, n_simulations=50000):
    """
    Pricing Monte Carlo d'un Call européen
    Comparaison avec Black-Scholes analytique
    """
    np.random.seed(42)
    paths = simulate_paths_antithetic(S, r, sigma, T, n_simulations)
    final_prices = paths[-1]

    payoffs = np.maximum(final_prices - K, 0)
    mc_price = float(np.exp(-r * T) * np.mean(payoffs))
    mc_std = float(np.std(payoffs) / np.sqrt(n_simulations))
    mc_ci_low = mc_price - 1.96 * mc_std
    mc_ci_high = mc_price + 1.96 * mc_std

    bs_price = black_scholes_call(S, K, T, r, sigma)
    error = abs(mc_price - bs_price)

    return {
        'type': 'Call Européen',
        'prix_mc': round(mc_price, 4),
        'prix_bs': round(bs_price, 4),
        'erreur_vs_bs': round(error, 4),
        'erreur_pct': round(error / bs_price * 100, 2) if bs_price > 0 else 0,
        'intervalle_confiance': (round(mc_ci_low, 4), round(mc_ci_high, 4)),
        'n_simulations': n_simulations,
        'std_erreur': round(mc_std, 6),
    }

def mc_european_put(S, K, T, r, sigma, n_simulations=50000):
    """Pricing Monte Carlo d'un Put européen"""
    np.random.seed(42)
    paths = simulate_paths_antithetic(S, r, sigma, T, n_simulations)
    final_prices = paths[-1]

    payoffs = np.maximum(K - final_prices, 0)
    mc_price = float(np.exp(-r * T) * np.mean(payoffs))
    mc_std = float(np.std(payoffs) / np.sqrt(n_simulations))

    bs_price = black_scholes_put(S, K, T, r, sigma)
    error = abs(mc_price - bs_price)

    return {
        'type': 'Put Européen',
        'prix_mc': round(mc_price, 4),
        'prix_bs': round(bs_price, 4),
        'erreur_vs_bs': round(error, 4),
        'erreur_pct': round(error / bs_price * 100, 2) if bs_price > 0 else 0,
        'intervalle_confiance': (round(mc_price - 1.96*mc_std, 4),
                                  round(mc_price + 1.96*mc_std, 4)),
        'n_simulations': n_simulations,
        'std_erreur': round(mc_std, 6),
    }

# ── OPTIONS BARRIÈRES ─────────────────────────────────────────

def mc_barrier_knock_out_call(S, K, T, r, sigma,
                               barrier, n_simulations=50000,
                               n_steps=252):
    """
    Option barrière Knock-Out Call :
    L'option est annulée si le prix touche la barrière
    Barrière Up-and-Out : barrière > S (barrière au-dessus)
    Barrière Down-and-Out : barrière < S (barrière en-dessous)
    """
    np.random.seed(42)
    dt = T / n_steps
    paths = simulate_paths(S, r, sigma, T, n_simulations, n_steps)

    barrier_type = 'Up-and-Out' if barrier > S else 'Down-and-Out'

    # Vérifier si la barrière est touchée
    if barrier > S:
        knocked_out = np.any(paths > barrier, axis=0)
    else:
        knocked_out = np.any(paths < barrier, axis=0)

    final_prices = paths[-1]
    payoffs = np.where(
        ~knocked_out,
        np.maximum(final_prices - K, 0),
        0
    )

    mc_price = float(np.exp(-r * T) * np.mean(payoffs))
    vanilla_price = black_scholes_call(S, K, T, r, sigma)
    knock_out_pct = float(knocked_out.mean() * 100)

    return {
        'type': f'Call Barrière {barrier_type}',
        'barriere': barrier,
        'barrier_type': barrier_type,
        'prix_mc': round(mc_price, 4),
        'prix_vanilla': round(vanilla_price, 4),
        'reduction_prime': round(vanilla_price - mc_price, 4),
        'reduction_pct': round((vanilla_price - mc_price) /
                                vanilla_price * 100, 2) if vanilla_price > 0 else 0,
        'pct_trajectoires_ko': round(knock_out_pct, 2),
        'n_simulations': n_simulations,
    }

def mc_barrier_knock_in_call(S, K, T, r, sigma,
                              barrier, n_simulations=50000,
                              n_steps=252):
    """
    Option barrière Knock-In Call :
    L'option est activée seulement si le prix touche la barrière
    """
    np.random.seed(42)
    paths = simulate_paths(S, r, sigma, T, n_simulations, n_steps)

    barrier_type = 'Up-and-In' if barrier > S else 'Down-and-In'

    # L'option est active seulement si la barrière est touchée
    if barrier > S:
        knocked_in = np.any(paths > barrier, axis=0)
    else:
        knocked_in = np.any(paths < barrier, axis=0)

    final_prices = paths[-1]
    payoffs = np.where(
        knocked_in,
        np.maximum(final_prices - K, 0),
        0
    )

    mc_price = float(np.exp(-r * T) * np.mean(payoffs))
    vanilla_price = black_scholes_call(S, K, T, r, sigma)
    knock_in_pct = float(knocked_in.mean() * 100)

    return {
        'type': f'Call Barrière {barrier_type}',
        'barriere': barrier,
        'barrier_type': barrier_type,
        'prix_mc': round(mc_price, 4),
        'prix_vanilla': round(vanilla_price, 4),
        'pct_trajectoires_ki': round(knock_in_pct, 2),
        'n_simulations': n_simulations,
    }

# ── OPTIONS ASIATIQUES ────────────────────────────────────────

def mc_asian_call_arithmetic(S, K, T, r, sigma,
                              n_simulations=50000, n_steps=252):
    """
    Option Asiatique Call (moyenne arithmétique) :
    Payoff = max(moyenne_arithmétique(S) - K, 0)
    Moins chère qu'un Call vanille car la moyenne lisse les pics
    """
    np.random.seed(42)
    paths = simulate_paths_antithetic(S, r, sigma, T,
                                       n_simulations, n_steps)

    # Moyenne arithmétique de chaque trajectoire
    arithmetic_avg = np.mean(paths[1:], axis=0)
    payoffs = np.maximum(arithmetic_avg - K, 0)

    mc_price = float(np.exp(-r * T) * np.mean(payoffs))
    vanilla_price = black_scholes_call(S, K, T, r, sigma)
    mc_std = float(np.std(payoffs) / np.sqrt(n_simulations))

    return {
        'type': 'Call Asiatique (Moyenne Arithmétique)',
        'prix_mc': round(mc_price, 4),
        'prix_vanilla': round(vanilla_price, 4),
        'reduction_vs_vanilla': round(vanilla_price - mc_price, 4),
        'reduction_pct': round((vanilla_price - mc_price) /
                                vanilla_price * 100, 2) if vanilla_price > 0 else 0,
        'intervalle_confiance': (round(mc_price - 1.96*mc_std, 4),
                                  round(mc_price + 1.96*mc_std, 4)),
        'n_simulations': n_simulations,
        'interpretation': 'Moins chère car la moyenne lisse la volatilité',
    }

def mc_asian_call_geometric(S, K, T, r, sigma,
                             n_simulations=50000, n_steps=252):
    """
    Option Asiatique Call (moyenne géométrique) :
    Payoff = max(moyenne_géométrique(S) - K, 0)
    A une solution analytique (utile pour validation)
    """
    np.random.seed(42)
    paths = simulate_paths_antithetic(S, r, sigma, T,
                                       n_simulations, n_steps)

    # Moyenne géométrique : exp(mean(log(S)))
    log_paths = np.log(paths[1:])
    geometric_avg = np.exp(np.mean(log_paths, axis=0))
    payoffs = np.maximum(geometric_avg - K, 0)

    mc_price = float(np.exp(-r * T) * np.mean(payoffs))
    vanilla_price = black_scholes_call(S, K, T, r, sigma)

    return {
        'type': 'Call Asiatique (Moyenne Géométrique)',
        'prix_mc': round(mc_price, 4),
        'prix_vanilla': round(vanilla_price, 4),
        'reduction_vs_vanilla': round(vanilla_price - mc_price, 4),
        'n_simulations': n_simulations,
        'interpretation': 'Encore moins chère que la moyenne arithmétique',
    }

def mc_asian_put_arithmetic(S, K, T, r, sigma,
                             n_simulations=50000, n_steps=252):
    """Option Asiatique Put (moyenne arithmétique)"""
    np.random.seed(42)
    paths = simulate_paths_antithetic(S, r, sigma, T,
                                       n_simulations, n_steps)

    arithmetic_avg = np.mean(paths[1:], axis=0)
    payoffs = np.maximum(K - arithmetic_avg, 0)

    mc_price = float(np.exp(-r * T) * np.mean(payoffs))
    vanilla_price = black_scholes_put(S, K, T, r, sigma)

    return {
        'type': 'Put Asiatique (Moyenne Arithmétique)',
        'prix_mc': round(mc_price, 4),
        'prix_vanilla': round(vanilla_price, 4),
        'reduction_vs_vanilla': round(vanilla_price - mc_price, 4),
        'n_simulations': n_simulations,
    }

# ── OPTIONS LOOKBACK ──────────────────────────────────────────

def mc_lookback_call_fixed(S, K, T, r, sigma,
                            n_simulations=50000, n_steps=252):
    """
    Lookback Call à strike fixe :
    Payoff = max(max(S) - K, 0)
    L'acheteur bénéficie du prix maximum atteint
    """
    np.random.seed(42)
    paths = simulate_paths(S, r, sigma, T, n_simulations, n_steps)

    max_prices = np.max(paths, axis=0)
    payoffs = np.maximum(max_prices - K, 0)

    mc_price = float(np.exp(-r * T) * np.mean(payoffs))
    vanilla_price = black_scholes_call(S, K, T, r, sigma)

    return {
        'type': 'Lookback Call (Strike Fixe)',
        'prix_mc': round(mc_price, 4),
        'prix_vanilla': round(vanilla_price, 4),
        'premium_vs_vanilla': round(mc_price - vanilla_price, 4),
        'premium_pct': round((mc_price - vanilla_price) /
                              vanilla_price * 100, 2) if vanilla_price > 0 else 0,
        'n_simulations': n_simulations,
        'interpretation': 'Plus chère car payoff basé sur le prix maximum',
    }

def mc_lookback_put_fixed(S, K, T, r, sigma,
                           n_simulations=50000, n_steps=252):
    """
    Lookback Put à strike fixe :
    Payoff = max(K - min(S), 0)
    L'acheteur bénéficie du prix minimum atteint
    """
    np.random.seed(42)
    paths = simulate_paths(S, r, sigma, T, n_simulations, n_steps)

    min_prices = np.min(paths, axis=0)
    payoffs = np.maximum(K - min_prices, 0)

    mc_price = float(np.exp(-r * T) * np.mean(payoffs))
    vanilla_price = black_scholes_put(S, K, T, r, sigma)

    return {
        'type': 'Lookback Put (Strike Fixe)',
        'prix_mc': round(mc_price, 4),
        'prix_vanilla': round(vanilla_price, 4),
        'premium_vs_vanilla': round(mc_price - vanilla_price, 4),
        'premium_pct': round((mc_price - vanilla_price) /
                              vanilla_price * 100, 2) if vanilla_price > 0 else 0,
        'n_simulations': n_simulations,
        'interpretation': 'Plus chère car payoff basé sur le prix minimum',
    }

def mc_lookback_call_floating(S, T, r, sigma,
                               n_simulations=50000, n_steps=252):
    """
    Lookback Call à strike flottant :
    Payoff = S_final - min(S)
    L'acheteur achète au prix le plus bas
    """
    np.random.seed(42)
    paths = simulate_paths(S, r, sigma, T, n_simulations, n_steps)

    final_prices = paths[-1]
    min_prices = np.min(paths, axis=0)
    payoffs = np.maximum(final_prices - min_prices, 0)

    mc_price = float(np.exp(-r * T) * np.mean(payoffs))

    return {
        'type': 'Lookback Call (Strike Flottant)',
        'prix_mc': round(mc_price, 4),
        'n_simulations': n_simulations,
        'interpretation': 'Acheter au prix le plus bas sur la période',
    }

# ── OPTIONS DIGITALES ─────────────────────────────────────────

def mc_digital_call(S, K, T, r, sigma,
                    payout=1.0, n_simulations=50000):
    """
    Option Digitale (Binary) Call :
    Payoff = payout si S_final > K, sinon 0
    """
    np.random.seed(42)
    paths = simulate_paths_antithetic(S, r, sigma, T, n_simulations)
    final_prices = paths[-1]

    payoffs = np.where(final_prices > K, payout, 0)
    mc_price = float(np.exp(-r * T) * np.mean(payoffs))

    # Prix analytique : e^(-rT) * N(d2)
    from scipy.stats import norm
    from modules.black_scholes import d2
    _d2 = d2(S, K, T, r, sigma)
    analytical_price = float(payout * np.exp(-r * T) * norm.cdf(_d2))

    return {
        'type': f'Digital Call (payout={payout})',
        'prix_mc': round(mc_price, 4),
        'prix_analytique': round(analytical_price, 4),
        'erreur': round(abs(mc_price - analytical_price), 4),
        'prob_in_the_money': round(float((final_prices > K).mean() * 100), 2),
        'n_simulations': n_simulations,
        'interpretation': f'Paye {payout} si le prix dépasse {K:.2f} à maturité',
    }

# ── ANALYSE COMPLÈTE MC OPTIONS ───────────────────────────────

def run_mc_options_analysis(prices, risk_free_rate=0.02):
    """
    Lance l'analyse complète Monte Carlo des options
    sur un actif réel
    """
    S = float(prices.iloc[-1])
    sigma = float(prices.pct_change().dropna().std() * np.sqrt(252))
    r = risk_free_rate
    T = 3/12  # 3 mois
    K = round(S, 2)  # ATM

    print(f"    MC Options — S={S:.2f}, K={K:.2f}, "
          f"σ={sigma*100:.1f}%, T=3 mois")

    results = {
        'parametres': {
            'S': S, 'K': K, 'T': T,
            'r': round(r * 100, 2),
            'sigma': round(sigma * 100, 2),
        },
        'vanille': {},
        'barrieres': {},
        'asiatiques': {},
        'lookback': {},
        'digitales': {},
        'comparaison': {},
    }

    # ── Vanille ──
    print("      Options Vanille...")
    results['vanille']['call'] = mc_european_call(S, K, T, r, sigma)
    results['vanille']['put'] = mc_european_put(S, K, T, r, sigma)

    # ── Barrières ──
    print("      Options Barrières...")
    barrier_up = round(S * 1.15, 2)
    barrier_down = round(S * 0.85, 2)
    results['barrieres']['knock_out_up'] = mc_barrier_knock_out_call(
        S, K, T, r, sigma, barrier_up
    )
    results['barrieres']['knock_out_down'] = mc_barrier_knock_out_call(
        S, K, T, r, sigma, barrier_down
    )
    results['barrieres']['knock_in_up'] = mc_barrier_knock_in_call(
        S, K, T, r, sigma, barrier_up
    )

    # ── Asiatiques ──
    print("      Options Asiatiques...")
    results['asiatiques']['call_arith'] = mc_asian_call_arithmetic(
        S, K, T, r, sigma
    )
    results['asiatiques']['call_geo'] = mc_asian_call_geometric(
        S, K, T, r, sigma
    )
    results['asiatiques']['put_arith'] = mc_asian_put_arithmetic(
        S, K, T, r, sigma
    )

    # ── Lookback ──
    print("      Options Lookback...")
    results['lookback']['call_fixed'] = mc_lookback_call_fixed(
        S, K, T, r, sigma
    )
    results['lookback']['put_fixed'] = mc_lookback_put_fixed(
        S, K, T, r, sigma
    )
    results['lookback']['call_floating'] = mc_lookback_call_floating(
        S, T, r, sigma
    )

    # ── Digitales ──
    print("      Options Digitales...")
    results['digitales']['digital_call'] = mc_digital_call(
        S, K, T, r, sigma, payout=1.0
    )

    # ── Comparaison des prix ──
    results['comparaison'] = {
        'Call Vanille (BS)': results['vanille']['call']['prix_bs'],
        'Call Vanille (MC)': results['vanille']['call']['prix_mc'],
        'Call Asiatique': results['asiatiques']['call_arith']['prix_mc'],
        'Call Barrière KO': results['barrieres']['knock_out_up']['prix_mc'],
        'Call Barrière KI': results['barrieres']['knock_in_up']['prix_mc'],
        'Call Lookback': results['lookback']['call_fixed']['prix_mc'],
        'Digital Call': results['digitales']['digital_call']['prix_mc'],
    }

    print(f"      ✓ {len(results['comparaison'])} options pricées")
    return results