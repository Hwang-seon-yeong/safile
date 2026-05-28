from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import os
import sqlite3
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'safile_secret_key_for_session' # 로그인 세션 관리를 위한 비밀키 설정

# uploads 폴더 자동 생성
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 위험 확장자 목록
BLOCKED_EXTENSIONS = ['exe', 'bat', 'cmd', 'sh', 'msi']

# DB 연결 및 테이블 초기화 함수
def init_db():
    conn = sqlite3.connect('safile.db')
    cursor = conn.cursor()
    
    # 1. 사용자(User) 테이블 생성
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # 2. 업로드 히스토리(History) 테이블 생성 (실시간 연동용 완료)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            status TEXT NOT NULL,
            risk TEXT NOT NULL,
            reason TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# 앱 구동 시 자동으로 SQLite 테이블 생성
init_db()


# ----------------------------
# 로그인 페이지 및 검증 로직
# ----------------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = sqlite3.connect('safile.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        # 유저가 존재하고 암호 해시가 일치하는지 확인
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('dashboard'))
        else:
            # 로그인 실패 시 메시지를 띄우거나 로그인 창으로 바운스
            return render_template('login.html', error="Invalid username or password.")
            
    return render_template('login.html')


# ----------------------------
# 회원가입 페이지 및 DB 저장
# ----------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 패스워드 안전 암호화 처리 (Werkzeug 패키지 활용)
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        try:
            conn = sqlite3.connect('safile.db')
            cursor = conn.cursor()
            # DB에 아이디와 암호화된 비밀번호 인서트
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
            conn.close()
            return redirect(url_for('login')) # 가입 성공 시 로그인 창으로 이동
        except sqlite3.IntegrityError:
            # 중복된 아이디가 존재할 경우 에러 처리
            return render_template('signup.html', error="Username already exists.")
            
    return render_template('signup.html')


# ----------------------------
# 로그아웃 처리
# ----------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ----------------------------
# 대시보드
# ----------------------------
@app.route('/dashboard')
def dashboard():
    # 세션 체크 (로그인 안 한 사용자는 로그인 페이지로 튕겨내기)
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')


# ----------------------------
# 파일 업로드 (비동기 Fetch 통신 및 DB 인서트 완성본)
# ----------------------------
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # 케이스 A: 프론트 자바스크립트 모달 필터(.exe 등)에서 사전 차단된 로그 기록용
        if 'filename_only' in request.form:
            filename = request.form.get('filename_only')
            status, risk, reason = 'BLOCKED', 'HIGH', 'Dangerous file extension detected (Interception)'
            
            conn = sqlite3.connect('safile.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO history (filename, status, risk, reason) VALUES (?, ?, ?, ?)', 
                           (filename, status, risk, reason))
            conn.commit()
            conn.close()
            return jsonify({"filename": filename, "status": status, "risk": risk, "reason": reason})

        # 케이스 B: 실제 서버로 파일이 넘겨진 경우 실시간 검증 및 DB 적재
        if 'file' not in request.files:
            return jsonify({"filename": "No File", "status": "BLOCKED", "risk": "HIGH", "reason": "No file selected"})

        file = request.files['file']
        if file.filename == '':
            return jsonify({"filename": "No File", "status": "BLOCKED", "risk": "HIGH", "reason": "No file selected"})

        if file:
            filename = secure_filename(file.filename)
            extension = filename.split('.')[-1].lower()

            # 초기 기본 스캔 결과값 세팅
            status, risk, reason = 'SAFE', 'LOW', 'File uploaded successfully'

            # 보안 필터 검사
            if extension in BLOCKED_EXTENSIONS:
                status, risk, reason = 'BLOCKED', 'HIGH', 'Dangerous file extension detected'
            elif extension in ['zip', 'rar']:
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                status, risk, reason = 'WARNING', 'MEDIUM', 'Compressed files require caution'
            else:
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # 🛠️ [실제 DB 저장] 최종 스캔 결과를 SQLite history 테이블에 영구 저장
            conn = sqlite3.connect('safile.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO history (filename, status, risk, reason) VALUES (?, ?, ?, ?)', 
                           (filename, status, risk, reason))
            conn.commit()
            conn.close()

            # 프론트엔드 자바스크립트단으로 결과 구조를 JSON 형태로 반환
            return jsonify({"filename": filename, "status": status, "risk": risk, "reason": reason})

    return render_template('upload.html')


# ----------------------------
# 결과 페이지
# ----------------------------
@app.route('/result')
def result():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('result.html')


# ----------------------------
# 업로드 기록
# ----------------------------
@app.route('/history')
def history():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('history.html')


# ----------------------------
# 보안 정책
# ----------------------------
@app.route('/policy')
def policy():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('policy.html')


# ----------------------------
# 서버 실행
# ----------------------------
if __name__ == '__main__':
    app.run(debug=True, port=5001)