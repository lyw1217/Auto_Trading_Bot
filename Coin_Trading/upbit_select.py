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
with open(os.path.join(dirname, '../file/upbit_aces_key.txt'), 'r') as file:
        access_key = file.read().rstrip('\n')
# security key 가져오기
with open(os.path.join(dirname, '../file/upbit_sec_key.txt'), 'r') as file:
        secret_key = file.read().rstrip('\n')
# slack_key 가져오기
with open(os.path.join(dirname, '../file/slack_key.txt'), 'r') as file:
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
        return item['balance']
    except Exception as ex:
        dbgout("`get_current_cash() -> exception! " + str(ex) + "`")
        return None

def get_current_minute_candles(market, minute):
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
    
def get_ohlc(market, qty):
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
            print ( "timestamp = " + str(item[i]['timestamp']))
            index.append(datetime.fromtimestamp(int(item[i]['timestamp'])).strftime('%Y%m%d'))
            rows.append([item[i]['opening_price'], item[i]['high_price'],
                item[i]['low_price'], item[i]['prev_closing_price']]) 
        df = pd.DataFrame(rows, columns=columns, index=index) 
        print(item)
        return df
    except Exception as ex:
        dbgout("`get_ohlc() -> exception! " + str(ex) + "`")
        return None

def get_target_price(market):
    """매수 목표가를 반환한다."""
    try:
        time_now = datetime.now()
        str_today = time_now.strftime('%Y%m%d')
        ohlc = get_ohlc(market, 10)
        if str_today == str(ohlc.iloc[0].name):
            today_open = ohlc.iloc[0].open
            lastday = ohlc.iloc[1]
        else:
            lastday = ohlc.iloc[0]                                      
            today_open = lastday[3]
        lastday_high = lastday[1]
        lastday_low = lastday[2]
        target_price = today_open + (lastday_high - lastday_low) * 0.5 # 0.5 = 수익률
        print ("time_now.strftime('%Y%m%d') = " + str(time_now.strftime('%Y%m%d')))
        print ("today_open = " + str(today_open))
        print ("lastday_high = " + str(lastday_high))
        print ("lastday_low = " + str(lastday_low))
        return target_price
    except Exception as ex:
        dbgout("`get_target_price() -> exception! " + str(ex) + "`")
        return None

def get_day_movingaverage(market, day):
    ''' market의 day 만큼의 이동평균가격을 반환 '''
    try:
        time_now = datetime.now()
        str_today = time_now.strftime('%Y%m%d')
        ohlc = get_ohlc(market, 20)
        if str_today == str(ohlc.iloc[0].name):
            lastday = ohlc.iloc[1].name
        else:
            lastday = ohlc.iloc[0].name
        closes = ohlc['close'].sort_index()         
        ma = closes.rolling(window=day).mean()
        return ma.loc[lastday]
    except Exception as ex:
        dbgout('get_movingavrg(' + str(day) + ') -> exception! ' + str(ex))
        return None  

if __name__ == '__main__':
    try :
        print(get_ohlc("KRW-BTC", 3))
        print(get_day_movingaverage("KRW-BTC", 5))
        print(get_target_price("KRW-BTC"))
        print(get_current_days_candles("KRW-BTC"))
    except Exception as ex:
        dbgout('`main -> exception! ' + str(ex) + '`')