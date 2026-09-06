# modules/monte_carlo.py
import numpy as np
import pandas as pd

def monte_carlo_simulation(prices, n_simulations=1000, n_days=252, 
                            risk_free_rate=0.02):
    """
    Simulation Monte Carlo des prix futurs
    Basée sur le modèle GBM (Geometric Brownian Motion)
    """
    returns = prices.pct_change().dropna()
    
    mu = returns.mean()          # Drift journalier
    sigma = returns.std()        # Volatilité journalière
    last_price = prices.iloc[-1]
    
    # Générer les simulations
    simulations = np.zeros((n_days, n_simulations))
    
    for i in range(n_simulations):
        prices_sim = [last_price]
        for d in range(n_days - 1):
            shock = np.random.normal(0, 1)
            drift = mu - 0.5 * sigma ** 2
            price = prices_sim[-1] * np.exp(drift + sigma * shock)
            prices_sim.append(price)
        simulations[:, i] = prices_sim
    
    # Statistiques sur les prix finaux
    final_prices = simulations[-1, :]
    
    stats = {
        'prix_actuel': float(last_price),
        'prix_median': float(np.median(final_prices)),
        'prix_moyen': float(np.mean(final_prices)),
        'prix_min': float(np.min(final_prices)),
        'prix_max': float(np.max(final_prices)),
        'rendement_median': float((np.median(final_prices) / last_price - 1) * 100),
        'rendement_moyen': float((np.mean(final_prices) / last_price - 1) * 100),
        'var_95': float(np.percentile(final_prices, 5)),
        'var_99': float(np.percentile(final_prices, 1)),
        'prob_hausse': float((final_prices > last_price).mean() * 100),
        'prob_baisse_10': float((final_prices < last_price * 0.9).mean() * 100),
        'prob_hausse_10': float((final_prices > last_price * 1.1).mean() * 100),
        'prob_hausse_20': float((final_prices > last_price * 1.2).mean() * 100),
        'intervalle_confiance_5': float(np.percentile(final_prices, 5)),
        'intervalle_confiance_95': float(np.percentile(final_prices, 95)),
        'n_simulations': n_simulations,
        'n_days': n_days,
        'mu_annualise': float(mu * 252 * 100),
        'sigma_annualise': float(sigma * np.sqrt(252) * 100),
    }
    
    return simulations, stats

def monte_carlo_var(returns, n_simulations=10000, horizon=1, 
                    confidence_levels=[0.95, 0.99]):
    """
    VaR Monte Carlo sur un horizon donné
    """
    mu = returns.mean()
    sigma = returns.std()
    
    simulated_returns = np.random.normal(
        mu * horizon,
        sigma * np.sqrt(horizon),
        n_simulations
    )
    
    var_results = {}
    for cl in confidence_levels:
        var = np.percentile(simulated_returns, (1 - cl) * 100)
        cvar = simulated_returns[simulated_returns <= var].mean()
        var_results[f'VaR_{int(cl*100)}'] = float(var * 100)
        var_results[f'CVaR_{int(cl*100)}'] = float(cvar * 100)
    
    return var_results, simulated_returns

def monte_carlo_portfolio(weights, returns_df, n_simulations=1000, 
                          n_days=252):
    """
    Simulation Monte Carlo d'un portefeuille multi-actifs
    """
    # Paramètres du portefeuille
    mean_returns = returns_df.mean()
    cov_matrix = returns_df.cov()
    
    portfolio_simulations = []
    
    for _ in range(n_simulations):
        # Générer des rendements corrélés via Cholesky
        L = np.linalg.cholesky(cov_matrix + 
                               np.eye(len(cov_matrix)) * 1e-8)
        Z = np.random.normal(0, 1, (n_days, len(weights)))
        correlated_returns = Z @ L.T + mean_returns.values
        
        # Rendement du portefeuille
        portfolio_returns = correlated_returns @ weights
        cumulative = np.cumprod(1 + portfolio_returns)
        portfolio_simulations.append(cumulative)
    
    simulations = np.array(portfolio_simulations).T
    
    final_values = simulations[-1, :]
    stats = {
        'valeur_mediane': float(np.median(final_values)),
        'valeur_moyenne': float(np.mean(final_values)),
        'var_95_portfolio': float(np.percentile(final_values, 5)),
        'prob_gain': float((final_values > 1.0).mean() * 100),
        'prob_perte_10': float((final_values < 0.9).mean() * 100),
    }
    
    return simulations, stats