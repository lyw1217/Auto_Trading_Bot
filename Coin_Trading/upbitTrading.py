import pyupbit
import os
from slacker import Slacker
import time
from datetime import datetime
import requests
import multiprocessing
from CoinTradeUtil import write_ws, write_wb
#from logger import logger

def dbout(message, *args):
    """인자로 받은 문자열을 파이썬 셸과 슬랙으로 동시에 출력한다."""
    tmp_msg = message
    for text in args:
        tmp_msg += str(text)
    strbuf = datetime.now().strftime('[%m/%d %H:%M:%S] ') + tmp_msg
    print(strbuf)
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

def get_slope_min(ticker, ma_old, min):
    """ 이전 값과 비교, 새로운 조회값이 더 크면 양수 """
    ma_new = get_ma_min(ticker, min)

    if (ma_old - ma_new) < 0 :
        return 1
    else :
        return (-1)

def get_min_order_amount(ticker):
    price = get_current_price(ticker)

    return (5000 / price)



lock = multiprocessing.Lock()

def trade_start(ticker) :
    ''' 
    ticker 거래 시작, worker 함수
    example > ticker = "KRW-ETH"
    '''

    lock.acquire()
    time.sleep(len(ticker_list)-1)        # 1초에 1개의 ticker만 시작되게끔 Lock, sleep
    lock.release()

    while True :
        ma15_old    = get_ma_min(ticker, 15)
        ma50_old    = get_ma_min(ticker, 50)
        min_amount  = get_min_order_amount(ticker)
        if ma15_old == None or ma50_old == None or min_amount == None :
            time.sleep(1)
            continue
        break

    amount = upbit.get_balance(ticker[4:])
    if amount == None :
        amount = 0

    ticker_amount = 0   # 원 단위 ticker 별 관리 금액
    ma15_slope    = 0
    buy_flag      = False
    sell_flag     = False
    send_cnt      = 0
    if amount > min_amount :
        buy_state = True
        ticker_amount = amount * get_current_price(ticker)   
    else:
        buy_state = False
        # 다른 ticker 들과 비슷한 수준의 금액으로 amount 맞추기
        total_amount = int(upbit.get_balance("KRW"))

        for t in ticker_list :
            total_amount = total_amount + int(float(upbit.get_balance(t[4:])) * float(get_current_price(t)))
        
        ticker_amount = int(total_amount / len(ticker_list))    # 전체 ticker들 자산의 1/n

    dbout(str(ticker) + "> autotrade start, ticker_amount = " + ticker_amount)

    # 자동매매 시작
    while True:
        try:
            time.sleep(len(ticker_list))    # 1초에 1개의 ticker만 시작되게끔 sleep

            ma15_slope  = get_slope_min(ticker, ma15_old, 15)
            ma15_new    = get_ma_min(ticker, 15)
            ma50_new    = get_ma_min(ticker, 50)

            if ma15_slope == None or ma15_new == None or ma50_new == None :
                continue

            t_now = datetime.now()
            if (t_now.minute % 6 == 0) and (send_cnt == 0) :
                if (t_now.minute == 36) :
                    amount      = upbit.get_balance(ticker[4:])
                    krw         = upbit.get_balance("KRW")
                    if krw < 5000 :
                        dbout("%s > %s : %.0f, ma_slope : %s\nma15_old : %.0f , ma15_new : %.0f\nma50_old : %.0f , ma50_new : %.0f"%(ticker, ticker, (float(amount) * get_current_price(ticker)), ma15_slope, float(ma15_old), float(ma15_new), float(ma50_old), float(ma50_new)))
                    else :
                        dbout("%s > krw : %.0f, ma_slope : %s\nma15_old : %.0f , ma15_new : %.0f\nma50_old : %.0f , ma50_new : %.0f"%(ticker, float(krw), ma15_slope, float(ma15_old), float(ma15_new), float(ma50_old), float(ma50_new)))
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
                if krw == None or krw < 5000 :
                    dbout( ticker + " > Match BUY condition, but krw is " + krw)
                    continue
                if krw >= ticker_amount and krw > 5000 :
                    upbit.buy_market_order(ticker, ticker_amount*0.9995) # 저장된 매도 금액 만큼 매수, 수수료 고려 0.9995 (99.95%)    
                else :
                    dbout("%s > Warning! BUY. krw is '%.0f', but ticker_amount = '%d'"%(ticker, float(krw*0.9995), ticker_amount))
                    upbit.buy_market_order(ticker, krw*0.9995)           # 남은 예수금 만큼 매수, 수수료 고려 0.9995 (99.95%)
                
                # 엑셀 출력
                write_ws.append( [datetime.now().strftime('%m/%d %H:%M:%S'), ticker, "BUY", krw*0.9995, ma15_new, ma50_new] )
                write_wb.save('./Coin_Trading_Bot.xlsx')
                buy_state   = True
                buy_flag    = False
                dbout("%s > BUY!! 매수금액 : %s"%(ticker, str(krw*0.9995)))

            elif (sell_flag == True) and (buy_state == True):
                amount     = upbit.get_balance(ticker[4:])
                min_amount = get_min_order_amount(ticker)
                if amount == None or min_amount == None :
                    dbout( ticker + " > Match SELL condition, but amount is " + krw)
                    continue
                if amount > min_amount :
                    upbit.sell_market_order(ticker, amount*0.9995)             # 보유 수량 전부 매도
                    buy_state   = False
                    sell_flag   = False
                    time.sleep(10)  # 매도 금액 반영될 때까지 sleep
                    krw = upbit.get_balance("KRW")
                    if krw == None or krw < 5000 :
                        time.sleep(1)
                        krw = upbit.get_balance("KRW")
                    dbout("%s > SELL!! 잔고 : %.0f" % (ticker, float(krw)))
                    ticker_amount = krw     # 매도 금액 저장
                    # 엑셀 출력
                    write_ws.append( [datetime.now().strftime('%m/%d %H:%M:%S'), ticker, "SELL", krw, ma15_new, ma50_new] )
                    write_wb.save('./Coin_Trading_Bot.xlsx')
                else :
                    dbout("%s > Failed SELL. %s is '%.0f'"%(ticker, ticker, float(amount*0.9995)))

        except Exception as e:
            dbout(ticker + " > Err! ", e)
            time.sleep(1)

    return

ticker_list = ['KRW-ETH', 'KRW-XRP']
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
    slack     = Slacker(slack_key)

# 로그인
global upbit
upbit = pyupbit.Upbit(access_key, secret_key)

if __name__ == '__main__' :
    
    # 시작 메세지
    dbout("A U T O T R A D E !")

    t_str = ""
    for t in ticker_list :
        t_str = t_str + t + " "
    dbout("tickers = " + t_str)

    multiprocessing.freeze_support()
    pool = multiprocessing.Pool(processes=len(ticker_list))
    results = pool.map(trade_start, ticker_list)
    pool.close()
    pool.join()
