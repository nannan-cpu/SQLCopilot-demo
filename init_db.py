
import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "card_transactions.db"

states = ["NY", "CA", "TX", "WA", "FL", "IL", "NJ", "VA", "NV", "AZ"]
card_types = ["Platinum", "Gold", "Silver", "Freedom", "Basic"]
channels = ["Online", "Branch", "Mobile", "ATM", "POS"]
merchant_cats = ["Grocery", "Travel", "Dining", "Fuel", "Shopping", "Entertainment", "Utilities"]

def create_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Create transactions table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS card_transactions (
        transaction_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id      INTEGER,
        state           TEXT,
        card_type       TEXT,
        channel         TEXT,
        transaction_date TEXT,
        amount          REAL,
        is_fraud        INTEGER,
        merchant_cat    TEXT,
        product_version TEXT  -- for A/B Test comparisons
    );
    """)

    # Delete if old data exists
    cur.execute("DELETE FROM card_transactions;")

    # Generate 5000 synthetic rows
    today = datetime.today()
    rows = []
    for _ in range(5000):
        customer_id = random.randint(10000, 99999)
        state = random.choice(states)
        card = random.choice(card_types)
        channel = random.choice(channels)
        merchant = random.choice(merchant_cats)
        category = random.choice(merchant_cats)
        date = today - timedelta(days=random.randint(0, 365))
        amount = round(random.uniform(5, 5000), 2)
        is_fraud = 1 if random.random() < 0.03 else 0  # 3% fraud rate
        version = random.choice(["A", "B"])  # for A/B Test user branch comparison

        rows.append((
            customer_id, state, card, channel,
            date.strftime("%Y-%m-%d"), amount,
            is_fraud, category, version, "Grocery"
        ))

    cur.executemany("""
    INSERT INTO card_transactions (
        customer_id, state, card_type, channel,
        transaction_date, amount, is_fraud,
        merchant_cat, product_version, merchant_cat
    ) VALUES (?,?,?,?,?,?,?,?,?,?);
    """, rows)

    conn.commit()
    conn.close()
    print("✅ Synthetic JPM credit DB created! You're a step closer to analyst superpowers.")

if __name__ == "__main__":
    create_db()
# init_db.py
# Synthetic database generator for credit card analytics demo

import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "card_transactions.db"

states = ["NY", "CA", "TX", "WA", "FL", "IL", "NJ", "VA", "NV", "AZ"]
card_types = ["Platinum", "Gold", "Silver", "Freedom", "Basic"]
channels = ["Online", "Branch", "Mobile", "ATM", "POS"]
merchant_cats = ["Grocery", "Travel", "Dining", "Fuel", "Shopping", "Entertainment", "Utilities"]

def create_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 重建表结构
    cur.execute("DROP TABLE IF EXISTS card_transactions;")

    cur.execute("""
    CREATE TABLE card_transactions (
        transaction_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id       INTEGER,
        state             TEXT,
        card_type         TEXT,
        channel           TEXT,
        transaction_date  TEXT,
        amount            REAL,
        is_fraud          INTEGER,
        merchant_cat      TEXT,
        product_version   TEXT   -- A/B test version flag: 'A' or 'B'
    );
    """)

    today = datetime.today()
    rows = []
    for _ in range(5000):
        customer_id = random.randint(10000, 99999)
        state = random.choice(states)
        card_type = random.choice(card_types)
        channel = random.choice(channels)
        merchant_cat = random.choice(merchant_cats)
        days_ago = random.randint(0, 365)
        dt = today - timedelta(days=days_ago)
        transaction_date = dt.strftime("%Y-%m-%d")
        amount = round(random.uniform(5, 5000), 2)
        is_fraud = 1 if random.random() < 0.03 else 0  # ~3% fraud rate
        product_version = random.choice(["A", "B"])

        rows.append((
            customer_id, state, card_type, channel,
            transaction_date, amount, is_fraud,
            merchant_cat, product_version
        ))

    cur.executemany("""
    INSERT INTO card_transactions (
        customer_id, state, card_type, channel,
        transaction_date, amount, is_fraud,
        merchant_cat, product_version
    ) VALUES (?,?,?,?,?,?,?,?,?);
    """, rows)

    conn.commit()
    conn.close()
    print(f"✅ Created {len(rows)} synthetic transactions in {DB_PATH}")

if __name__ == "__main__":
    create_db()

