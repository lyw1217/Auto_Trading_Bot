import os
import sys
import jwt
import uuid
import hashlib
from urllib.parse import urlencode
import pandas as pd
import json
from slacker import Slacker
from datetime import date, datetime
from logger import logger

import requests

import time, calendar

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from coin_util import *

from logger import logger

dirname = os.path.dirname(__file__)

# access key 가져오기
with open(os.path.join(dirname, '../../file/upbit_aces_key.txt'), 'r') as file:
        access_key = file.read().rstrip('\n')
# security key 가져오기
with open(os.path.join(dirname, '../../file/upbit_sec_key.txt'), 'r') as file:
        secret_key = file.read().rstrip('\n')
# slack_key 가져오기
with open(os.path.join(dirname, '../../file/slack_key.txt'), 'r') as file:
    slack_key = file.read().rstrip('\n')
    slack = Slacker(slack_key)

def dbgout(message):
    """인자로 받은 문자열을 파이썬 셸과 슬랙으로 동시에 출력한다."""
    print(datetime.now().strftime('[%m/%d %H:%M:%S]'), message)
    strbuf = datetime.now().strftime('[%m/%d %H:%M:%S] ') + message
    slack.chat.post_message('#python-trading-bot', strbuf)

def printlog(message, *args):
    """인자로 받은 문자열을 파이썬 셸에 출력한다."""
    tmp_msg = message
    for text in args:
        tmp_msg += str(text)
    logger.info(tmp_msg)
    #print(datetime.now().strftime('[%m/%d %H:%M:%S]'), message, *args)

server_url = 'https://api.upbit.com'

def get_market_all():
    try:
        url = server_url + "/v1/market/all"

        querystring = {"isDetails":"true"}

        response = requests.request("GET", url , params=querystring)
        
        return response.json()
    except Exception as ex:
        dbgout("`get_market_all() -> exception! " + str(ex) + "`")
        return None

def get_current_cash():
    ''' 주문 가능 금액 '''
    try:
        url = server_url + "/v1/accounts"
        payload = {
            'access_key': access_key,
            'nonce': str(uuid.uuid4()),
        }
        jwt_token = jwt.encode(payload, secret_key)
        authorize_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorize_token}
        res = requests.get( url , headers=headers)
        item = res.json()[0]
        return float(item['balance'])
    except Exception as ex:
        dbgout("`get_current_cash() -> exception! " + str(ex) + "`")
        return None

def get_stock_balance(market):
    ''' 인자로 받은 종목의 종목명과 수량을 반환 '''
    try:
        url = "/v1/orders/chance"
        query = {
            'market': market,
        }
        query_string = urlencode(query).encode()

        m = hashlib.sha512()
        m.update(query_string)
        query_hash = m.hexdigest()

        payload = {
            'access_key': access_key,
            'nonce': str(uuid.uuid4()),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512',
        }

        jwt_token = jwt.encode(payload, secret_key)
        authorize_token = 'Bearer {}'.format(jwt_token)
        headers = {"Authorization": authorize_token}

        res = requests.get(server_url + url, params=query, headers=headers)

        print(res.json())
    except Exception as ex:
        dbgout("`get_stock_balance() -> exception! " + str(ex) + "`")
        return None

def get_current_orderbook(market):
    ''' 1호가의 매수호가, 매도호가 반환 '''
    try:
        url = server_url + "/v1/orderbook"
        querystring = {
            "markets":market,
        }
        response = requests.request("GET", url , params=querystring)

        item = response.json()[0]['orderbook_units']
        return item[0]['ask_price'] , item[0]['bid_price']
    except Exception as ex:
        dbgout("`get_current_price(" + str(market) + ") -> exception! " + str(ex) + "`")
        return None

def get_current_minute_candles(market, minute):
    ''' 현재 가격 반환 '''
    try:
        url = server_url + "/v1/candles/minutes/" + str(minute)
        querystring = {
            "market":market,
            "count":"1"
        }
        response = requests.request("GET", url , params=querystring)
        item = response.json()[0]
        return item['trade_price']
    except Exception as ex:
        dbgout("`get_current_minute_candles() -> exception! " + str(ex) + "`")
        return None

def get_current_days_candles(market):
    ''' 현재 가격 반환 '''
    try:
        url = server_url + "/v1/candles/days"
        querystring = {
            "market":market,
            "count":"1"
        }
        response = requests.request("GET", url , params=querystring)
        item = response.json()[0]
        return item['trade_price']
    except Exception as ex:
        dbgout("`get_current_days_candles() -> exception! " + str(ex) + "`")
        return None
    
def get_ohlc_day(market, qty):
    ''' market의 OHLC 가격 정보를 qty 개수만큼 반환 '''
    try:
        url = server_url + "/v1/candles/days"
        count = qty
        querystring = {
            "market":market,
            "count":count
        }
        response = requests.request("GET", url , params=querystring)
        item = response.json()
        columns = ['open', 'high', 'low', 'close']
        index = []
        rows = []
        for i in range(count): 
            #index.append(datetime.fromtimestamp(int(item[i]['timestamp'])).strftime('%Y%m%d'))
            index.append(item[i]['candle_date_time_kst'])
            rows.append([item[i]['opening_price'], item[i]['high_price'],
                item[i]['low_price'], item[i]['prev_closing_price']]) 
        df = pd.DataFrame(rows, columns=columns, index=index) 
        return df
    except Exception as ex:
        dbgout("`get_ohlc_day() -> exception! " + str(ex) + "`")
        return None

def get_target_price_day(market):
    """매수 목표가를 반환한다."""
    try:
        time_now = datetime.now()
        str_today = time_now.strftime('%Y%m%d')
        ohlc = get_ohlc_day(market, 10)
        if str_today == str(ohlc.iloc[0].name):
            today_open = ohlc.iloc[0].open
            lastday = ohlc.iloc[1]
        else:
            lastday = ohlc.iloc[0]                                      
            today_open = lastday[3]
        lastday_high = lastday[1]
        lastday_low = lastday[2]
        target_price = today_open + (lastday_high - lastday_low) * 0.5 # 0.5 = 수익률
        return target_price
    except Exception as ex:
        dbgout("`get_target_price_day() -> exception! " + str(ex) + "`")
        return None

def get_movingavrg_day(market, day):
    ''' market의 day일 만큼의 이동평균가격을 반환 '''
    try:
        time_now = datetime.now()
        str_today = time_now.strftime('%Y%m%d')
        ohlc = get_ohlc_day(market, 20)
        if str_today == str(ohlc.iloc[0].name):
            lastday = ohlc.iloc[1].name
        else:
            lastday = ohlc.iloc[0].name
        closes = ohlc['close'].sort_index()         
        ma = closes.rolling(window=day).mean()
        return ma.loc[lastday]
    except Exception as ex:
        dbgout('get_movingavrg_day(' + str(day) + ') -> exception! ' + str(ex))
        return None  

def get_ohlc_min(market, qty, minute):
    ''' market의 OHLC 가격 정보를 qty 개수만큼 반환 '''
    try:
        url = server_url + "/v1/candles/minutes/" + str(minute)
        count = qty
        querystring = {
            "market":market,
            "count":count
        }
        response = requests.request("GET", url , params=querystring)
        item = response.json()
        columns = ['open', 'high', 'low', 'close']
        index = []
        rows = []
        for i in range(count): 
            index.append(item[i]['candle_date_time_kst'])
            rows.append([item[i]['opening_price'], item[i]['high_price'],
                item[i]['low_price'], item[i]['trade_price']]) 
        df = pd.DataFrame(rows, columns=columns, index=index) 
        return df
    except Exception as ex:
        dbgout("`get_ohlc_day() -> exception! " + str(ex) + "`")
        return None

def get_target_price_min(market, minute):
    """매수 목표가를 반환한다."""
    try:
        time_now = datetime.now()
        str_today = time_now.strftime('%Y%m%d')
        ohlc = get_ohlc_min(market, 10, minute)
        if str_today == str(ohlc.iloc[0].name):
            today_open = ohlc.iloc[0].open
            lastday = ohlc.iloc[1]
        else:
            lastday = ohlc.iloc[0]                                      
            today_open = lastday[3]
        lastday_high = lastday[1]
        lastday_low = lastday[2]
        target_price = today_open + (lastday_high - lastday_low) * 0.5 # 0.5 = 수익률
        return target_price
    except Exception as ex:
        dbgout("`get_target_price_day() -> exception! " + str(ex) + "`")
        return None

def get_movingavrg_min(market, qty, minute):
    ''' market의 qty분 만큼의 이동평균가격을 반환 '''
    try:
        time_now = datetime.now()
        str_today = time_now.strftime('%Y%m%d')
        ohlc = get_ohlc_min(market, 20, minute)
        if str_today == str(ohlc.iloc[0].name):
            lastday = ohlc.iloc[1].name
        else:
            lastday = ohlc.iloc[0].name
        closes = ohlc['close'].sort_index()         
        ma = closes.rolling(window=qty).mean()
        return ma.loc[lastday]
    except Exception as ex:
        dbgout('get_movingavrg_day(' + str(qty) + ') -> exception! ' + str(ex))
        return None  

def buy_coin(market):
    try:
        global bought_list
        if market in bought_list: # 매수 완료 종목이면 더 이상 안 사도록 함수 종료
            #printlog('code:', code, 'in', bought_list)
            return False

        time_now = datetime.now()
        current_price = get_current_days_candles(market)
        ask_price, bid_price = get_current_orderbook(market)
        target_price = get_target_price_min(market, 1)    # 매수 목표가
        ma60_price = get_movingavrg_min(market, 10, 60)   # 60 min 이동평균가
        ma240_price = get_movingavrg_min(market, 10, 240) # 240 min 이동평균가
        buy_qty = 0        # 매수할 수량 초기화
        if ask_price > 0:  # 매수호가가 존재하면   
            buy_qty = buy_amount // ask_price  
    except Exception as ex:
        dbgout('buy_coin(' + str(market) + ') -> exception! ' + str(ex))
        return None   

if __name__ == '__main__':
    try :
        symbol_list = [
             'KRW-BTT', 'KRW-MVL', 'KRW-ANKR', 'KRW-DKA',
             'KRW-TT' , 'KRW-MBL'
                      ]      # 이미 구매한 종목들
        bought_list = []     # 매수 완료된 종목 리스트
        target_buy_count = len(get_market_all()) # 매수할 종목 수
        buy_percent = 0.25   # 종목 당 전체 가용 금액에서 매수할 비율
        #stocks = get_stock_balance('ALL')      # 보유한 모든 종목 조회
        total_cash = int(get_current_cash())   # 100% 증거금 주문 가능 금액 조회
        buy_amount = total_cash * buy_percent  # 종목별 주문 금액 계산
        printlog('전체 마켓 수 : ', target_buy_count)
        printlog('100% 증거금 주문 가능 금액 : ', total_cash)
        printlog('종목별 주문 비율 : ', buy_percent)
        printlog('종목별 주문 금액 : ', buy_amount)
        printlog('시작 시간 : ', datetime.now().strftime('%m/%d %H:%M:%S'))
        soldout = False
        send_cnt = 0

        get_stock_balance('KRW-BTT')

    except Exception as ex:
        dbgout('`main -> exception! ' + str(ex) + '`')