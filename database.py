import sqlite3
import datetime

def init_db():
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            tier TEXT,
            customer_info TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def save_order(user_id, username, tier, customer_info, status='pending'):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO orders (user_id, username, tier, customer_info, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, username, tier, customer_info, status))
    
    order_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return order_id

def get_order(order_id):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    
    c.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
    order = c.fetchone()
    
    conn.close()
    return order

def get_user_orders(user_id):
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    
    c.execute('SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
    orders = c.fetchall()
    
    conn.close()
    return orders