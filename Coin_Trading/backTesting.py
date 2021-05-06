import pyupbit
import pandas
import numpy as np
import time

date = None
dfs = [ ]

for i in range(20) :     # 1회 조회당 200개씩
    df = pyupbit.get_ohlcv("KRW-ETH", interval="minute30", to=date)
    dfs.append(df)

    date = df.index[0]
    time.sleep(0.5)

df = pandas.concat(dfs).sort_index()

df['ma_15'] = df['close'].rolling(15).mean()
df['ma_50'] = df['close'].rolling(50).mean()

df['cond_1'] = np.where( ( (df['ma_15'] >= df['ma_50']) ), 0, 1 )
df['cond_2'] = np.where( ( (df['ma_15'].shift(-1) < df['ma_50'].shift(-1)) ), 0, 1 )

df['buy'] = np.where( (df['cond_1'] == 1) & (df['cond_2'] == 1) , 1, 0)
df['sell'] = np.where( (df['cond_1'] == 0) & (df['cond_2'] == 0) , 1, 0)

df.to_excel("dd.xlsx")