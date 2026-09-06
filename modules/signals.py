# modules/signals.py
import numpy as np
import pandas as pd

def signal_rsi(prices, period=14):
    """Signal basé sur le RSI"""
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    current_rsi = float(rsi.iloc[-1])

    if current_rsi < 30:
        signal = "ACHETER"
        conviction = min((30 - current_rsi) / 30 * 100, 100)
        reason = f"RSI={current_rsi:.1f} → Zone de survente (<30)"
    elif current_rsi > 70:
        signal = "VENDRE"
        conviction = min((current_rsi - 70) / 30 * 100, 100)
        reason = f"RSI={current_rsi:.1f} → Zone de surachat (>70)"
    else:
        signal = "NEUTRE"
        conviction = 50
        reason = f"RSI={current_rsi:.1f} → Zone neutre (30-70)"

    return {
        'indicateur': 'RSI',
        'signal': signal,
        'conviction': round(conviction, 1),
        'valeur': round(current_rsi, 2),
        'raison': reason
    }

def signal_macd(prices, fast=12, slow=26, signal_period=9):
    """Signal basé sur le MACD"""
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal_period).mean()
    histogram = macd - signal_line

    current_hist = float(histogram.iloc[-1])
    prev_hist = float(histogram.iloc[-2])
    current_macd = float(macd.iloc[-1])
    current_signal = float(signal_line.iloc[-1])

    # Croisement haussier
    if prev_hist < 0 and current_hist > 0:
        signal = "ACHETER"
        conviction = 85
        reason = f"MACD croise la ligne signal par le haut"
    # Croisement baissier
    elif prev_hist > 0 and current_hist < 0:
        signal = "VENDRE"
        conviction = 85
        reason = f"MACD croise la ligne signal par le bas"
    # MACD positif et croissant
    elif current_macd > current_signal and current_hist > prev_hist:
        signal = "ACHETER"
        conviction = 65
        reason = f"MACD au-dessus du signal et en hausse"
    # MACD négatif et décroissant
    elif current_macd < current_signal and current_hist < prev_hist:
        signal = "VENDRE"
        conviction = 65
        reason = f"MACD en dessous du signal et en baisse"
    else:
        signal = "NEUTRE"
        conviction = 50
        reason = f"Pas de signal clair"

    return {
        'indicateur': 'MACD',
        'signal': signal,
        'conviction': conviction,
        'valeur': round(current_macd, 4),
        'raison': reason
    }

def signal_bollinger(prices, period=20, std_dev=2):
    """Signal basé sur les Bandes de Bollinger"""
    rolling_mean = prices.rolling(period).mean()
    rolling_std = prices.rolling(period).std()
    upper = rolling_mean + std_dev * rolling_std
    lower = rolling_mean - std_dev * rolling_std

    current_price = float(prices.iloc[-1])
    current_upper = float(upper.iloc[-1])
    current_lower = float(lower.iloc[-1])
    current_mean = float(rolling_mean.iloc[-1])

    # Position dans les bandes
    band_width = current_upper - current_lower
    position = (current_price - current_lower) / band_width if band_width != 0 else 0.5

    if current_price < current_lower:
        signal = "ACHETER"
        conviction = min(((current_lower - current_price) / current_lower) * 1000, 95)
        reason = f"Prix sous la bande basse → retour à la moyenne probable"
    elif current_price > current_upper:
        signal = "VENDRE"
        conviction = min(((current_price - current_upper) / current_upper) * 1000, 95)
        reason = f"Prix au-dessus de la bande haute → retour à la moyenne probable"
    elif position < 0.3:
        signal = "ACHETER"
        conviction = 60
        reason = f"Prix dans le tiers inférieur des bandes"
    elif position > 0.7:
        signal = "VENDRE"
        conviction = 60
        reason = f"Prix dans le tiers supérieur des bandes"
    else:
        signal = "NEUTRE"
        conviction = 50
        reason = f"Prix au centre des bandes"

    return {
        'indicateur': 'Bollinger',
        'signal': signal,
        'conviction': round(conviction, 1),
        'valeur': round(current_price, 2),
        'raison': reason
    }

def signal_moving_average(prices, short=20, long=50):
    """Signal basé sur le croisement de moyennes mobiles"""
    sma_short = prices.rolling(short).mean()
    sma_long = prices.rolling(long).mean()

    current_short = float(sma_short.iloc[-1])
    current_long = float(sma_long.iloc[-1])
    prev_short = float(sma_short.iloc[-2])
    prev_long = float(sma_long.iloc[-2])

    current_price = float(prices.iloc[-1])
    sma200 = float(prices.rolling(200).mean().iloc[-1]) if len(prices) >= 200 else None

    # Croisement golden cross
    if prev_short <= prev_long and current_short > current_long:
        signal = "ACHETER"
        conviction = 90
        reason = f"Golden Cross : SMA{short} croise SMA{long} par le haut"
    # Croisement death cross
    elif prev_short >= prev_long and current_short < current_long:
        signal = "VENDRE"
        conviction = 90
        reason = f"Death Cross : SMA{short} croise SMA{long} par le bas"
    # Tendance haussière
    elif current_short > current_long:
        pct_diff = (current_short - current_long) / current_long * 100
        signal = "ACHETER"
        conviction = min(50 + pct_diff * 5, 80)
        reason = f"SMA{short} ({current_short:.2f}) > SMA{long} ({current_long:.2f}) → Tendance haussière"
    # Tendance baissière
    else:
        pct_diff = (current_long - current_short) / current_long * 100
        signal = "VENDRE"
        conviction = min(50 + pct_diff * 5, 80)
        reason = f"SMA{short} ({current_short:.2f}) < SMA{long} ({current_long:.2f}) → Tendance baissière"

    return {
        'indicateur': f'MA Crossover ({short}/{long})',
        'signal': signal,
        'conviction': round(conviction, 1),
        'valeur': round(current_price, 2),
        'raison': reason
    }

def signal_momentum(prices, period=20):
    """Signal basé sur le momentum pur"""
    returns = prices.pct_change().dropna()
    momentum = float((prices.iloc[-1] / prices.iloc[-period] - 1) * 100)
    recent_vol = float(returns.tail(20).std() * np.sqrt(252) * 100)

    # Momentum ajusté par la volatilité
    adj_momentum = momentum / (recent_vol / 100) if recent_vol != 0 else 0

    if adj_momentum > 1.5:
        signal = "ACHETER"
        conviction = min(50 + adj_momentum * 10, 90)
        reason = f"Momentum fort : +{momentum:.1f}% sur {period}j"
    elif adj_momentum < -1.5:
        signal = "VENDRE"
        conviction = min(50 + abs(adj_momentum) * 10, 90)
        reason = f"Momentum négatif : {momentum:.1f}% sur {period}j"
    else:
        signal = "NEUTRE"
        conviction = 50
        reason = f"Momentum faible : {momentum:.1f}% sur {period}j"

    return {
        'indicateur': f'Momentum ({period}j)',
        'signal': signal,
        'conviction': round(conviction, 1),
        'valeur': round(momentum, 2),
        'raison': reason
    }

def signal_mean_reversion(prices, period=60):
    """Signal de mean reversion"""
    rolling_mean = float(prices.rolling(period).mean().iloc[-1])
    rolling_std = float(prices.rolling(period).std().iloc[-1])
    current_price = float(prices.iloc[-1])

    if rolling_std == 0:
        return None

    z_score = (current_price - rolling_mean) / rolling_std

    if z_score < -2:
        signal = "ACHETER"
        conviction = min(50 + abs(z_score) * 15, 95)
        reason = f"Z-score={z_score:.2f} → Prix très bas vs moyenne ({period}j)"
    elif z_score > 2:
        signal = "VENDRE"
        conviction = min(50 + z_score * 15, 95)
        reason = f"Z-score={z_score:.2f} → Prix très haut vs moyenne ({period}j)"
    elif z_score < -1:
        signal = "ACHETER"
        conviction = 60
        reason = f"Z-score={z_score:.2f} → Prix sous la moyenne"
    elif z_score > 1:
        signal = "VENDRE"
        conviction = 60
        reason = f"Z-score={z_score:.2f} → Prix au-dessus de la moyenne"
    else:
        signal = "NEUTRE"
        conviction = 50
        reason = f"Z-score={z_score:.2f} → Prix proche de la moyenne"

    return {
        'indicateur': f'Mean Reversion (Z-score {period}j)',
        'signal': signal,
        'conviction': round(conviction, 1),
        'valeur': round(z_score, 3),
        'raison': reason
    }

def compute_final_signal(signals_list):
    """
    Agrège tous les signaux en un signal final pondéré
    avec un score de conviction global
    """
    weights = {
        'RSI': 1.5,
        'MACD': 2.0,
        'Bollinger': 1.5,
        'MA Crossover (20/50)': 2.0,
        'Momentum (20j)': 1.5,
        'Mean Reversion (Z-score 60j)': 1.5,
    }

    buy_score = 0
    sell_score = 0
    total_weight = 0
    nb_buy = 0
    nb_sell = 0
    nb_neutral = 0

    for s in signals_list:
        if s is None:
            continue
        indicateur = s['indicateur']
        w = weights.get(indicateur, 1.0)
        conviction = s['conviction'] / 100

        if s['signal'] == 'ACHETER':
            buy_score += w * conviction
            nb_buy += 1
        elif s['signal'] == 'VENDRE':
            sell_score += w * conviction
            nb_sell += 1
        else:
            nb_neutral += 1
        total_weight += w

    if total_weight == 0:
        return None

    buy_pct = buy_score / total_weight * 100
    sell_pct = sell_score / total_weight * 100
    net_score = buy_pct - sell_pct

    if net_score > 25:
        final_signal = "ACHETER"
        final_conviction = min(buy_pct, 95)
        emoji = "🟢"
    elif net_score < -25:
        final_signal = "VENDRE"
        final_conviction = min(sell_pct, 95)
        emoji = "🔴"
    else:
        final_signal = "NEUTRE"
        final_conviction = 50
        emoji = "🟡"

    return {
        'signal_final': final_signal,
        'conviction_finale': round(final_conviction, 1),
        'score_achat': round(buy_pct, 1),
        'score_vente': round(sell_pct, 1),
        'net_score': round(net_score, 1),
        'nb_signaux_achat': nb_buy,
        'nb_signaux_vente': nb_sell,
        'nb_signaux_neutres': nb_neutral,
        'emoji': emoji,
        'interpretation': (
            "Signal fort d'achat — momentum positif et indicateurs alignés"
            if final_signal == "ACHETER" and final_conviction > 70
            else "Signal modéré d'achat — surveiller la confirmation"
            if final_signal == "ACHETER"
            else "Signal fort de vente — pression baissière dominante"
            if final_signal == "VENDRE" and final_conviction > 70
            else "Signal modéré de vente — attendre confirmation"
            if final_signal == "VENDRE"
            else "Pas de signal clair — rester en dehors du marché"
        )
    }

def run_all_signals(prices):
    """Lance tous les signaux sur un actif"""
    if len(prices) < 50:
        print("  ⚠ Pas assez de données pour les signaux")
        return None

    signals_list = []

    if len(prices) >= 14:
        signals_list.append(signal_rsi(prices))

    if len(prices) >= 26:
        signals_list.append(signal_macd(prices))

    if len(prices) >= 20:
        signals_list.append(signal_bollinger(prices))
        signals_list.append(signal_moving_average(prices))
        signals_list.append(signal_momentum(prices))

    if len(prices) >= 60:
        signals_list.append(signal_mean_reversion(prices))

    final = compute_final_signal(signals_list)

    return {
        'signaux_individuels': signals_list,
        'signal_final': final,
        'prix_actuel': float(prices.iloc[-1]),
        'date_signal': str(prices.index[-1])[:10]
            if hasattr(prices.index[-1], 'strftime')
            else 'Aujourd\'hui'
    }