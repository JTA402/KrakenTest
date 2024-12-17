import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import numpy as np
np.seterr(invalid='ignore')

import pandas as pd
import krakenex
from pykrakenapi import KrakenAPI
import mplfinance as mpf
import matplotlib.pyplot as plt
import time
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

class KrakenAPIWithoutSSL(krakenex.API):
   def __init__(self):
       super().__init__()
       self.session = requests.Session()
       retry_strategy = Retry(
           total=3,
           backoff_factor=1,
           status_forcelist=[429, 500, 502, 503, 504]
       )
       adapter = HTTPAdapter(max_retries=retry_strategy)
       self.session.mount("https://", adapter)
       self.session.verify = False

api = KrakenAPIWithoutSSL()
k = KrakenAPI(api)

pair = 'XXBTZUSD'
interval = 60
fast_ema = 8
slow_ema = 21
adx_period = 14

def calculate_adx(df, period=14):
   high = df['high']
   low = df['low']
   close = df['close']
   
   df['TR'] = np.maximum(
       np.maximum(
           high - low,
           abs(high - close.shift(1))
       ),
       abs(low - close.shift(1))
   )
   
   df['plus_DM'] = np.where(
       (high - high.shift(1)) > (low.shift(1) - low),
       np.maximum(high - high.shift(1), 0),
       0
   )
   
   df['minus_DM'] = np.where(
       (low.shift(1) - low) > (high - high.shift(1)),
       np.maximum(low.shift(1) - low, 0),
       0
   )
   
   df['ATR'] = df['TR'].ewm(span=period, adjust=False).mean()
   df['plus_DI'] = 100 * (df['plus_DM'].ewm(span=period, adjust=False).mean() / df['ATR'])
   df['minus_DI'] = 100 * (df['minus_DM'].ewm(span=period, adjust=False).mean() / df['ATR'])
   
   df['DX'] = 100 * abs(df['plus_DI'] - df['minus_DI']) / (df['plus_DI'] + df['minus_DI'])
   df['ADX'] = df['DX'].ewm(span=period, adjust=False).mean()
   
   return df

def fetch_and_calculate_indicators(pair, interval, fast_period=8, slow_period=21, adx_period=14):
   try:
       lookback_days = 120
       data, _ = k.get_ohlc_data(pair, interval=interval, 
                               since=pd.Timestamp.now() - pd.Timedelta(days=lookback_days))
       
       print("DataFrame columns:", data.columns.tolist())  # Add this line here
       
       data['time'] = pd.to_datetime(data['time'], unit='s')
       data.set_index('time', inplace=True)
       
       data.rename(columns={'vol': 'volume'}, inplace=True)
       
       data[f'EMA_{fast_period}'] = data['close'].ewm(span=fast_period, adjust=False).mean()
       data[f'EMA_{slow_period}'] = data['close'].ewm(span=slow_period, adjust=False).mean()
       
       data['Signal'] = (data[f'EMA_{fast_period}'] > data[f'EMA_{slow_period}']).astype(int)
       data['Crossover'] = data['Signal'].diff()
       data['Trend_Strength'] = (data[f'EMA_{fast_period}'] - data[f'EMA_{slow_period}']) / data[f'EMA_{slow_period}'] * 100
       
       data = calculate_adx(data, adx_period)
       
       return data
       
   except Exception as e:
       print(f"Error fetching data: {e}")
       return None

def plot_analysis(data, fast_period=8, slow_period=21):
    # Convert all columns to float
    data_plot = data[['open', 'high', 'low', 'close', 'volume']].astype(float)
    
    ap = [
        mpf.make_addplot(data[f'EMA_{fast_period}'], color='green'),
        mpf.make_addplot(data[f'EMA_{slow_period}'], color='red')
    ]
    
    style = mpf.make_mpf_style(base_mpf_style='charles', gridstyle='', rc={'figure.figsize': (15, 8)})
    
    fig, _ = mpf.plot(data_plot,
                      type='candle',
                      style=style,
                      addplot=ap,
                      volume=True,
                      warn_too_much_data=10000,  # Silence warning
                      panel_ratios=(4,1),
                      returnfig=True,
                      title=f'\nBTC/USD {fast_period}/{slow_period} EMA Crossover')
    
    return fig

def analyze_current_position(data):
   current_signal = "BULLISH" if data['Signal'].iloc[-1] else "BEARISH"
   trend_strength = data['Trend_Strength'].iloc[-1]
   adx_value = data['ADX'].iloc[-1]
   days_in_trend = len(data[data['Signal'] == data['Signal'].iloc[-1]].index)
   
   if abs(trend_strength) <= 2:
       strength_interpretation = "Very weak trend (EMAs are close together)"
   elif abs(trend_strength) <= 5:
       strength_interpretation = "Moderate trend"
   else:
       strength_interpretation = "Strong trend"
       
   adx_interpretation = (
       "No trend (ranging market)" if adx_value < 25 else
       "Strong trend" if adx_value < 50 else
       "Very strong trend" if adx_value < 75 else
       "Extremely strong trend"
   )
   
   return {
       'current_signal': current_signal,
       'trend_strength': trend_strength,
       'trend_interpretation': strength_interpretation,
       'adx_value': adx_value,
       'adx_interpretation': adx_interpretation,
       'days_in_trend': days_in_trend
   }

def run_analysis():
   plt.ion()
   fig = None
   while True:
       try:
           data = fetch_and_calculate_indicators(pair, interval, fast_ema, slow_ema, adx_period)
           
           if data is not None:
               if fig is not None:
                   plt.close(fig)
               
               fig = plot_analysis(data, fast_ema, slow_ema)
               
               analysis = analyze_current_position(data)
               
               print("\033[H\033[J")
               print("\nCurrent Position Analysis:")
               print(f"Signal: {analysis['current_signal']}")
               print(f"EMA Trend Strength: {analysis['trend_strength']:.2f}% - {analysis['trend_interpretation']}")
               print(f"ADX Value: {analysis['adx_value']:.2f} - {analysis['adx_interpretation']}")
               print(f"Days in Current Trend: {analysis['days_in_trend']}")
               
               current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
               print(f"\nLast Updated: {current_time}")
               
               plt.show()
               plt.pause(60)
               
           else:
               print("Failed to fetch data. Retrying in 1 minute...")
               time.sleep(60)
               
       except KeyboardInterrupt:
           if fig is not None:
               plt.close(fig)
           plt.close('all')
           print("\nStopping analysis...")
           break
       except Exception as e:
           print(f"Error: {e}. Retrying in 1 minute...")
           time.sleep(60)

if __name__ == "__main__":
   run_analysis()