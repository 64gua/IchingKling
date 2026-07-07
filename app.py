from flask import Flask, request, jsonify
import yfinance as yf
import pandas as pd
from datetime import datetime
from dataSource import get_kline_data,Ktype,kdf_to_json
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ===== 首页路由 - 提供index.html =====
@app.route('/')
def index():
    return open('index.html', encoding='utf-8').read()

@app.route('/api/stock', methods=['GET'])
def get_stock_data():
    # 1. 获取查询参数
    symbol = request.args.get('symbol', '').strip()
    start_date = request.args.get('start', '').strip()
    end_date = request.args.get('end', '').strip()

    # 2. 参数校验
    if not symbol:
        return jsonify({'error': '股票代码不能为空'}), 400

    if not start_date or not end_date:
        return jsonify({'error': '请提供完整的开始日期和结束日期'}), 400

    # 验证日期格式 (YYYY-MM-DD)
    try:
        datetime.strptime(start_date, '%Y-%m-%d')
        datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': '日期格式错误，请使用 YYYY-MM-DD 格式'}), 400
    try:
        df=get_kline_data(symbol,start_date,end_date,Ktype.DAILY,source="baostock") 
        # ⭐ 调试：打印列名和索引名
        print("DataFrame columns:", df.columns.tolist())
        print("DataFrame index name:", df.index.name)
        print("DataFrame head:\n", df.head())
        # 如果数据为空
        if df.empty:
            return jsonify([]), 200  # 返回空列表，前端会显示无数据
        # df['date'] = df['date'].dt.strftime('%Y-%m-%d')
        print(df.head(5))
        # ⭐ 添加这一行：重置索引，把日期从索引变成列
        df = df.reset_index()
        data = kdf_to_json(df)
        return jsonify(data), 200
    except Exception as e:
        # 捕获 yfinance 或其他异常
        return jsonify({'error': f'获取数据失败: {str(e)}'}), 500

if __name__ == '__main__':
    # 启动 Flask 服务，默认端口 5000
    # app.run(debug=True, host='0.0.0.0', port=5000)
    app.run()