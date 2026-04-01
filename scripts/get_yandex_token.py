#!/usr/bin/env python3
"""
Один раз получить access_token и refresh_token для Yandex Direct / Wordstat.

1. Заполни в .env: YANDEX_CLIENT_ID, YANDEX_CLIENT_SECRET
2. Запусти: python3 scripts/get_yandex_token.py
3. Откроется браузер — войди в Яндекс, нажми «Разрешить»
4. Скопируй code из URL (параметр code=...) и вставь в консоль
5. Скрипт выведет access_token и refresh_token — добавь их в .env
"""
import os
import webbrowser
from pathlib import Path

root = Path(__file__).resolve().parent.parent
os.chdir(root)


def main():
    from dotenv import load_dotenv
    load_dotenv()
    client_id = os.getenv("YANDEX_CLIENT_ID", "").strip()
    client_secret = os.getenv("YANDEX_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        print("Добавь в .env: YANDEX_CLIENT_ID и YANDEX_CLIENT_SECRET (из настроек приложения Яндекс OAuth).")
        return
    # Ссылка авторизации: права на Direct + Wordstat
    redirect_uri = "https://oauth.yandex.ru/verification_code"
    scope = "direct:api"
    url = (
        "https://oauth.yandex.ru/authorize?"
        f"response_type=code&client_id={client_id}&redirect_uri={redirect_uri}"
        f"&scope={scope}&force_confirm=yes"
    )
    print("Открываю в браузере:", url)
    print("После входа и нажатия «Разрешить» тебя перенаправит на страницу с кодом.")
    webbrowser.open(url)
    code = input("\nВставь code из URL (параметр code=...): ").strip()
    if not code:
        print("Код не введён.")
        return
    import httpx
    r = httpx.post(
        "https://oauth.yandex.com/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    r.raise_for_status()
    data = r.json()
    access = data.get("access_token", "")
    refresh = data.get("refresh_token", "")
    print("\nДобавь в .env:")
    print(f"YANDEX_DIRECT_TOKEN={access}")
    print(f"YANDEX_WORDSTAT_TOKEN={access}")
    if refresh:
        print(f"YANDEX_REFRESH_TOKEN={refresh}")
    print("\n(access_token можно использовать сразу; refresh_token — для автообновления без повторного входа.)")


if __name__ == "__main__":
    main()
