import pandas as pd

def set_multiindex(df):
    return df.set_index(['trade_date', 'ticker', 'expirDate']).sort_index()

def get_closest_to_delta(df, target_delta):
    def closest_rows(group):
        above = group[group['delta'] >= target_delta].sort_values('delta').head(1)
        below = group[group['delta'] < target_delta].sort_values('delta', ascending=False).head(1)
        return pd.concat([below, above])
    return df.groupby(level=['trade_date', 'ticker', 'expirDate'], group_keys=False).apply(closest_rows)

def get_closest_to_price_for_ticker(df, ticker, target_price):
    sub = df[df.index.get_level_values('ticker') == ticker]
    above = sub[sub['spot_px'] >= target_price].sort_values('spot_px').head(1)
    below = sub[sub['spot_px'] < target_price].sort_values('spot_px', ascending=False).head(1)
    return pd.concat([below, above])

def get_ticker_chain_for_expiry(df, ticker, expirDate):
    return df.xs((ticker, expirDate), level=['ticker', 'expirDate'])

def get_ticker_all_chains(df, ticker):
    return df.xs(ticker, level='ticker')

def get_expiries_for_ticker(df, ticker):
    return sorted(df.xs(ticker, level='ticker').index.get_level_values('expirDate').unique())

def get_subset_by_tickers(df, tickers):
    idx = pd.IndexSlice
    return df.loc[idx[:, tickers, :], :]