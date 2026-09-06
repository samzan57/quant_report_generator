# modules/stress_testing.py
import numpy as np
import pandas as pd

# Crises historiques avec leurs caractéristiques
HISTORICAL_CRISES = {
    'Crise 2008 (Subprime)': {
        'description': 'Crise des subprimes et faillite de Lehman Brothers',
        'date_debut': '2008-09-01',
        'date_fin': '2009-03-31',
        'choc_marche': -0.50,      # S&P 500 a chuté de ~50%
        'choc_volatilite': 3.5,    # Volatilité multipliée par 3.5
        'choc_correlation': 0.85,  # Corrélations proches de 1
        'duree_jours': 180,
    },
    'COVID-19 (2020)': {
        'description': 'Pandémie mondiale et arrêt de l économie',
        'date_debut': '2020-02-20',
        'date_fin': '2020-03-23',
        'choc_marche': -0.34,
        'choc_volatilite': 4.0,
        'choc_correlation': 0.90,
        'duree_jours': 33,
    },
    'Crise Dot-com (2000)': {
        'description': 'Éclatement de la bulle internet',
        'date_debut': '2000-03-10',
        'date_fin': '2002-10-09',
        'choc_marche': -0.49,
        'choc_volatilite': 2.5,
        'choc_correlation': 0.70,
        'duree_jours': 929,
    },
    'Flash Crash (2010)': {
        'description': 'Krach éclair du 6 mai 2010',
        'date_debut': '2010-05-06',
        'date_fin': '2010-05-06',
        'choc_marche': -0.09,
        'choc_volatilite': 5.0,
        'choc_correlation': 0.95,
        'duree_jours': 1,
    },
    'Crise Dette Européenne (2011)': {
        'description': 'Crise de la dette souveraine en Europe',
        'date_debut': '2011-07-01',
        'date_fin': '2011-10-03',
        'choc_marche': -0.19,
        'choc_volatilite': 2.0,
        'choc_correlation': 0.75,
        'duree_jours': 94,
    },
    'Krach Obligataire (2022)': {
        'description': 'Hausse agressive des taux par la Fed',
        'date_debut': '2022-01-01',
        'date_fin': '2022-10-13',
        'choc_marche': -0.25,
        'choc_volatilite': 2.2,
        'choc_correlation': 0.80,
        'duree_jours': 285,
    },
}

def apply_historical_stress(returns, crisis_name):
    """
    Applique un choc historique aux rendements actuels
    et simule l'impact sur le portefeuille
    """
    if crisis_name not in HISTORICAL_CRISES:
        return None

    crisis = HISTORICAL_CRISES[crisis_name]
    
    # Paramètres actuels
    current_vol = returns.std() * np.sqrt(252)
    current_mean = returns.mean() * 252

    # Choc appliqué
    choc_marche = crisis['choc_marche']
    choc_vol = crisis['choc_volatilite']
    duree = crisis['duree_jours']

    # Simuler les rendements sous stress
    stressed_vol = current_vol * choc_vol / np.sqrt(252)
    stressed_mean = choc_marche / duree  # Rendement journalier moyen sous stress

    np.random.seed(42)
    stressed_returns = np.random.normal(
        stressed_mean, stressed_vol, duree
    )
    stressed_series = pd.Series(stressed_returns)

    # Impact total
    cumulative_loss = float((1 + stressed_series).cumprod().iloc[-1] - 1) * 100
    max_daily_loss = float(stressed_series.min() * 100)
    var_stress = float(np.percentile(stressed_series, 5) * 100)

    result = {
        'nom': crisis_name,
        'description': crisis['description'],
        'duree_jours': duree,
        'choc_marche_historique': float(choc_marche * 100),
        'perte_simulee': cumulative_loss,
        'perte_max_journaliere': max_daily_loss,
        'var_sous_stress': var_stress,
        'volatilite_multipliee': choc_vol,
        'stressed_returns': stressed_series,
    }

    return result

def scenario_analysis(returns, scenarios=None):
    """
    Analyse de scénarios personnalisés
    """
    if scenarios is None:
        scenarios = {
            'Scénario Pessimiste (-20%)': -0.20,
            'Scénario Très Pessimiste (-40%)': -0.40,
            'Scénario Crash (-60%)': -0.60,
            'Scénario Optimiste (+20%)': 0.20,
            'Scénario Très Optimiste (+40%)': 0.40,
        }

    current_vol = returns.std() * np.sqrt(252)
    results = {}

    for scenario_name, choc in scenarios.items():
        duree = 252  # 1 an
        daily_return = choc / duree
        daily_vol = current_vol / np.sqrt(252)

        np.random.seed(42)
        sim_returns = np.random.normal(daily_return, daily_vol, duree)
        sim_series = pd.Series(sim_returns)

        cumulative = float((1 + sim_series).cumprod().iloc[-1] - 1) * 100
        max_dd = float(
            ((1 + sim_series).cumprod() /
             (1 + sim_series).cumprod().expanding().max() - 1).min() * 100
        )

        results[scenario_name] = {
            'choc_applique': float(choc * 100),
            'perte_gain_simule': cumulative,
            'max_drawdown': max_dd,
            'var_95': float(np.percentile(sim_returns, 5) * 100),
        }

    return results

def run_all_stress_tests(returns):
    """Lance tous les stress tests et scénarios"""
    results = {
        'crises_historiques': {},
        'scenarios': {},
        'resume': {}
    }

    # Stress tests historiques
    print("  Stress tests historiques...")
    for crisis_name in HISTORICAL_CRISES.keys():
        result = apply_historical_stress(returns, crisis_name)
        if result:
            results['crises_historiques'][crisis_name] = result
            print(f"    ✓ {crisis_name}: {result['perte_simulee']:.1f}%")

    # Analyse de scénarios
    print("  Analyse de scénarios...")
    results['scenarios'] = scenario_analysis(returns)

    # Résumé
    pertes = [
        r['perte_simulee']
        for r in results['crises_historiques'].values()
    ]
    if pertes:
        results['resume'] = {
            'pire_scenario': min(pertes),
            'meilleur_scenario': max(pertes),
            'perte_moyenne': np.mean(pertes),
            'crise_la_plus_impactante': min(
                results['crises_historiques'].items(),
                key=lambda x: x[1]['perte_simulee']
            )[0]
        }

    return results