import sqlite3
import json
from datetime import datetime

class Database:
    def __init__(self, db_name='orders.db'):
        self.db_name = db_name
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                phone TEXT,
                business_name TEXT,
                selected_tier TEXT,
                selected_addons TEXT,
                total_price INTEGER,
                special_requests TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_order(self, order_data):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO orders (
                user_id, username, first_name, last_name, phone, 
                business_name, selected_tier, selected_addons, 
                total_price, special_requests
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            order_data['user_id'],
            order_data['username'],
            order_data['first_name'],
            order_data['last_name'],
            order_data['phone'],
            order_data['business_name'],
            order_data['selected_tier'],
            json.dumps(order_data['selected_addons']),
            order_data['total_price'],
            order_data['special_requests']
        ))
        
        order_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return order_id
    
    def get_orders(self, status='pending'):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM orders WHERE status = ? ORDER BY created_at DESC', (status,))
        orders = cursor.fetchall()
        
        conn.close()
        return orders