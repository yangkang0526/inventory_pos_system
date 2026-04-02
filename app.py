from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from database import Database
import uuid
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'
db = Database()

@app.route('/')
def index():
    stats = db.get_dashboard_stats()
    low_stock = db.get_low_stock_products()
    return render_template('index.html', stats=stats, low_stock=low_stock)

@app.route('/inventory')
def inventory():
    products = db.get_all_products()
    return render_template('inventory.html', products=products)

@app.route('/api/products', methods=['GET'])
def get_products():
    products = db.get_all_products()
    return jsonify([{
        'id': p[0],
        'code': p[1],
        'name': p[2],
        'category': p[3],
        'price': p[4],
        'cost': p[5],
        'quantity': p[6],
        'min_quantity': p[7],
        'unit': p[8]
    } for p in products])

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    product_id = db.add_product(
        data['code'],
        data['name'],
        data['category'],
        float(data['price']),
        float(data['cost']),
        int(data['quantity']),
        int(data['min_quantity']),
        data['unit']
    )
    return jsonify({'success': True, 'id': product_id})

@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.json
    db.update_product(
        product_id,
        data['code'],
        data['name'],
        data['category'],
        float(data['price']),
        float(data['cost']),
        int(data['min_quantity']),
        data['unit']
    )
    return jsonify({'success': True})

@app.route('/api/stock/in', methods=['POST'])
def stock_in():
    data = request.json
    db.add_stock_in(
        data['product_id'],
        int(data['quantity']),
        float(data.get('cost_price', 0)),
        data.get('supplier', ''),
        data.get('remark', '')
    )
    return jsonify({'success': True})

@app.route('/api/stock/out', methods=['POST'])
def stock_out():
    data = request.json
    db.add_stock_out(
        data['product_id'],
        int(data['quantity']),
        data.get('reason', ''),
        data.get('remark', '')
    )
    return jsonify({'success': True})

@app.route('/pos')
def pos():
    products = db.get_all_products()
    return render_template('pos.html', products=products)

@app.route('/api/sale', methods=['POST'])
def add_sale():
    data = request.json
    order_no = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4]}"
    
    # 检查库存
    product = db.get_product_by_id(data['product_id'])
    if product[6] < data['quantity']:
        return jsonify({'success': False, 'error': '库存不足'})
    
    db.add_sale(
        order_no,
        data['product_id'],
        data['quantity'],
        float(data['price']),
        float(data['total']),
        data.get('payment_method', '现金'),
        data.get('customer_name', '散客'),
        data.get('remark', '')
    )
    return jsonify({'success': True, 'order_no': order_no})

@app.route('/reports')
def reports():
    return render_template('reports.html')

@app.route('/api/reports/sales', methods=['GET'])
def get_sales_report():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    sales = db.get_sales_report(start_date, end_date)
    return jsonify([{
        'id': s[0],
        'order_no': s[1],
        'product_id': s[2],
        'quantity': s[3],
        'price': s[4],
        'total': s[5],
        'payment_method': s[6],
        'customer_name': s[7],
        'remark': s[8],
        'created_at': s[9],
        'product_name': s[11],
        'product_code': s[10]
    } for s in sales])

@app.route('/api/reports/stock-in', methods=['GET'])
def get_stock_in_report():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    stock_in = db.get_stock_in_report(start_date, end_date)
    return jsonify([{
        'id': s[0],
        'product_id': s[1],
        'quantity': s[2],
        'cost_price': s[3],
        'supplier': s[4],
        'remark': s[5],
        'created_at': s[6],
        'product_name': s[8],
        'product_code': s[7]
    } for s in stock_in])

@app.route('/api/low-stock', methods=['GET'])
def get_low_stock():
    products = db.get_low_stock_products()
    return jsonify([{
        'id': p[0],
        'code': p[1],
        'name': p[2],
        'quantity': p[6],
        'min_quantity': p[7]
    } for p in products])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
