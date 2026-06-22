 

# 🛡️ SAFILE: Secure File Upload System

**SAFILE**은 안전한 파일 업로드 환경을 제공하기 위해 설계된 보안 기반 웹 시스템입니다. 단순한 확장자 검사를 넘어, 파일의 본질(MIME Type 및 매직 넘버)을 분석하여 악성 파일의 유입을 원천 차단합니다.

## 📑 프로젝트 개요 (Introduction)

현대 웹 서비스의 필수 기능인 '파일 업로드'는 해커의 주요 공격 경로입니다. **SAFILE**은 사용자가 업로드한 파일의 확장자 위장(Spoofing) 및 악성코드 실행 시도를 분석하고, 보안 정책에 따라 이를 탐지·차단하여 서버를 보호합니다.

- **Core Technology:** Flask, Python, SQLite3, Magic Number(MIME) Detection
- **Security Focus:** 본질 기반 검사(Content-based Analysis), 이중 확장자 탐지, 보안 감사 로그(History) 기록

## ✨ Features

- **본질 기반 검증 (MIME Detection):** 파일 헤더의 매직 넘버(`MZ` 등)를 분석하여 실제 실행 파일 여부를 판별합니다.
- **이중 확장자 방어:** `test.jpg.exe`와 같은 악성 파일의 은닉 기법을 정규표현식으로 차단합니다.
- **보안 감사 기록 (Security Audit):** 모든 차단 시도를 DB(`sqlite3`)에 기록하여 관리자가 공격 패턴을 추적할 수 있습니다.
- **무결성 보호:** 악성 파일은 서버 디스크에 저장하지 않고 즉시 폐기하여 공격 흔적을 원천 차단합니다.

## 🚀 Quick Start

Bash

```
# 서버 실행
python app.py
```

### 🧭 테스트 가이드

1. **로그인:** 접속 (계정: abc@gmail.com / 비밀번호:`12345678`)
2. **차단 테스트:** 내용물이 `MZ`로 시작하는 파일(윈도우 실행 파일)의 이름을 `.jpg`로 바꿔 업로드합니다.
3. **결과 확인:** 화면에 `BLOCKED` 메시지가 뜨는지, 그리고 `History` 탭에 차단 기록이 남았는지 확인합니다.

## 📋 Security Policies

| **정책 항목** | **설명** |
| --- | --- |
| **MIME Validation** | `application/x-dosexec` 등 실행 파일 형식 차단 |
| **Name Spoofing** | 이중 확장자 및 공백을 이용한 우회 공격 탐지 |
| **Non-Persistent Storage** | 차단된 파일은 디스크에 저장하지 않음 |

## 📁 Project Structure

Plaintext

```
safile/
├── app.py             # Flask 메인 라우터 및 보안 검사 흐름
├── models.py          # 보안 정책 및 검사 서비스 로직
├── safile.db          # 공격 이력 기록용 데이터베이스
├── templates/         # HTML 대시보드 및 업로드 페이지
└── static/            # CSS/JS 디자인 소스
```

## 🗺️ Roadmap & Help Wanted

이 시스템은 더 강력한 보안 도구로 발전하기 위해 다음 기능을 준비 중입니다.

- 🔍 **바이러스 스캔 API:** 외부 보안 API(ClamAV 등) 연동 기능
- 📊 **실시간 보안 대시보드:** 공격 빈도 시각화 차트 추가
- 🔐 **암호화:** 안전한 파일 저장 시 자동 암호화 적용
- 🛡️ **IPS 연동:** 동일 IP의 연속적인 공격 시도 자동 IP 차단

##
