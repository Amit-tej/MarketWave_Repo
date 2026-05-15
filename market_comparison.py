import pandas as pd
import numpy as np
from utils import get_logger

logger = get_logger('market_comparison')

def rank_markets(df, price_col='p_modal'):
    # Compute modal price per market and volatility
    grp = df.groupby('market_name')[price_col].agg(['median','mean','std']).reset_index()
    grp = grp.rename(columns={'median':'modal','std':'volatility'})
    # Rank by modal desc, lower volatility preferred
    grp['rank_score'] = grp['modal'] - grp['volatility']
    grp = grp.sort_values('rank_score', ascending=False)
    return grp

def categorize_market(row, modal_thresholds):
    # modal_thresholds: dict with percentiles
    if row['modal'] >= modal_thresholds['best']:
        return 'Best'
    if row['modal'] >= modal_thresholds['good']:
        return 'Good'
    if row['modal'] >= modal_thresholds['fair']:
        return 'Fair'
    return 'Avoid'

def market_recommendations(df, price_col='p_modal'):
    ranked = rank_markets(df, price_col)
    pct = np.percentile(ranked['modal'], [75,90])
    thresholds = {'fair': pct[0], 'good': pct[0], 'best': pct[1]}
    ranked['category'] = ranked.apply(lambda r: categorize_market(r, thresholds), axis=1)
    return ranked

def potential_profit(best_price_per_quintal, selected_price_per_quintal, qty_kg, transport_cost_per_kg=0.0):
    """Compute potential extra profit given prices in ₹/quintal and quantity in kg.
    best_price_per_quintal, selected_price_per_quintal: prices in ₹/quintal
    qty_kg: quantity in kilograms
    transport_cost_per_kg: transport cost in ₹ per kg
    Returns profit in ₹
    """
    # convert per quintal to per kg
    best_per_kg = best_price_per_quintal / 100.0
    sel_per_kg = selected_price_per_quintal / 100.0
    extra = (best_per_kg - sel_per_kg) * qty_kg - transport_cost_per_kg * qty_kg
    return extra


def top_recommendation_summary(df, price_col='p_modal'):
    """Compute how often each market is the top recommendation across commodities.
    Returns a DataFrame with counts and percentages overall and per-commodity.
    """
    # ensure inputs
    if price_col not in df.columns:
        raise ValueError(f'Price column {price_col} not in dataframe')
    # group by commodity and determine top market (by modal price)
    commodities = df['cmdty'].dropna().unique()
    rows = []
    top_counts = {}
    for cmd in commodities:
        sub = df[df['cmdty'].str.lower().str.strip() == str(cmd).lower().strip()]
        if sub.empty:
            continue
        grp = sub.groupby('market_name')[price_col].median().reset_index().rename(columns={price_col:'modal'})
        grp = grp.sort_values('modal', ascending=False)
        top_market = grp.iloc[0]['market_name']
        rows.append({'commodity': cmd, 'top_market': top_market, 'top_modal': grp.iloc[0]['modal']})
        top_counts[top_market] = top_counts.get(top_market, 0) + 1

    summary = pd.DataFrame(rows)
    # overall counts
    total = len(summary)
    overall = pd.DataFrame([{'market_name': k, 'count': v, 'percent': v/total*100.0} for k,v in top_counts.items()])
    overall = overall.sort_values('count', ascending=False).reset_index(drop=True)
    return {'per_commodity': summary, 'overall': overall, 'total_commodities': total}
