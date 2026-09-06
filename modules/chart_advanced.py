# modules/chart_advanced.py
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import numpy as np
import pandas as pd
import os
from config import OUTPUT_DIR

plt.style.use('dark_background')
COLORS = {
    'primary': '#00D4FF',
    'secondary': '#FF6B35',
    'success': '#00FF88',
    'danger': '#FF4444',
    'warning': '#FFD700',
    'purple': '#9B59B6',
    'pink': '#FF69B4',
    'background': '#0D1117',
    'grid': '#21262D'
}

def save_fig(fig, filename):
    path = os.path.join(OUTPUT_DIR, filename)
    fig.patch.set_facecolor(COLORS['background'])
    fig.savefig(path, dpi=150, bbox_inches='tight',
                facecolor=COLORS['background'])
    plt.close(fig)
    return path

def setup_ax(ax, title, xlabel="", ylabel=""):
    ax.set_facecolor(COLORS['background'])
    ax.set_title(title, color='white', fontsize=13,
                 fontweight='bold', pad=15)
    ax.set_xlabel(xlabel, color='#8B949E', fontsize=10)
    ax.set_ylabel(ylabel, color='#8B949E', fontsize=10)
    ax.tick_params(colors='#8B949E')
    ax.grid(True, color=COLORS['grid'], alpha=0.5, linestyle='--')
    for spine in ax.spines.values():
        spine.set_edgecolor(COLORS['grid'])

# ── ROLLING METRICS ──────────────────────────────────────────
def plot_rolling_sharpe(rolling_data, asset_name, prefix=""):
    fig, ax = plt.subplots(figsize=(12, 5))
    setup_ax(ax, f"Sharpe Ratio Glissant — {asset_name}", "Date", "Sharpe")

    colors_list = [COLORS['primary'], COLORS['success'], COLORS['warning']]
    windows = [30, 60, 90]

    for i, w in enumerate(windows):
        key = f'sharpe_{w}j'
        if key in rolling_data:
            series = rolling_data[key].dropna()
            ax.plot(series.index, series.values,
                    color=colors_list[i], linewidth=1.5,
                    label=f'Sharpe {w}j')

    ax.axhline(1.0, color=COLORS['success'], linestyle='--',
               linewidth=1, alpha=0.5, label='Seuil = 1')
    ax.axhline(0.0, color='gray', linestyle='-', linewidth=0.8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.xticks(rotation=45)
    ax.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
              labelcolor='white', fontsize=9)
    fig.tight_layout()
    return save_fig(fig, f"{prefix}rolling_sharpe.png")

def plot_rolling_volatility(rolling_data, asset_name, prefix=""):
    fig, ax = plt.subplots(figsize=(12, 5))
    setup_ax(ax, f"Volatilité Glissante — {asset_name}",
             "Date", "Volatilité (%)")

    colors_list = [COLORS['primary'], COLORS['success'], COLORS['warning']]
    windows = [30, 60, 90]

    for i, w in enumerate(windows):
        key = f'volatilite_{w}j'
        if key in rolling_data:
            series = rolling_data[key].dropna()
            ax.plot(series.index, series.values,
                    color=colors_list[i], linewidth=1.5,
                    label=f'Vol {w}j')

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.xticks(rotation=45)
    ax.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
              labelcolor='white', fontsize=9)
    fig.tight_layout()
    return save_fig(fig, f"{prefix}rolling_volatility.png")

# ── MONTE CARLO ───────────────────────────────────────────────
def plot_monte_carlo(simulations, stats, asset_name, prefix=""):
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Graphique 1 : Trajectoires
    ax1 = axes[0]
    setup_ax(ax1, f"Monte Carlo — Trajectoires ({stats['n_simulations']} sim.)",
             "Jours", "Prix")

    n_show = min(200, simulations.shape[1])
    for i in range(n_show):
        ax1.plot(simulations[:, i], color=COLORS['primary'],
                 alpha=0.02, linewidth=0.5)

    # Percentiles
    p5 = np.percentile(simulations, 5, axis=1)
    p50 = np.percentile(simulations, 50, axis=1)
    p95 = np.percentile(simulations, 95, axis=1)

    ax1.plot(p50, color=COLORS['warning'], linewidth=2,
             label='Médiane', zorder=5)
    ax1.plot(p5, color=COLORS['danger'], linewidth=1.5,
             linestyle='--', label='5ème percentile', zorder=5)
    ax1.plot(p95, color=COLORS['success'], linewidth=1.5,
             linestyle='--', label='95ème percentile', zorder=5)
    ax1.axhline(stats['prix_actuel'], color='white',
                linestyle=':', linewidth=1, label='Prix actuel')
    ax1.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
               labelcolor='white', fontsize=9)

    # Graphique 2 : Distribution des prix finaux
    ax2 = axes[1]
    setup_ax(ax2, "Distribution des Prix Finaux",
             "Prix Final", "Fréquence")

    final_prices = simulations[-1, :]
    ax2.hist(final_prices, bins=50, color=COLORS['primary'],
             alpha=0.7, edgecolor='black', linewidth=0.3)
    ax2.axvline(stats['prix_actuel'], color='white',
                linestyle='--', linewidth=2, label='Prix actuel')
    ax2.axvline(stats['var_95'], color=COLORS['danger'],
                linestyle='--', linewidth=2,
                label=f"VaR 95%: {stats['var_95']:.2f}")
    ax2.axvline(stats['prix_median'], color=COLORS['warning'],
                linestyle='--', linewidth=2,
                label=f"Médiane: {stats['prix_median']:.2f}")
    ax2.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
               labelcolor='white', fontsize=9)

    fig.tight_layout()
    return save_fig(fig, f"{prefix}monte_carlo.png")

def plot_monte_carlo_stats(stats, asset_name, prefix=""):
    """Dashboard des statistiques Monte Carlo"""
    fig, axes = plt.subplots(2, 3, figsize=(16, 8))
    fig.suptitle(f"Statistiques Monte Carlo — {asset_name}",
                 color='white', fontsize=15, fontweight='bold')

    metrics = [
        ("Prix Actuel", f"{stats['prix_actuel']:.2f}", COLORS['primary']),
        ("Prix Médian (1an)", f"{stats['prix_median']:.2f}", COLORS['warning']),
        ("Rendement Médian", f"{stats['rendement_median']:.1f}%",
         COLORS['success'] if stats['rendement_median'] > 0 else COLORS['danger']),
        ("Prob. Hausse", f"{stats['prob_hausse']:.1f}%",
         COLORS['success'] if stats['prob_hausse'] > 50 else COLORS['danger']),
        ("Prob. +10%", f"{stats['prob_hausse_10']:.1f}%", COLORS['success']),
        ("Prob. -10%", f"{stats['prob_baisse_10']:.1f}%", COLORS['danger']),
    ]

    for idx, (ax, (label, value, color)) in enumerate(
            zip(axes.flat, metrics)):
        ax.set_facecolor('#161B22')
        ax.text(0.5, 0.6, value, transform=ax.transAxes,
                ha='center', va='center', fontsize=22,
                fontweight='bold', color=color)
        ax.text(0.5, 0.25, label, transform=ax.transAxes,
                ha='center', va='center', fontsize=11, color='#8B949E')
        for spine in ax.spines.values():
            spine.set_edgecolor(color)
            spine.set_linewidth(2)
        ax.set_xticks([])
        ax.set_yticks([])

    fig.patch.set_facecolor(COLORS['background'])
    fig.tight_layout()
    return save_fig(fig, f"{prefix}monte_carlo_stats.png")

# ── BACKTESTING ───────────────────────────────────────────────
def plot_backtest_comparison(backtest_results, asset_name, prefix=""):
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))

    # Graphique 1 : Performance cumulée
    ax1 = axes[0]
    setup_ax(ax1, f"Comparaison des Stratégies — {asset_name}",
             "Date", "Performance Cumulée")

    strategy_colors = [COLORS['primary'], COLORS['success'],
                       COLORS['warning'], COLORS['secondary'],
                       COLORS['purple']]

    for i, (name, data) in enumerate(backtest_results.items()):
        cumulative = data['cumulative'].dropna()
        color = strategy_colors[i % len(strategy_colors)]
        ax1.plot(cumulative.index, cumulative.values,
                 color=color, linewidth=1.8, label=name)

    ax1.axhline(1.0, color='gray', linestyle='--',
                linewidth=0.8, alpha=0.5)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.sca(ax1)
    plt.xticks(rotation=45)
    ax1.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
               labelcolor='white', fontsize=9)

    # Graphique 2 : Métriques comparatives
    ax2 = axes[1]
    setup_ax(ax2, "Métriques par Stratégie", "Stratégie", "Valeur")

    strategies = list(backtest_results.keys())
    sharpes = [backtest_results[s]['metrics'].get('sharpe_ratio', 0)
               for s in strategies]
    returns = [backtest_results[s]['metrics'].get('rendement_total', 0)
               for s in strategies]

    x = np.arange(len(strategies))
    width = 0.35

    bars1 = ax2.bar(x - width/2, returns, width,
                    label='Rendement Total (%)',
                    color=[COLORS['success'] if r > 0 else COLORS['danger']
                           for r in returns],
                    alpha=0.8)
    ax2_twin = ax2.twinx()
    ax2_twin.set_ylabel('Sharpe Ratio', color=COLORS['warning'])
    ax2_twin.tick_params(colors=COLORS['warning'])
    bars2 = ax2_twin.bar(x + width/2, sharpes, width,
                         label='Sharpe Ratio',
                         color=COLORS['warning'], alpha=0.8)

    ax2.set_xticks(x)
    ax2.set_xticklabels(
        [s.replace(' ', '\n') for s in strategies],
        color='white', fontsize=9
    )
    ax2.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
               labelcolor='white', loc='upper left', fontsize=9)
    ax2_twin.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
                    labelcolor='white', loc='upper right', fontsize=9)

    fig.tight_layout()
    return save_fig(fig, f"{prefix}backtest_comparison.png")

# ── STRESS TESTING ────────────────────────────────────────────
def plot_stress_test(stress_results, asset_name, prefix=""):
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # Graphique 1 : Pertes par crise
    ax1 = axes[0]
    setup_ax(ax1, f"Impact des Crises Historiques — {asset_name}",
             "Perte Simulée (%)", "Crise")

    crises = stress_results.get('crises_historiques', {})
    names = [c.replace(' (', '\n(') for c in crises.keys()]
    pertes = [c['perte_simulee'] for c in crises.values()]
    historiques = [c['choc_marche_historique'] for c in crises.values()]

    y_pos = np.arange(len(names))
    ax1.barh(y_pos - 0.2, pertes, 0.4,
             color=COLORS['danger'], alpha=0.8, label='Perte Simulée')
    ax1.barh(y_pos + 0.2, historiques, 0.4,
             color=COLORS['warning'], alpha=0.8, label='Choc Historique')
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(names, color='white', fontsize=8)
    ax1.axvline(0, color='gray', linewidth=0.8)
    ax1.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
               labelcolor='white', fontsize=9)

    # Graphique 2 : Scénarios
    ax2 = axes[1]
    setup_ax(ax2, "Analyse de Scénarios", "Scénario", "Impact (%)")

    scenarios = stress_results.get('scenarios', {})
    sc_names = [s.replace(' (', '\n(').replace(')', '') 
                for s in scenarios.keys()]
    sc_values = [s['perte_gain_simule'] for s in scenarios.values()]

    colors_bar = [COLORS['success'] if v > 0 else COLORS['danger']
                  for v in sc_values]
    bars = ax2.bar(range(len(sc_names)), sc_values,
                   color=colors_bar, alpha=0.8)
    ax2.set_xticks(range(len(sc_names)))
    ax2.set_xticklabels(sc_names, color='white', fontsize=8, rotation=15)
    ax2.axhline(0, color='gray', linewidth=0.8)

    for bar, val in zip(bars, sc_values):
        ax2.text(bar.get_x() + bar.get_width()/2,
                 bar.get_height() + (1 if val > 0 else -3),
                 f'{val:.1f}%', ha='center', color='white', fontsize=9)

    fig.tight_layout()
    return save_fig(fig, f"{prefix}stress_test.png")

# ── FACTOR MODEL ──────────────────────────────────────────────
def plot_factor_model(factor_results, asset_name, prefix=""):
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # Graphique 1 : Comparaison Alpha des modèles
    ax1 = axes[0]
    setup_ax(ax1, f"Alpha par Modèle Factoriel — {asset_name}",
             "Modèle", "Alpha Annualisé (%)")

    model_names = []
    alphas = []
    r_squareds = []

    for key, data in factor_results.items():
        model_names.append(data.get('modele', key))
        alphas.append(data.get('alpha_annualise', 0))
        r_squareds.append(data.get('r_squared', 0))

    colors_bar = [COLORS['success'] if a > 0 else COLORS['danger']
                  for a in alphas]
    bars = ax1.bar(range(len(model_names)), alphas,
                   color=colors_bar, alpha=0.8)
    ax1.set_xticks(range(len(model_names)))
    ax1.set_xticklabels(model_names, color='white', fontsize=10)
    ax1.axhline(0, color='gray', linewidth=0.8)

    for bar, val in zip(bars, alphas):
        ax1.text(bar.get_x() + bar.get_width()/2,
                 bar.get_height() + (0.1 if val > 0 else -0.3),
                 f'{val:.2f}%', ha='center', color='white', fontsize=10)

    # Graphique 2 : Betas par facteur (FF5)
    ax2 = axes[1]
    setup_ax(ax2, "Exposition aux Facteurs (FF5)",
             "Facteur", "Beta")

    if 'ff5' in factor_results:
        ff5 = factor_results['ff5']
        factors = ['Marché', 'SMB', 'HML', 'RMW', 'CMA']
        betas = [
            ff5.get('beta_marche', 0),
            ff5.get('beta_smb', 0),
            ff5.get('beta_hml', 0),
            ff5.get('beta_rmw', 0),
            ff5.get('beta_cma', 0),
        ]
        colors_bar = [COLORS['success'] if b > 0 else COLORS['danger']
                      for b in betas]
        bars = ax2.bar(factors, betas, color=colors_bar, alpha=0.8)
        ax2.axhline(0, color='gray', linewidth=0.8)
        ax2.set_xticklabels(factors, color='white')

        for bar, val in zip(bars, betas):
            ax2.text(bar.get_x() + bar.get_width()/2,
                     bar.get_height() + (0.01 if val > 0 else -0.03),
                     f'{val:.3f}', ha='center', color='white', fontsize=9)
    else:
        ax2.text(0.5, 0.5, 'Données insuffisantes',
                 transform=ax2.transAxes, ha='center',
                 color='white', fontsize=12)

    fig.tight_layout()
    return save_fig(fig, f"{prefix}factor_model.png")

# ── PORTFOLIO OPTIMIZATION ────────────────────────────────────
def plot_efficient_frontier(portfolio_results, prefix=""):
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # Graphique 1 : Frontière efficiente
    ax1 = axes[0]
    setup_ax(ax1, "Frontière Efficiente de Markowitz",
             "Volatilité (%)", "Rendement (%)")

    frontier = portfolio_results.get('frontier', {})
    if frontier and frontier['volatilites']:
        sharpes = frontier['sharpes']
        sc = ax1.scatter(frontier['volatilites'], frontier['rendements'],
                        c=sharpes, cmap='RdYlGn', s=20, zorder=3)
        plt.colorbar(sc, ax=ax1, label='Sharpe Ratio')

    portfolios = portfolio_results.get('portfolios', {})
    port_colors = {
        'equal_weight': (COLORS['primary'], 'Équipondéré', '*'),
        'min_variance': (COLORS['success'], 'Var. Minimale', 'D'),
        'max_sharpe': (COLORS['warning'], 'Sharpe Max', '^'),
        'risk_parity': (COLORS['purple'], 'Risk Parity', 's'),
    }

    for key, (color, label, marker) in port_colors.items():
        if key in portfolios:
            p = portfolios[key]
            ax1.scatter(p['volatilite'], p['rendement'],
                       color=color, s=200, marker=marker,
                       zorder=5, label=label,
                       edgecolors='white', linewidth=1.5)

    ax1.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
               labelcolor='white', fontsize=9)

    # Graphique 2 : Composition des portefeuilles
    ax2 = axes[1]
    setup_ax(ax2, "Composition des Portefeuilles Optimaux",
             "", "Allocation (%)")

    asset_names = portfolio_results.get('asset_names', [])
    port_names = []
    allocations = []

    for key, (_, label, _) in port_colors.items():
        if key in portfolios:
            port_names.append(label)
            allocations.append(
                portfolios[key]['weights'] * 100
            )

    if allocations:
        x = np.arange(len(port_names))
        width = 0.8 / len(asset_names)
        bar_colors = [COLORS['primary'], COLORS['success'],
                      COLORS['warning'], COLORS['secondary'],
                      COLORS['purple']]

        for i, asset in enumerate(asset_names):
            vals = [alloc[i] if i < len(alloc) else 0
                    for alloc in allocations]
            ax2.bar(x + i * width, vals, width,
                   label=asset,
                   color=bar_colors[i % len(bar_colors)],
                   alpha=0.8)

        ax2.set_xticks(x + width * len(asset_names) / 2)
        ax2.set_xticklabels(port_names, color='white', fontsize=9)
        ax2.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
                   labelcolor='white', fontsize=9)

    fig.tight_layout()
    return save_fig(fig, f"{prefix}portfolio_optimization.png")

def plot_portfolio_comparison(portfolio_results, prefix=""):
    """Tableau comparatif des portefeuilles"""
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.set_facecolor(COLORS['background'])
    ax.axis('off')
    fig.patch.set_facecolor(COLORS['background'])

    portfolios = portfolio_results.get('portfolios', {})
    asset_names = portfolio_results.get('asset_names', [])

    if not portfolios:
        return None

    headers = ['Stratégie', 'Rendement', 'Volatilité',
               'Sharpe'] + asset_names
    rows = []

    port_labels = {
        'equal_weight': 'Équipondéré',
        'min_variance': 'Var. Minimale',
        'max_sharpe': 'Sharpe Max',
        'risk_parity': 'Risk Parity',
    }

    for key, label in port_labels.items():
        if key in portfolios:
            p = portfolios[key]
            row = [
                label,
                f"{p['rendement']:.1f}%",
                f"{p['volatilite']:.1f}%",
                f"{p['sharpe']:.3f}",
            ]
            for i in range(len(asset_names)):
                w = p['weights'][i] * 100 if i < len(p['weights']) else 0
                row.append(f"{w:.1f}%")
            rows.append(row)

    table = ax.table(
        cellText=rows,
        colLabels=headers,
        cellLoc='center',
        loc='center',
    )
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1.2, 2.5)

    for (row, col), cell in table.get_celld().items():
        cell.set_facecolor('#161B22' if row > 0 else '#00D4FF')
        cell.set_text_props(
            color='#0D1117' if row == 0 else 'white'
        )
        cell.set_edgecolor(COLORS['grid'])

    ax.set_title("Comparaison des Stratégies d'Allocation",
                 color='white', fontsize=14, fontweight='bold', pad=20)

    fig.tight_layout()
    return save_fig(fig, f"{prefix}portfolio_comparison.png")


def generate_advanced_charts(advanced_results, prefix=""):
    """Génère tous les graphiques avancés"""
    chart_paths = []
    asset_name = prefix.split('_')[1] if '_' in prefix else 'Actif'

    # Rolling Metrics
    if 'rolling' in advanced_results:
        print("    Graphiques rolling metrics...")
        chart_paths.append(
            plot_rolling_sharpe(
                advanced_results['rolling'], asset_name, prefix
            )
        )
        chart_paths.append(
            plot_rolling_volatility(
                advanced_results['rolling'], asset_name, prefix
            )
        )

    # Monte Carlo
    if 'monte_carlo' in advanced_results:
        print("    Graphiques Monte Carlo...")
        mc = advanced_results['monte_carlo']
        chart_paths.append(
            plot_monte_carlo(
                mc['simulations'], mc['stats'], asset_name, prefix
            )
        )
        chart_paths.append(
            plot_monte_carlo_stats(mc['stats'], asset_name, prefix)
        )

    # Backtesting
    if 'backtest' in advanced_results:
        print("    Graphiques backtesting...")
        chart_paths.append(
            plot_backtest_comparison(
                advanced_results['backtest'], asset_name, prefix
            )
        )

    # Stress Testing
    if 'stress' in advanced_results:
        print("    Graphiques stress testing...")
        chart_paths.append(
            plot_stress_test(
                advanced_results['stress'], asset_name, prefix
            )
        )

    # Factor Model
    if 'factors' in advanced_results:
        print("    Graphiques factor model...")
        chart_paths.append(
            plot_factor_model(
                advanced_results['factors'], asset_name, prefix
            )
        )

    # Portfolio Optimization
    if 'portfolio' in advanced_results and advanced_results['portfolio']:
        print("    Graphiques optimisation portefeuille...")
        chart_paths.append(
            plot_efficient_frontier(
                advanced_results['portfolio'], prefix
            )
        )
        chart_paths.append(
            plot_portfolio_comparison(
                advanced_results['portfolio'], prefix
            )
        )
    
    # Signaux de trading
    if 'signals' in advanced_results and advanced_results['signals']:
        print("    Graphiques signaux de trading...")
        try:
            chart_paths.append(
                plot_signals_dashboard(
                    advanced_results['signals'],
                    asset_name,
                    None,
                    prefix
                )
            )
        except Exception as e:
            print(f"    ⚠ Graphique signaux échoué : {e}")
    # Black-Scholes
    if 'black_scholes' in advanced_results and advanced_results['black_scholes']:
        print("    Graphiques Black-Scholes...")
        try:
            bs_paths = generate_bs_charts(
                advanced_results['black_scholes'],
                asset_name,
                prefix
            )
            chart_paths.extend(bs_paths)
        except Exception as e:
            print(f"    ⚠ Graphiques BS échoués : {e}")
            import traceback
            traceback.print_exc()
    # Monte Carlo Options
    if 'mc_options' in advanced_results and advanced_results['mc_options']:
        print("    Graphiques MC Options...")
        try:
            mc_paths = generate_mc_options_charts(
                advanced_results['mc_options'],
                asset_name,
                prefix
            )
            chart_paths.extend(mc_paths)
        except Exception as e:
            print(f"    ⚠ Graphiques MC Options échoués : {e}")
    # Heston
    if 'heston' in advanced_results and advanced_results['heston']:
        print("    Graphiques Heston...")
        try:
            heston_paths = generate_heston_charts(
                advanced_results['heston'],
                asset_name,
                prefix
            )
            chart_paths.extend(heston_paths)
        except Exception as e:
            print(f"    ⚠ Graphiques Heston échoués : {e}")

    return [p for p in chart_paths if p is not None]

   # ── TRADING SIGNALS ───────────────────────────────────────────
def plot_signals_dashboard(signals_data, asset_name, prices, prefix=""):
    """Dashboard visuel des signaux de trading"""
    fig = plt.figure(figsize=(16, 10))
    fig.patch.set_facecolor(COLORS['background'])

    # Layout : signal final en haut, signaux individuels en bas
    gs = fig.add_gridspec(3, 4, hspace=0.5, wspace=0.4)

    # ── Signal Final (grande carte en haut) ──
    ax_main = fig.add_subplot(gs[0, :])
    ax_main.set_facecolor('#161B22')
    ax_main.axis('off')

    final = signals_data.get('signal_final', {})
    signal = final.get('signal_final', 'NEUTRE')
    conviction = final.get('conviction_finale', 50)
    emoji = final.get('emoji', '🟡')

    signal_color = (COLORS['success'] if signal == 'ACHETER'
                    else COLORS['danger'] if signal == 'VENDRE'
                    else COLORS['warning'])

    # Fond coloré selon signal
    bg_color = ('#003300' if signal == 'ACHETER'
                else '#330000' if signal == 'VENDRE'
                else '#333300')
    for spine in ax_main.spines.values():
        spine.set_edgecolor(signal_color)
        spine.set_linewidth(3)

    ax_main.text(0.5, 0.75,
                 f"SIGNAL : {signal}  —  Conviction : {conviction:.0f}%",
                 transform=ax_main.transAxes, ha='center', va='center',
                 fontsize=24, fontweight='bold', color=signal_color)

    ax_main.text(0.5, 0.3,
                 final.get('interpretation', ''),
                 transform=ax_main.transAxes, ha='center', va='center',
                 fontsize=13, color='white')

    nb_buy = final.get('nb_signaux_achat', 0)
    nb_sell = final.get('nb_signaux_vente', 0)
    nb_neutral = final.get('nb_signaux_neutres', 0)
    ax_main.text(0.15, 0.3,
                 f"🟢 {nb_buy} Achat",
                 transform=ax_main.transAxes, ha='center',
                 fontsize=12, color=COLORS['success'])
    ax_main.text(0.85, 0.3,
                 f"🔴 {nb_sell} Vente",
                 transform=ax_main.transAxes, ha='center',
                 fontsize=12, color=COLORS['danger'])

    ax_main.set_title(f"SIGNAUX DE TRADING EN TEMPS RÉEL — {asset_name.upper()}"
                      f"  |  Prix actuel : {signals_data.get('prix_actuel', 0):.2f}"
                      f"  |  Date : {signals_data.get('date_signal', '')}",
                      color='white', fontsize=13, fontweight='bold', pad=10)

    # ── Signaux individuels ──
    signaux = signals_data.get('signaux_individuels', [])
    axes_signals = [
        fig.add_subplot(gs[1, 0]),
        fig.add_subplot(gs[1, 1]),
        fig.add_subplot(gs[1, 2]),
        fig.add_subplot(gs[1, 3]),
        fig.add_subplot(gs[2, 0]),
        fig.add_subplot(gs[2, 1]),
    ]

    for i, (ax, sig) in enumerate(zip(axes_signals, signaux)):
        if sig is None:
            ax.axis('off')
            continue

        s_color = (COLORS['success'] if sig['signal'] == 'ACHETER'
                   else COLORS['danger'] if sig['signal'] == 'VENDRE'
                   else COLORS['warning'])

        ax.set_facecolor('#161B22')
        ax.axis('off')
        for spine in ax.spines.values():
            spine.set_edgecolor(s_color)
            spine.set_linewidth(2)

        ax.text(0.5, 0.82, sig['indicateur'],
                transform=ax.transAxes, ha='center',
                fontsize=9, color='#8B949E', fontweight='bold')
        ax.text(0.5, 0.58, sig['signal'],
                transform=ax.transAxes, ha='center',
                fontsize=16, fontweight='bold', color=s_color)
        ax.text(0.5, 0.38, f"Conviction : {sig['conviction']:.0f}%",
                transform=ax.transAxes, ha='center',
                fontsize=9, color='white')
        ax.text(0.5, 0.15, sig['raison'],
                transform=ax.transAxes, ha='center',
                fontsize=7, color=COLORS['warning'], wrap=True)

    # ── Gauge de conviction (jauge visuelle) ──
    ax_gauge = fig.add_subplot(gs[2, 2:])
    ax_gauge.set_facecolor(COLORS['background'])
    setup_ax(ax_gauge, "Score Achat vs Vente", "", "Score (%)")

    categories = ['Score\nAchat', 'Score\nVente']
    scores = [final.get('score_achat', 0), final.get('score_vente', 0)]
    colors_gauge = [COLORS['success'], COLORS['danger']]

    bars = ax_gauge.bar(categories, scores, color=colors_gauge,
                        alpha=0.85, width=0.4)
    ax_gauge.set_ylim(0, 100)
    ax_gauge.axhline(50, color='white', linestyle='--',
                     linewidth=1, alpha=0.5, label='Seuil 50%')

    for bar, score in zip(bars, scores):
        ax_gauge.text(bar.get_x() + bar.get_width()/2,
                      bar.get_height() + 2,
                      f'{score:.1f}%', ha='center',
                      color='white', fontsize=14, fontweight='bold')

    ax_gauge.tick_params(colors='white')
    ax_gauge.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
                    labelcolor='white', fontsize=9)

    return save_fig(fig, f"{prefix}trading_signals.png") 

# ── BLACK-SCHOLES & OPTIONS ───────────────────────────────────
def plot_greeks_dashboard(bs_results, asset_name, prefix=""):
    """Dashboard des Greeks"""
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle(f"Greeks Black-Scholes — {asset_name} (ATM, 3 mois)",
                 color='white', fontsize=15, fontweight='bold')
    fig.patch.set_facecolor(COLORS['background'])

    S = bs_results['parametres']['S']
    sigma = bs_results['parametres']['sigma'] / 100
    r = bs_results['parametres']['r'] / 100
    T = 3/12
    K_atm = round(S, 2)

    # Range de prix du sous-jacent
    S_range = np.linspace(S * 0.7, S * 1.3, 200)

    # ── Delta ──
    ax = axes[0, 0]
    setup_ax(ax, "Delta", "Prix Sous-jacent", "Delta")
    call_deltas = [delta(s, K_atm, T, r, sigma, 'call') for s in S_range]
    put_deltas = [delta(s, K_atm, T, r, sigma, 'put') for s in S_range]
    ax.plot(S_range, call_deltas, color=COLORS['success'],
            linewidth=2, label='Call Delta')
    ax.plot(S_range, put_deltas, color=COLORS['danger'],
            linewidth=2, label='Put Delta')
    ax.axvline(S, color='white', linestyle='--', linewidth=1,
               label=f'Prix actuel ({S:.2f})')
    ax.axhline(0, color='gray', linewidth=0.8)
    ax.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
              labelcolor='white', fontsize=8)

    # ── Gamma ──
    ax = axes[0, 1]
    setup_ax(ax, "Gamma", "Prix Sous-jacent", "Gamma")
    gammas = [gamma(s, K_atm, T, r, sigma) for s in S_range]
    ax.plot(S_range, gammas, color=COLORS['primary'],
            linewidth=2, label='Gamma')
    ax.axvline(S, color='white', linestyle='--', linewidth=1)
    ax.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
              labelcolor='white', fontsize=8)

    # ── Vega ──
    ax = axes[0, 2]
    setup_ax(ax, "Vega (pour 1% vol)", "Prix Sous-jacent", "Vega")
    vegas = [vega(s, K_atm, T, r, sigma) for s in S_range]
    ax.plot(S_range, vegas, color=COLORS['warning'],
            linewidth=2, label='Vega')
    ax.axvline(S, color='white', linestyle='--', linewidth=1)
    ax.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
              labelcolor='white', fontsize=8)

    # ── Theta ──
    ax = axes[1, 0]
    setup_ax(ax, "Theta (par jour)", "Prix Sous-jacent", "Theta")
    call_thetas = [theta(s, K_atm, T, r, sigma, 'call') for s in S_range]
    put_thetas = [theta(s, K_atm, T, r, sigma, 'put') for s in S_range]
    ax.plot(S_range, call_thetas, color=COLORS['success'],
            linewidth=2, label='Call Theta')
    ax.plot(S_range, put_thetas, color=COLORS['danger'],
            linewidth=2, label='Put Theta')
    ax.axvline(S, color='white', linestyle='--', linewidth=1)
    ax.axhline(0, color='gray', linewidth=0.8)
    ax.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
              labelcolor='white', fontsize=8)

    # ── Rho ──
    ax = axes[1, 1]
    setup_ax(ax, "Rho (pour 1% taux)", "Prix Sous-jacent", "Rho")
    call_rhos = [rho(s, K_atm, T, r, sigma, 'call') for s in S_range]
    put_rhos = [rho(s, K_atm, T, r, sigma, 'put') for s in S_range]
    ax.plot(S_range, call_rhos, color=COLORS['success'],
            linewidth=2, label='Call Rho')
    ax.plot(S_range, put_rhos, color=COLORS['danger'],
            linewidth=2, label='Put Rho')
    ax.axvline(S, color='white', linestyle='--', linewidth=1)
    ax.axhline(0, color='gray', linewidth=0.8)
    ax.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
              labelcolor='white', fontsize=8)

    # ── Prix Option vs Maturité ──
    ax = axes[1, 2]
    setup_ax(ax, "Prix Option vs Maturité (ATM)",
             "Maturité (mois)", "Prix Option")
    mats = np.linspace(1/252, 2, 100)
    call_prices = [black_scholes_call(S, K_atm, t, r, sigma)
                   for t in mats]
    put_prices = [black_scholes_put(S, K_atm, t, r, sigma)
                  for t in mats]
    ax.plot(mats * 12, call_prices, color=COLORS['success'],
            linewidth=2, label='Call')
    ax.plot(mats * 12, put_prices, color=COLORS['danger'],
            linewidth=2, label='Put')
    ax.axvline(3, color='white', linestyle='--', linewidth=1,
               label='3 mois')
    ax.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
              labelcolor='white', fontsize=8)

    fig.tight_layout()
    return save_fig(fig, f"{prefix}greeks_dashboard.png")

def plot_volatility_surface(bs_results, asset_name, prefix=""):
    """Surface de volatilité implicite en 3D"""
    from mpl_toolkits.mplot3d import Axes3D

    surface_df = bs_results.get('surface_vol')
    if surface_df is None:
        return None

    fig = plt.figure(figsize=(14, 8))
    fig.patch.set_facecolor(COLORS['background'])
    ax = fig.add_subplot(111, projection='3d')
    ax.set_facecolor(COLORS['background'])

    X = np.arange(len(surface_df.columns))
    Y = np.arange(len(surface_df.index))
    X, Y = np.meshgrid(X, Y)
    Z = surface_df.values * 100  # En pourcentage

    surf = ax.plot_surface(X, Y, Z, cmap='RdYlGn_r',
                           alpha=0.9, edgecolor='none')

    ax.set_xticks(range(len(surface_df.columns)))
    ax.set_xticklabels(surface_df.columns,
                       color='white', fontsize=7, rotation=45)
    ax.set_yticks(range(len(surface_df.index)))
    ax.set_yticklabels(surface_df.index, color='white', fontsize=8)
    ax.set_zlabel('Vol Implicite (%)', color='white', fontsize=10)
    ax.set_xlabel('Strike', color='white', fontsize=10)
    ax.set_ylabel('Maturité', color='white', fontsize=10)
    ax.tick_params(colors='white')
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False

    fig.colorbar(surf, ax=ax, shrink=0.5, label='Vol Implicite (%)')
    ax.set_title(f"Surface de Volatilité Implicite — {asset_name}",
                 color='white', fontsize=13, fontweight='bold', pad=20)

    return save_fig(fig, f"{prefix}vol_surface.png")

def plot_options_payoff(bs_results, asset_name, prefix=""):
    """Graphique des payoffs des options"""
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.patch.set_facecolor(COLORS['background'])

    S = bs_results['parametres']['S']
    sigma = bs_results['parametres']['sigma'] / 100
    r = bs_results['parametres']['r'] / 100
    T = 3/12
    K = round(S, 2)

    call_price = black_scholes_call(S, K, T, r, sigma)
    put_price = black_scholes_put(S, K, T, r, sigma)

    S_range = np.linspace(S * 0.7, S * 1.3, 300)

    # ── Payoff Call ──
    ax1 = axes[0]
    setup_ax(ax1, f"Payoff Call ATM — {asset_name}",
             "Prix à Maturité", "Profit/Perte")

    payoff_call = np.maximum(S_range - K, 0) - call_price
    intrinsic_call = np.maximum(S_range - K, 0)

    ax1.plot(S_range, payoff_call, color=COLORS['success'],
             linewidth=2.5, label=f'P&L Call (prime={call_price:.2f})')
    ax1.plot(S_range, intrinsic_call, color=COLORS['primary'],
             linewidth=1.5, linestyle='--', label='Valeur intrinsèque')
    ax1.axhline(0, color='gray', linewidth=1)
    ax1.axvline(K, color='white', linestyle='--', linewidth=1,
                label=f'Strike K={K:.2f}')
    ax1.axvline(S, color=COLORS['warning'], linestyle=':',
                linewidth=1.5, label=f'Prix actuel={S:.2f}')
    ax1.fill_between(S_range, payoff_call, 0,
                     where=(payoff_call > 0),
                     alpha=0.15, color=COLORS['success'])
    ax1.fill_between(S_range, payoff_call, 0,
                     where=(payoff_call < 0),
                     alpha=0.15, color=COLORS['danger'])
    ax1.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
               labelcolor='white', fontsize=9)

    # ── Payoff Put ──
    ax2 = axes[1]
    setup_ax(ax2, f"Payoff Put ATM — {asset_name}",
             "Prix à Maturité", "Profit/Perte")

    payoff_put = np.maximum(K - S_range, 0) - put_price
    intrinsic_put = np.maximum(K - S_range, 0)

    ax2.plot(S_range, payoff_put, color=COLORS['danger'],
             linewidth=2.5, label=f'P&L Put (prime={put_price:.2f})')
    ax2.plot(S_range, intrinsic_put, color=COLORS['primary'],
             linewidth=1.5, linestyle='--', label='Valeur intrinsèque')
    ax2.axhline(0, color='gray', linewidth=1)
    ax2.axvline(K, color='white', linestyle='--', linewidth=1,
                label=f'Strike K={K:.2f}')
    ax2.axvline(S, color=COLORS['warning'], linestyle=':',
                linewidth=1.5, label=f'Prix actuel={S:.2f}')
    ax2.fill_between(S_range, payoff_put, 0,
                     where=(payoff_put > 0),
                     alpha=0.15, color=COLORS['success'])
    ax2.fill_between(S_range, payoff_put, 0,
                     where=(payoff_put < 0),
                     alpha=0.15, color=COLORS['danger'])
    ax2.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
               labelcolor='white', fontsize=9)

    fig.tight_layout()
    return save_fig(fig, f"{prefix}options_payoff.png")

def plot_bs_summary(bs_results, asset_name, prefix=""):
    """Tableau récapitulatif des prix et Greeks"""
    fig, ax = plt.subplots(figsize=(16, 7))
    ax.set_facecolor(COLORS['background'])
    fig.patch.set_facecolor(COLORS['background'])
    ax.axis('off')

    headers = ['Maturité', 'Strike', 'Call Prix',
               'Put Prix', 'Delta C', 'Delta P',
               'Gamma', 'Vega', 'Theta C', 'Prob Ex.']
    rows = []

    for mat_name, mat_data in bs_results['options'].items():
        call = mat_data['call']
        put = mat_data['put']
        cg = call['greeks']
        pg = put['greeks']
        rows.append([
            mat_name,
            f"{mat_data['K']:.2f}",
            f"{cg['prix']:.4f}",
            f"{pg['prix']:.4f}",
            f"{cg['delta']:.4f}",
            f"{pg['delta']:.4f}",
            f"{cg['gamma']:.6f}",
            f"{cg['vega']:.4f}",
            f"{cg['theta']:.4f}",
            f"{call['prob_exercise']:.1f}%",
        ])

    table = ax.table(
        cellText=rows,
        colLabels=headers,
        cellLoc='center',
        loc='center',
    )
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1.2, 2.8)

    for (row, col), cell in table.get_celld().items():
        cell.set_facecolor('#161B22' if row > 0 else '#00D4FF')
        cell.set_text_props(
            color='#0D1117' if row == 0 else 'white'
        )
        cell.set_edgecolor(COLORS['grid'])

    ax.set_title(
        f"Récapitulatif Black-Scholes — {asset_name} "
        f"(S={bs_results['parametres']['S']:.2f}, "
        f"σ={bs_results['parametres']['sigma']:.1f}%, "
        f"r={bs_results['parametres']['r']:.1f}%)",
        color='white', fontsize=13, fontweight='bold', pad=20
    )

    fig.tight_layout()
    return save_fig(fig, f"{prefix}bs_summary.png")

def generate_bs_charts(bs_results, asset_name, prefix=""):
    """Génère tous les graphiques Black-Scholes"""
    from modules.black_scholes import (
        black_scholes_call, black_scholes_put,
        delta, gamma, vega, theta, rho
    )

    chart_paths = []
    print("    Graphique Greeks...")
    p = plot_greeks_dashboard(bs_results, asset_name, prefix)
    if p:
        chart_paths.append(p)

    print("    Graphique Payoffs...")
    p = plot_options_payoff(bs_results, asset_name, prefix)
    if p:
        chart_paths.append(p)

    print("    Surface de volatilité...")
    p = plot_volatility_surface(bs_results, asset_name, prefix)
    if p:
        chart_paths.append(p)

    print("    Tableau BS...")
    p = plot_bs_summary(bs_results, asset_name, prefix)
    if p:
        chart_paths.append(p)

    return [p for p in chart_paths if p is not None]

# ── MONTE CARLO OPTIONS ───────────────────────────────────────
def plot_mc_options_comparison(mc_results, asset_name, prefix=""):
    """Comparaison des prix de toutes les options"""
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.patch.set_facecolor(COLORS['background'])

    # ── Graphique 1 : Comparaison des prix ──
    ax1 = axes[0]
    setup_ax(ax1, f"Comparaison des Prix d'Options — {asset_name}",
             "Type d'Option", "Prix")

    comparaison = mc_results.get('comparaison', {})
    names = list(comparaison.keys())
    prices = list(comparaison.values())

    bar_colors = [
        COLORS['primary'],    # Call Vanille BS
        COLORS['success'],    # Call Vanille MC
        COLORS['warning'],    # Call Asiatique
        COLORS['danger'],     # Call Barrière KO
        COLORS['purple'],     # Call Barrière KI
        COLORS['pink'],       # Call Lookback
        COLORS['secondary'],  # Digital Call
    ]

    bars = ax1.bar(range(len(names)), prices,
                   color=bar_colors[:len(names)], alpha=0.85)
    ax1.set_xticks(range(len(names)))
    ax1.set_xticklabels(
        [n.replace(' ', '\n') for n in names],
        color='white', fontsize=8
    )

    for bar, price in zip(bars, prices):
        ax1.text(bar.get_x() + bar.get_width()/2,
                 bar.get_height() + max(prices) * 0.01,
                 f'{price:.4f}',
                 ha='center', color='white', fontsize=9,
                 fontweight='bold')

    # ── Graphique 2 : Trajectoires simulées ──
    ax2 = axes[1]
    setup_ax(ax2, "Trajectoires Monte Carlo (100 paths)",
             "Jours", "Prix")

    S = mc_results['parametres']['S']
    sigma = mc_results['parametres']['sigma'] / 100
    r = mc_results['parametres']['r'] / 100
    T = mc_results['parametres']['T']
    K = mc_results['parametres']['K']

    np.random.seed(42)
    n_show = 100
    n_steps = 63  # ~3 mois de trading
    dt = T / n_steps
    paths = np.zeros((n_steps + 1, n_show))
    paths[0] = S

    for t in range(1, n_steps + 1):
        Z = np.random.standard_normal(n_show)
        paths[t] = paths[t-1] * np.exp(
            (r - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z
        )

    for i in range(n_show):
        color = (COLORS['success'] if paths[-1, i] > K
                 else COLORS['danger'])
        ax2.plot(paths[:, i], color=color, alpha=0.15,
                 linewidth=0.8)

    ax2.axhline(K, color='white', linestyle='--',
                linewidth=2, label=f'Strike K={K:.2f}')
    ax2.axhline(S, color=COLORS['warning'], linestyle=':',
                linewidth=1.5, label=f'Prix actuel={S:.2f}')

    # Percentiles
    p5 = np.percentile(paths, 5, axis=1)
    p95 = np.percentile(paths, 95, axis=1)
    p50 = np.percentile(paths, 50, axis=1)
    ax2.plot(p50, color=COLORS['warning'], linewidth=2,
             label='Médiane', zorder=5)
    ax2.fill_between(range(n_steps + 1), p5, p95,
                     alpha=0.1, color=COLORS['primary'],
                     label='IC 90%')

    ax2.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
               labelcolor='white', fontsize=9)

    fig.tight_layout()
    return save_fig(fig, f"{prefix}mc_options_comparison.png")

def plot_barrier_analysis(mc_results, asset_name, prefix=""):
    """Analyse des options barrières"""
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.patch.set_facecolor(COLORS['background'])

    S = mc_results['parametres']['S']
    sigma = mc_results['parametres']['sigma'] / 100
    r = mc_results['parametres']['r'] / 100
    T = mc_results['parametres']['T']
    K = mc_results['parametres']['K']

    # ── Graphique 1 : Prix vs Barrière ──
    ax1 = axes[0]
    setup_ax(ax1, f"Prix Call KO vs Niveau de Barrière — {asset_name}",
             "Barrière (% du prix actuel)", "Prix de l'Option")

    barrier_pcts = np.linspace(1.02, 1.50, 50)
    barriers = S * barrier_pcts
    ko_prices = []

    for b in barriers:
        np.random.seed(42)
        n_sim = 5000
        n_steps = 63
        dt = T / n_steps
        paths = np.zeros((n_steps + 1, n_sim))
        paths[0] = S
        for t in range(1, n_steps + 1):
            Z = np.random.standard_normal(n_sim)
            paths[t] = paths[t-1] * np.exp(
                (r - 0.5 * sigma**2) * dt +
                sigma * np.sqrt(dt) * Z
            )
        knocked_out = np.any(paths > b, axis=0)
        payoffs = np.where(
            ~knocked_out,
            np.maximum(paths[-1] - K, 0),
            0
        )
        ko_prices.append(float(np.exp(-r * T) * np.mean(payoffs)))

    vanilla_price = mc_results['vanille']['call']['prix_bs']

    ax1.plot(barrier_pcts * 100, ko_prices,
             color=COLORS['primary'], linewidth=2,
             label='Call KO (Up-and-Out)')
    ax1.axhline(vanilla_price, color=COLORS['warning'],
                linestyle='--', linewidth=2,
                label=f'Call Vanille = {vanilla_price:.4f}')
    ax1.fill_between(barrier_pcts * 100, ko_prices, vanilla_price,
                     alpha=0.1, color=COLORS['danger'],
                     label='Réduction de prime')

    ax1.set_xlabel("Barrière (% du prix actuel)", color='#8B949E')
    ax1.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
               labelcolor='white', fontsize=9)

    # ── Graphique 2 : Tableau comparatif barrières ──
    ax2 = axes[1]
    ax2.set_facecolor(COLORS['background'])
    ax2.axis('off')

    barrieres = mc_results.get('barrieres', {})
    headers = ['Type', 'Barrière', 'Prix MC',
               'Prix Vanille', 'Réduction', '% KO/KI']
    rows = []

    for key, data in barrieres.items():
        barrier_val = data.get('barriere', 0)
        prix_mc = data.get('prix_mc', 0)
        prix_van = data.get('prix_vanilla', 0)
        reduction = data.get('reduction_prime',
                             data.get('premium_vs_vanilla', 0))
        pct = data.get('pct_trajectoires_ko',
                       data.get('pct_trajectoires_ki', 0))
        rows.append([
            data['type'].replace('Call Barrière ', ''),
            f"{barrier_val:.2f}",
            f"{prix_mc:.4f}",
            f"{prix_van:.4f}",
            f"{reduction:.4f}",
            f"{pct:.1f}%",
        ])

    if rows:
        table = ax2.table(
            cellText=rows,
            colLabels=headers,
            cellLoc='center',
            loc='center',
        )
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.1, 2.5)

        for (row, col), cell in table.get_celld().items():
            cell.set_facecolor('#161B22' if row > 0 else '#00D4FF')
            cell.set_text_props(
                color='#0D1117' if row == 0 else 'white'
            )
            cell.set_edgecolor(COLORS['grid'])

    ax2.set_title("Comparaison Options Barrières",
                  color='white', fontsize=12,
                  fontweight='bold', pad=20)

    fig.tight_layout()
    return save_fig(fig, f"{prefix}barrier_analysis.png")

def plot_exotic_comparison(mc_results, asset_name, prefix=""):
    """Comparaison Call Vanille vs Asiatique vs Lookback"""
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.patch.set_facecolor(COLORS['background'])

    S = mc_results['parametres']['S']
    sigma = mc_results['parametres']['sigma'] / 100
    r = mc_results['parametres']['r'] / 100
    T = mc_results['parametres']['T']
    K = mc_results['parametres']['K']

    # ── Graphique 1 : Distribution des payoffs ──
    ax1 = axes[0]
    setup_ax(ax1, f"Distribution des Payoffs — {asset_name}",
             "Payoff", "Fréquence")

    np.random.seed(42)
    n_sim = 20000
    n_steps = 63
    dt = T / n_steps
    paths = np.zeros((n_steps + 1, n_sim))
    paths[0] = S

    for t in range(1, n_steps + 1):
        Z = np.random.standard_normal(n_sim)
        paths[t] = paths[t-1] * np.exp(
            (r - 0.5 * sigma**2) * dt +
            sigma * np.sqrt(dt) * Z
        )

    # Payoffs
    vanilla_payoffs = np.maximum(paths[-1] - K, 0)
    asian_payoffs = np.maximum(np.mean(paths[1:], axis=0) - K, 0)
    lookback_payoffs = np.maximum(np.max(paths, axis=0) - K, 0)

    # Filtrer les payoffs non nuls pour la lisibilité
    for payoffs, label, color in [
        (vanilla_payoffs[vanilla_payoffs > 0],
         'Call Vanille', COLORS['success']),
        (asian_payoffs[asian_payoffs > 0],
         'Call Asiatique', COLORS['warning']),
        (lookback_payoffs[lookback_payoffs > 0],
         'Call Lookback', COLORS['primary']),
    ]:
        if len(payoffs) > 0:
            ax1.hist(payoffs, bins=40, alpha=0.5,
                     color=color, label=label,
                     edgecolor='black', linewidth=0.3)

    ax1.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
               labelcolor='white', fontsize=9)

    # ── Graphique 2 : Résumé exotiques ──
    ax2 = axes[1]
    ax2.set_facecolor(COLORS['background'])
    ax2.axis('off')

    headers = ['Type Option', 'Prix MC', 'vs Vanille', 'Interprétation']
    rows = []

    vanilla_price = mc_results['vanille']['call']['prix_mc']

    options_list = [
        ('Call Vanille', vanilla_price, 0, 'Référence'),
        ('Call Asiatique Arith.', mc_results['asiatiques']['call_arith']['prix_mc'], mc_results['asiatiques']['call_arith']['prix_mc'] - vanilla_price, 'Lisse la volatilite'),
        ('Call Asiatique Geo.', mc_results['asiatiques']['call_geo']['prix_mc'], mc_results['asiatiques']['call_geo']['prix_mc'] - vanilla_price, 'Encore moins chere'),
        ('Call Lookback Fixe', mc_results['lookback']['call_fixed']['prix_mc'], mc_results['lookback']['call_fixed']['prix_mc'] - vanilla_price, 'Prix maximum garanti'),
        ('Call Lookback Float.', mc_results['lookback']['call_floating']['prix_mc'], mc_results['lookback']['call_floating']['prix_mc'] - vanilla_price, 'Achete au plus bas'),
        ('Digital Call', mc_results['digitales']['digital_call']['prix_mc'], mc_results['digitales']['digital_call']['prix_mc'] - vanilla_price, 'Payoff binaire'),
    ]
# ── MODÈLE DE HESTON ─────────────────────────────────────────
def plot_heston_vs_bs(heston_results, asset_name, prefix=""):
    """Comparaison Heston vs Black-Scholes"""
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.patch.set_facecolor(COLORS['background'])

    comparaison = heston_results.get('comparaison')
    if comparaison is None:
        return None

    S = heston_results['parametres_marche']['S']

    # ── Graphique 1 : Prix Call Heston vs BS ──
    ax1 = axes[0]
    setup_ax(ax1, f"Prix Call : Heston vs Black-Scholes — {asset_name}",
             "Strike", "Prix de l'Option")

    ax1.plot(comparaison['strike'], comparaison['bs_call'],
             color=COLORS['primary'], linewidth=2.5,
             label='Black-Scholes', linestyle='--')
    ax1.plot(comparaison['strike'], comparaison['heston_call'],
             color=COLORS['success'], linewidth=2.5,
             label='Heston')
    ax1.fill_between(comparaison['strike'],
                     comparaison['bs_call'],
                     comparaison['heston_call'],
                     alpha=0.2, color=COLORS['warning'],
                     label='Différence')
    ax1.axvline(S, color='white', linestyle=':',
                linewidth=1.5, label=f'ATM (S={S:.2f})')
    ax1.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
               labelcolor='white', fontsize=9)

    # ── Graphique 2 : Différence en % ──
    ax2 = axes[1]
    setup_ax(ax2, f"Différence Heston vs BS (%) — {asset_name}",
             "Strike", "Différence (%)")

    diff_pct = comparaison['difference_pct']
    colors_bar = [COLORS['success'] if d > 0 else COLORS['danger']
                  for d in diff_pct]
    ax2.bar(comparaison['strike'], diff_pct,
            color=colors_bar, alpha=0.8,
            width=(comparaison['strike'].max() -
                   comparaison['strike'].min()) / len(comparaison) * 0.8)
    ax2.axhline(0, color='gray', linewidth=0.8)
    ax2.axvline(S, color='white', linestyle=':',
                linewidth=1.5, label=f'ATM (S={S:.2f})')

    for x, y in zip(comparaison['strike'], diff_pct):
        ax2.text(x, y + (0.1 if y > 0 else -0.3),
                 f'{y:+.1f}%', ha='center',
                 color='white', fontsize=8)

    ax2.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
               labelcolor='white', fontsize=9)

    fig.tight_layout()
    return save_fig(fig, f"{prefix}heston_vs_bs.png")

def plot_heston_paths(heston_results, asset_name, prefix=""):
    """Trajectoires Heston : Prix et Variance"""
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    fig.patch.set_facecolor(COLORS['background'])

    paths = heston_results.get('paths', {})
    S_paths = paths.get('S_paths')
    v_paths = paths.get('v_paths')

    if S_paths is None:
        return None

    S = heston_results['parametres_marche']['S']
    n_show = min(100, S_paths.shape[1])

    # ── Graphique 1 : Trajectoires de Prix ──
    ax1 = axes[0]
    setup_ax(ax1, f"Trajectoires de Prix — Modèle Heston ({asset_name})",
             "Jours", "Prix")

    for i in range(n_show):
        final = S_paths[-1, i]
        color = (COLORS['success'] if final > S
                 else COLORS['danger'])
        ax1.plot(S_paths[:, i], color=color,
                 alpha=0.1, linewidth=0.8)

    # Percentiles
    p5 = np.percentile(S_paths, 5, axis=1)
    p50 = np.percentile(S_paths, 50, axis=1)
    p95 = np.percentile(S_paths, 95, axis=1)

    ax1.plot(p50, color=COLORS['warning'], linewidth=2.5,
             label='Médiane', zorder=5)
    ax1.plot(p5, color=COLORS['danger'], linewidth=1.5,
             linestyle='--', label='5ème percentile', zorder=5)
    ax1.plot(p95, color=COLORS['success'], linewidth=1.5,
             linestyle='--', label='95ème percentile', zorder=5)
    ax1.axhline(S, color='white', linestyle=':',
                linewidth=1.5, label=f'Prix initial={S:.2f}')

    ax1.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
               labelcolor='white', fontsize=9)

    # ── Graphique 2 : Trajectoires de Variance ──
    ax2 = axes[1]
    setup_ax(ax2, "Volatilité Stochastique — Processus CIR",
             "Jours", "Volatilité (%)")

    # Convertir variance en volatilité
    vol_paths = np.sqrt(np.maximum(v_paths, 0)) * 100

    for i in range(n_show):
        ax2.plot(vol_paths[:, i], color=COLORS['purple'],
                 alpha=0.08, linewidth=0.8)

    vol_p50 = np.percentile(vol_paths, 50, axis=1)
    vol_p5 = np.percentile(vol_paths, 5, axis=1)
    vol_p95 = np.percentile(vol_paths, 95, axis=1)

    ax2.plot(vol_p50, color=COLORS['warning'], linewidth=2.5,
             label='Vol Médiane', zorder=5)
    ax2.fill_between(range(len(vol_p50)), vol_p5, vol_p95,
                     alpha=0.15, color=COLORS['purple'],
                     label='IC 90%')

    theta = heston_results['parametres_heston']['theta']
    long_term_vol = np.sqrt(theta) * 100
    ax2.axhline(long_term_vol, color=COLORS['success'],
                linestyle='--', linewidth=2,
                label=f'Vol long terme θ = {long_term_vol:.1f}%')

    ax2.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
               labelcolor='white', fontsize=9)

    fig.tight_layout()
    return save_fig(fig, f"{prefix}heston_paths.png")

def plot_heston_vol_surface(heston_results, asset_name, prefix=""):
    """Surface de volatilité implicite Heston en 3D"""
    from mpl_toolkits.mplot3d import Axes3D

    vol_surface = heston_results.get('vol_surface')
    if vol_surface is None:
        return None

    fig = plt.figure(figsize=(14, 8))
    fig.patch.set_facecolor(COLORS['background'])
    ax = fig.add_subplot(111, projection='3d')
    ax.set_facecolor(COLORS['background'])

    X = np.arange(len(vol_surface.columns))
    Y = np.arange(len(vol_surface.index))
    X, Y = np.meshgrid(X, Y)
    Z = vol_surface.values

    surf = ax.plot_surface(X, Y, Z, cmap='RdYlGn_r',
                           alpha=0.9, edgecolor='none')

    ax.set_xticks(range(len(vol_surface.columns)))
    ax.set_xticklabels(vol_surface.columns,
                       color='white', fontsize=8)
    ax.set_yticks(range(len(vol_surface.index)))
    ax.set_yticklabels(vol_surface.index,
                       color='white', fontsize=8)
    ax.set_zlabel('Vol Implicite (%)', color='white', fontsize=10)
    ax.set_xlabel('Moneyness (K/S)', color='white', fontsize=10)
    ax.set_ylabel('Maturité', color='white', fontsize=10)
    ax.tick_params(colors='white')
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False

    fig.colorbar(surf, ax=ax, shrink=0.5,
                 label='Vol Implicite (%)')
    ax.set_title(
        f"Surface de Volatilité Heston — {asset_name}",
        color='white', fontsize=13, fontweight='bold', pad=20
    )

    return save_fig(fig, f"{prefix}heston_vol_surface.png")

def plot_heston_summary(heston_results, asset_name, prefix=""):
    """Dashboard résumé du modèle Heston"""
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle(f"Modèle de Heston — {asset_name}",
                 color='white', fontsize=15, fontweight='bold')
    fig.patch.set_facecolor(COLORS['background'])

    params = heston_results['parametres_heston']
    marche = heston_results['parametres_marche']
    pricing = heston_results.get('pricing_atm', {})

    # ── Cartes des paramètres ──
    param_cards = [
        ("κ (Kappa)\nVitesse retour moyenne",
         f"{params['kappa']:.4f}", COLORS['primary']),
        ("θ (Theta)\nVariance long terme",
         f"{params['theta']:.4f}", COLORS['success']),
        ("ξ (Xi)\nVol de Vol",
         f"{params['xi']:.4f}", COLORS['warning']),
        ("ρ (Rho)\nCorrélation",
         f"{params['rho']:.4f}", COLORS['purple']),
        ("v₀\nVariance initiale",
         f"{params['v0']:.4f}", COLORS['secondary']),
        ("Feller\nCondition",
         "✓ Vérifiée" if params['condition_feller'] else "✗ Violée",
         COLORS['success'] if params['condition_feller']
         else COLORS['danger']),
    ]

    for ax, (label, value, color) in zip(axes.flat, param_cards):
        ax.set_facecolor('#161B22')
        ax.text(0.5, 0.62, value, transform=ax.transAxes,
                ha='center', va='center', fontsize=20,
                fontweight='bold', color=color)
        ax.text(0.5, 0.25, label, transform=ax.transAxes,
                ha='center', va='center', fontsize=9,
                color='#8B949E')
        for spine in ax.spines.values():
            spine.set_edgecolor(color)
            spine.set_linewidth(2)
        ax.set_xticks([])
        ax.set_yticks([])

    fig.tight_layout()
    path1 = save_fig(fig, f"{prefix}heston_params.png")

    # ── Graphique comparaison pricing ──
    fig2, ax = plt.subplots(figsize=(14, 5))
    fig2.patch.set_facecolor(COLORS['background'])
    setup_ax(ax, f"Comparaison Pricing ATM (3 mois) — {asset_name}",
             "", "Prix")
    ax.axis('off')

    headers = ['Modèle', 'Prix Call ATM',
               'Différence', 'Diff %',
               'Vol BS', 'Vol Heston Init.']
    rows = [
        ['Black-Scholes',
         f"{pricing.get('bs_call', 0):.4f}",
         '—', '—',
         f"{marche['sigma_bs']:.1f}%",
         f"{params['vol_initiale']:.1f}%"],
        ['Heston',
         f"{pricing.get('heston_call', 0):.4f}",
         f"{pricing.get('difference', 0):+.4f}",
         f"{pricing.get('difference_pct', 0):+.2f}%",
         f"{marche['sigma_bs']:.1f}%",
         f"{params['vol_long_terme']:.1f}%"],
    ]

    table = ax.table(
        cellText=rows,
        colLabels=headers,
        cellLoc='center',
        loc='center',
    )
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1.2, 3.0)

    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor('#00D4FF')
            cell.set_text_props(color='#0D1117', fontweight='bold')
        elif row == 1:
            cell.set_facecolor('#161B22')
            cell.set_text_props(color='white')
        else:
            cell.set_facecolor('#1A2A1A')
            diff_val = rows[row-1][3] if col == 3 else ''
            if col == 3 and diff_val and diff_val != '—':
                color = (COLORS['success'] if '+' in diff_val
                         else COLORS['danger'])
                cell.set_text_props(color=color)
            else:
                cell.set_text_props(color=COLORS['success'])
        cell.set_edgecolor(COLORS['grid'])

    fig2.tight_layout()
    path2 = save_fig(fig2, f"{prefix}heston_pricing.png")

    return path1, path2

def generate_heston_charts(heston_results, asset_name, prefix=""):
    """Génère tous les graphiques Heston"""
    chart_paths = []

    print("    Paramètres Heston...")
    paths = plot_heston_summary(heston_results, asset_name, prefix)
    if paths:
        chart_paths.extend([p for p in paths if p])

    print("    Heston vs Black-Scholes...")
    p = plot_heston_vs_bs(heston_results, asset_name, prefix)
    if p:
        chart_paths.append(p)

    print("    Trajectoires Heston...")
    p = plot_heston_paths(heston_results, asset_name, prefix)
    if p:
        chart_paths.append(p)

    print("    Surface de volatilité Heston...")
    p = plot_heston_vol_surface(heston_results, asset_name, prefix)
    if p:
        chart_paths.append(p)

    return [p for p in chart_paths if p is not None]

def generate_mc_options_charts(mc_results, asset_name, prefix=""):
    """Génère tous les graphiques Monte Carlo Options"""
    chart_paths = []

    print("    Comparaison des options...")
    p = plot_mc_options_comparison(mc_results, asset_name, prefix)
    if p:
        chart_paths.append(p)

    print("    Analyse barrières...")
    p = plot_barrier_analysis(mc_results, asset_name, prefix)
    if p:
        chart_paths.append(p)

    print("    Comparaison exotiques...")
    p = plot_exotic_comparison(mc_results, asset_name, prefix)
    if p:
        chart_paths.append(p)

    return [p for p in chart_paths if p is not None]