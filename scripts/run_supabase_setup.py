#!/usr/bin/env python3
"""
Run supabase_setup.sql against Supabase Postgres.
Requires DATABASE_URL in .env (Supabase Dashboard → Connect → Connection string URI).
"""
import os
import sys
from pathlib import Path

# project root
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
os.chdir(root)

def main():
    from dotenv import load_dotenv
    load_dotenv()
    url = os.getenv("DATABASE_URL")
    if not url or url.startswith("your-") or "your-project" in url:
        print(
            "DATABASE_URL не задан. Добавь в .env строку подключения из Supabase:\n"
            "Dashboard → твой проект → Connect → Connection string (URI) → скопируй и вставь как DATABASE_URL=..."
        )
        sys.exit(1)

    try:
        import psycopg2
    except ImportError:
        print("Установи: pip install psycopg2-binary")
        sys.exit(1)

    sql_file = root / "supabase_setup.sql"
    if not sql_file.exists():
        print(f"Файл не найден: {sql_file}")
        sys.exit(1)
    sql = sql_file.read_text(encoding="utf-8")

    print("Подключение к Supabase Postgres...")
    try:
        conn = psycopg2.connect(url)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.close()
        print("supabase_setup.sql выполнен успешно.")
    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
