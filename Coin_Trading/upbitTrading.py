import pyupbit
import os
from slacker import Slacker
import time
from datetime import datetime
import requests
from logger import logger

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
    logger.info(tmp_msg)
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

def get_ma15(ticker):
    """15일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=15)
    ma15 = df['close'].rolling(15).mean().iloc[-1]
    return ma15

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

# 로그인
upbit = pyupbit.Upbit(access_key, secret_key)
print("autotrade start")
# 시작 메세지 슬랙 전송
dbout("autotrade start")
'''
# 자동매매 시작
while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-BTC")
        end_time = start_time + datetime.timedelta(days=1)      # 시작 시간에서 1일을 더해준 값

        # 09:00:00 < 현재 시간 < 08:59:50 (hh:mm:ss)
        if start_time < now < end_time - datetime.timedelta(seconds=10):        # 8시 59분 50초
            target_price = get_target_price("KRW-BTC", 0.5)
            ma15 = get_ma15("KRW-BTC")
            current_price = get_current_price("KRW-BTC")
            if target_price < current_price and ma15 < current_price:
                krw = get_balance("KRW")
                if krw > 5000:
                    upbit.buy_market_order("KRW-BTC", krw*0.9995)       # 수수료 고려 0.9995 (99.95%)
        else:
            btc = get_balance("BTC")
            if btc > 0.00008:
                upbit.sell_market_order("KRW-BTC", btc*0.9995)
        time.sleep(1)
    except Exception as e:
        print(e)
        time.sleep(1)
'''