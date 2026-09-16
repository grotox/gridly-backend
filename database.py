import aiosqlite
import json
from pathlib import Path

DB_PATH = Path(__file__).parent / "gridly.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                username TEXT,
                created_at INTEGER
            );

            CREATE TABLE IF NOT EXISTS user_data (
                user_id INTEGER PRIMARY KEY,
                data TEXT NOT NULL,
                updated_at INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
        """)
        await db.commit()


async def upsert_user(user_id: int, first_name: str, username: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, first_name, username, created_at)
            VALUES (?, ?, ?, strftime('%s','now'))
            ON CONFLICT(user_id) DO UPDATE SET
                first_name=excluded.first_name,
                username=excluded.username
        """, (user_id, first_name, username))
        await db.commit()


async def save_user_data(user_id: int, data: dict):
    json_data = json.dumps(data, ensure_ascii=False)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO user_data (user_id, data, updated_at)
            VALUES (?, ?, strftime('%s','now'))
            ON CONFLICT(user_id) DO UPDATE SET
                data=excluded.data,
                updated_at=strftime('%s','now')
        """, (user_id, json_data))
        await db.commit()


async def load_user_data(user_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT data FROM user_data WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return json.loads(row[0])
    return {"tables": [], "rows": {}, "nextTableId": 1, "nextRowId": 1}