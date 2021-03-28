import os
import sys
import jwt
import uuid
import hashlib
from urllib.parse import urlencode

import requests

from slacker import Slacker
import time, calendar

from coin_util import *
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from logger import logger



dirname = os.path.dirname(__file__)

# if os.name == 'nt' : # Windows OS
#     with open('.\\file\\upbit_aces_key.txt', 'r') as file:
#         access_key = file.read().rstrip('\n')
#     with open('.\\file\\upbit_sec_key.txt', 'r') as file:
#         secret_key = file.read().rstrip('\n')
# else : # Others
#     with open('./file/upbit_aces_key.txt', 'r') as file:
#         access_key = file.read().rstrip('\n')
#     with open('./file/upbit_sec_key.txt', 'r') as file:
#         secret_key = file.read().rstrip('\n')

with open(os.path.join(dirname, '../file/upbit_aces_key.txt'), 'r') as file:
        access_key = file.read().rstrip('\n')
with open(os.path.join(dirname, '../file/upbit_sec_key.txt'), 'r') as file:
        secret_key = file.read().rstrip('\n')

# slack_key 가져오기
with open(os.path.join(dirname, '../file/slack_key.txt'), 'r') as file:
    slack_key = file.read().rstrip('\n')
    slack = Slacker(slack_key)

server_url = 'https://api.upbit.com'

payload = {
    'access_key': access_key,
    'nonce': str(uuid.uuid4()),
}

jwt_token = jwt.encode(payload, secret_key)
authorize_token = 'Bearer {}'.format(jwt_token)
headers = {"Authorization": authorize_token}

res = requests.get(server_url + "/v1/accounts", headers=headers)

print(res.json())
