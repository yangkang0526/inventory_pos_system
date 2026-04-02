import sqlite3
from datetime import datetime

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('inventory_pos.db', check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # 产品表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                category TEXT,
                price REAL NOT NULL,
                cost REAL,
                quantity INTEGER DEFAULT 0,
                min_quantity INTEGER DEFAULT 0,
                unit TEXT DEFAULT '个',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 入库记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_in (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                quantity INTEGER NOT NULL,
                cost_price REAL,
                supplier TEXT,
                remark TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')
        
        # 出库记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_out (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                quantity INTEGER NOT NULL,
                reason TEXT,
                remark TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')
        
        # 销售记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_no TEXT UNIQUE NOT NULL,
                product_id INTEGER,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                total REAL NOT NULL,
                payment_method TEXT,
                customer_name TEXT,
                remark TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')
        
        self.conn.commit()
        self.add_sample_data()
    
    def add_sample_data(self):
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM products")
        if cursor.fetchone()[0] == 0:
            sample_products = [
                ('P001', '笔记本电脑', '电子产品', 5999.00, 4500.00, 10, 5, '台'),
                ('P002', '鼠标', '电子产品', 99.00, 50.00, 50, 10, '个'),
                ('P003', '键盘', '电子产品', 299.00, 150.00, 30, 10, '个'),
                ('P004', '显示器', '电子产品', 1299.00, 900.00, 15, 5, '台'),
                ('P005', '矿泉水', '饮料', 2.00, 1.00, 100, 20, '瓶'),
                ('P006', '可乐', '饮料', 3.00, 1.50, 80, 15, '瓶'),
            ]
            
            cursor.executemany('''
                INSERT INTO products (code, name, category, price, cost, quantity, min_quantity, unit)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', sample_products)
            self.conn.commit()
    
    def get_all_products(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM products ORDER BY id")
        return cursor.fetchall()
    
    def get_product_by_id(self, product_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        return cursor.fetchone()
    
    def add_product(self, code, name, category, price, cost, quantity, min_quantity, unit):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO products (code, name, category, price, cost, quantity, min_quantity, unit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (code, name, category, price, cost, quantity, min_quantity, unit))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_stock(self, product_id, quantity_change):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE products SET quantity = quantity + ? WHERE id = ?", 
                      (quantity_change, product_id))
        self.conn.commit()
    
    def add_stock_in(self, product_id, quantity, cost_price, supplier, remark):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO stock_in (product_id, quantity, cost_price, supplier, remark)
            VALUES (?, ?, ?, ?, ?)
        ''', (product_id, quantity, cost_price, supplier, remark))
        self.update_stock(product_id, quantity)
        self.conn.commit()
        return cursor.lastrowid
    
    def add_stock_out(self, product_id, quantity, reason, remark):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO stock_out (product_id, quantity, reason, remark)
            VALUES (?, ?, ?, ?)
        ''', (product_id, quantity, reason, remark))
        self.update_stock(product_id, -quantity)
        self.conn.commit()
        return cursor.lastrowid
    
    def add_sale(self, order_no, product_id, quantity, price, total, payment_method, customer_name, remark):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO sales (order_no, product_id, quantity, price, total, payment_method, customer_name, remark)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (order_no, product_id, quantity, price, total, payment_method, customer_name, remark))
        self.update_stock(product_id, -quantity)
        self.conn.commit()
        return cursor.lastrowid
    
    def get_sales_report(self, start_date=None, end_date=None):
        cursor = self.conn.cursor()
        if start_date and end_date:
            cursor.execute('''
                SELECT s.*, p.name, p.code 
                FROM sales s 
                JOIN products p ON s.product_id = p.id 
                WHERE DATE(s.created_at) BETWEEN ? AND ?
                ORDER BY s.created_at DESC
            ''', (start_date, end_date))
        else:
            cursor.execute('''
                SELECT s.*, p.name, p.code 
                FROM sales s 
                JOIN products p ON s.product_id = p.id 
                ORDER BY s.created_at DESC
            ''')
        return cursor.fetchall()
    
    def get_stock_in_report(self, start_date=None, end_date=None):
        cursor = self.conn.cursor()
        if start_date and end_date:
            cursor.execute('''
                SELECT si.*, p.name, p.code 
                FROM stock_in si 
                JOIN products p ON si.product_id = p.id 
                WHERE DATE(si.created_at) BETWEEN ? AND ?
                ORDER BY si.created_at DESC
            ''', (start_date, end_date))
        else:
            cursor.execute('''
                SELECT si.*, p.name, p.code 
                FROM stock_in si 
                JOIN products p ON si.product_id = p.id 
                ORDER BY si.created_at DESC
            ''')
        return cursor.fetchall()
    
    def get_low_stock_products(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM products WHERE quantity <= min_quantity")
        return cursor.fetchall()
    
    def get_dashboard_stats(self):
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COALESCE(SUM(total), 0) FROM sales WHERE DATE(created_at) = DATE('now')")
        today_sales = cursor.fetchone()[0]
        
        cursor.execute("SELECT COALESCE(SUM(quantity), 0) FROM sales WHERE DATE(created_at) = DATE('now')")
        today_quantity = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM products")
        total_products = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM products WHERE quantity <= min_quantity")
        low_stock_count = cursor.fetchone()[0]
        
        return {
            'today_sales': today_sales,
            'today_quantity': today_quantity,
            'total_products': total_products,
            'low_stock_count': low_stock_count
        }
    
    def close(self):
        self.conn.close()
