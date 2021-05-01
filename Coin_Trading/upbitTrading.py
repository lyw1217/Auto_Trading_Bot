import pyupbit
import os
from slacker import Slacker
import time
from datetime import datetime
import requests
#from logger import logger

dirname = os.path.dirname(__file__)

# access_key key 가져오기
with open(os.path.join(dirname, '../file/upbit_aces_key.txt'), 'r') as file:
        access_key = file.read().rstrip('\n')
# security key 가져오기
with open(os.path.join(dirname, '../file/upbit_sec_key.txt'), 'r') as file:
        secret_key = file.read().rstrip('\n')
# slack_key 가져오기
with open(os.path.join(dirname, '../file/slack_key.txt'), 'r') as file:
    slack_key = file.read().rstrip('\n')
    slack = Slacker(slack_key)

def dbout(message, *args):
    """인자로 받은 문자열을 파이썬 셸과 슬랙으로 동시에 출력한다."""
    tmp_msg = message
    for text in args:
        tmp_msg += str(text)
    print(datetime.now().strftime('[%m/%d %H:%M:%S]'), tmp_msg)
    strbuf = datetime.now().strftime('[%m/%d %H:%M:%S] ') + tmp_msg
    slack.chat.post_message('#python-trading-bot', strbuf)

def printlog(message, *args):
    """인자로 받은 문자열을 파이썬 셸에 출력한다."""
    tmp_msg = message
    for text in args:
        tmp_msg += str(text)
    ##logger.info(tmp_msg)
    #print(datetime.now().strftime('[%m/%d %H:%M:%S]'), message, *args)

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker):
    """시작 시간 조회"""
    # 일봉 조회 시 09시 기준으로 조회
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_ma_day(ticker, day):
    """day일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=int(day))
    ma = df['close'].rolling(int(day)).mean().iloc[-1]
    return ma

def get_ma_min(ticker, min):
    """min분 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute30", count=int(min))
    ma5 = df['close'].rolling(int(min)).mean().iloc[-1]
    return ma5

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()

    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

def get_slope_min(ma_old, min):
    """ 이전 값과 비교, 새로운 조회값이 더 크면 양수 """
    ma_new = get_ma_min("KRW-ETH", min)

    if (ma_old - ma_new) < 0 :
        return 1
    else :
        return (-1)

def get_min_order_amount(ticker):
    price = get_current_price(ticker)

    return (5000 / price)

# 로그인
upbit = pyupbit.Upbit(access_key, secret_key)
# 시작 메세지
dbout("autotrade start")

ma15_old    = get_ma_min("KRW-ETH", 15)
ma50_old    = get_ma_min("KRW-ETH", 50)
ma15_slope  = 0

eth         = upbit.get_balance("ETH")
min_amount  = get_min_order_amount("KRW-ETH")
buy_flag    = False
sell_flag   = False
send_cnt    = 0
if eth > min_amount :
    buy_state = True
else:
    buy_state = False

# 자동매매 시작
while True:
    try:
        time.sleep(1)
        ma15_slope  = get_slope_min(ma15_old, 15)
        ma15_new    = get_ma_min("KRW-ETH", 15)
        ma50_new    = get_ma_min("KRW-ETH", 50)

        t_now       = datetime.now()
        if (t_now.minute % 6 == 0) and (send_cnt == 0) :
            if (t_now.minute % 36 == 0) :
                dbout("ma_slope : %s, ma15_old : %.3f, ma15_new : %.3f , ma50_old : %.3f , ma50_new : %.3f"%(ma15_slope, float(ma15_old), float(ma15_new), float(ma50_old), float(ma50_new)))
            send_cnt = 1
        else :
            if (t_now.minute % 6 == 5) :
                send_cnt = 0
            continue

        if  (buy_state == False) and (ma15_old < ma50_old) and (ma15_new >= ma50_new) :
            buy_flag = True
        elif (buy_state == True) and (ma15_old > ma50_old) and (ma15_new <= ma50_new) :
            sell_flag = True

        ma15_old    = ma15_new
        ma50_old    = ma50_new

        if (ma15_slope > 0) and (buy_flag == True) and (buy_state == False) :       # 기울기 양수, ma15의 상승으로 인해 ma50과 교차 시
            krw = upbit.get_balance("KRW")
            if krw > 5000:
                upbit.buy_market_order("KRW-ETH", krw*0.9995)       # 수수료 고려 0.9995 (99.95%)
                buy_state   = True
                buy_flag    = False
                dbout("BUY!! 매수금액 : " + str(krw))

        elif (sell_flag == True) and (buy_state == True):
            eth        = upbit.get_balance("ETH")
            min_amount = get_min_order_amount("KRW-ETH")
            if eth > min_amount :
                upbit.sell_market_order("KRW-ETH", eth*0.9995)
                buy_state   = False
                sell_flag   = False
                time.sleep(10)
                krw       = upbit.get_balance("KRW")
                dbout("SELL!! 잔고 : " + str(krw))

    except Exception as e:
        dbout(e)
        time.sleep(1)
