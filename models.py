from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Flask 앱과 연동할 SQLAlchemy 객체 생성
db = SQLAlchemy()

# ============================================================
# [데이터 구조 클래스 정의 영역 - models.py 구현체]
# ============================================================

# 1) User 클래스 (사용자 정보 테이블)
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)   # 사용자 아이디
    password = db.Column(db.String(200), nullable=False)              # 암호화된 비밀번호
    email = db.Column(db.String(120), nullable=True)                  # 이메일 (선택 변수)


# 2) FileUpload 클래스 (업로드된 파일 메타데이터 테이블)
class FileUpload(db.Model):
    __tablename__ = 'file_uploads'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    file_name = db.Column(db.String(255), nullable=False)             # 파일 이름
    file_type = db.Column(db.String(100), nullable=True)              # 파일 타입 (MIME)
    file_size = db.Column(db.Integer, nullable=True)                  # 파일 크기 (Byte)


# 3) ScanResult 클래스 (보안 스캔 결과 테이블)
class ScanResult(db.Model):
    __tablename__ = 'scan_results'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    status = db.Column(db.String(20), nullable=False)                 # SAFE, WARNING, BLOCKED
    risk_level = db.Column(db.String(20), nullable=False)             # LOW, MEDIUM, HIGH
    blocked_reason = db.Column(db.String(255), nullable=False)         # 상세 차단 사유


# 4) UploadRecord 클래스 (User, FileUpload, ScanResult를 연결하는 이력 영수증)
class UploadRecord(db.Model):
    __tablename__ = 'upload_records'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # 외래키(Foreign Key) 설정으로 데이터 간의 관계를 촘촘하게 연결
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    file_id = db.Column(db.Integer, db.ForeignKey('file_uploads.id', ondelete='CASCADE'), nullable=False)
    scan_result_id = db.Column(db.Integer, db.ForeignKey('scan_results.id', ondelete='CASCADE'), nullable=False)
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)       # 업로드 일시


    # 💡 [객체지향 설계 핵심] 파이썬 코드상에서 관계성을 직관적으로 조회할 수 있게 매핑
    user = db.relationship('User', backref=db.backref('records', lazy=True))
    file = db.relationship('FileUpload', backref=db.backref('records', lazy=True))
    scan_result = db.relationship('ScanResult', backref=db.backref('records', lazy=True))