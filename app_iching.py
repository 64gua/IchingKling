# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import re
import codeToName


app = Flask(__name__)
app.secret_key = 'iching_secret_key_12345'  # Session需要密钥
app.database = 'IchingDB.db'

def normalize_date(date_str):
    """标准化日期格式，将 2010-1-14 转换为 2010-01-14"""
    if not date_str:
        return None
    try:
        parts = date_str.split('-')
        if len(parts) == 3:
            year, month, day = parts
            return f"{year}-{int(month):02d}-{int(day):02d}"
    except:
        pass
    return None

def get_db_connection():
    conn = sqlite3.connect(app.database)
    conn.row_factory = sqlite3.Row
    conn.create_function("normalize_date", 1, normalize_date)
    return conn

def extract_images_from_content(content):
    """从content中提取图片链接"""
    if not content:
        return []
    pattern = r'!\[?\]\((?:images/)?([^)]+\.(?:jpg|jpeg|png|gif))\)'
    matches = re.findall(pattern, content, re.IGNORECASE)
    return matches

@app.route('/', methods=['GET', 'POST'])
def search():
    """搜索页面 - 搜索和结果在同一个页面"""
    results = None
    if request.method == 'POST':
        guaname = request.form.get('guaname', '').strip()
        stockname = request.form.get('stockname', '').strip()
        stockcode,stockname=codeToName.get_stock_tuple(stockname)
        start_date = request.form.get('start_date', '').strip()
        end_date = request.form.get('end_date', '').strip()
        keyword = request.form.get('keyword', '').strip()
        
        # 保存搜索条件到session
        session['search_criteria'] = {
            'guaname': guaname,
            'stockname': stockcode,
            'start_date': start_date,
            'end_date': end_date,
            'keyword': keyword
        }
        
        results = do_search(guaname, stockcode, start_date, end_date, keyword)
    elif request.args.get('from_detail') and 'search_criteria' in session:
        # 从详情页返回，使用保存的搜索条件重新查询
        criteria = session['search_criteria']
        results = do_search(
            criteria.get('guaname', ''),
            criteria.get('stockname', ''),
            criteria.get('start_date', ''),
            criteria.get('end_date', ''),
            criteria.get('keyword', '')
        )
    
    return render_template('search.html', results=results)

def do_search(guaname, stockname, start_date, end_date, keyword):
    """执行搜索查询"""
    conn = get_db_connection()
    query = 'SELECT * FROM ichinglist WHERE 1=1'
    orderby= '  order by cast( substr(mydatetime,6,2) as integer),mydatetime '
    params = []
    
    if guaname:
        query += ' AND guaname LIKE ?'
        params.append(f'%{guaname}%')
    if stockname:
        query += ' AND stockname LIKE ?'
        params.append(f'%{stockname}%')
    if start_date:
        query += ' AND normalize_date(mydatetime) >= ?'
        params.append(start_date)
    if end_date:
        query += ' AND normalize_date(mydatetime) <= ?'
        params.append(end_date)
    if keyword:
        query += ' AND (subject LIKE ? OR content LIKE ?)'
        params.append(f'%{keyword}%')
        params.append(f'%{keyword}%')
    
    query += orderby
    
    cur = conn.execute(query, params)
    results = cur.fetchall()
    conn.close()
    return results

@app.route('/detail/<int:id>')
def detail(id):
    """详情页面"""
    conn = get_db_connection()
    cur = conn.execute('SELECT * FROM ichinglist WHERE ID = ?', (id,))
    item = cur.fetchone()
    conn.close()
    
    if item is None:
        return "记录不存在", 404
    
    images = extract_images_from_content(item['content'])
    
    return render_template('detail.html', item=item, images=images)

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    """删除记录"""
    conn = get_db_connection()
    conn.execute('DELETE FROM ichinglist WHERE ID = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('search'))

@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    """更新记录"""
    guaname = request.form.get('guaname', '').strip()
    stockname = request.form.get('stockname', '').strip()
    mydatetime = request.form.get('mydatetime', '').strip()
    subject = request.form.get('subject', '').strip()
    content = request.form.get('content', '').strip()
    new_image = request.form.get('new_image', '').strip()
    
    conn = get_db_connection()
    
    conn.execute('''UPDATE ichinglist 
                    SET guaname = ?, stockname = ?, mydatetime = ?, subject = ?, content = ?
                    WHERE ID = ?''',
                 (guaname, stockname, mydatetime, subject, content, id))
    
    if new_image:
        if new_image not in content:
            content_with_image = content + '\n![](images/' + new_image + ')'
            conn.execute('UPDATE ichinglist SET content = ? WHERE ID = ?', (content_with_image, id))
    conn.commit()
    conn.close()
    
    return redirect(url_for('detail', id=id))

@app.route('/delete_image/<int:id>', methods=['POST'])
def delete_image(id):
    """删除记录中的某张图片"""
    image_path = request.form.get('image_path', '')
    conn = get_db_connection()
    cur = conn.execute('SELECT content FROM ichinglist WHERE ID = ?', (id,))
    row = cur.fetchone()
    
    if row:
        content = row['content']
        pattern = r'\n*!\[?\]\(images/' + re.escape(image_path) + r'\)'
        new_content = re.sub(pattern, '', content)
        conn.execute('UPDATE ichinglist SET content = ? WHERE ID = ?', (new_content, id))
        conn.commit()
    
    conn.close()
    return redirect(url_for('detail', id=id))

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000,debug=True)
    # app.run()
