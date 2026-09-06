# modules/portfolio.py
import numpy as np
import pandas as pd
from scipy.optimize import minimize

def compute_portfolio_metrics(weights, mean_returns, cov_matrix,
                               risk_free_rate=0.02):
    """Calcule les métriques d'un portefeuille"""
    weights = np.array(weights)
    portfolio_return = float(np.dot(weights, mean_returns) * 252)
    portfolio_vol = float(
        np.sqrt(weights @ cov_matrix @ weights) * np.sqrt(252)
    )
    sharpe = float((portfolio_return - risk_free_rate) / portfolio_vol) \
        if portfolio_vol != 0 else 0
    return portfolio_return, portfolio_vol, sharpe

def minimum_variance_portfolio(mean_returns, cov_matrix):
    """Portefeuille à variance minimale"""
    n = len(mean_returns)
    constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
    bounds = tuple((0, 1) for _ in range(n))
    initial = np.array([1/n] * n)

    result = minimize(
        lambda w: np.sqrt(w @ cov_matrix @ w) * np.sqrt(252),
        initial,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints
    )

    if result.success:
        weights = result.x
        ret, vol, sharpe = compute_portfolio_metrics(
            weights, mean_returns, cov_matrix
        )
        return {
            'nom': 'Variance Minimale',
            'weights': weights,
            'rendement': ret * 100,
            'volatilite': vol * 100,
            'sharpe': sharpe,
        }
    return None

def maximum_sharpe_portfolio(mean_returns, cov_matrix,
                              risk_free_rate=0.02):
    """Portefeuille à Sharpe maximum (tangency portfolio)"""
    n = len(mean_returns)
    constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
    bounds = tuple((0, 1) for _ in range(n))
    initial = np.array([1/n] * n)

    def neg_sharpe(weights):
        ret, vol, sharpe = compute_portfolio_metrics(
            weights, mean_returns, cov_matrix, risk_free_rate
        )
        return -sharpe

    result = minimize(
        neg_sharpe,
        initial,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints
    )

    if result.success:
        weights = result.x
        ret, vol, sharpe = compute_portfolio_metrics(
            weights, mean_returns, cov_matrix, risk_free_rate
        )
        return {
            'nom': 'Sharpe Maximum',
            'weights': weights,
            'rendement': ret * 100,
            'volatilite': vol * 100,
            'sharpe': sharpe,
        }
    return None

def equal_weight_portfolio(mean_returns, cov_matrix):
    """Portefeuille équipondéré"""
    n = len(mean_returns)
    weights = np.array([1/n] * n)
    ret, vol, sharpe = compute_portfolio_metrics(
        weights, mean_returns, cov_matrix
    )
    return {
        'nom': 'Équipondéré',
        'weights': weights,
        'rendement': ret * 100,
        'volatilite': vol * 100,
        'sharpe': sharpe,
    }

def risk_parity_portfolio(mean_returns, cov_matrix):
    """Portefeuille Risk Parity (égalité des contributions au risque)"""
    n = len(mean_returns)

    def risk_parity_objective(weights):
        weights = np.array(weights)
        port_vol = np.sqrt(weights @ cov_matrix @ weights)
        marginal_risk = cov_matrix @ weights / port_vol
        risk_contribution = weights * marginal_risk
        target = port_vol / n
        return float(np.sum((risk_contribution - target) ** 2))

    constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
    bounds = tuple((0.01, 1) for _ in range(n))
    initial = np.array([1/n] * n)

    result = minimize(
        risk_parity_objective,
        initial,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints
    )

    if result.success:
        weights = result.x
        ret, vol, sharpe = compute_portfolio_metrics(
            weights, mean_returns, cov_matrix
        )
        return {
            'nom': 'Risk Parity',
            'weights': weights,
            'rendement': ret * 100,
            'volatilite': vol * 100,
            'sharpe': sharpe,
        }
    return None

def efficient_frontier(mean_returns, cov_matrix, n_points=50):
    """Calcule la frontière efficiente de Markowitz"""
    n = len(mean_returns)
    target_returns = np.linspace(
        float(mean_returns.min() * 252),
        float(mean_returns.max() * 252),
        n_points
    )

    frontier_vols = []
    frontier_rets = []
    frontier_sharpes = []

    for target in target_returns:
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
            {'type': 'eq',
             'fun': lambda x: np.dot(x, mean_returns) * 252 - target}
        ]
        bounds = tuple((0, 1) for _ in range(n))
        initial = np.array([1/n] * n)

        result = minimize(
            lambda w: np.sqrt(w @ cov_matrix @ w) * np.sqrt(252),
            initial,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        if result.success:
            vol = float(np.sqrt(
                result.x @ cov_matrix @ result.x
            ) * np.sqrt(252))
            sharpe = float((target - 0.02) / vol) if vol != 0 else 0
            frontier_vols.append(vol * 100)
            frontier_rets.append(target * 100)
            frontier_sharpes.append(sharpe)

    return {
        'volatilites': frontier_vols,
        'rendements': frontier_rets,
        'sharpes': frontier_sharpes,
    }

def black_litterman(mean_returns, cov_matrix, views=None,
                     risk_aversion=2.5, tau=0.05):
    """
    Modèle Black-Litterman :
    Combine les rendements d'équilibre du marché avec
    les vues subjectives de l'investisseur
    """
    n = len(mean_returns)

    # Poids du marché (équipondérés comme proxy)
    market_weights = np.array([1/n] * n)

    # Rendements d'équilibre implicites (prior)
    pi = risk_aversion * cov_matrix @ market_weights

    if views is None:
        # Vues neutres : légère surperformance attendue
        views = {
            'P': np.eye(n),
            'Q': mean_returns.values * 252 * 1.05,
            'omega_scale': 0.1
        }

    P = np.array(views['P'])
    Q = np.array(views['Q'])
    omega_scale = views.get('omega_scale', 0.1)
    omega = np.diag(np.diag(P @ (tau * cov_matrix) @ P.T)) * omega_scale

    # Formule Black-Litterman
    tau_cov = tau * cov_matrix
    M1 = np.linalg.inv(tau_cov)
    M2 = P.T @ np.linalg.inv(omega) @ P
    M3 = np.linalg.inv(tau_cov) @ pi + P.T @ np.linalg.inv(omega) @ Q

    bl_returns = np.linalg.inv(M1 + M2) @ M3
    bl_cov = np.linalg.inv(M1 + M2) + cov_matrix

    # Optimisation sur les rendements BL
    bl_mean = pd.Series(bl_returns, index=mean_returns.index)

    max_sharpe = maximum_sharpe_portfolio(bl_mean, bl_cov)
    if max_sharpe:
        max_sharpe['nom'] = 'Black-Litterman'

    return {
        'bl_returns': bl_mean,
        'bl_cov': pd.DataFrame(
            bl_cov,
            index=mean_returns.index,
            columns=mean_returns.index
        ),
        'portfolio': max_sharpe,
        'prior_returns': pi,
    }

def run_portfolio_optimization(dfs):
    """
    Lance l'optimisation complète du portefeuille
    sur tous les actifs disponibles
    """
    # Construire la matrice des rendements
    returns_dict = {}
    for name, df in dfs.items():
        for candidate in ['Close', 'close', 'Adj Close', 'Prix']:
            if candidate in df.columns:
                prices = df[candidate].dropna()
                prices = prices[prices > 0]
                if len(prices) >= 30:
                    returns_dict[name] = prices.pct_change().dropna()
                break

    if len(returns_dict) < 2:
        print("  ⚠ Optimisation portefeuille nécessite au moins 2 actifs")
        return None

    # Aligner les séries temporelles
    returns_df = pd.DataFrame(returns_dict).dropna()

    if len(returns_df) < 30:
        print("  ⚠ Pas assez de données communes pour l'optimisation")
        return None

    mean_returns = returns_df.mean()
    cov_matrix = returns_df.cov()
    asset_names = list(returns_dict.keys())

    print(f"  Optimisation sur {len(asset_names)} actifs : "
          f"{', '.join(asset_names)}")

    results = {
        'asset_names': asset_names,
        'returns_df': returns_df,
        'mean_returns': mean_returns,
        'cov_matrix': cov_matrix,
        'portfolios': {},
        'frontier': None,
        'black_litterman': None,
    }

    # Portefeuille équipondéré
    print("  Calcul portefeuille équipondéré...")
    eq = equal_weight_portfolio(mean_returns, cov_matrix)
    if eq:
        results['portfolios']['equal_weight'] = eq
        print(f"    ✓ Sharpe: {eq['sharpe']:.3f} | "
              f"Vol: {eq['volatilite']:.1f}%")

    # Variance minimale
    print("  Calcul variance minimale...")
    mv = minimum_variance_portfolio(mean_returns, cov_matrix)
    if mv:
        results['portfolios']['min_variance'] = mv
        print(f"    ✓ Sharpe: {mv['sharpe']:.3f} | "
              f"Vol: {mv['volatilite']:.1f}%")

    # Sharpe maximum
    print("  Calcul Sharpe maximum...")
    ms = maximum_sharpe_portfolio(mean_returns, cov_matrix)
    if ms:
        results['portfolios']['max_sharpe'] = ms
        print(f"    ✓ Sharpe: {ms['sharpe']:.3f} | "
              f"Vol: {ms['volatilite']:.1f}%")

    # Risk Parity
    print("  Calcul Risk Parity...")
    rp = risk_parity_portfolio(mean_returns, cov_matrix)
    if rp:
        results['portfolios']['risk_parity'] = rp
        print(f"    ✓ Sharpe: {rp['sharpe']:.3f} | "
              f"Vol: {rp['volatilite']:.1f}%")

    # Frontière efficiente
    print("  Calcul frontière efficiente...")
    frontier = efficient_frontier(mean_returns, cov_matrix)
    if frontier:
        results['frontier'] = frontier
        print(f"    ✓ {len(frontier['volatilites'])} points calculés")

    # Black-Litterman
    print("  Calcul Black-Litterman...")
    bl = black_litterman(mean_returns, cov_matrix)
    if bl:
        results['black_litterman'] = bl
        if bl['portfolio']:
            print(f"    ✓ Sharpe BL: {bl['portfolio']['sharpe']:.3f}")

    return results