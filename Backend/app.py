import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv()

import sqlite3
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# 세션을 위한 키 설정
app.secret_key = "super_secret_key"  # 세션을 위한 비밀 키

# SQLite 사용자 데이터베이스 파일 경로
USER_DB_PATH = os.path.join(os.path.dirname(__file__), 'user_data.db')

# SQLAlchemy 설정
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'  # 장소 정보 데이터베이스 경로 설정
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Item 모델 정의 (장소 정보 데이터베이스)
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=False)  # 설명 컬럼 추가

    def __repr__(self):
        return f'<Item {self.name}>'

# 사용자 데이터베이스 초기화: users 테이블 생성
def init_user_db():
    with sqlite3.connect(USER_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        """)
        conn.commit()

# 데이터베이스 초기화: 테이블 생성 (users, posts 테이블)
def init_db():
    with sqlite3.connect(USER_DB_PATH) as conn:
        cursor = conn.cursor()
        # 사용자 테이블 생성
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        """)
        # 게시글 테이블 생성
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        conn.commit()

# 초기 샘플 데이터 삽입 (장소 정보)
with app.app_context():
    db.create_all()  # SQLAlchemy로 테이블 생성
    if not Item.query.first():  # 샘플 데이터가 없다면 삽입
        sample_items = [
            Item(name='자이스터디카페', description='경북 경주시 충효천길 263-2 2층'),
            Item(name='경주 황성점 멘토즈스터디카페', description='경상북도 경주시 황성동 원지길12번길 31 2층'),
            # 더 많은 샘플 항목을 추가할 수 있음
        ]
        db.session.bulk_save_objects(sample_items)
        db.session.commit()

# 루트 경로: 메인 페이지 렌더링
from flask import Flask, render_template
import folium  # Folium 추가

app = Flask(__name__)

@app.route('/')
def index():
    # Folium 지도 생성
    start_coords = (35.0, 129.0)  # 기본 좌표 (예: 경주시)
    folium_map = folium.Map(location=start_coords, zoom_start=10)

    # 샘플 마커 추가
    sample_locations = [
        {"name": "자이스터디카페", "coords": (35.8562, 129.2246)},
        {"name": "황성점 멘토즈스터디카페", "coords": (35.8463, 129.2181)}
    ]
    for location in sample_locations:
        folium.Marker(
            location=location["coords"],
            popup=location["name"],
            tooltip=location["name"]
        ).add_to(folium_map)

    map_html = folium_map._repr_html_()  # Folium HTML 생성
    return render_template('index.html', map_html=map_html)  # 'home.html'로 전달


# 사용자 등록 처리 (GET과 POST)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # POST 요청 처리
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return render_template('register.html', error="Both username and password are required")

        try:
            with sqlite3.connect(USER_DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                conn.commit()
            return render_template('register.html', success=f'User {username} registered successfully')
        except sqlite3.IntegrityError:
            return render_template('register.html', error="Username already exists")
    return render_template('register.html')

# 사용자 목록 조회 API
@app.route('/users', methods=['GET'])
def get_users():
    with sqlite3.connect(USER_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password FROM users")
        users = cursor.fetchall()

    return jsonify([{
        'id': user[0], 'username': user[1], 'password': user[2]
    } for user in users]), 200

# 로그인 처리 (GET과 POST)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # POST 요청 시 사용자 인증
        username = request.form.get('username')
        password = request.form.get('password')

        with sqlite3.connect(USER_DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
            user = cursor.fetchone()

        if user:
            # 로그인 성공 시 세션에 사용자 정보 저장
            session['user_id'] = user[0]
            session['username'] = username
            return redirect(url_for('posts'))  # 게시글 목록으로 리디렉션
        else:
            return render_template('login.html', error="Invalid username or password")
    return render_template('login.html')

# 로그아웃 처리
@app.route('/logout')
def logout():
    session.clear()  # 세션 데이터 삭제
    return redirect(url_for('index'))

# 게시글 목록 조회
@app.route('/posts', methods=['GET'])
def posts():
    with sqlite3.connect(USER_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT posts.id, title, content, created_at, username
            FROM posts
            JOIN users ON posts.user_id = users.id
            ORDER BY created_at DESC
        """)
        posts = cursor.fetchall()
    return render_template('posts.html', posts=posts)

# 게시글 작성
@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # 로그인하지 않으면 로그인 페이지로 리디렉션

    if request.method == 'POST':
        # 게시글 제목 및 내용 입력 처리
        title = request.form.get('title')
        content = request.form.get('content')
        user_id = session['user_id']

        if not title or not content:
            return render_template('create_post.html', error="Title and content are required")

        with sqlite3.connect(USER_DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO posts (title, content, user_id) VALUES (?, ?, ?)", (title, content, user_id))
            conn.commit()
        return redirect(url_for('posts'))  # 게시글 목록으로 리디렉션

    return render_template('create_post.html')

# 게시글 상세보기
@app.route('/post/<int:post_id>', methods=['GET'])
def post_detail(post_id):
    with sqlite3.connect(USER_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT posts.id, title, content, created_at, username
            FROM posts
            JOIN users ON posts.user_id = users.id
            WHERE posts.id = ?
        """, (post_id,))
        post = cursor.fetchone()

    if post is None:
        return "Post not found", 404

    return render_template('post_detail.html', post=post)

# 검색 페이지: 장소 정보 검색
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if query:
        results = Item.query.filter(Item.name.contains(query)).all()  # 이름에 쿼리 포함된 항목 찾기
    else:
        results = []
    return render_template('search.html', results=results)
def init_tasks_db():
    with sqlite3.connect(USER_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                detail TEXT NOT NULL,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        conn.commit()
# 애플리케이션 실행 전 데이터베이스 초기화
with app.app_context():
    init_db()
    init_user_db()
    init_tasks_db()

@app.route('/planner')
def planner():
    # 로그인 여부 확인
    if 'user_id' not in session:
        return redirect(url_for('login'))  # 로그인하지 않은 경우 로그인 페이지로 리디렉션

    user_id = session['user_id']
    # 사용자별 할 일 목록을 데이터베이스에서 불러옴
    with sqlite3.connect(USER_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT title, detail FROM tasks WHERE user_id = ?", (user_id,))
        tasks = cursor.fetchall()

    # 할 일 목록을 planner.html에 전달
    return render_template('planner.html', tasks=tasks)


if __name__ == '__main__':
    # 서버 실행
    app.run(debug=True)


