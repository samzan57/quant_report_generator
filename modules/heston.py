# modules/heston.py
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from modules.black_scholes import black_scholes_call, black_scholes_put

# ── MODÈLE DE HESTON ─────────────────────────────────────────
"""
Le modèle de Heston (1993) est une extension de Black-Scholes
où la VOLATILITÉ est elle-même stochastique (aléatoire).

Équations différentielles stochastiques :
dS = S * (r*dt + sqrt(v)*dW1)          ← Prix suit un GBM
dv = kappa*(theta - v)*dt + xi*sqrt(v)*dW2  ← Variance suit un CIR

Paramètres :
- kappa : Vitesse de retour à la moyenne de la variance
- theta : Variance long terme (mean reversion level)
- xi    : Volatilité de la volatilité (vol of vol)
- rho   : Corrélation entre dW1 et dW2 (prix et variance)
- v0    : Variance initiale

Avantage vs Black-Scholes :
- Capture le smile de volatilité
- Volatilité n'est plus constante
- Plus réaliste pour les options exotiques
"""

def simulate_heston(S, v0, r, kappa, theta, xi, rho, T,
                    n_simulations=10000, n_steps=252):
    """
    Simulation du modèle de Heston par schéma d'Euler
    avec corrélation entre les deux mouvements browniens
    """
    dt = T / n_steps
    
    S_paths = np.zeros((n_steps + 1, n_simulations))
    v_paths = np.zeros((n_steps + 1, n_simulations))
    
    S_paths[0] = S
    v_paths[0] = v0

    for t in range(1, n_steps + 1):
        # Générer deux browniens corrélés
        Z1 = np.random.standard_normal(n_simulations)
        Z2 = np.random.standard_normal(n_simulations)
        W1 = Z1
        W2 = rho * Z1 + np.sqrt(1 - rho**2) * Z2

        # Variance (processus CIR) — Full Truncation pour éviter v<0
        v_prev = np.maximum(v_paths[t-1], 0)
        v_paths[t] = (v_prev +
                      kappa * (theta - v_prev) * dt +
                      xi * np.sqrt(v_prev * dt) * W2)
        v_paths[t] = np.maximum(v_paths[t], 0)  # Truncation

        # Prix
        S_paths[t] = S_paths[t-1] * np.exp(
            (r - 0.5 * v_prev) * dt +
            np.sqrt(v_prev * dt) * W1
        )

    return S_paths, v_paths

def heston_call_price(S, K, T, r, v0, kappa, theta, xi, rho,
                       n_simulations=20000):
    """Prix d'un Call par simulation de Heston"""
    np.random.seed(42)
    S_paths, v_paths = simulate_heston(
        S, v0, r, kappa, theta, xi, rho, T,
        n_simulations=n_simulations
    )
    payoffs = np.maximum(S_paths[-1] - K, 0)
    price = float(np.exp(-r * T) * np.mean(payoffs))
    std = float(np.std(payoffs) / np.sqrt(n_simulations))
    return price, std

def heston_put_price(S, K, T, r, v0, kappa, theta, xi, rho,
                      n_simulations=20000):
    """Prix d'un Put par simulation de Heston"""
    np.random.seed(42)
    S_paths, v_paths = simulate_heston(
        S, v0, r, kappa, theta, xi, rho, T,
        n_simulations=n_simulations
    )
    payoffs = np.maximum(K - S_paths[-1], 0)
    price = float(np.exp(-r * T) * np.mean(payoffs))
    std = float(np.std(payoffs) / np.sqrt(n_simulations))
    return price, std

def calibrate_heston(S, r, market_prices, strikes, maturities,
                     option_types=None):
    """
    Calibration du modèle de Heston sur des prix de marché
    Minimise l'erreur quadratique entre prix modèle et prix marché
    """
    if option_types is None:
        option_types = ['call'] * len(market_prices)

    def objective(params):
        kappa, theta, xi, rho, v0 = params

        # Contraintes de Feller : 2*kappa*theta > xi^2
        if (kappa <= 0 or theta <= 0 or xi <= 0 or
                abs(rho) >= 1 or v0 <= 0):
            return 1e10

        total_error = 0
        for i, (K, T, opt_type, mkt_price) in enumerate(
                zip(strikes, maturities, option_types, market_prices)):
            try:
                if opt_type == 'call':
                    model_price, _ = heston_call_price(
                        S, K, T, r, v0, kappa, theta, xi, rho,
                        n_simulations=5000
                    )
                else:
                    model_price, _ = heston_put_price(
                        S, K, T, r, v0, kappa, theta, xi, rho,
                        n_simulations=5000
                    )
                total_error += (model_price - mkt_price) ** 2
            except:
                total_error += 1e6

        return total_error

    # Point de départ initial
    x0 = [2.0, 0.04, 0.3, -0.7, 0.04]
    bounds = [
        (0.01, 10.0),   # kappa
        (0.01, 1.0),    # theta
        (0.01, 2.0),    # xi
        (-0.99, 0.99),  # rho
        (0.001, 1.0),   # v0
    ]

    result = minimize(objective, x0, method='L-BFGS-B', bounds=bounds,
                      options={'maxiter': 100})

    if result.success:
        kappa, theta, xi, rho, v0 = result.x
        return {
            'kappa': round(float(kappa), 4),
            'theta': round(float(theta), 4),
            'xi': round(float(xi), 4),
            'rho': round(float(rho), 4),
            'v0': round(float(v0), 4),
            'vol_long_terme': round(float(np.sqrt(theta)) * 100, 2),
            'vol_initiale': round(float(np.sqrt(v0)) * 100, 2),
            'condition_feller': 2 * kappa * theta > xi ** 2,
            'erreur_calibration': round(float(result.fun), 6),
            'success': True,
        }
    else:
        # Paramètres par défaut si calibration échoue
        return {
            'kappa': 2.0,
            'theta': 0.04,
            'xi': 0.3,
            'rho': -0.7,
            'v0': 0.04,
            'vol_long_terme': 20.0,
            'vol_initiale': 20.0,
            'condition_feller': True,
            'erreur_calibration': float(result.fun),
            'success': False,
        }

def compare_heston_vs_bs(S, K_range, T, r, sigma,
                          heston_params, n_simulations=10000):
    """
    Compare les prix Heston vs Black-Scholes
    sur une gamme de strikes → montre le smile de volatilité
    """
    results = []

    kappa = heston_params['kappa']
    theta = heston_params['theta']
    xi = heston_params['xi']
    rho = heston_params['rho']
    v0 = heston_params['v0']

    for K in K_range:
        # Prix Black-Scholes
        bs_call = black_scholes_call(S, K, T, r, sigma)
        bs_put = black_scholes_put(S, K, T, r, sigma)

        # Prix Heston
        heston_call, heston_std = heston_call_price(
            S, K, T, r, v0, kappa, theta, xi, rho, n_simulations
        )

        # Moneyness
        moneyness = S / K

        results.append({
            'strike': K,
            'moneyness': round(moneyness, 4),
            'bs_call': round(bs_call, 4),
            'heston_call': round(heston_call, 4),
            'difference': round(heston_call - bs_call, 4),
            'difference_pct': round(
                (heston_call - bs_call) / bs_call * 100, 2
            ) if bs_call > 0 else 0,
        })

    return pd.DataFrame(results)

def heston_volatility_surface(S, strikes, maturities, r,
                               heston_params, n_simulations=5000):
    """
    Génère la surface de volatilité implicite du modèle de Heston
    en inversant les prix Heston par Black-Scholes
    """
    from scipy.optimize import brentq
    from scipy.stats import norm

    kappa = heston_params['kappa']
    theta = heston_params['theta']
    xi = heston_params['xi']
    rho = heston_params['rho']
    v0 = heston_params['v0']

    surface = []

    for T in maturities:
        row = []
        for K in strikes:
            try:
                # Prix Heston
                heston_price, _ = heston_call_price(
                    S, K, T, r, v0, kappa, theta, xi, rho,
                    n_simulations=n_simulations
                )

                # Inverser BS pour trouver la vol implicite
                intrinsic = max(S - K * np.exp(-r * T), 0)
                if heston_price <= intrinsic:
                    row.append(np.sqrt(v0) * 100)
                    continue

                def bs_minus_heston(vol):
                    return (black_scholes_call(S, K, T, r, vol)
                            - heston_price)

                try:
                    iv = brentq(bs_minus_heston, 1e-6, 5.0)
                    row.append(round(iv * 100, 2))
                except:
                    row.append(round(np.sqrt(v0) * 100, 2))

            except:
                row.append(round(np.sqrt(v0) * 100, 2))

        surface.append(row)

    return pd.DataFrame(
        surface,
        index=[f'{int(T*365)}j' for T in maturities],
        columns=[f'{k/S*100:.0f}%' for k in strikes]
    )

def run_heston_analysis(prices, risk_free_rate=0.02):
    """
    Lance l'analyse complète du modèle de Heston
    sur un actif réel
    """
    S = float(prices.iloc[-1])
    returns = prices.pct_change().dropna()
    sigma = float(returns.std() * np.sqrt(252))
    r = risk_free_rate

    print(f"    Heston — S={S:.2f}, σ_hist={sigma*100:.1f}%")

    # Paramètres Heston estimés depuis les données historiques
    v0 = sigma ** 2
    kappa = 2.0
    theta = v0
    xi = max(0.1, sigma * 0.5)
    rho = float(np.clip(
        np.corrcoef(
            returns.values[:-1],
            np.diff(returns.values ** 2)
        )[0, 1], -0.99, 0.99
    )) if len(returns) > 10 else -0.7

    heston_params = {
        'kappa': round(kappa, 4),
        'theta': round(theta, 4),
        'xi': round(xi, 4),
        'rho': round(rho, 4),
        'v0': round(v0, 4),
        'vol_long_terme': round(np.sqrt(theta) * 100, 2),
        'vol_initiale': round(np.sqrt(v0) * 100, 2),
        'condition_feller': 2 * kappa * theta > xi ** 2,
        'success': True,
    }

    print(f"    Paramètres : κ={kappa:.2f}, θ={theta:.4f}, "
          f"ξ={xi:.2f}, ρ={rho:.2f}")

    results = {
        'parametres_heston': heston_params,
        'parametres_marche': {
            'S': S,
            'sigma_bs': round(sigma * 100, 2),
            'r': round(r * 100, 2),
        },
    }

    # Comparaison Heston vs BS sur différents strikes
    print("    Comparaison Heston vs BS...")
    T = 3/12
    strikes = np.linspace(S * 0.80, S * 1.20, 10)
    results['comparaison'] = compare_heston_vs_bs(
        S, strikes, T, r, sigma, heston_params,
        n_simulations=5000
    )

    # Simulation de trajectoires Heston
    print("    Simulation trajectoires Heston...")
    np.random.seed(42)
    S_paths, v_paths = simulate_heston(
        S, v0, r, kappa, theta, xi, rho, T,
        n_simulations=500, n_steps=63
    )
    results['paths'] = {
        'S_paths': S_paths,
        'v_paths': v_paths,
    }

    # Surface de volatilité Heston
    print("    Surface de volatilité Heston...")
    strikes_surf = np.linspace(S * 0.85, S * 1.15, 6)
    maturities_surf = [1/12, 3/12, 6/12, 1.0]
    results['vol_surface'] = heston_volatility_surface(
        S, strikes_surf, maturities_surf, r,
        heston_params, n_simulations=3000
    )

    # Pricing Call ATM Heston vs BS
    print("    Pricing ATM Call Heston vs BS...")
    K_atm = round(S, 2)
    heston_price, heston_std = heston_call_price(
        S, K_atm, T, r, v0, kappa, theta, xi, rho,
        n_simulations=20000
    )
    bs_price = black_scholes_call(S, K_atm, T, r, sigma)

    results['pricing_atm'] = {
        'strike': K_atm,
        'maturite': '3 mois',
        'heston_call': round(heston_price, 4),
        'bs_call': round(bs_price, 4),
        'difference': round(heston_price - bs_price, 4),
        'difference_pct': round(
            (heston_price - bs_price) / bs_price * 100, 2
        ) if bs_price > 0 else 0,
        'heston_std': round(heston_std, 6),
    }

    print(f"    ✓ Heston Call ATM: {heston_price:.4f} | "
          f"BS Call: {bs_price:.4f} | "
          f"Diff: {heston_price - bs_price:+.4f}")

    return results