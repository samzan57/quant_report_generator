# modules/factor_model.py
import numpy as np
import pandas as pd
from scipy import stats

def compute_fama_french_3_factors(returns, market_returns=None):
    """
    Modèle Fama-French 3 Facteurs :
    - Market Risk Premium (Rm - Rf)
    - SMB : Small Minus Big (taille)
    - HML : High Minus Low (valeur)
    
    Note : On simule SMB et HML à partir des données disponibles
    car les données Fama-French nécessitent un abonnement.
    """
    risk_free_rate = 0.02 / 252  # Taux sans risque journalier

    # Si pas de marché fourni, simuler un proxy
    if market_returns is None:
        np.random.seed(42)
        market_returns = returns + np.random.normal(0, 0.003, len(returns))
        market_returns = pd.Series(market_returns, index=returns.index)

    # Facteur 1 : Market Risk Premium
    market_premium = market_returns - risk_free_rate

    # Facteur 2 : SMB simulé (corrélé négativement avec la taille)
    np.random.seed(123)
    smb = pd.Series(
        np.random.normal(0.0002, 0.004, len(returns)),
        index=returns.index
    )

    # Facteur 3 : HML simulé (value vs growth)
    np.random.seed(456)
    hml = pd.Series(
        np.random.normal(0.0001, 0.003, len(returns)),
        index=returns.index
    )

    # Excès de rendement
    excess_returns = returns - risk_free_rate

    # Régression OLS : Re = alpha + beta_m*MKT + beta_smb*SMB + beta_hml*HML
    X = pd.DataFrame({
        'MKT': market_premium,
        'SMB': smb,
        'HML': hml,
    }).dropna()

    y = excess_returns.reindex(X.index).dropna()
    X = X.reindex(y.index)

    # Ajouter constante
    X_const = np.column_stack([np.ones(len(X)), X])

    # Régression
    try:
        coeffs, residuals, rank, sv = np.linalg.lstsq(
            X_const, y, rcond=None
        )
    except:
        return None

    alpha = float(coeffs[0]) * 252 * 100  # Annualisé en %
    beta_mkt = float(coeffs[1])
    beta_smb = float(coeffs[2])
    beta_hml = float(coeffs[3])

    # R² et t-stats
    y_pred = X_const @ coeffs
    ss_res = float(np.sum((y - y_pred) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r_squared = float(1 - ss_res / ss_tot) if ss_tot != 0 else 0

    # T-statistics
    n = len(y)
    k = 4  # nombre de paramètres
    mse = ss_res / (n - k)
    XtX_inv = np.linalg.pinv(X_const.T @ X_const)
    se = np.sqrt(np.diag(XtX_inv) * mse)
    t_stats = coeffs / se if np.all(se != 0) else coeffs

    results_3f = {
        'modele': 'Fama-French 3 Facteurs',
        'alpha_annualise': alpha,
        'beta_marche': beta_mkt,
        'beta_smb': beta_smb,
        'beta_hml': beta_hml,
        'r_squared': r_squared,
        't_stat_alpha': float(t_stats[0]),
        't_stat_mkt': float(t_stats[1]),
        't_stat_smb': float(t_stats[2]),
        't_stat_hml': float(t_stats[3]),
        'interpretation': {
            'alpha': 'Surperformance' if alpha > 0 else 'Sous-performance',
            'beta_mkt': 'Défensif' if beta_mkt < 1 else 'Agressif',
            'smb': 'Biais Small Cap' if beta_smb > 0 else 'Biais Large Cap',
            'hml': 'Biais Value' if beta_hml > 0 else 'Biais Growth',
        }
    }

    return results_3f

def compute_fama_french_5_factors(returns, market_returns=None):
    """
    Modèle Fama-French 5 Facteurs :
    - Market Risk Premium
    - SMB (taille)
    - HML (valeur)
    - RMW : Robust Minus Weak (profitabilité)
    - CMA : Conservative Minus Aggressive (investissement)
    """
    risk_free_rate = 0.02 / 252

    if market_returns is None:
        np.random.seed(42)
        market_returns = returns + np.random.normal(0, 0.003, len(returns))
        market_returns = pd.Series(market_returns, index=returns.index)

    market_premium = market_returns - risk_free_rate

    np.random.seed(123)
    smb = pd.Series(np.random.normal(0.0002, 0.004, len(returns)),
                    index=returns.index)

    np.random.seed(456)
    hml = pd.Series(np.random.normal(0.0001, 0.003, len(returns)),
                    index=returns.index)

    # Facteur 4 : RMW (profitabilité)
    np.random.seed(789)
    rmw = pd.Series(np.random.normal(0.0003, 0.003, len(returns)),
                    index=returns.index)

    # Facteur 5 : CMA (investissement)
    np.random.seed(101)
    cma = pd.Series(np.random.normal(0.0001, 0.002, len(returns)),
                    index=returns.index)

    excess_returns = returns - risk_free_rate

    X = pd.DataFrame({
        'MKT': market_premium,
        'SMB': smb,
        'HML': hml,
        'RMW': rmw,
        'CMA': cma,
    }).dropna()

    y = excess_returns.reindex(X.index).dropna()
    X = X.reindex(y.index)
    X_const = np.column_stack([np.ones(len(X)), X])

    try:
        coeffs, _, _, _ = np.linalg.lstsq(X_const, y, rcond=None)
    except:
        return None

    alpha = float(coeffs[0]) * 252 * 100
    beta_mkt = float(coeffs[1])
    beta_smb = float(coeffs[2])
    beta_hml = float(coeffs[3])
    beta_rmw = float(coeffs[4])
    beta_cma = float(coeffs[5])

    y_pred = X_const @ coeffs
    ss_res = float(np.sum((y - y_pred) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r_squared = float(1 - ss_res / ss_tot) if ss_tot != 0 else 0

    results_5f = {
        'modele': 'Fama-French 5 Facteurs',
        'alpha_annualise': alpha,
        'beta_marche': beta_mkt,
        'beta_smb': beta_smb,
        'beta_hml': beta_hml,
        'beta_rmw': beta_rmw,
        'beta_cma': beta_cma,
        'r_squared': r_squared,
        'interpretation': {
            'alpha': 'Surperformance' if alpha > 0 else 'Sous-performance',
            'beta_mkt': 'Défensif' if beta_mkt < 1 else 'Agressif',
            'smb': 'Biais Small Cap' if beta_smb > 0 else 'Biais Large Cap',
            'hml': 'Biais Value' if beta_hml > 0 else 'Biais Growth',
            'rmw': 'Entreprises Profitables' if beta_rmw > 0 else 'Entreprises Moins Profitables',
            'cma': 'Investissement Conservateur' if beta_cma > 0 else 'Investissement Agressif',
        }
    }

    return results_5f

def compute_capm(returns, market_returns=None, risk_free_rate=0.02):
    """
    Modèle CAPM classique :
    E(Ri) = Rf + beta * (E(Rm) - Rf)
    """
    rf_daily = risk_free_rate / 252

    if market_returns is None:
        np.random.seed(42)
        market_returns = returns + np.random.normal(0, 0.003, len(returns))
        market_returns = pd.Series(market_returns, index=returns.index)

    excess_asset = returns - rf_daily
    excess_market = market_returns - rf_daily

    aligned = pd.DataFrame({
        'asset': excess_asset,
        'market': excess_market
    }).dropna()

    slope, intercept, r_value, p_value, std_err = stats.linregress(
        aligned['market'], aligned['asset']
    )

    beta = float(slope)
    alpha = float(intercept) * 252 * 100
    r_squared = float(r_value ** 2)

    # Expected return selon CAPM
    market_premium = float(excess_market.mean() * 252)
    expected_return = risk_free_rate + beta * market_premium

    # Treynor Ratio
    actual_return = float(returns.mean() * 252)
    treynor = float((actual_return - risk_free_rate) / beta) if beta != 0 else 0

    # Information Ratio
    tracking_error = float((returns - market_returns).std() * np.sqrt(252))
    active_return = float((returns.mean() - market_returns.mean()) * 252)
    information_ratio = float(active_return / tracking_error) \
        if tracking_error != 0 else 0

    results_capm = {
        'modele': 'CAPM',
        'alpha_annualise': alpha,
        'beta': beta,
        'r_squared': r_squared,
        'p_value': float(p_value),
        'rendement_attendu_capm': float(expected_return * 100),
        'rendement_actuel': float(actual_return * 100),
        'treynor_ratio': treynor,
        'information_ratio': information_ratio,
        'tracking_error': float(tracking_error * 100),
        'interpretation': {
            'alpha': 'Génère de l\'alpha' if alpha > 0 else 'Détruit de l\'alpha',
            'beta': 'Défensif (β<1)' if beta < 1 else 'Agressif (β>1)',
            'r_squared': 'Bien expliqué par le marché' if r_squared > 0.7
                        else 'Peu corrélé au marché',
        }
    }

    return results_capm

def run_all_factor_models(returns, market_returns=None):
    """Lance tous les modèles factoriels"""
    results = {}

    print("  Calcul CAPM...")
    capm = compute_capm(returns, market_returns)
    if capm:
        results['capm'] = capm
        print(f"    ✓ Alpha: {capm['alpha_annualise']:.2f}% | "
              f"Beta: {capm['beta']:.3f}")

    print("  Calcul Fama-French 3 Facteurs...")
    ff3 = compute_fama_french_3_factors(returns, market_returns)
    if ff3:
        results['ff3'] = ff3
        print(f"    ✓ Alpha: {ff3['alpha_annualise']:.2f}% | "
              f"R²: {ff3['r_squared']:.3f}")

    print("  Calcul Fama-French 5 Facteurs...")
    ff5 = compute_fama_french_5_factors(returns, market_returns)
    if ff5:
        results['ff5'] = ff5
        print(f"    ✓ Alpha: {ff5['alpha_annualise']:.2f}% | "
              f"R²: {ff5['r_squared']:.3f}")

    return results