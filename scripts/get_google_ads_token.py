"""
Google Ads OAuth2 Token получение.

Запуск:
    cd "PPC Master Tool"
    source .venv/bin/activate
    python scripts/get_google_ads_token.py

Что нужно подготовить заранее:
1. Google Cloud Console (console.cloud.google.com):
   - Создать проект (или использовать существующий)
   - APIs & Services → Enable API → включить "Google Ads API"
   - APIs & Services → Credentials → Create Credentials → OAuth client ID
   - Тип приложения: Desktop app
   - Скачать JSON или скопировать Client ID и Client Secret

2. Google Ads аккаунт:
   - Войти в ads.google.com
   - Инструменты → Настройки → API центр
   - Запросить Developer Token (если нет)
   - Скопировать Customer ID (формат: 123-456-7890)

После получения refresh_token добавить в .env:
    GOOGLE_ADS_CLIENT_ID=...
    GOOGLE_ADS_CLIENT_SECRET=...
    GOOGLE_ADS_DEVELOPER_TOKEN=...
    GOOGLE_ADS_REFRESH_TOKEN=...
    GOOGLE_ADS_CUSTOMER_ID=1234567890   # без дефисов
"""

import os
import sys
import webbrowser
from urllib.parse import urlencode, urlparse, parse_qs

try:
    import httpx
except ImportError:
    print("ERROR: httpx не установлен. Запустите: pip install httpx")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ─────────────────────────────────────────────────────────────
# Конфигурация
# ─────────────────────────────────────────────────────────────

CLIENT_ID     = os.getenv("GOOGLE_ADS_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("GOOGLE_ADS_CLIENT_SECRET", "")

REDIRECT_URI  = "urn:ietf:wg:oauth:2.0:oob"   # для Desktop app
SCOPE         = "https://www.googleapis.com/auth/adwords"
AUTH_URL      = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URL     = "https://oauth2.googleapis.com/token"

# ─────────────────────────────────────────────────────────────
# Шаг 1: Ввод credentials если не в .env
# ─────────────────────────────────────────────────────────────

print("=" * 60)
print("Google Ads OAuth2 — получение refresh_token")
print("=" * 60)

if not CLIENT_ID:
    CLIENT_ID = input("\nВведите GOOGLE_ADS_CLIENT_ID: ").strip()
if not CLIENT_SECRET:
    CLIENT_SECRET = input("Введите GOOGLE_ADS_CLIENT_SECRET: ").strip()

if not CLIENT_ID or not CLIENT_SECRET:
    print("\nERROR: CLIENT_ID и CLIENT_SECRET обязательны.")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────
# Шаг 2: Открыть браузер для авторизации
# ─────────────────────────────────────────────────────────────

params = {
    "client_id":     CLIENT_ID,
    "redirect_uri":  REDIRECT_URI,
    "response_type": "code",
    "scope":         SCOPE,
    "access_type":   "offline",
    "prompt":        "consent",   # обязательно для получения refresh_token
}

auth_url = f"{AUTH_URL}?{urlencode(params)}"

print(f"\n{'─'*60}")
print("Открываю браузер для авторизации Google...")
print(f"{'─'*60}")
print(f"\nURL: {auth_url}\n")

try:
    webbrowser.open(auth_url)
except Exception:
    print("Не удалось открыть браузер автоматически.")
    print("Скопируйте URL выше и откройте вручную.")

# ─────────────────────────────────────────────────────────────
# Шаг 3: Получить код от пользователя
# ─────────────────────────────────────────────────────────────

print("\nПосле авторизации Google покажет код.")
print("Скопируйте его и вставьте ниже:\n")
auth_code = input("Введите код авторизации: ").strip()

if not auth_code:
    print("ERROR: Код не введён.")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────
# Шаг 4: Обменять код на токены
# ─────────────────────────────────────────────────────────────

print("\nОбмениваю код на токены...")

r = httpx.post(TOKEN_URL, data={
    "code":          auth_code,
    "client_id":     CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "redirect_uri":  REDIRECT_URI,
    "grant_type":    "authorization_code",
}, timeout=15)

data = r.json()

if "error" in data:
    print(f"\nERROR: {data['error']}: {data.get('error_description', '')}")
    sys.exit(1)

refresh_token = data.get("refresh_token", "")
access_token  = data.get("access_token", "")

if not refresh_token:
    print("\nERROR: refresh_token не получен. Убедитесь что в URL был параметр prompt=consent.")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────
# Шаг 5: Вывод результата
# ─────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("УСПЕХ! Добавьте в .env файл:")
print("=" * 60)
print(f"\nGOOGLE_ADS_CLIENT_ID={CLIENT_ID}")
print(f"GOOGLE_ADS_CLIENT_SECRET={CLIENT_SECRET}")
print(f"GOOGLE_ADS_REFRESH_TOKEN={refresh_token}")
print("\n# Developer Token — скопируйте из Google Ads → Инструменты → API центр:")
print("GOOGLE_ADS_DEVELOPER_TOKEN=")
print("\n# Customer ID — без дефисов (123-456-7890 → 1234567890):")
print("GOOGLE_ADS_CUSTOMER_ID=")
print("\n" + "=" * 60)

# Проверка: попробовать получить список аккаунтов
dev_token = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN", "")
if dev_token:
    print("\nПроверяю доступ к Google Ads API...")
    test = httpx.get(
        "https://googleads.googleapis.com/v17/customers:listAccessibleCustomers",
        headers={
            "Authorization": f"Bearer {access_token}",
            "developer-token": dev_token,
        },
        timeout=10
    )
    if test.status_code == 200:
        customers = test.json().get("resourceNames", [])
        print(f"Доступные Customer ID: {len(customers)}")
        for c in customers:
            print(f"  {c.split('/')[-1]}")
    else:
        print(f"Ответ API: {test.status_code} — {test.text[:200]}")
