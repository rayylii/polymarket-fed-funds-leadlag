import requests
import pandas as pd
import numpy as np
import json
import datetime
import zoneinfo


def get_polymarket_event(slug, meeting_date):
    url = f"https://gamma-api.polymarket.com/events?slug={slug}"
    response = requests.get(url)
    event = response.json()[0]

    et = zoneinfo.ZoneInfo('America/New_York')
    meeting_dt_et = datetime.datetime.strptime(meeting_date, "%Y-%m-%d").replace(hour=14, minute=0, tzinfo=et)
    start_ts = int((meeting_dt_et - datetime.timedelta(hours=2)).timestamp())
    end_ts = int((meeting_dt_et + datetime.timedelta(hours=2)).timestamp())

    all_probs = {}
    for market in event['markets']:
        outcome_name = market['groupItemTitle']
        token_ids = json.loads(market['clobTokenIds'])
        yes_id = token_ids[0]

        params = {"market": yes_id, "fidelity": 1, "startTs": start_ts, "endTs": end_ts}
        resp = requests.get("https://clob.polymarket.com/prices-history", params=params)
        hist = resp.json()

        if 'history' not in hist or len(hist['history']) == 0:
            print(f"warning: no price history for '{outcome_name}' in event '{slug}'")
            continue

        odf = pd.DataFrame(hist['history'])
        odf['datetime'] = pd.to_datetime(odf['t'], unit='s').dt.tz_localize('UTC').dt.tz_convert('America/New_York')
        all_probs[outcome_name] = odf

    return event, all_probs


def lead_lag_correlation(series_x, series_y, max_lag_minutes=30):
    x = series_x.diff().dropna()
    y = series_y.diff().dropna()

    results = []
    for lag in range(-max_lag_minutes, max_lag_minutes + 1):
        y_shifted = y.shift(lag)
        aligned = pd.concat([x, y_shifted], axis=1, join='inner').dropna()
        aligned.columns = ['x', 'y']

        if len(aligned) < 5:
            continue

        if aligned['x'].std() == 0 or aligned['y'].std() == 0:
            continue
            
        corr = aligned['x'].corr(aligned['y'])
        results.append({'lag': lag, 'correlation': corr, 'n_obs': len(aligned)})

    lags_df = pd.DataFrame(results)
    best_row = lags_df.loc[lags_df['correlation'].abs().idxmax()]
    best_lag = int(best_row['lag'])
    best_corr = best_row['correlation']

    return lags_df, best_lag, best_corr


def bootstrap_significance(series_x, series_y, observed_corr, max_lag_minutes=30, n_bootstrap=1000, seed=1):
    rng = np.random.default_rng(seed=seed)

    y_values = series_y.values.copy()

    exceed_count = 0
    for _ in range(n_bootstrap):
        rng.shuffle(y_values)
        y_shuffled = pd.Series(y_values, index=series_y.index)

        _, _, shuf_corr = lead_lag_correlation(series_x, y_shuffled, max_lag_minutes=max_lag_minutes)

        if abs(shuf_corr) >= abs(observed_corr):
            exceed_count += 1

    return exceed_count / n_bootstrap
    

def cusum(series, mu, sigma, k_multiplier=0.5, h_multiplier=4):
    diffs = series.diff().dropna()
    k = k_multiplier * sigma
    h = h_multiplier * sigma

    S_high = 0
    S_low = 0
    for t, d in diffs.items():
        S_high = max(0, S_high + (d - mu) - k)
        S_low = max(0, S_low + (mu - d) - k)

        if S_high > h or S_low > h:
            direction = 'up' if S_high > h else 'down'
            return t, direction, S_high, S_low

    return None, None, S_high, S_low