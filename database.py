import sqlite3

class DatabaseManager:
    def __init__(self, db_name='saves.db'):
        self.conn = sqlite3.connect(db_name)
        self.c = self.conn.cursor()
        self.setup_tables()

    def setup_tables(self):
        self.c.execute('''CREATE TABLE IF NOT EXISTS saves
                         (score REAL)''')
        self.c.execute('''CREATE TABLE IF NOT EXISTS purchased_items
                         (id INTEGER PRIMARY KEY, effect TEXT)''')
        self.conn.commit()

    def get_total_saves(self):
        self.c.execute("SELECT SUM(score) FROM saves")
        result = self.c.fetchone()[0]
        return result if result is not None else 0

    def save_score(self, score):
        self.c.execute("INSERT INTO saves VALUES (?)", (score,))
        self.conn.commit()

    def load_purchased_items(self):
        self.c.execute("SELECT id FROM purchased_items")
        return [row[0] for row in self.c.fetchall()]

    def purchase_item(self, item_id, effect):
        self.c.execute("INSERT INTO purchased_items (id, effect) VALUES (?, ?)", (item_id, effect))
        self.conn.commit()

    def deduct_score(self, amount):
        remaining = amount
        while remaining > 0:
            self.c.execute("SELECT rowid, score FROM saves ORDER BY rowid LIMIT 1")
            record = self.c.fetchone()
            if not record:
                break
            rowid, score = record
            if score <= remaining:
                self.c.execute("DELETE FROM saves WHERE rowid = ?", (rowid,))
                remaining -= score
            else:
                self.c.execute("UPDATE saves SET score = score - ? WHERE rowid = ?", (remaining, rowid))
                remaining = 0
        self.conn.commit()

    def __del__(self):
        self.conn.close()