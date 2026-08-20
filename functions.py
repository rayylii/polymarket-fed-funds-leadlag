import requests
import pandas as pd
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
