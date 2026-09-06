# chart_generator.py
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import numpy as np
import pandas as pd
import os
from config import OUTPUT_DIR
from modules.chart_advanced import generate_advanced_charts

# Style général
plt.style.use('dark_background')
COLORS = {
    'primary': '#00D4FF',
    'secondary': '#FF6B35',
    'success': '#00FF88',
    'danger': '#FF4444',
    'warning': '#FFD700',
    'purple': '#9B59B6',
    'background': '#0D1117',
    'grid': '#21262D'
}

def setup_ax(ax, title, xlabel="", ylabel=""):
    """Style uniforme pour tous les graphiques"""
    ax.set_facecolor(COLORS['background'])
    ax.set_title(title, color='white', fontsize=13, fontweight='bold', pad=15)
    ax.set_xlabel(xlabel, color='#8B949E', fontsize=10)
    ax.set_ylabel(ylabel, color='#8B949E', fontsize=10)
    ax.tick_params(colors='#8B949E')
    ax.grid(True, color=COLORS['grid'], alpha=0.5, linestyle='--')
    for spine in ax.spines.values():
        spine.set_edgecolor(COLORS['grid'])

def save_fig(fig, filename):
    """Sauvegarde le graphique"""
    path = os.path.join(OUTPUT_DIR, filename)
    fig.patch.set_facecolor(COLORS['background'])
    fig.savefig(path, dpi=150, bbox_inches='tight',
                facecolor=COLORS['background'])
    plt.close(fig)
    return path

def plot_price_history(prices, title="Évolution du Prix"):
    """Graphique de l'évolution des prix"""
    fig, ax = plt.subplots(figsize=(12, 5))
    setup_ax(ax, title, "Date", "Prix")

    ax.plot(prices.index, prices.values,
            color=COLORS['primary'], linewidth=1.5, label='Prix')
    ax.fill_between(prices.index, prices.values,
                    prices.min(), alpha=0.1, color=COLORS['primary'])

    # Marquer min et max
    max_idx = prices.idxmax()
    min_idx = prices.idxmin()
    ax.scatter([max_idx], [prices.max()], color=COLORS['success'],
               s=100, zorder=5, label=f'Max: {prices.max():.2f}')
    ax.scatter([min_idx], [prices.min()], color=COLORS['danger'],
               s=100, zorder=5, label=f'Min: {prices.min():.2f}')

    ax.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
              labelcolor='white', fontsize=9)
    fig.tight_layout()
    return save_fig(fig, "01_price_history.png")

def plot_returns_distribution(returns, title="Distribution des Rendements"):
    """Histogramme des rendements"""
    fig, ax = plt.subplots(figsize=(10, 5))
    setup_ax(ax, title, "Rendement (%)", "Fréquence")

    returns_pct = returns * 100
    ax.hist(returns_pct, bins=50, color=COLORS['primary'],
            alpha=0.7, edgecolor='black', linewidth=0.5)

    # Ligne VaR 95%
    var_95 = np.percentile(returns_pct, 5)
    ax.axvline(var_95, color=COLORS['danger'], linestyle='--',
               linewidth=2, label=f'VaR 95%: {var_95:.2f}%')

    # Ligne moyenne
    mean_ret = returns_pct.mean()
    ax.axvline(mean_ret, color=COLORS['success'], linestyle='--',
               linewidth=2, label=f'Moyenne: {mean_ret:.2f}%')

    ax.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
              labelcolor='white', fontsize=9)
    fig.tight_layout()
    return save_fig(fig, "02_returns_distribution.png")

def plot_moving_averages(ma_df, title="Moyennes Mobiles"):
    """Graphique des moyennes mobiles"""
    fig, ax = plt.subplots(figsize=(12, 5))
    setup_ax(ax, title, "Date", "Prix")

    ax.plot(ma_df.index, ma_df['prix'],
            color=COLORS['primary'], linewidth=1, label='Prix', alpha=0.8)

    if 'SMA_20' in ma_df.columns:
        ax.plot(ma_df.index, ma_df['SMA_20'],
                color=COLORS['success'], linewidth=1.5, label='SMA 20')
    if 'SMA_50' in ma_df.columns:
        ax.plot(ma_df.index, ma_df['SMA_50'],
                color=COLORS['warning'], linewidth=1.5, label='SMA 50')
    if 'SMA_200' in ma_df.columns:
        ax.plot(ma_df.index, ma_df['SMA_200'],
                color=COLORS['secondary'], linewidth=1.5, label='SMA 200')

    ax.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
              labelcolor='white', fontsize=9)
    fig.tight_layout()
    return save_fig(fig, "03_moving_averages.png")

def plot_rsi(rsi, title="RSI (Relative Strength Index)"):
    """Graphique RSI"""
    fig, ax = plt.subplots(figsize=(12, 4))
    setup_ax(ax, title, "Date", "RSI")

    ax.plot(rsi.index, rsi.values,
            color=COLORS['purple'], linewidth=1.5, label='RSI')
    ax.axhline(70, color=COLORS['danger'], linestyle='--',
               linewidth=1.5, label='Surachat (70)')
    ax.axhline(30, color=COLORS['success'], linestyle='--',
               linewidth=1.5, label='Survente (30)')
    ax.axhline(50, color='gray', linestyle='-', linewidth=0.8, alpha=0.5)

    ax.fill_between(rsi.index, rsi.values, 70,
                    where=(rsi.values >= 70), alpha=0.2, color=COLORS['danger'])
    ax.fill_between(rsi.index, rsi.values, 30,
                    where=(rsi.values <= 30), alpha=0.2, color=COLORS['success'])

    ax.set_ylim(0, 100)
    ax.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
              labelcolor='white', fontsize=9)
    fig.tight_layout()
    return save_fig(fig, "04_rsi.png")

def plot_bollinger_bands(bb_df, title="Bandes de Bollinger"):
    """Graphique Bollinger Bands"""
    fig, ax = plt.subplots(figsize=(12, 5))
    setup_ax(ax, title, "Date", "Prix")

    ax.plot(bb_df.index, bb_df['prix'],
            color=COLORS['primary'], linewidth=1.2, label='Prix')
    ax.plot(bb_df.index, bb_df['moyenne'],
            color=COLORS['warning'], linewidth=1.2,
            linestyle='--', label='Moyenne 20j')
    ax.plot(bb_df.index, bb_df['bande_haute'],
            color=COLORS['danger'], linewidth=1, label='Bande Haute')
    ax.plot(bb_df.index, bb_df['bande_basse'],
            color=COLORS['success'], linewidth=1, label='Bande Basse')
    ax.fill_between(bb_df.index, bb_df['bande_haute'],
                    bb_df['bande_basse'], alpha=0.05, color=COLORS['primary'])

    ax.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
              labelcolor='white', fontsize=9)
    fig.tight_layout()
    return save_fig(fig, "05_bollinger_bands.png")

def plot_macd(macd_df, title="MACD"):
    """Graphique MACD"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6), height_ratios=[2, 1])
    setup_ax(ax1, title, "", "MACD")
    setup_ax(ax2, "", "Date", "Histogramme")

    ax1.plot(macd_df.index, macd_df['macd'],
             color=COLORS['primary'], linewidth=1.5, label='MACD')
    ax1.plot(macd_df.index, macd_df['signal'],
             color=COLORS['secondary'], linewidth=1.5, label='Signal')
    ax1.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
               labelcolor='white', fontsize=9)

    colors = [COLORS['success'] if v >= 0 else COLORS['danger']
              for v in macd_df['histogramme']]
    ax2.bar(macd_df.index, macd_df['histogramme'],
            color=colors, alpha=0.7, width=1)
    ax2.axhline(0, color='gray', linewidth=0.8)

    fig.tight_layout()
    return save_fig(fig, "06_macd.png")

def plot_drawdown(returns, title="Drawdown"):
    """Graphique du Drawdown"""
    fig, ax = plt.subplots(figsize=(12, 4))
    setup_ax(ax, title, "Date", "Drawdown (%)")

    cumulative = (1 + returns).cumprod()
    rolling_max = cumulative.expanding().max()
    drawdown = (cumulative - rolling_max) / rolling_max * 100

    ax.fill_between(drawdown.index, drawdown.values, 0,
                    alpha=0.5, color=COLORS['danger'])
    ax.plot(drawdown.index, drawdown.values,
            color=COLORS['danger'], linewidth=1)
    ax.axhline(0, color='gray', linewidth=0.8)

    fig.tight_layout()
    return save_fig(fig, "07_drawdown.png")

def plot_metrics_dashboard(metrics, title="Tableau de Bord des Métriques", prefix=""):
    """Dashboard visuel des métriques clés"""
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    fig.suptitle(title, color='white', fontsize=15, fontweight='bold')

    key_metrics = [
        ('Rendement Total', f"{metrics.get('rendement_total', 0):.2f}%", COLORS['success'] if metrics.get('rendement_total', 0) > 0 else COLORS['danger']),
        ('Volatilité Ann.', f"{metrics.get('volatilite_annualisee', 0):.2f}%", COLORS['warning']),
        ('Sharpe Ratio', f"{metrics.get('sharpe_ratio', 0):.3f}", COLORS['primary']),
        ('Sortino Ratio', f"{metrics.get('sortino_ratio', 0):.3f}", COLORS['purple']),
        ('Max Drawdown', f"{metrics.get('max_drawdown', 0):.2f}%", COLORS['danger']),
        ('VaR 95%', f"{metrics.get('var_95', 0):.2f}%", COLORS['secondary']),
        ('Win Rate', f"{metrics.get('win_rate', 0):.1f}%", COLORS['success']),
        ('Beta', f"{metrics.get('beta', 0):.3f}", COLORS['primary']),
    ]

    for idx, (ax, (label, value, color)) in enumerate(zip(axes.flat, key_metrics)):
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
    return save_fig(fig, f"{prefix}metrics_dashboard.png")

def plot_correlation_matrix(corr_matrix, title="Matrice de Corrélation"):
    """Heatmap de corrélation"""
    fig, ax = plt.subplots(figsize=(10, 8))
    setup_ax(ax, title)

    mask = np.zeros_like(corr_matrix, dtype=bool)
    np.fill_diagonal(mask, True)

    sns.heatmap(corr_matrix, ax=ax, annot=True, fmt='.2f',
                cmap='RdYlGn', center=0, vmin=-1, vmax=1,
                mask=mask, square=True,
                annot_kws={'size': 10, 'color': 'white'},
                linewidths=0.5, linecolor=COLORS['grid'])

    ax.tick_params(colors='white', labelsize=10)
    fig.tight_layout()
    return save_fig(fig, "09_correlation_matrix.png")

def generate_all_charts(results, analysis):
    """Génère tous les graphiques disponibles"""
    chart_paths = []

    if not results:
        print("⚠ Aucun résultat à visualiser")
        return chart_paths

    asset_names = analysis.get('actifs_detectes', ['Actif'])
    asset_index = 0

    for sheet_name, data in results.items():
        if sheet_name in ['correlation_matrix', 'portfolio_optimization']:
            continue

        asset_name = asset_names[asset_index] if asset_index < len(asset_names) else sheet_name
        prefix = f"{asset_index+1:02d}_{sheet_name}_"
        asset_index += 1

        # ── Graphiques de base ────────────────────────────────
        if 'prices' in data:
            fig, ax = plt.subplots(figsize=(12, 5))
            setup_ax(ax, f"Évolution du Prix — {asset_name}", "Date", "Prix")
            prices = data['prices']
            ax.plot(prices.index, prices.values,
                    color=COLORS['primary'], linewidth=1.5)
            ax.fill_between(prices.index, prices.values,
                            prices.min(), alpha=0.1, color=COLORS['primary'])
            max_idx = prices.idxmax()
            min_idx = prices.idxmin()
            ax.scatter([max_idx], [prices.max()], color=COLORS['success'],
                       s=100, zorder=5, label=f'Max: {prices.max():.2f}')
            ax.scatter([min_idx], [prices.min()], color=COLORS['danger'],
                       s=100, zorder=5, label=f'Min: {prices.min():.2f}')
            import matplotlib.dates as mdates
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            plt.xticks(rotation=45)
            ax.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
                      labelcolor='white', fontsize=9)
            fig.tight_layout()
            chart_paths.append(save_fig(fig, f"{prefix}price_history.png"))

        if 'returns' in data:
            returns = data['returns']

            # Distribution
            fig, ax = plt.subplots(figsize=(10, 5))
            setup_ax(ax, f"Distribution des Rendements — {asset_name}",
                     "Rendement (%)", "Fréquence")
            returns_pct = returns * 100
            ax.hist(returns_pct, bins=50, color=COLORS['primary'],
                    alpha=0.7, edgecolor='black', linewidth=0.5)
            var_95 = np.percentile(returns_pct, 5)
            ax.axvline(var_95, color=COLORS['danger'], linestyle='--',
                       linewidth=2, label=f'VaR 95%: {var_95:.2f}%')
            ax.axvline(returns_pct.mean(), color=COLORS['success'],
                       linestyle='--', linewidth=2,
                       label=f'Moyenne: {returns_pct.mean():.2f}%')
            ax.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
                      labelcolor='white', fontsize=9)
            fig.tight_layout()
            chart_paths.append(save_fig(fig, f"{prefix}returns_dist.png"))

            # Drawdown
            fig, ax = plt.subplots(figsize=(12, 4))
            setup_ax(ax, f"Drawdown — {asset_name}", "Date", "Drawdown (%)")
            cumulative = (1 + returns).cumprod()
            rolling_max = cumulative.expanding().max()
            drawdown = (cumulative - rolling_max) / rolling_max * 100
            ax.fill_between(drawdown.index, drawdown.values, 0,
                            alpha=0.5, color=COLORS['danger'])
            ax.plot(drawdown.index, drawdown.values,
                    color=COLORS['danger'], linewidth=1)
            import matplotlib.dates as mdates
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            plt.xticks(rotation=45)
            fig.tight_layout()
            chart_paths.append(save_fig(fig, f"{prefix}drawdown.png"))

        if 'moving_averages' in data:
            ma_df = data['moving_averages']
            fig, ax = plt.subplots(figsize=(12, 5))
            setup_ax(ax, f"Moyennes Mobiles — {asset_name}", "Date", "Prix")
            ax.plot(ma_df.index, ma_df['prix'], color=COLORS['primary'],
                    linewidth=1, label='Prix', alpha=0.8)
            for col, color, label in [
                ('SMA_20', COLORS['success'], 'SMA 20'),
                ('SMA_50', COLORS['warning'], 'SMA 50'),
                ('SMA_200', COLORS['secondary'], 'SMA 200'),
            ]:
                if col in ma_df.columns:
                    ax.plot(ma_df.index, ma_df[col], color=color,
                            linewidth=1.5, label=label)
            import matplotlib.dates as mdates
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            plt.xticks(rotation=45)
            ax.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
                      labelcolor='white', fontsize=9)
            fig.tight_layout()
            chart_paths.append(save_fig(fig, f"{prefix}moving_averages.png"))

        if 'rsi' in data:
            rsi = data['rsi']
            fig, ax = plt.subplots(figsize=(12, 4))
            setup_ax(ax, f"RSI — {asset_name}", "Date", "RSI")
            ax.plot(rsi.index, rsi.values, color=COLORS['purple'],
                    linewidth=1.5)
            ax.axhline(70, color=COLORS['danger'], linestyle='--',
                       linewidth=1.5, label='Surachat (70)')
            ax.axhline(30, color=COLORS['success'], linestyle='--',
                       linewidth=1.5, label='Survente (30)')
            ax.fill_between(rsi.index, rsi.values, 70,
                            where=(rsi.values >= 70), alpha=0.2,
                            color=COLORS['danger'])
            ax.fill_between(rsi.index, rsi.values, 30,
                            where=(rsi.values <= 30), alpha=0.2,
                            color=COLORS['success'])
            ax.set_ylim(0, 100)
            import matplotlib.dates as mdates
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            plt.xticks(rotation=45)
            ax.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
                      labelcolor='white', fontsize=9)
            fig.tight_layout()
            chart_paths.append(save_fig(fig, f"{prefix}rsi.png"))

        if 'bollinger' in data:
            bb_df = data['bollinger']
            fig, ax = plt.subplots(figsize=(12, 5))
            setup_ax(ax, f"Bandes de Bollinger — {asset_name}",
                     "Date", "Prix")
            ax.plot(bb_df.index, bb_df['prix'], color=COLORS['primary'],
                    linewidth=1.2, label='Prix')
            ax.plot(bb_df.index, bb_df['moyenne'], color=COLORS['warning'],
                    linewidth=1.2, linestyle='--', label='Moyenne 20j')
            ax.plot(bb_df.index, bb_df['bande_haute'], color=COLORS['danger'],
                    linewidth=1, label='Bande Haute')
            ax.plot(bb_df.index, bb_df['bande_basse'], color=COLORS['success'],
                    linewidth=1, label='Bande Basse')
            ax.fill_between(bb_df.index, bb_df['bande_haute'],
                            bb_df['bande_basse'], alpha=0.05,
                            color=COLORS['primary'])
            import matplotlib.dates as mdates
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            plt.xticks(rotation=45)
            ax.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
                      labelcolor='white', fontsize=9)
            fig.tight_layout()
            chart_paths.append(save_fig(fig, f"{prefix}bollinger.png"))

        if 'macd' in data:
            macd_df = data['macd']
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6),
                                            height_ratios=[2, 1])
            setup_ax(ax1, f"MACD — {asset_name}", "", "MACD")
            setup_ax(ax2, "", "Date", "Histogramme")
            ax1.plot(macd_df.index, macd_df['macd'], color=COLORS['primary'],
                     linewidth=1.5, label='MACD')
            ax1.plot(macd_df.index, macd_df['signal'],
                     color=COLORS['secondary'], linewidth=1.5, label='Signal')
            ax1.legend(facecolor='#161B22', edgecolor=COLORS['grid'],
                       labelcolor='white', fontsize=9)
            colors_bar = [COLORS['success'] if v >= 0 else COLORS['danger']
                          for v in macd_df['histogramme']]
            ax2.bar(macd_df.index, macd_df['histogramme'],
                    color=colors_bar, alpha=0.7, width=1)
            ax2.axhline(0, color='gray', linewidth=0.8)
            import matplotlib.dates as mdates
            for ax in [ax1, ax2]:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
                ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            plt.xticks(rotation=45)
            fig.tight_layout()
            chart_paths.append(save_fig(fig, f"{prefix}macd.png"))

        if 'metrics' in data:
            chart_paths.append(
                plot_metrics_dashboard(
                    data['metrics'],
                    f"Métriques — {asset_name}",
                    prefix
                )
            )

        # ── Graphiques avancés ────────────────────────────────
        print(f"  Graphiques avancés — {asset_name}...")
        advanced_paths = generate_advanced_charts(data, prefix)
        chart_paths.extend(advanced_paths)

    # Corrélation
    if 'correlation_matrix' in results:
        chart_paths.append(
            plot_correlation_matrix(results['correlation_matrix'])
        )

    # Optimisation portefeuille
    if 'portfolio_optimization' in results:
        from modules.chart_advanced import (plot_efficient_frontier,
                                             plot_portfolio_comparison)
        chart_paths.append(
            plot_efficient_frontier(results['portfolio_optimization'], "00_")
        )
        chart_paths.append(
            plot_portfolio_comparison(results['portfolio_optimization'], "00_")
        )

    return [p for p in chart_paths if p is not None]