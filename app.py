from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Render 会自动设置 PORT 环境变量
PORT = int(os.environ.get('PORT', 5000))

# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'warehouse.db')


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 创建货物表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS goods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            location TEXT NOT NULL,
            quantity INTEGER DEFAULT 0,
            stock INTEGER DEFAULT 0,
            min_quantity INTEGER DEFAULT 0,
            description TEXT DEFAULT '',
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    # 创建历史记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goods_name TEXT NOT NULL,
            operation_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            notes TEXT DEFAULT '',
            timestamp TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()


# 初始化数据库
init_db()


def load_goods():
    """加载货物数据"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM goods ORDER BY id')
    rows = cursor.fetchall()
    conn.close()
    
    goods_list = []
    for row in rows:
        goods = {
            "id": row["id"],
            "_id": str(row["id"]),
            "name": row["name"],
            "price": row["price"],
            "location": row["location"],
            "quantity": row["quantity"],
            "stock": row["stock"],
            "min_quantity": row["min_quantity"],
            "description": row["description"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }
        goods_list.append(goods)
    
    return {"goods": goods_list}


def save_goods(data):
    """保存货物数据（已弃用，使用数据库操作）"""
    pass


def load_history():
    """加载操作历史"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM history ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    
    history_list = []
    for row in rows:
        record = {
            "id": row["id"],
            "_id": str(row["id"]),
            "goods_name": row["goods_name"],
            "operation_type": row["operation_type"],
            "quantity": row["quantity"],
            "notes": row["notes"],
            "timestamp": row["timestamp"],
            "time": row["timestamp"]
        }
        history_list.append(record)
    
    return {"history": history_list}


def save_history(data):
    """保存操作历史（已弃用，使用数据库操作）"""
    pass


def add_history_record(goods_name, operation_type, quantity, notes=""):
    """添加操作历史记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        'INSERT INTO history (goods_name, operation_type, quantity, notes, timestamp) VALUES (?, ?, ?, ?, ?)',
        (goods_name, operation_type, quantity, notes, timestamp)
    )
    
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        "id": record_id,
        "_id": str(record_id),
        "goods_name": goods_name,
        "operation_type": operation_type,
        "quantity": quantity,
        "notes": notes,
        "timestamp": timestamp,
        "time": timestamp
    }


# 主页
@app.route('/')
def index():
    return render_template('index.html')


# ============ 货物管理API ============

# 获取所有货物
@app.route('/api/goods', methods=['GET'])
def get_goods():
    data = load_goods()
    return jsonify(data)


# 根据 _id 获取货物（兼容小程序）
@app.route('/api/goods/by/_id/<string:goods_id>', methods=['GET'])
def get_goods_by_uuid(goods_id):
    data = load_goods()
    for goods in data["goods"]:
        if str(goods.get("id")) == goods_id or goods.get("_id") == goods_id:
            return jsonify(goods)
    return jsonify({"error": "货物不存在"}), 404


# 搜索货物
@app.route('/api/goods/search', methods=['GET'])
def search_goods():
    query = request.args.get('q', '').strip()
    data = load_goods()
    
    if not query:
        return jsonify(data)
    
    # 模糊搜索
    results = [g for g in data["goods"] if query.lower() in g["name"].lower()]
    return jsonify({"goods": results})


# 根据 _id 修改货物（兼容小程序）
@app.route('/api/goods/by/_id/<string:goods_id>', methods=['PUT'])
def update_goods_by_uuid(goods_id):
    goods_data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 先查询货物
    cursor.execute('SELECT * FROM goods WHERE id = ?', (goods_id,))
    goods = cursor.fetchone()
    
    if not goods:
        conn.close()
        return jsonify({"error": "货物不存在"}), 404
    
    # 构建更新语句
    update_fields = []
    params = []
    
    if "name" in goods_data:
        update_fields.append("name = ?")
        params.append(goods_data["name"])
    if "price" in goods_data:
        update_fields.append("price = ?")
        params.append(float(goods_data["price"]))
    if "location" in goods_data:
        update_fields.append("location = ?")
        params.append(goods_data["location"])
    if "quantity" in goods_data:
        update_fields.append("quantity = ?")
        update_fields.append("stock = ?")
        params.append(int(goods_data["quantity"]))
        params.append(int(goods_data["quantity"]))
    elif "stock" in goods_data:
        update_fields.append("stock = ?")
        update_fields.append("quantity = ?")
        params.append(int(goods_data["stock"]))
        params.append(int(goods_data["stock"]))
    if "min_quantity" in goods_data:
        update_fields.append("min_quantity = ?")
        params.append(int(goods_data["min_quantity"]))
    if "description" in goods_data:
        update_fields.append("description = ?")
        params.append(goods_data["description"])
    
    update_fields.append("updated_at = ?")
    params.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    params.append(goods_id)
    
    cursor.execute(f"UPDATE goods SET {', '.join(update_fields)} WHERE id = ?", params)
    conn.commit()
    
    # 获取更新后的数据
    cursor.execute('SELECT * FROM goods WHERE id = ?', (goods_id,))
    updated_goods = cursor.fetchone()
    conn.close()
    
    return jsonify({
        "success": True,
        "goods": {
            "id": updated_goods["id"],
            "_id": str(updated_goods["id"]),
            "name": updated_goods["name"],
            "price": updated_goods["price"],
            "location": updated_goods["location"],
            "quantity": updated_goods["quantity"],
            "stock": updated_goods["stock"],
            "min_quantity": updated_goods["min_quantity"],
            "description": updated_goods["description"],
            "created_at": updated_goods["created_at"],
            "updated_at": updated_goods["updated_at"]
        }
    })


# 根据 _id 删除货物（兼容小程序）
@app.route('/api/goods/by/_id/<string:goods_id>', methods=['DELETE'])
def delete_goods_by_uuid(goods_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM goods WHERE id = ?', (goods_id,))
    goods = cursor.fetchone()
    
    if not goods:
        conn.close()
        return jsonify({"error": "货物不存在"}), 404
    
    deleted_goods = {
        "id": goods["id"],
        "_id": str(goods["id"]),
        "name": goods["name"],
        "price": goods["price"],
        "location": goods["location"],
        "quantity": goods["quantity"],
        "stock": goods["stock"],
        "min_quantity": goods["min_quantity"],
        "description": goods["description"],
        "created_at": goods["created_at"],
        "updated_at": goods["updated_at"]
    }
    
    cursor.execute('DELETE FROM goods WHERE id = ?', (goods_id,))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "goods": deleted_goods})


# 添加货物
@app.route('/api/goods', methods=['POST'])
def add_goods():
    goods_data = request.get_json()
    
    # 验证必填字段
    required_fields = ['name', 'price', 'location']
    for field in required_fields:
        if field not in goods_data or not goods_data[field]:
            return jsonify({"error": f"缺少必填字段: {field}"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    quantity = int(goods_data.get("quantity", goods_data.get("stock", 0)))
    
    cursor.execute(
        '''INSERT INTO goods (name, price, location, quantity, stock, min_quantity, description, created_at, updated_at) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (
            goods_data["name"],
            float(goods_data["price"]),
            goods_data["location"],
            quantity,
            quantity,
            int(goods_data.get("min_quantity", 0)),
            goods_data.get("description", ""),
            timestamp,
            timestamp
        )
    )
    
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    new_goods = {
        "id": new_id,
        "_id": str(new_id),
        "name": goods_data["name"],
        "price": float(goods_data["price"]),
        "location": goods_data["location"],
        "quantity": quantity,
        "stock": quantity,
        "min_quantity": int(goods_data.get("min_quantity", 0)),
        "description": goods_data.get("description", ""),
        "created_at": timestamp,
        "updated_at": timestamp
    }
    
    return jsonify({"success": True, "goods": new_goods})


# 修改货物
@app.route('/api/goods/<int:goods_id>', methods=['PUT'])
def update_goods(goods_id):
    goods_data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 先查询货物
    cursor.execute('SELECT * FROM goods WHERE id = ?', (goods_id,))
    goods = cursor.fetchone()
    
    if not goods:
        conn.close()
        return jsonify({"error": "货物不存在"}), 404
    
    # 构建更新语句
    update_fields = []
    params = []
    
    if "name" in goods_data:
        update_fields.append("name = ?")
        params.append(goods_data["name"])
    if "price" in goods_data:
        update_fields.append("price = ?")
        params.append(float(goods_data["price"]))
    if "location" in goods_data:
        update_fields.append("location = ?")
        params.append(goods_data["location"])
    if "quantity" in goods_data:
        update_fields.append("quantity = ?")
        update_fields.append("stock = ?")
        params.append(int(goods_data["quantity"]))
        params.append(int(goods_data["quantity"]))
    elif "stock" in goods_data:
        update_fields.append("stock = ?")
        update_fields.append("quantity = ?")
        params.append(int(goods_data["stock"]))
        params.append(int(goods_data["stock"]))
    if "min_quantity" in goods_data:
        update_fields.append("min_quantity = ?")
        params.append(int(goods_data["min_quantity"]))
    if "description" in goods_data:
        update_fields.append("description = ?")
        params.append(goods_data["description"])
    
    update_fields.append("updated_at = ?")
    params.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    params.append(goods_id)
    
    cursor.execute(f"UPDATE goods SET {', '.join(update_fields)} WHERE id = ?", params)
    conn.commit()
    
    # 获取更新后的数据
    cursor.execute('SELECT * FROM goods WHERE id = ?', (goods_id,))
    updated_goods = cursor.fetchone()
    conn.close()
    
    return jsonify({
        "success": True,
        "goods": {
            "id": updated_goods["id"],
            "_id": str(updated_goods["id"]),
            "name": updated_goods["name"],
            "price": updated_goods["price"],
            "location": updated_goods["location"],
            "quantity": updated_goods["quantity"],
            "stock": updated_goods["stock"],
            "min_quantity": updated_goods["min_quantity"],
            "description": updated_goods["description"],
            "created_at": updated_goods["created_at"],
            "updated_at": updated_goods["updated_at"]
        }
    })


# 删除货物
@app.route('/api/goods/<int:goods_id>', methods=['DELETE'])
def delete_goods(goods_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM goods WHERE id = ?', (goods_id,))
    goods = cursor.fetchone()
    
    if not goods:
        conn.close()
        return jsonify({"error": "货物不存在"}), 404
    
    deleted_goods = {
        "id": goods["id"],
        "_id": str(goods["id"]),
        "name": goods["name"],
        "price": goods["price"],
        "location": goods["location"],
        "quantity": goods["quantity"],
        "stock": goods["stock"],
        "min_quantity": goods["min_quantity"],
        "description": goods["description"],
        "created_at": goods["created_at"],
        "updated_at": goods["updated_at"]
    }
    
    cursor.execute('DELETE FROM goods WHERE id = ?', (goods_id,))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "goods": deleted_goods})


# ============ 库存操作API ============

# 货物入库（放入）
@app.route('/api/goods/<int:goods_id>/stock_in', methods=['POST'])
def stock_in(goods_id):
    post_data = request.get_json()
    quantity = int(post_data.get('quantity', 0))
    
    if quantity <= 0:
        return jsonify({"error": "数量必须大于0"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM goods WHERE id = ?', (goods_id,))
    goods = cursor.fetchone()
    
    if not goods:
        conn.close()
        return jsonify({"error": "货物不存在"}), 404
    
    new_quantity = goods["quantity"] + quantity
    cursor.execute('UPDATE goods SET quantity = ?, stock = ?, updated_at = ? WHERE id = ?',
                   (new_quantity, new_quantity, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), goods_id))
    conn.commit()
    
    # 记录操作历史
    add_history_record(
        goods["name"],
        "入库",
        quantity,
        post_data.get("notes", "")
    )
    
    # 获取更新后的数据
    cursor.execute('SELECT * FROM goods WHERE id = ?', (goods_id,))
    updated_goods = cursor.fetchone()
    conn.close()
    
    return jsonify({
        "success": True,
        "goods": {
            "id": updated_goods["id"],
            "_id": str(updated_goods["id"]),
            "name": updated_goods["name"],
            "price": updated_goods["price"],
            "location": updated_goods["location"],
            "quantity": updated_goods["quantity"],
            "stock": updated_goods["stock"],
            "min_quantity": updated_goods["min_quantity"],
            "description": updated_goods["description"],
            "created_at": updated_goods["created_at"],
            "updated_at": updated_goods["updated_at"]
        }
    })


# 货物出库（取出）
@app.route('/api/goods/<int:goods_id>/stock_out', methods=['POST'])
def stock_out(goods_id):
    post_data = request.get_json()
    quantity = int(post_data.get('quantity', 0))
    
    if quantity <= 0:
        return jsonify({"error": "数量必须大于0"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM goods WHERE id = ?', (goods_id,))
    goods = cursor.fetchone()
    
    if not goods:
        conn.close()
        return jsonify({"error": "货物不存在"}), 404
    
    if goods["quantity"] < quantity:
        conn.close()
        return jsonify({"error": f"库存不足，当前库存: {goods['quantity']}"}), 400
    
    new_quantity = goods["quantity"] - quantity
    cursor.execute('UPDATE goods SET quantity = ?, stock = ?, updated_at = ? WHERE id = ?',
                   (new_quantity, new_quantity, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), goods_id))
    conn.commit()
    
    # 记录操作历史
    add_history_record(
        goods["name"],
        "出库",
        -quantity,
        post_data.get("notes", "")
    )
    
    # 获取更新后的数据
    cursor.execute('SELECT * FROM goods WHERE id = ?', (goods_id,))
    updated_goods = cursor.fetchone()
    conn.close()
    
    return jsonify({
        "success": True,
        "goods": {
            "id": updated_goods["id"],
            "_id": str(updated_goods["id"]),
            "name": updated_goods["name"],
            "price": updated_goods["price"],
            "location": updated_goods["location"],
            "quantity": updated_goods["quantity"],
            "stock": updated_goods["stock"],
            "min_quantity": updated_goods["min_quantity"],
            "description": updated_goods["description"],
            "created_at": updated_goods["created_at"],
            "updated_at": updated_goods["updated_at"]
        }
    })


# ============ 查询API ============

# 查询货物位置
@app.route('/api/goods/<int:goods_id>/location', methods=['GET'])
def get_location(goods_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, location FROM goods WHERE id = ?', (goods_id,))
    goods = cursor.fetchone()
    conn.close()
    
    if not goods:
        return jsonify({"error": "货物不存在"}), 404
    
    return jsonify({
        "id": goods["id"],
        "name": goods["name"],
        "location": goods["location"]
    })


# 查询货物价格
@app.route('/api/goods/<int:goods_id>/price', methods=['GET'])
def get_price(goods_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, price FROM goods WHERE id = ?', (goods_id,))
    goods = cursor.fetchone()
    conn.close()
    
    if not goods:
        return jsonify({"error": "货物不存在"}), 404
    
    return jsonify({
        "id": goods["id"],
        "name": goods["name"],
        "price": goods["price"]
    })


# 获取低库存货物
@app.route('/api/goods/low_stock', methods=['GET'])
def get_low_stock():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM goods WHERE quantity <= min_quantity ORDER BY id')
    rows = cursor.fetchall()
    conn.close()
    
    goods_list = []
    for row in rows:
        goods = {
            "id": row["id"],
            "_id": str(row["id"]),
            "name": row["name"],
            "price": row["price"],
            "location": row["location"],
            "quantity": row["quantity"],
            "stock": row["stock"],
            "min_quantity": row["min_quantity"],
            "description": row["description"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }
        goods_list.append(goods)
    
    return jsonify({"goods": goods_list})


# ============ 操作历史API ============

# 获取操作历史
@app.route('/api/history', methods=['GET'])
def get_history():
    data = load_history()
    return jsonify(data)


# 筛选历史记录
@app.route('/api/history/search', methods=['GET'])
def search_history():
    query = request.args.get('q', '').strip()
    data = load_history()
    
    if not query:
        return jsonify(data)
    
    results = [h for h in data["history"] if query.lower() in h["goods_name"].lower()]
    return jsonify({"history": results})


# 删除历史记录
@app.route('/api/history/<int:record_id>', methods=['DELETE'])
def delete_history_record(record_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM history WHERE id = ?', (record_id,))
    record = cursor.fetchone()
    
    if not record:
        conn.close()
        return jsonify({"error": "记录不存在"}), 404
    
    deleted_record = {
        "id": record["id"],
        "_id": str(record["id"]),
        "goods_name": record["goods_name"],
        "operation_type": record["operation_type"],
        "quantity": record["quantity"],
        "notes": record["notes"],
        "timestamp": record["timestamp"],
        "time": record["timestamp"]
    }
    
    cursor.execute('DELETE FROM history WHERE id = ?', (record_id,))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "record": deleted_record})


# 根据 _id 删除历史记录（兼容小程序）
@app.route('/api/history/by/_id/<string:record_id>', methods=['DELETE'])
def delete_history_record_by_uuid(record_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM history WHERE id = ?', (record_id,))
    record = cursor.fetchone()
    
    if not record:
        conn.close()
        return jsonify({"error": "记录不存在"}), 404
    
    deleted_record = {
        "id": record["id"],
        "_id": str(record["id"]),
        "goods_name": record["goods_name"],
        "operation_type": record["operation_type"],
        "quantity": record["quantity"],
        "notes": record["notes"],
        "timestamp": record["timestamp"],
        "time": record["timestamp"]
    }
    
    cursor.execute('DELETE FROM history WHERE id = ?', (record_id,))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "record": deleted_record})


# 清空所有历史记录
@app.route('/api/history/clear', methods=['DELETE'])
def clear_history():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM history')
    conn.commit()
    conn.close()
    return jsonify({"success": True})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=PORT)
