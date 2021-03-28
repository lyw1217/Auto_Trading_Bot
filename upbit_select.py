import os
import jwt
import uuid
import hashlib
from urllib.parse import urlencode

import requests

with open('./file/upbit_aces_key.txt', 'r') as file:
    access_key = file.read().rstrip('\n')
with open('./file/upbit_sec_key.txt', 'r') as file:
    secret_key = file.read().rstrip('\n')

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
