# polymarket-fed-funds-leadlag
tests whether polymarket's fed rate odds lead cme 30-day fed funds futures around fomc announcements.

## method
cross-correlation on first-differenced series, lags -30 to +30min, significance via 1000-trial permutation test (shuffle, recompute, count how often noise beats the real result).

cusum on the rate of change (not raw levels) to find when each series first shifts from baseline.

## data
polymarket implied probabilities via the gamma/clob apis, converted to a probability-weighted implied rate. cme zq futures, 1min ohlc, implied rate = 100 - price. four fomc meetings: march, april, june, july 2026.

## results
july 2026: cusum onset polymarket 13:47 vs zq 14:00 (~13min lead), cross-correlation found no fixed lag (lag=0, p<0.001) confirming the divergence isn't a repeating pattern.

march/april/june: no significant cross-correlation (p=0.36, 0.11, 0.99). no zq cusum onset detected on any of the three.

polymarket led futures by ~13min in the one meeting with a real surprise. no lead-lag in the three priced-in meetings.

## limitations
n=4 meetings, a case study not a general claim. data limited due to tradingview trial account limitations.

## future work
extend to a full year(s) of meetings. backtest a signal, trade zq the moment polymarket's cusum-detected shift fires, exit at a fixed horizon.

## stack
python

## run
```bash
git clone https://github.com/rayylii/polymarket-fed-funds-leadlag.git
cd polymarket-fed-funds-leadlag
pip install -r requirements.txt
jupyter notebook
```