import aiosqlite

DB_NAME = 'vpn_bot.db'


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # Таблица пользователей
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица ключей
        await db.execute("""
            CREATE TABLE IF NOT EXISTS amneziawg_vpn_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_text TEXT UNIQUE,
                key_type TEXT,
                is_used INTEGER DEFAULT 0,
                user_id INTEGER DEFAULT NULL,
                assigned_at TEXT DEFAULT NULL,
                FOREIGN KEY (user_id) REFERENCES users (telegram_id)
            )
        """)
        await db.commit()
