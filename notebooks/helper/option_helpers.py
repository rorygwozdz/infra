import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
from scipy.optimize import curve_fit
import warnings

def filter_expir_dates_per_ticker(df, date_column='expirDate', min_days=7, max_days=60, ticker_column='ticker'):
    today = datetime.date.today()
    min_date = today + datetime.timedelta(days=min_days)
    max_date = today + datetime.timedelta(days=max_days)
    df[date_column] = pd.to_datetime(df[date_column])

    filtered_df = df[(df[date_column].dt.date > min_date) & (df[date_column].dt.date < max_date)].copy()

    def get_best_expir_date(group):
        if group.empty:
            return pd.DataFrame()
        first_expir_date = group[date_column].min()
        return group[group[date_column] == first_expir_date]

    filtered_best_expir_per_ticker = filtered_df.groupby(ticker_column).apply(get_best_expir_date).reset_index(drop=True)
    return filtered_best_expir_per_ticker

def calculate_forward_volatility(df, strike_column='strike', stkpx_column='stkPx', expir_date_column='expirDate', vol_column='smoothSmvVol', new_col_name='forward_vol'):
    try:
        df[expir_date_column] = pd.to_datetime(df[expir_date_column])
        def calculate_forward_vol(group):
            group = group.sort_values(by=strike_column)
            forward_vols = []
            for i in range(len(group) - 1):
                lower_strike_row = group.iloc[i]
                upper_strike_row = group.iloc[i + 1]
                lower_vol = lower_strike_row[vol_column]
                upper_vol = upper_strike_row[vol_column]
                forward_vol = (lower_vol + upper_vol) / 2
                forward_vols.append(forward_vol)
            forward_vols.insert(0, forward_vols[0])
            if len(forward_vols) < len(group):
                forward_vols.extend([forward_vols[-1]] * (len(group) - len(forward_vols)))
            group[new_col_name] = forward_vols
            return group
        df = df.groupby(expir_date_column).apply(calculate_forward_vol)
        return df
    except KeyError as e:
        print(f"KeyError: Column '{e.args[0]}' not found in DataFrame.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def plot_iv_vol_by_strike(df, strike_column='strike', stkpx_column='stkPx'):
    iv_vol_columns = [col for col in df.columns if 'MidIv' in col or 'smoothSmvVol' in col]
    if not iv_vol_columns:
        print("No columns containing 'MidIv' or 'smoothSmvVol' found.")
        return
    try:
        df_sorted = df.sort_values(by=strike_column)
        plt.figure(figsize=(12, 8))
        for col in iv_vol_columns:
            plt.plot(df_sorted[strike_column], df_sorted[col], label=col, marker='o')
        stk_px_value = df_sorted[stkpx_column].iloc[0]
        plt.axvline(x=stk_px_value, color='red', linestyle='--', label=f'stkPx: {stk_px_value}')
        plt.title('Implied Volatility by Strike')
        plt.xlabel('Strike')
        plt.ylabel('Value')
        plt.legend()
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
    except KeyError:
        print(f"Error: Column '{strike_column}' not found in DataFrame.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def get_nearest_strikes_per_ticker(df, strike_column='strike', stkpx_column='stkPx', expir_date_column='expirDate', ticker_column='ticker'):
    try:
        df[expir_date_column] = pd.to_datetime(df[expir_date_column])
        def nearest_strikes(group):
            stk_px = group[stkpx_column].iloc[0]
            group['distance'] = abs(group[strike_column] - stk_px)
            nearest = group.nsmallest(2, 'distance')
            return nearest
        nearest_strikes_df = df.groupby([expir_date_column, ticker_column]).apply(nearest_strikes).reset_index(drop=True)
        return nearest_strikes_df
    except KeyError:
        print(f"Error: Column '{strike_column}', '{stkpx_column}', '{expir_date_column}', or '{ticker_column}' not found.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def calculate_weighted_average_columns_per_ticker(df, strike_column='strike', stkpx_column='stkPx', expir_date_column='expirDate', ticker_column='ticker'):
    try:
        df[expir_date_column] = pd.to_datetime(df[expir_date_column])
        def weighted_avg(group):
            stk_px = group[stkpx_column].iloc[0]
            strikes = group[strike_column].values
            if len(strikes) != 2:
                if len(group) > 0:
                    return pd.DataFrame([group.iloc[0].to_dict()])
                else:
                    return None
            lower_strike = min(strikes)
            upper_strike = max(strikes)
            if not (lower_strike <= stk_px <= upper_strike):
                return None
            weight_upper = (stk_px - lower_strike) / (upper_strike - lower_strike)
            weight_lower = 1 - weight_upper
            result = {}
            for col in group.select_dtypes(include='number').columns:
                if col not in [strike_column, ticker_column, expir_date_column, stkpx_column]:
                    lower_val = group.loc[group[strike_column] == lower_strike, col].iloc[0]
                    upper_val = group.loc[group[strike_column] == upper_strike, col].iloc[0]
                    result[col] = lower_val * weight_lower + upper_val * weight_upper
            return pd.DataFrame([result])
        weighted_averages = df.groupby([expir_date_column, ticker_column]).apply(weighted_avg)
        return weighted_averages.reset_index()
    except KeyError as e:
        print(f"KeyError: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def plot_histogram(df, column_to_plot):
    try:
        plt.figure(figsize=(10, 6))
        df[column_to_plot].hist(bins=30)
        plt.title(f'Histogram of {column_to_plot}')
        plt.xlabel(column_to_plot)
        plt.ylabel('Frequency')
        plt.grid(True)
        plt.tight_layout()
        plt.show()
    except KeyError:
        print(f"Error: Column '{column_to_plot}' not found in DataFrame.")
    except TypeError:
        print(f"Error: Column '{column_to_plot}' is not suitable for a histogram.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def plot_histogram_interactive(df, column_name):
    plt.figure(figsize=(10, 6))
    if column_name in df.columns:
        df[column_name].hist(bins=30)
        plt.title(f'Histogram of {column_name}')
        plt.xlabel(column_name)
        plt.ylabel('Frequency')
        plt.grid(True)
        plt.tight_layout()
        plt.show()
    else:
        print(f"Error: Column '{column_name}' not found in DataFrame.")

def create_plot_interface(df):
    import ipywidgets as widgets
    from IPython.display import display
    column_names = df.columns.tolist()
    buttons = []
    for col in column_names:
        button = widgets.Button(description=col)
        def on_button_clicked(b, column=col):
            plot_histogram_interactive(df, column)
        button.on_click(on_button_clicked)
        buttons.append(button)
    display(widgets.HBox(buttons))

def plot_column_by_expir_date(df, column_to_plot, expir_date_column='expirDate'):
    try:
        df[expir_date_column] = pd.to_datetime(df[expir_date_column])
        df_sorted = df.sort_values(by=expir_date_column)
        plt.figure(figsize=(10, 6))
        plt.plot(df_sorted[expir_date_column], df_sorted[column_to_plot], marker='o')
        plt.title(f'{column_to_plot} by Expiration Date')
        plt.xlabel('Expiration Date')
        plt.ylabel(column_to_plot)
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
    except KeyError:
        print(f"Error: Column '{column_to_plot}' or '{expir_date_column}' not found in DataFrame.")
    except TypeError:
        print(f"Error: '{expir_date_column}' is not a datetime column.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def create_interactive_ticker_plot(df, ticker_column='ticker', date_column='expirDate', value_column='smoothSmvVol'):
    import ipywidgets as widgets
    from IPython.display import display
    import altair as alt
    tickers = sorted(df[ticker_column].unique().tolist())
    ticker_dropdown = widgets.Dropdown(options=tickers, description='Select Ticker:', disabled=False)
    output = widgets.Output()
    def update_plot(selected_ticker):
        with output:
            output.clear_output(wait=True)
            try:
                check = df.query(f"{ticker_column} == '{selected_ticker}'")[[date_column, value_column]].groupby(date_column).mean().reset_index()
                chart = alt.Chart(check).mark_line(point=True).encode(
                    x=alt.X(date_column, axis=alt.Axis(title=date_column)),
                    y=alt.Y(value_column, axis=alt.Axis(title=value_column)),
                    tooltip=[date_column, value_column]
                ).interactive()
                display(chart)
            except KeyError as e:
                print(f"Error: {e}")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
    def on_ticker_change(change):
        update_plot(change.new)
    ticker_dropdown.observe(on_ticker_change, names='value')
    display(ticker_dropdown, output)

def nelson_siegel_fit(df, ticker_col='ticker', expir_date_col='expirDate', vol_col='vol', yte_col='yte', output_vol_col='ns_fit', dte_fit_cutoff=21/365):
    def ns_curve(tau, beta0, beta1, beta2, lamda):
        return beta0 + beta1 * (1 - np.exp(-tau / lamda)) / (tau / lamda) + \
               beta2 * ((1 - np.exp(-tau / lamda)) / (tau / lamda) - np.exp(-tau / lamda))
    def fit_ns_group(group_raw):
        group = group_raw.query(f"yte > {dte_fit_cutoff}").copy()
        tau = np.array(group[yte_col])
        vol = group[vol_col].values
        if len(tau) < 3:
            group[output_vol_col] = group[vol_col]
            print(f"Insufficient data points for fitting: {group.iloc[0][ticker_col]}, {group.iloc[0][expir_date_col]}")
            return group_raw
        p0 = [0.1, -0.05, -0.05, 1.0]
        try:
            popt, pcov = curve_fit(ns_curve, tau, vol, p0=p0,
                                 bounds=((-np.inf, -np.inf, -np.inf, 0.00001),
                                         (np.inf, np.inf, np.inf, np.inf)),
                                 maxfev=5000)
            group[output_vol_col] = ns_curve(tau, *popt)
            group_raw = group_raw.merge(group[[expir_date_col, output_vol_col]], how="left")
        except (RuntimeError, TypeError) as e:
            print(f"Fit failed for group: {group.iloc[0][ticker_col]}, {group.iloc[0][expir_date_col]}. Error: {e}")
            group[output_vol_col] = np.nan
        return group_raw
    if df[expir_date_col].dtype != 'datetime64[ns]':
        df[expir_date_col] = pd.to_datetime(df[expir_date_col])
    result_df = df.groupby([ticker_col], group_keys=False).apply(fit_ns_group)
    return result_df

def compare_vols_plot(df, vol_col1='smoothSmvVol', vol_col2='ns_fit', ticker_col='ticker', expir_date_col='expirDate'):
    try:
        df = df.copy()
        df['vol_diff'] = df[vol_col1] - df[vol_col2]
        df['vol_pct_diff'] = (df[vol_col1] - df[vol_col2]) / df[vol_col1] * 100
        df['vol_abs_pct_diff'] = abs(df['vol_pct_diff'])
        df['vol_sq_diff'] = df['vol_diff']**2
        grouped_stats = df.groupby([ticker_col]).agg(
            mean_diff=('vol_diff', 'mean'),
            std_diff=('vol_diff', 'std'),
            mean_pct_diff=('vol_pct_diff', 'mean'),
            std_pct_diff=('vol_pct_diff', 'std'),
            mean_abs_pct_diff=('vol_abs_pct_diff', 'mean'),
            mean_sq_diff=('vol_sq_diff', 'mean')
        ).reset_index()
        df = df.merge(grouped_stats, on=[ticker_col], how='left')
        print(f"Volatility Comparison Statistics (Grouped by {ticker_col} and {expir_date_col}):\n")
        print(grouped_stats.to_markdown(index=False, numalign="left", stralign="left"))
        plt.figure(figsize=(10, 6))
        plt.plot(df[expir_date_col], df[vol_col1], label=vol_col1, marker='o')
        plt.plot(df[expir_date_col], df[vol_col2], label=vol_col2, marker='x')
        plt.title(f'Volatility Comparison: {vol_col1} vs. {vol_col2}')
        plt.xlabel(expir_date_col)
        plt.ylabel('Volatility')
        plt.legend()
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
        return df
    except KeyError as e:
        print(f"KeyError: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def filter_df_by_matching_tickers(df1, df2, ticker_col1='ticker', ticker_col2='ticker'):
    matching_tickers = set(df2[ticker_col2])
    filtered_df1 = df1[df1[ticker_col1].isin(matching_tickers)].copy()
    return filtered_df1

def calculate_forward_volatility_shifted_with_expir(df, vol_col_short='smoothSmvVol', shift_period=1):
    df['expirDate'] = pd.to_datetime(df['expirDate'])
    df['time_to_maturity_short'] = df['yte']
    shifted_vol_col_name = f'{vol_col_short}_shifted'
    df[shifted_vol_col_name] = df[vol_col_short].shift(-shift_period)
    df['shifted_expirDate'] = df['expirDate'].shift(-shift_period)
    df['time_to_maturity_long'] = (df['shifted_expirDate'] - df['tradeDate']).dt.days / 365.25
    valid_rows = ~df[shifted_vol_col_name].isna() & ~df['time_to_maturity_long'].isna()
    df['forwardVol'] = pd.NA
    df.loc[valid_rows, 'forwardVol'] = (
        (df.loc[valid_rows, 'time_to_maturity_long'] * df.loc[valid_rows, shifted_vol_col_name]**2 -
         df.loc[valid_rows, 'time_to_maturity_short'] * df.loc[valid_rows, vol_col_short]**2) /
        (df.loc[valid_rows, 'time_to_maturity_long'] - df.loc[valid_rows, 'time_to_maturity_short'])
    )**0.5
    df.drop(columns=['time_to_maturity_long', 'time_to_maturity_short'], inplace=True)
    df["forwardVol"] = df["forwardVol"].fillna(df[vol_col_short])
    return df

def plot_volatilities(df, regular_vol_col='smoothSmvVol', second_vol_col='forwardVol', third_vol_col='forwardVol', title='Volatility Comparison'):
    plt.figure(figsize=(10, 6))
    plt.plot(df['expirDate'], df[regular_vol_col], marker='o', linestyle='-', label=regular_vol_col, color='darkgreen')
    plt.plot(df['expirDate'], df[second_vol_col], marker='x', linestyle='--', label=second_vol_col, color='green')
    if third_vol_col in df.columns:
        plt.plot(df['expirDate'], df[third_vol_col], marker='h', linestyle=':', label=third_vol_col, color='black')

    plt.xlabel('Expiration Date')
    plt.ylabel('Implied Volatility')
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()