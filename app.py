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


# ============================================================
# [1~4] 데이터 구조 클래스 정의 영역 (Entity Layer)
# ============================================================

# 1) User 클래스
class User:
    def __init__(self, user_id, username, password=None):
        self.id = user_id
        self.username = username
        self.password = password

# 2) FileUpload 클래스 (MIME 타입과 크기 저장 기능 반영)
class FileUpload:
    def __init__(self, file_name, file_type=None, file_size=None):
        self.file_name = file_name
        self.file_type = file_type
        self.file_size = file_size

# 3) UploadRecord 클래스
class UploadRecord:
    def __init__(self, record_id, filename, status, risk, reason, timestamp):
        self.id = record_id
        self.filename = filename
        self.status = status
        self.risk = risk
        self.reason = reason
        self.timestamp = timestamp

# 4) ScanResult 클래스
class ScanResult:
    def __init__(self, status, risk_level, blocked_reason):
        self.status = status                  # SAFE, WARNING, BLOCKED
        self.risk_level = risk_level          # LOW, MEDIUM, HIGH
        self.blocked_reason = blocked_reason  # 상세 설명 및 차단 사유


# ============================================================
# [5~11] 비즈니스 로직 및 기능 클래스 영역 (Service Layer)
# ============================================================

# 5) SecurityPolicy 클래스
class SecurityPolicy:
    def __init__(self):
        self.blocked_extensions = ['exe', 'bat', 'cmd', 'sh', 'msi']


# 6) SecurityScanService 클래스 (🎯 고도화: 이중 확장자 위장 공격 정밀 차단)
class SecurityScanService:
    @staticmethod
    def evaluate(filename, policy):
        # 파일명을 점('.') 기준으로 전부 쪼개기
        parts = filename.split('.')
        
        # 1. 초기 기본 스캔 결과값 세팅
        status, risk, reason = 'SAFE', 'LOW', 'File uploaded successfully'
        
        # 2. 이중 확장자 탐지 로직 (점의 개수가 2개 이상이고, 중간에 위험 확장자가 숨어있는지 정밀 추적)
        if len(parts) > 2:
            # 맨 마지막 확장자를 제외한 중간 확장자들 추출 (예: abc.exe.txt -> 중간 배열에 'exe' 포착)
            middle_extensions = [p.lower() for p in parts[1:-1]]
            
            # 중간 영역에 차단 목록 정책(exe, bat 등)이 숨어있다면 우회 공격으로 간주하고 즉시 차단
            for mid_ext in middle_extensions:
                if mid_ext in policy.blocked_extensions:
                    status, risk, reason = 'BLOCKED', 'HIGH', 'Dangerous double extension detected (Spoofing Alert)'
                    return ScanResult(status=status, risk_level=risk, blocked_reason=reason)

        # 3. 일반 단일 확장자 검사 (가장 뒤쪽 최종 확장자 기준)
        final_extension = parts[-1].lower()
        if final_extension in policy.blocked_extensions:
            status, risk, reason = 'BLOCKED', 'HIGH', 'Dangerous file extension detected'
        elif final_extension in ['zip', 'rar']:
            status, risk, reason = 'WARNING', 'MEDIUM', 'Compressed files require caution'
            
        return ScanResult(status=status, risk_level=risk, blocked_reason=reason)


# 7) SecurityAlert 클래스 (경고 메시지 및 안내 생성)
class SecurityAlert:
    @staticmethod
    def generate_alert(status, reason):
        if status == 'BLOCKED':
            return f"🚨 [보안 경고] 위험 파일이 탐지되어 차단되었습니다. 사유: {reason}"
        elif status == 'WARNING':
            return f"⚠️ [주의] 압축 파일이 탐지되었습니다. 사유: {reason}"
        return "✅ 안전한 파일입니다."


# 8) FileFilter 클래스 (조건별 필터링 조회 구현)
class FileFilter:
    @staticmethod
    def filter_by_status(status_criterion):
        conn = sqlite3.connect('safile.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM history WHERE status = ? ORDER BY timestamp DESC', (status_criterion,))
        rows = cursor.fetchall()
        conn.close()
        return [UploadRecord(r[0], r[1], r[2], r[3], r[4], r[5]) for r in rows]


# 9) HistorySearch 클래스 (파일명 검색 및 결과 관리 구현)
class HistorySearch:
    @staticmethod
    def get_all_history():
        conn = sqlite3.connect('safile.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM history ORDER BY timestamp DESC')
        rows = cursor.fetchall()
        conn.close()
        return [UploadRecord(r[0], r[1], r[2], r[3], r[4], r[5]) for r in rows]

    @staticmethod
    def search_by_filename(keyword):
        conn = sqlite3.connect('safile.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM history WHERE filename LIKE ? ORDER BY timestamp DESC', (f"%{keyword}%",))
        rows = cursor.fetchall()
        conn.close()
        return [UploadRecord(r[0], r[1], r[2], r[3], r[4], r[5]) for r in rows]


# 10) FileDeletion 클래스 (삭제 성공/실패 에러 제어 구현)
class FileDeletion:
    @staticmethod
    def delete_record(record_id):
        try:
            conn = sqlite3.connect('safile.db')
            cursor = conn.cursor()
            # 해당 기록이 존재하는지 먼저 확인
            cursor.execute('SELECT filename FROM history WHERE id = ?', (record_id,))
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return False, "삭제 실패: 해당 업로드 기록을 찾을 수 없습니다."
                
            cursor.execute('DELETE FROM history WHERE id = ?', (record_id,))
            conn.commit()
            conn.close()
            return True, "삭제 성공"
        except sqlite3.Error as e:
            return False, f"삭제 과정에서 데이터베이스 오류가 발생했습니다: {str(e)}"


# 11) AuthenticationService 클래스 (사용자 인증 담당)
class AuthenticationService:
    @staticmethod
    def register_user(username, password):
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        try:
            conn = sqlite3.connect('safile.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
            conn.close()
            return True, "Success"
        except sqlite3.IntegrityError:
            return False, "Username already exists."

    @staticmethod
    def authenticate(username, password):
        conn = sqlite3.connect('safile.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user_row = cursor.fetchone()
        conn.close()
        
        if user_row and check_password_hash(user_row[2], password):
            return True, User(user_row[0], user_row[1])
        return False, None


# ----------------------------
# DB 테이블 초기화 함수
# ----------------------------
def init_db():
    conn = sqlite3.connect('safile.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
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

init_db()


# ============================================================
# [Flask 라우터 제어 영역]
# ============================================================

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        is_success, user_obj = AuthenticationService.authenticate(username, password)
        if is_success:
            session['user_id'] = user_obj.id
            session['username'] = user_obj.username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid username or password.")
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        is_success, error_msg = AuthenticationService.register_user(username, password)
        if is_success:
            return redirect(url_for('login'))
        else:
            return render_template('signup.html', error=error_msg)
    return render_template('signup.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# 🎯 대시보드 라우터 (선영님의 dashboard.html 스펙에 맞게 통계 쿼리 및 최근 내역 5개 연동)
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session.get('username', 'Admin')
    email = f"{username.lower()}@safile.local"  # 화면 가독성을 위한 가상 메일 포맷
    
    try:
        conn = sqlite3.connect('safile.db')
        cursor = conn.cursor()
        
        # 1. 상단 대시보드 위젯 카운팅 연동
        cursor.execute('SELECT COUNT(*) FROM history')
        total_uploads = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM history WHERE status = 'SAFE'")
        safe_files = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM history WHERE status = 'BLOCKED'")
        blocked_files = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM history WHERE status = 'WARNING'")
        warning_files = cursor.fetchone()[0]
        
        # 2. 하단 실시간 최근 이력(Recent Uploads) 5개 매핑 연동
        cursor.execute('SELECT filename, status, risk, timestamp FROM history ORDER BY timestamp DESC LIMIT 5')
        rows = cursor.fetchall()
        conn.close()
        
        recent_uploads = []
        for r in rows:
            recent_uploads.append({
                "filename": r[0],
                "result": r[1],  # SAFE, WARNING, BLOCKED 문자열 필터링 매칭
                "risk": r[2],    # LOW, MEDIUM, HIGH 위험도 텍스트 매칭
                "time": r[3]     # 타임스탬프 기록 매칭
            })
            
    except sqlite3.Error:
        total_uploads, safe_files, blocked_files, warning_files = 0, 0, 0, 0
        recent_uploads = []

    # html 변수명 배열 구조와 복수형 명칭까지 100% 동일하게 렌더링 전달
    return render_template(
        'dashboard.html', 
        username=username,
        email=email,
        total_uploads=total_uploads, 
        safe_files=safe_files, 
        blocked_files=blocked_files, 
        warning_files=warning_files,
        recent_uploads=recent_uploads
    )


# 파일 업로드 (2번 FileUpload 데이터 및 이중 확장자 보안 스캔 완벽 구동)
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
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

        if 'file' not in request.files:
            return jsonify({"filename": "No File", "status": "BLOCKED", "risk": "HIGH", "reason": "No file selected"})

        file = request.files['file']
        if file.filename == '':
            return jsonify({"filename": "No File", "status": "BLOCKED", "risk": "HIGH", "reason": "No file selected"})

        if file:
            filename = secure_filename(file.filename)
            
            # [2번 FileUpload 스펙 반영] 파일 정보 추출
            file_type = file.content_type  
            file.seek(0, os.SEEK_END)
            file_size = file.tell()        
            file.seek(0)                   
            
            file_obj = FileUpload(filename, file_type, file_size)

            policy = SecurityPolicy()
            # 🎯 업데이트된 이중 확장자 탐지 로직으로 정밀 보안 검사 수행
            scan_result = SecurityScanService.evaluate(file_obj.file_name, policy)

            if scan_result.status == 'WARNING':
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            elif scan_result.status == 'SAFE':
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            conn = sqlite3.connect('safile.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO history (filename, status, risk, reason) VALUES (?, ?, ?, ?)', 
                           (filename, scan_result.status, scan_result.risk_level, scan_result.blocked_reason))
            conn.commit()
            conn.close()

            return jsonify({
                "filename": filename, 
                "status": scan_result.status, 
                "risk": scan_result.risk_level, 
                "reason": scan_result.blocked_reason
            })

    return render_template('upload.html')


# 🎯 [8번 검색 구현] 파일명 검색 및 결과 부재 시 에러 메시지 출력 연동
@app.route('/history')
def history():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    search_keyword = request.args.get('search', '').strip()
    error_msg = ""
    
    if search_keyword:
        # HistorySearch 클래스를 호출하여 검색 수행
        records = HistorySearch.search_by_filename(search_keyword)
        if not records:
            error_msg = "검색 결과가 존재하지 않습니다."
    else:
        records = HistorySearch.get_all_history()
        
    return render_template('history.html', records=records, error_msg=error_msg)


# 🎯 [10번 필터 구현] SAFE, WARNING, BLOCKED 조건별 조회 라우터 추가
@app.route('/history/filter/<status>')
def history_filter(status):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    filtered_records = FileFilter.filter_by_status(status.upper())
    return render_template('history.html', records=filtered_records, error_msg="")


# 🎯 [11번 삭제 구현] 삭제 성공 여부 및 실패 메시지 관리 라우터 추가
@app.route('/history/delete/<int:record_id>', methods=['POST'])
def delete_history(record_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    success, msg = FileDeletion.delete_record(record_id)
    if success:
        flash("기록이 안전하게 삭제되었습니다.")
    else:
        flash(msg) # 에러 메시지 출력 처리 완료
        
    return redirect(url_for('history'))


@app.route('/result')
def result():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('result.html')


@app.route('/policy')
def policy():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('policy.html')


if __name__ == '__main__':
    app.run(debug=True, port=5001)