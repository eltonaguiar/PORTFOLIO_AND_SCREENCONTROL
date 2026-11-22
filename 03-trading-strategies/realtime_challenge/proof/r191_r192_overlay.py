#!/usr/bin/env python3
from __future__ import annotations
import json, math, sys
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import yfinance as yf
OUT = Path(__file__).resolve().parent.parent / 'results' / 'r191_r192_reconciliation.json'
PEER = {'spy_bnh': {'cagr': 0.1027, 'max_drawdown': -0.552, 'window': '2006-2026'},
        'trend_overlay': {'cagr': 0.0837, 'max_drawdown': -0.205, 'window': '2006-2026'},
        'note': 'peer verdict quotes these two rows; this script reconciles them'}
UNIVERSE = ['SPY', 'AOA', 'SHV', 'BND']
START_EARLY = '2004-01-01'
START_LATE = '2006-01-01'
COST_PER_SIDE = 0.0005
def cagr_from_eq(eq, idx):
    yrs = (idx[-1] - idx[0]).days / 365.25
    return float(eq.iloc[-1] ** (1 / yrs) - 1) if eq.iloc[-1] > 0 else float('nan')
def dd(eq):
    return float((eq / eq.cummax() - 1.0).min())
def sharpe(r):
    sd = r.std(ddof=1)
    return float(r.mean() / sd * math.sqrt(252)) if sd and sd > 0 else float('nan')
def turnover(w):
    return w.diff().abs().sum(axis=1).fillna(w.abs().sum(axis=1)).fillna(0.0)
def spy_bnh(close, cost=COST_PER_SIDE):
    r = close.pct_change().fillna(0.0)
    r.iloc[0] -= cost
    eq = (1 + r).cumprod()
    return {'eq': eq, 'cagr': cagr_from_eq(eq, close.index), 'sharpe': sharpe(r),
            'max_drawdown': dd(eq), 'total_return': float(eq.iloc[-1] - 1)}
def trend_overlay(close, open_, window_days=200, cost_per_side=COST_PER_SIDE):
    idx = close.index
    n = len(idx)
    sma = close.rolling(window_days, min_periods=window_days).mean()
    long_flag = (close > sma).reindex(idx).fillna(False)
    W = pd.DataFrame({'SPY': long_flag.astype(float), 'CASH': (~long_flag).astype(float)}, index=idx)
    ret = pd.DataFrame({'SPY': close.pct_change(), 'CASH': 0.0}, index=idx)
    s2 = pd.Series(idx, index=idx)
    me = sorted(s2.groupby([idx.year, idx.month]).max().tolist())
    for i in range(len(me) - 1):
        pos = idx.get_loc(me[i])
        fill = pos + 1
        if fill >= n:
            break
        ret.iloc[fill] = {'SPY': float(close.iloc[fill] / open_.iloc[fill] - 1.0), 'CASH': 0.0}
    gross = (W.shift(1) * ret).sum(axis=1).fillna(0.0)
    costs = turnover(W) * cost_per_side
    net = gross - costs
    eq = (1.0 + net).cumprod()
    yrs = (idx[-1] - idx[0]).days / 365.25
    return {'eq': eq, 'net': net, 'cagr': cagr_from_eq(eq, idx), 'sharpe': sharpe(net),
            'max_drawdown': dd(eq), 'total_return': float(eq.iloc[-1] - 1),
            'turnover_per_year': float(turnover(W).sum() / yrs)}
def aoa_6040_gic(close, cost_per_side=COST_PER_SIDE):
    tickers = ['SPY', 'BND', 'SHV', 'AOA']
    idx = close['SPY'].index
    W = pd.DataFrame(0.0, index=idx, columns=tickers)
    W['AOA'] = 1.0
    W6040 = pd.DataFrame({'SPY': 0.6, 'BND': 0.4, 'SHV': 0.0, 'AOA': 0.0}, index=idx)
    gic = pd.DataFrame({'SPY': 0.0, 'BND': 0.0, 'SHV': 1.0, 'AOA': 0.0}, index=idx)
    ret = pd.DataFrame({t: close[t].pct_change() for t in tickers}, index=idx).fillna(0.0)
    gross6040 = (W6040.shift(1) * ret).sum(axis=1).fillna(0.0)
    grossgic = (gic.shift(1) * ret).sum(axis=1).fillna(0.0)
    grossaoa = (W.shift(1) * ret).sum(axis=1).fillna(0.0)
    to6040 = turnover(W6040) * cost_per_side
    eq6040 = (1 + gross6040 - to6040).cumprod()
    eqgic = (1 + grossgic).cumprod()
    eqaoa = (1 + grossaoa - turnover(W) * cost_per_side).cumprod()
    def summarise(eq, net):
        r = net
        sd = r.std(ddof=1)
        return {'eq': eq, 'cagr': cagr_from_eq(eq, idx),
                'sharpe': float(r.mean() / sd * math.sqrt(252)) if sd and sd > 0 else float('nan'),
                'max_drawdown': dd(eq), 'total_return': float(eq.iloc[-1] - 1)}
    return {'aoa': summarise(eqaoa, grossaoa), '6040': summarise(eq6040, gross6040 - to6040),
            'gic': summarise(eqgic, grossgic)}
def slice_window(df, start):
    return df.loc[start:]
def main():
    raw = yf.download(UNIVERSE, start=START_EARLY, auto_adjust=True, progress=False, group_by='column')
    close = {t: raw['Close'][t].dropna() for t in UNIVERSE}
    open_ = {t: raw['Open'][t].reindex(close[t].index) for t in UNIVERSE}
    print('loaded', len(close['SPY']), 'bars', close['SPY'].index[0].date(), '->', close['SPY'].index[-1].date())
    results = {'generated_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
               'peer': PEER, 'window_early': START_EARLY, 'window_late': START_LATE,
               'convention': 'month-end close signal -> next-day open fill, 5bps/side', 'rows': {}}
    for label, start in (('early_2004', START_EARLY), ('late_2006', START_LATE)):
        c = {t: slice_window(close[t], start) for t in UNIVERSE}
        o = {t: slice_window(open_[t], start) for t in UNIVERSE}
        rows = {}
        rows['spy_buy_and_hold'] = spy_bnh(c['SPY'])
        rows['spy_200d_overlay'] = trend_overlay(c['SPY'], o['SPY'], window_days=200)
        rows.update(aoa_6040_gic(c))
        results['rows'][label] = rows
        print('\n=== %s (%s -> latest) ===' % (label, start))
        for name, r in rows.items():
            print('  %-22s CAGR %+.2f%%  Sharpe %+.2f  maxDD %+.2f%%  total %+.2f%%' % (name, r['cagr']*100, r['sharpe'], r['max_drawdown']*100, r['total_return']*100))
    early = results['rows']['early_2004']
    late = results['rows']['late_2006']
    attribution = {'spy_cagr_peer': PEER['spy_bnh']['cagr'],
                   'spy_cagr_early_2004': early['spy_buy_and_hold']['cagr'],
                   'spy_cagr_late_2006': late['spy_buy_and_hold']['cagr'],
                   'spy_dd_peer': PEER['spy_bnh']['max_drawdown'],
                   'spy_dd_early_2004': early['spy_buy_and_hold']['max_drawdown'],
                   'spy_dd_late_2006': late['spy_buy_and_hold']['max_drawdown'],
                   'overlay_cagr_peer': PEER['trend_overlay']['cagr'],
                   'overlay_cagr_early_2004': early['spy_200d_overlay']['cagr'],
                   'overlay_cagr_late_2006': late['spy_200d_overlay']['cagr'],
                   'overlay_dd_peer': PEER['trend_overlay']['max_drawdown'],
                   'overlay_dd_early_2004': early['spy_200d_overlay']['max_drawdown'],
                   'overlay_dd_late_2006': late['spy_200d_overlay']['max_drawdown'],
                   'conclusion': None}
    ov_gap_peer_vs_early = PEER['trend_overlay']['cagr'] - early['spy_200d_overlay']['cagr']
    ov_gap_early_vs_late = early['spy_200d_overlay']['cagr'] - late['spy_200d_overlay']['cagr']
    attribution['gap_peer_vs_2004_bps'] = round(ov_gap_peer_vs_early * 1e4, 1)
    attribution['gap_2004_vs_2006_bps'] = round(ov_gap_early_vs_late * 1e4, 1)
    if abs(ov_gap_early_vs_late) >= abs(ov_gap_peer_vs_early) * 0.6:
        attribution['conclusion'] = 'most of the peer gap is the START DATE (2004 vs 2006), not the rebalance convention'
    else:
        attribution['conclusion'] = 'gap is not explained by start date alone; rebalance convention / cash drag is a contributor'
    results['gap_attribution'] = attribution
    serial = {'generated_utc': results['generated_utc'], 'peer': results['peer'],
              'window_early': results['window_early'], 'window_late': results['window_late'],
              'convention': results['convention'], 'rows': {},
              'gap_attribution': results['gap_attribution']}
    for label, rows in results['rows'].items():
        serial['rows'][label] = {}
        for book_name, book in rows.items():
            serial['rows'][label][book_name] = {}
            for k, v in book.items():
                if k not in ('cagr', 'sharpe', 'max_drawdown', 'total_return', 'turnover_per_year'):
                    continue
                try:
                    serial['rows'][label][book_name][k] = round(float(v), 6)
                except (TypeError, ValueError):
                    continue
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(serial, indent=1, default=float), encoding='utf-8')
    print('\n--- R192 gap attribution ---')
    print('peer SPY CAGR %+.2f%% | 2004 %+.2f%% | 2006 %+.2f%%' % (PEER['spy_bnh']['cagr'], early['spy_buy_and_hold']['cagr'], late['spy_buy_and_hold']['cagr']))
    print('peer overlay CAGR %+.2f%% | 2004 %+.2f%% | 2006 %+.2f%%' % (PEER['trend_overlay']['cagr'], early['spy_200d_overlay']['cagr'], late['spy_200d_overlay']['cagr']))
    print('peer DD %+.2f%% | 2004 %+.2f%% | 2006 %+.2f%%' % (PEER['spy_bnh']['max_drawdown'], early['spy_buy_and_hold']['max_drawdown'], late['spy_buy_and_hold']['max_drawdown']))
    print('conclusion: %s' % attribution['conclusion'])
    print('\nwrote %s' % OUT)
    return 0
if __name__ == '__main__':
    sys.exit(main())
