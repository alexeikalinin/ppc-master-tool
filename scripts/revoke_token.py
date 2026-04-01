import httpx, os
from dotenv import load_dotenv
load_dotenv()

token = os.getenv('YANDEX_WORDSTAT_TOKEN', '')
client_id = os.getenv('YANDEX_CLIENT_ID', '')
client_secret = os.getenv('YANDEX_CLIENT_SECRET', '')

r = httpx.post('https://oauth.yandex.com/revoke_token', data={
    'access_token': token,
    'client_id': client_id,
    'client_secret': client_secret,
})
print("HTTP", r.status_code)
print(r.text[:300])
