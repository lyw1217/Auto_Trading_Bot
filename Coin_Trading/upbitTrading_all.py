import pyupbit
import os
from slacker import Slacker
import time
import datetime
import threading
from CoinTradeUtil import write_ws, write_wb
#from logger import logger

def dbout(message, *args):
    """인자로 받은 문자열을 파이썬 셸과 슬랙으로 동시에 출력한다."""
    tmp_msg = message
    for text in args:
        tmp_msg += str(text)
    strbuf = datetime.datetime.now().strftime('[%m/%d %H:%M:%S] ') + tmp_msg
    print(strbuf)
    slack.chat.post_message('#python-trading-bot', strbuf)

# not used
def printlog(message, *args):
    """인자로 받은 문자열을 파이썬 셸에 출력한다."""
    tmp_msg = message
    for text in args:
        tmp_msg += str(text)
    ##logger.info(tmp_msg)
    #print(datetime.now().strftime('[%m/%d %H:%M:%S]'), message, *args)
# not used

# not used
def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price
# not used

def get_start_time(ticker):
    """시작 시간 조회"""
    # 일봉 조회 시 09시 기준으로 조회
    df = pyupbit.get_ohlcv(ticker, interval="minute30", count=1)
    start_time = df.index[0]
    return start_time

# not used
def get_ma_day(ticker, day):
    """day일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=int(day))
    ma = df['close'].rolling(int(day)).mean().iloc[-1]
    return ma
# not used

def get_ma_min(ticker, min):
    """min분 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute30", count=int(min))
    while True :
        if df is None :
            time.sleep(0.7)
            df = pyupbit.get_ohlcv(ticker, interval="minute30", count=int(min))
        else :
            break
    ma5 = df['close'].rolling(int(min)).mean().iloc[-1]
    return ma5

def get_balance(ticker):
    """잔고 조회"""
    balances, limits = upbit.get_balances()
    wait_limit(limits)  
    while True :
        if balances is None :
            time.sleep(0.7)
            balances, limits = upbit.get_balances()
            wait_limit(limits)  
        else :
            break

    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    

def get_current_price(ticker):
    """현재가 조회"""
    orderbook = pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]
    while True :
        if orderbook is None :
            time.sleep(0.7)
            orderbook = pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]
        else :
            break
    return orderbook

def get_slope_min(ticker, ma_old, min):
    """ 이전 값과 비교, 새로운 조회값이 더 크면 양수 """
    ma_new = get_ma_min(ticker, min)

    if (ma_old - ma_new) < 0 :
        return 1
    else :
        return (-1)

def get_min_order_balance(ticker):
    price = get_current_price(ticker)

    return (5000 / price)

def wait_limit(_limits) :
    # limit 도달 시 대기
    if _limits.get("sec") <= 1 :
        print("limit sec!")
        time.sleep(1)
    elif _limits.get("min") <= 5 :
        d_old = datetime.datetime.now().minute
        print("limit min start!")
        while True :
            d_now = datetime.datetime.now().minute
            if d_old != d_now :
                break
            time.sleep(0.5)
        print("limit min end!")
        time.sleep(1)

def get_avail_tickers_cnt(money) :
    '''
    매수 가능한 ticker 의 개수 반환,
    1 ticker 당 money 원 기준
    '''
    _buy_cnt = 0

    total_balance, limits = upbit.get_balance("KRW", contain_req=True)
    wait_limit(limits)
    #print("tot : " + str(total_balance) + ", limit : " + str(limits))
    
    # 이미 매수한 ticker 금액 더하기
    for t in ticker_list :
        if t in exclude_tickers :
            continue

        balance, limits = upbit.get_balance(t[4:], contain_req=True)
        if balance > 0 :
            total_balance = total_balance + (balance * get_current_price(t))
            _buy_cnt = _buy_cnt + 1

        wait_limit(limits)        

    return int(total_balance / money), _buy_cnt


def get_ma(_ticker) :
    '''
    # return : ma15, ma50
    '''
    while True :
        _ma15    = get_ma_min(_ticker, 15)
        _ma50    = get_ma_min(_ticker, 50)
        time.sleep(0.05)
        if _ma15 is None or _ma50 is None :
            time.sleep(0.7)
            continue
        break
    
    return _ma15, _ma50

def set_order_flag(_ma, _ma15_new, _ma50_new) :
    _buy_flag  = False
    _sell_flag = False
    # if (ma15_old < ma50_old) and (ma15_new >= ma50_new)
    if  (_ma[t][0] < _ma[t][1]) and (_ma15_new >= _ma50_new) :
        _buy_flag  = True
    # elif (ma15_old > ma50_old) and (ma15_new <= ma50_new)
    elif (_ma[t][0] > _ma[t][1]) and (_ma15_new <= _ma50_new) :
        _sell_flag = True

    return _buy_flag, _sell_flag

##########################################


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

exclude_tickers = [ 'KRW-BTC', 'KRW-BTT', 'KRW-MED', 'KRW-LOOM' ]
#exclude_tickers = ['KRW-ETC', 'KRW-OMG', 'KRW-SNT', 'KRW-WAVES', 'KRW-XEM', 'KRW-QTUM', 'KRW-LSK', 'KRW-STEEM', 'KRW-XLM', 'KRW-ARDR', 'KRW-KMD', 'KRW-ARK', 'KRW-STORJ', 'KRW-GRS', 'KRW-REP', 'KRW-EMC2', 'KRW-ADA', 'KRW-SBD', 'KRW-POWR', 'KRW-BTG', 'KRW-ICX', 'KRW-EOS', 'KRW-TRX', 'KRW-SC', 'KRW-IGNIS', 'KRW-ONT', 'KRW-ZIL', 'KRW-POLY', 'KRW-ZRX', 'KRW-LOOM', 'KRW-BCH', 'KRW-ADX', 'KRW-BAT', 'KRW-IOST', 'KRW-DMT', 'KRW-RFR', 'KRW-CVC', 'KRW-IQ', 'KRW-IOTA', 'KRW-MFT', 'KRW-ONG', 'KRW-GAS', 'KRW-UPP', 'KRW-ELF', 'KRW-KNC', 'KRW-BSV', 'KRW-THETA', 'KRW-EDR', 'KRW-QKC', 'KRW-BTT', 'KRW-MOC', 'KRW-ENJ', 'KRW-TFUEL', 'KRW-MANA', 'KRW-ANKR', 'KRW-AERGO', 'KRW-ATOM', 'KRW-TT', 'KRW-CRE', 'KRW-SOLVE', 'KRW-MBL', 'KRW-TSHP', 'KRW-WAXP', 'KRW-HBAR', 'KRW-MED', 'KRW-MLK', 'KRW-STPT', 'KRW-ORBS', 'KRW-VET', 'KRW-CHZ', 'KRW-PXL', 'KRW-STMX', 'KRW-DKA', 'KRW-HIVE', 'KRW-KAVA', 'KRW-AHT', 'KRW-LINK', 'KRW-XTZ', 'KRW-BORA', 'KRW-JST', 'KRW-CRO', 'KRW-TON', 'KRW-SXP', 'KRW-LAMB', 'KRW-HUNT', 'KRW-MARO', 'KRW-PLA', 'KRW-DOT', 'KRW-SRM', 'KRW-MVL', 'KRW-PCI', 'KRW-STRAX', 'KRW-AQT', 'KRW-BCHA', 'KRW-GLM', 'KRW-QTCON', 'KRW-SSX', 'KRW-META', 'KRW-OBSR', 'KRW-FCT2', 'KRW-LBC', 'KRW-CBK', 'KRW-SAND', 'KRW-HUM', 'KRW-DOGE', 'KRW-STRK', 'KRW-PUNDIX', 'KRW-FLOW', 'KRW-DAWN', 'KRW-AXS', 'KRW-STX']

ticker_list = [ ]
limits      = { }
ticker_list, limits = pyupbit.get_tickers(fiat="KRW", limit_info=True)

buy_flag      = False
sell_flag     = False
f_loop        = 0
ma15_slope    = 0
avail_cnt     = 0
buy_cnt       = 0

if __name__ == '__main__' :

    # 시작 메세지
    dbout("Initialize...")

    avail_cnt, buy_cnt = get_avail_tickers_cnt(100000)

    # (dic) ma : { ticker : [ma15, ma50, buy_state] , ... }
    ma = {}
    for t in ticker_list :
        if t in exclude_tickers :
            continue
        ma15_old, ma50_old = get_ma(t)
        balance, limits = upbit.get_balance(t[4:], contain_req=True)
        wait_limit(limits)
        min_balance = get_min_order_balance(t)
        if balance > min_balance :
            ma[t] = [ma15_old, ma50_old, True]
        else :
            ma[t] = [ma15_old, ma50_old, False]
        
        #print(ma)

    dbout("A U T O T R A D E !")

    while True :
        try :
            now = datetime.datetime.now()
            start_time = get_start_time("KRW-BTC")
            end_time = start_time + datetime.timedelta(minutes=30)

            #print("start_time : " + str(start_time))
            #print("end_time : " + str(end_time))

            if (start_time < now < end_time - datetime.timedelta(seconds=30)) and (f_loop == 0):
                print("")
                krw = upbit.get_balance("KRW")
                dbout("seek start, krw = [%.0f]"%(float(krw)))
                for t in ticker_list :
                    if t in exclude_tickers :
                        continue
                    print("")
                    print("TICKER : " + t)
                    print("avail_cnt = " + str(avail_cnt) + " buy_cnt : " + str(buy_cnt))

                    ma15_new, ma50_new = get_ma(t)
                    if (ma[t][0] - ma15_new) < 0 :
                        ma15_slope = 1
                    else :
                        ma15_slope = (-1)

                    print("ma15_old = %.1f"%(float(ma[t][0])) + " ma50_old = %.1f"%(float(ma[t][1])))
                    print("ma15_new = %.1f"%(float(ma15_new)) + " ma50_new = %.1f"%(float(ma50_new)) + " ma15_slope = " + str(ma15_slope))
                    
                    buy_flag, sell_flag = set_order_flag(ma, ma15_new, ma50_new)

                    print("buy_flag = " + str(buy_flag) + " sell_flag = " + str(sell_flag))

                    # 기울기 양수, ma15의 상승으로 인해 ma50과 교차 시, 최대 가능 ticker수보다 구매 ticker 수가 더 작을 때
                    if (ma15_slope > 0) and (buy_flag == True) and (ma[t][2] == False) and (avail_cnt > buy_cnt) :
                        krw, limits = upbit.get_balance("KRW", contain_req=True)
                        wait_limit(limits)
                        if krw is None or krw < 5000 :
                            dbout( t + " > Match BUY condition, but krw is " + str(krw))
                            continue
                        if krw >= 100000 and krw > 5000 :
                            # 저장된 매도 금액 만큼 매수, 수수료 고려 0.9995 (99.95%)
                            ans = upbit.buy_market_order(t, 100000*0.9995, contain_req=True)
                            limits = ans[1]
                        else :
                            dbout("%s > Warning! BUY. krw is '%.0f', but ticker_balance = '%d'"%(t, float(krw*0.9995), 100000))
                            # 남은 예수금 만큼 매수, 수수료 고려 0.9995 (99.95%)
                            ans = upbit.buy_market_order(t, krw*0.9995, contain_req=True)
                            limits = ans[1]
                        wait_limit(limits)
                        
                        # 엑셀 출력
                        write_ws.append( [datetime.datetime.now().strftime('%m/%d %H:%M:%S'), t, "BUY", krw*0.9995, ma15_new, ma50_new] )
                        write_wb.save('./Coin_Trading_Bot.xlsx')
                        ma[t][2]    = True
                        buy_flag    = False
                        buy_cnt     = buy_cnt + 1
                        dbout("%s > BUY!! 매수금액 : %s"%(t, str(krw*0.9995)))

                    elif (sell_flag == True) and (ma[t][2] == True):
                        balance, limits = upbit.get_balance(t[4:], contain_req=True)
                        wait_limit(limits)
                        min_balance = get_min_order_balance(t)
                        if balance is None or min_balance is None :
                            dbout( t + " > Match SELL condition, but balance is " + balance)
                            continue
                        if balance > min_balance :
                            # 보유 수량 전부 매도
                            ans = upbit.sell_market_order(t, balance*0.9995)
                            limits = ans[1]
                            wait_limit(limits)
                            ma[t][2]    = False
                            sell_flag   = False
                            time.sleep(10)  # 매도 금액 반영될 때까지 sleep
                            krw, limits = upbit.get_balance("KRW", contain_req=True)
                            wait_limit(limits)
                            if krw is None or krw < 5000 :
                                time.sleep(0.7)
                                krw, limits = upbit.get_balance("KRW", contain_req=True)
                                wait_limit(limits)
                            
                            # 엑셀 출력
                            write_ws.append( [datetime.datetime.now().strftime('%m/%d %H:%M:%S'), t, "SELL", krw, ma15_new, ma50_new] )
                            write_wb.save('./Coin_Trading_Bot.xlsx')
                            buy_cnt = buy_cnt - 1
                            dbout("%s > SELL!! 잔고 : %.0f" % (t, float(krw)))
                        else :
                            dbout("%s > Failed SELL. %s is '%.0f'"%(t, t, float(balance*0.9995)))

                    ma[t][0] = ma15_new
                    ma[t][1] = ma50_new

                    time.sleep(1)
                f_loop = 1
            else : 
                if now > end_time - datetime.timedelta(seconds=30) :
                    f_loop = 0
            
            time.sleep(1) 
                
        except Exception as e:
            dbout("Err! " + e)
            time.sleep(1)