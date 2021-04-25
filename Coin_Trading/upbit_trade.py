import pyupbit
import os
from slacker import Slacker

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

upbit = Upbit(access_key, secret_key)

print (upbit.get_balance("KRW-XRP"))
print (upbit.get_balance("KRW"))