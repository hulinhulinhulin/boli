from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Render 会自动设置 PORT 环境变量
PORT = int(os.environ.get('PORT', 5000))

# 数据文件路径
GOODS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'goods.json')
HISTORY_FILE = os.path.join(os.path.dirname(__file__), 'data', 'history.json')


def load_goods():
    """加载货物数据"""
    try:
        with open(GOODS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 确保每个货物都有兼容字段
            for goods in data.get("goods", []):
                if "id" in goods:
                    goods["_id"] = str(goods["id"])
                if "quantity" in goods:
                    goods["stock"] = goods["quantity"]
                elif "stock" in goods:
                    goods["quantity"] = goods["stock"]
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {"goods": []}


def save_goods(data):
    """保存货物数据"""
    with open(GOODS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_history():
    """加载操作历史"""
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 添加兼容字段
            for record in data.get("history", []):
                if "id" in record:
                    record["_id"] = str(record["id"])
                if "timestamp" in record and "time" not in record:
                    record["time"] = record["timestamp"]
                elif "time" in record and "timestamp" not in record:
                    record["timestamp"] = record["time"]
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {"history": []}


def save_history(data):
    """保存操作历史"""
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_history_record(goods_name, operation_type, quantity, notes=""):
    """添加操作历史记录"""
    history_data = load_history()
    record = {
        "id": len(history_data["history"]) + 1,
        "goods_name": goods_name,
        "operation_type": operation_type,
        "quantity": quantity,
        "notes": notes,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    history_data["history"].append(record)
    save_history(history_data)
    return record


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
    data = load_goods()
    goods_data = request.get_json()
    
    for goods in data["goods"]:
        if str(goods.get("id")) == goods_id or goods.get("_id") == goods_id:
            # 更新字段
            if "name" in goods_data:
                goods["name"] = goods_data["name"]
            if "price" in goods_data:
                goods["price"] = float(goods_data["price"])
            if "location" in goods_data:
                goods["location"] = goods_data["location"]
            if "quantity" in goods_data:
                goods["quantity"] = int(goods_data["quantity"])
                goods["stock"] = int(goods_data["quantity"])
            elif "stock" in goods_data:
                goods["stock"] = int(goods_data["stock"])
                goods["quantity"] = int(goods_data["stock"])
            if "min_quantity" in goods_data:
                goods["min_quantity"] = int(goods_data["min_quantity"])
            if "description" in goods_data:
                goods["description"] = goods_data["description"]
            
            goods["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_goods(data)
            return jsonify({"success": True, "goods": goods})
    
    return jsonify({"error": "货物不存在"}), 404


# 根据 _id 删除货物（兼容小程序）
@app.route('/api/goods/by/_id/<string:goods_id>', methods=['DELETE'])
def delete_goods_by_uuid(goods_id):
    data = load_goods()
    
    for i, goods in enumerate(data["goods"]):
        if str(goods.get("id")) == goods_id or goods.get("_id") == goods_id:
            deleted_goods = data["goods"].pop(i)
            save_goods(data)
            return jsonify({"success": True, "goods": deleted_goods})
    
    return jsonify({"error": "货物不存在"}), 404


# 添加货物
@app.route('/api/goods', methods=['POST'])
def add_goods():
    data = load_goods()
    goods_data = request.get_json()
    
    # 验证必填字段
    required_fields = ['name', 'price', 'location']
    for field in required_fields:
        if field not in goods_data or not goods_data[field]:
            return jsonify({"error": f"缺少必填字段: {field}"}), 400
    
    # 生成新ID
    new_id = max([g["id"] for g in data["goods"]], default=0) + 1
    
    new_goods = {
        "id": new_id,
        "_id": str(new_id),  # 兼容小程序使用的 _id
        "name": goods_data["name"],
        "price": float(goods_data["price"]),
        "location": goods_data["location"],
        "quantity": int(goods_data.get("quantity", goods_data.get("stock", 0))),
        "stock": int(goods_data.get("stock", goods_data.get("quantity", 0))),  # 兼容小程序使用的 stock
        "min_quantity": int(goods_data.get("min_quantity", 0)),
        "description": goods_data.get("description", ""),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    data["goods"].append(new_goods)
    save_goods(data)
    
    return jsonify({"success": True, "goods": new_goods})


# 修改货物
@app.route('/api/goods/<int:goods_id>', methods=['PUT'])
def update_goods(goods_id):
    data = load_goods()
    goods_data = request.get_json()
    
    for goods in data["goods"]:
        if goods["id"] == goods_id:
            # 更新字段
            if "name" in goods_data:
                goods["name"] = goods_data["name"]
            if "price" in goods_data:
                goods["price"] = float(goods_data["price"])
            if "location" in goods_data:
                goods["location"] = goods_data["location"]
            if "quantity" in goods_data:
                goods["quantity"] = int(goods_data["quantity"])
                goods["stock"] = int(goods_data["quantity"])  # 兼容 stock
            elif "stock" in goods_data:  # 兼容小程序使用的 stock
                goods["stock"] = int(goods_data["stock"])
                goods["quantity"] = int(goods_data["stock"])
            if "min_quantity" in goods_data:
                goods["min_quantity"] = int(goods_data["min_quantity"])
            if "description" in goods_data:
                goods["description"] = goods_data["description"]
            
            goods["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_goods(data)
            return jsonify({"success": True, "goods": goods})
    
    return jsonify({"error": "货物不存在"}), 404


# 删除货物
@app.route('/api/goods/<int:goods_id>', methods=['DELETE'])
def delete_goods(goods_id):
    data = load_goods()
    
    for i, goods in enumerate(data["goods"]):
        if goods["id"] == goods_id:
            deleted_goods = data["goods"].pop(i)
            save_goods(data)
            return jsonify({"success": True, "goods": deleted_goods})
    
    return jsonify({"error": "货物不存在"}), 404


# ============ 库存操作API ============

# 货物入库（放入）
@app.route('/api/goods/<int:goods_id>/stock_in', methods=['POST'])
def stock_in(goods_id):
    data = load_goods()
    post_data = request.get_json()
    quantity = int(post_data.get('quantity', 0))
    
    if quantity <= 0:
        return jsonify({"error": "数量必须大于0"}), 400
    
    for goods in data["goods"]:
        if goods["id"] == goods_id:
            goods["quantity"] += quantity
            goods["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_goods(data)
            
            # 记录操作历史
            add_history_record(
                goods["name"], 
                "入库", 
                quantity, 
                post_data.get("notes", "")
            )
            
            return jsonify({"success": True, "goods": goods})
    
    return jsonify({"error": "货物不存在"}), 404


# 货物出库（取出）
@app.route('/api/goods/<int:goods_id>/stock_out', methods=['POST'])
def stock_out(goods_id):
    data = load_goods()
    post_data = request.get_json()
    quantity = int(post_data.get('quantity', 0))
    
    if quantity <= 0:
        return jsonify({"error": "数量必须大于0"}), 400
    
    for goods in data["goods"]:
        if goods["id"] == goods_id:
            if goods["quantity"] < quantity:
                return jsonify({"error": f"库存不足，当前库存: {goods['quantity']}"}), 400
            
            goods["quantity"] -= quantity
            goods["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_goods(data)
            
            # 记录操作历史
            add_history_record(
                goods["name"], 
                "出库", 
                -quantity, 
                post_data.get("notes", "")
            )
            
            return jsonify({"success": True, "goods": goods})
    
    return jsonify({"error": "货物不存在"}), 404


# ============ 查询API ============

# 查询货物位置
@app.route('/api/goods/<int:goods_id>/location', methods=['GET'])
def get_location(goods_id):
    data = load_goods()
    
    for goods in data["goods"]:
        if goods["id"] == goods_id:
            return jsonify({
                "id": goods["id"],
                "name": goods["name"],
                "location": goods["location"]
            })
    
    return jsonify({"error": "货物不存在"}), 404


# 查询货物价格
@app.route('/api/goods/<int:goods_id>/price', methods=['GET'])
def get_price(goods_id):
    data = load_goods()
    
    for goods in data["goods"]:
        if goods["id"] == goods_id:
            return jsonify({
                "id": goods["id"],
                "name": goods["name"],
                "price": goods["price"]
            })
    
    return jsonify({"error": "货物不存在"}), 404


# 获取低库存货物
@app.route('/api/goods/low_stock', methods=['GET'])
def get_low_stock():
    data = load_goods()
    low_stock_goods = [g for g in data["goods"] if g["quantity"] <= g.get("min_quantity", 0)]
    return jsonify({"goods": low_stock_goods})


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
    data = load_history()
    
    for i, record in enumerate(data["history"]):
        if record["id"] == record_id:
            deleted_record = data["history"].pop(i)
            save_history(data)
            return jsonify({"success": True, "record": deleted_record})
    
    return jsonify({"error": "记录不存在"}), 404


# 根据 _id 删除历史记录（兼容小程序）
@app.route('/api/history/by/_id/<string:record_id>', methods=['DELETE'])
def delete_history_record_by_uuid(record_id):
    data = load_history()
    
    for i, record in enumerate(data["history"]):
        if str(record.get("id")) == record_id or record.get("_id") == record_id:
            deleted_record = data["history"].pop(i)
            save_history(data)
            return jsonify({"success": True, "record": deleted_record})
    
    return jsonify({"error": "记录不存在"}), 404


# 清空所有历史记录
@app.route('/api/history/clear', methods=['DELETE'])
def clear_history():
    data = load_history()
    data["history"] = []
    save_history(data)
    return jsonify({"success": True})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=PORT)
