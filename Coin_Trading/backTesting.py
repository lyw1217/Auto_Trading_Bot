import pyupbit
import pandas
import numpy as np
import time

date = None
dfs = [ ]

for i in range(5) :     # 1회 조회당 200개씩
    df = pyupbit.get_ohlcv("KRW-ETH", interval="minute5", to=date)
    dfs.append(df)

    date = df.index[0]
    time.sleep(0.5)

df = pandas.concat(dfs).sort_index()

df['ma_15'] = df['close'].rolling(15).mean()
df['ma_50'] = df['close'].rolling(50).mean()

df['is_ma'] = np.where(df['ma_50'] > 0 , 1, 0)

df['cond_1'] = np.where( ( (df['is_ma'] == 1) & (df['ma_15'] >= df['ma_50']) ), 0, 1 )
df['cond_2'] = np.where( ( (df['ma_15'].shift(-1) < df['ma_50'].shift(-1)) ), 0, 1 )

df['f_buy'] = np.where( (df['cond_1'] == 1) & (df['cond_2'] == 1) , 1, 0)
df['f_sell'] = np.where( (df['cond_1'] == 0) & (df['cond_2'] == 0) , 1, 0)

df['buy'] = np.where( (df['f_buy'] == 1) & (df['ma_15'] > 0) & ((df['ma_50'] > 0)), (-1)*df['open'], 0)
df['sell'] = np.where( (df['f_sell'] == 1) & (df['ma_15'] > 0) & ((df['ma_50'] > 0)), df['open'], 0)

#print ( np.where( (df['buy'] != 0) & ((df['sell'] != 0))) )
#df['total'] = np.cumsum(np.where( (df['buy'] != 0) & ((df['sell'] != 0))))

df.to_excel("dd.xlsx")