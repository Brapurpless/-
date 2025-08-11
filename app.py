from flask import Flask, render_template, request, jsonify, session, redirect
import sqlite3
import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, session, jsonify, send_from_directory

# 加载.env文件中的环境变量
load_dotenv()

app = Flask(__name__)
app.secret_key = 'ai_teaching_platform'
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 导入AI API模块
from ai_api import AIAPI
ai_client = AIAPI()

# 数据库初始化
def init_db():
    conn = sqlite3.connect('ai_teaching_platform.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  role TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS courses
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT NOT NULL,
                  subject TEXT NOT NULL,
                  grade TEXT NOT NULL,
                  creator_id INTEGER NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS lesson_plans
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  course_id INTEGER NOT NULL,
                  title TEXT NOT NULL,
                  content TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    # 插入测试数据
    c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('admin', 'admin123', 'admin')")
    c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('school', 'school123', 'school')")
    c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('teacher', 'teacher123', 'teacher')")
    c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('parent', 'parent123', 'parent')")
    c.execute("INSERT OR IGNORE INTO courses (title, subject, grade, creator_id) VALUES ('高中数学', '数学', '高中', 1)")
    conn.commit()
    conn.close()

# 文件上传路由
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if session.get('role') != 'admin':
        return redirect('/login')
    
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': '没有文件部分'})
        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': '没有选择文件'})
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return jsonify({'status': 'success', 'message': '文件上传成功', 'filename': filename})
    return render_template('upload.html')

# 文件管理路由 - 列出所有文件
@app.route('/files')
def list_files():
    if session.get('role') != 'admin':
        return redirect('/login')
    
    files = []
    upload_folder = app.config['UPLOAD_FOLDER']
    if os.path.exists(upload_folder):
        for filename in os.listdir(upload_folder):
            file_path = os.path.join(upload_folder, filename)
            if os.path.isfile(file_path):
                file_size = os.path.getsize(file_path) / 1024  # KB
                modified_time = os.path.getmtime(file_path)
                files.append({
                    'name': filename,
                    'size': f'{file_size:.2f} KB',
                    'modified': datetime.fromtimestamp(modified_time).strftime('%Y-%m-%d %H:%M:%S')
                })
    
    return render_template('files.html', files=files, username=session.get('username', ''), role=session.get('role', ''))

# 文件下载路由
@app.route('/files/download/<filename>')
def download_file(filename):
    if session.get('role') != 'admin':
        return redirect('/login')
    
    upload_folder = app.config['UPLOAD_FOLDER']
    file_path = os.path.join(upload_folder, filename)
    
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_from_directory(upload_folder, filename, as_attachment=True)
    else:
        return jsonify({'status': 'error', 'message': '文件不存在'})

# 文件删除路由
@app.route('/files/delete/<filename>')
def delete_file(filename):
    if session.get('role') != 'admin':
        return redirect('/login')
    
    upload_folder = app.config['UPLOAD_FOLDER']
    file_path = os.path.join(upload_folder, filename)
    
    if os.path.exists(file_path) and os.path.isfile(file_path):
        os.remove(file_path)
        return jsonify({'status': 'success', 'message': '文件删除成功'})
    else:
        return jsonify({'status': 'error', 'message': '文件不存在'})

# 路由
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    conn = sqlite3.connect('ai_teaching_platform.db')
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
    result = c.fetchone()
    conn.close()
    
    if result:
        session['role'] = result[0]
        session['username'] = username
        # 根据角色跳转到对应页面
        if result[0] == 'school':
            return redirect('/school/dashboard')
        elif result[0] == 'teacher':
            return redirect('/teacher/dashboard')
        elif result[0] == 'parent':
            return redirect('/parent/dashboard')
        else:
            return redirect('/dashboard')
    return "登录失败", 401

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', role=session.get('role', ''), username=session.get('username', ''))

@app.route('/school/dashboard')
def school_dashboard():
    if session.get('role') != 'school':
        return redirect('/login')
    return render_template('school_dashboard.html', username=session.get('username', ''))

@app.route('/teacher/dashboard')
def teacher_dashboard():
    if session.get('role') != 'teacher':
        return redirect('/login')
    return render_template('teacher_dashboard.html', username=session.get('username', ''))

@app.route('/parent/dashboard')
def parent_dashboard():
    if session.get('role') != 'parent':
        return redirect('/login')
    return render_template('parent_dashboard.html', username=session.get('username', ''))

@app.route('/api/generate_lesson_plan', methods=['POST'])
def api_generate_lesson_plan():
    try:
        data = request.json
        subject = data.get('subject', '')
        grade = data.get('grade', '')
        topic = data.get('topic', '')
        template_type = data.get('template_type', 'standard')
        
        # 构建提示词
        prompt = f"请为{grade}的{subject}学科生成一个关于{topic}的教案。"
        if template_type == 'standard':
            prompt += "教案应包含教学目标、教学重难点、教学过程和作业设计等部分。"
        
        result = ai_client.generate_lesson_plan(prompt)
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": f"生成教案失败: {str(e)}"})

@app.route('/api/courses')
def api_courses():
    conn = sqlite3.connect('ai_teaching_platform.db')
    courses = conn.execute('SELECT id, title, subject, grade FROM courses').fetchall()
    conn.close()
    return jsonify([{"id": c[0], "title": c[1], "subject": c[2], "grade": c[3]} for c in courses])

@app.route('/api/ask_question', methods=['POST'])
def api_ask_question():
    try:
        data = request.json
        question = data.get('question', '')
        user_role = session.get('role', '')
        
        if not user_role:
            return jsonify({"status": "error", "message": "用户未登录"})
        
        result = ai_client.ask_question(question, user_role)
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": f"回答问题失败: {str(e)}"})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)