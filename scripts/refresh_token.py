import httpx, os
from dotenv import load_dotenv
load_dotenv()

r = httpx.post('https://oauth.yandex.com/token', data={
    'grant_type': 'refresh_token',
    'refresh_token': os.getenv('YANDEX_REFRESH_TOKEN'),
    'client_id': os.getenv('YANDEX_CLIENT_ID'),
    'client_secret': os.getenv('YANDEX_CLIENT_SECRET'),
})
data = r.json()
if 'access_token' in data:
    print("Новый токен:")
    print(f"YANDEX_DIRECT_TOKEN={data['access_token']}")
    print(f"YANDEX_WORDSTAT_TOKEN={data['access_token']}")
    if 'refresh_token' in data:
        print(f"YANDEX_REFRESH_TOKEN={data['refresh_token']}")
else:
    print("Ошибка:", data)
