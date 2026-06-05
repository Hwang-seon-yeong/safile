<div align="center">

# **SAFILE**

### **Student No** 22412410  
### **Name** 황선영  
### **E-Mail** 0xsy54@gmail.com  

<br>

<img src="./images/logo.png" width="220"/>

</div>

---
# Design

### [ Revision history ]

| Revision date | Version # | Description | Author |
| --- | --- | --- | --- |
| 2026.06.05 | 1.0.0 | First Draft |  |
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |

---

# 1. Introduction

최근 웹 서비스에서는 파일 업로드 기능이 다양한 환경에서 사용되고 있다.  
예를 들어 과제 제출 시스템, 커뮤니티 게시판, 클라우드 저장소, 메신저 첨부파일 서비스 등 대부분의 웹 애플리케이션은 파일 업로드 기능을 제공한다.

하지만 파일 업로드 기능은 웹 보안 측면에서 매우 위험한 취약점이 될 수 있다. 공격자는 악성 실행 파일(.exe), 스크립트 파일(.php, .js), 또는 이중 확장자 파일(example.pdf.exe)과 같은 위험 파일을 업로드하여 서버 공격, 악성코드 실행, 정보 유출 등의 보안 문제를 발생시킬 수 있다.

본 프로젝트 “Safile”은 안전한 파일 업로드 환경을 제공하기 위한 보안 기반 웹 시스템이다. 사용자가 업로드한 파일의 확장자 및 파일 패턴을 검사하여 위험 파일 여부를 판단하고, 보안 정책에 따라 업로드를 허용하거나 차단한다. 또한 시스템은 위험 파일 탐지 결과, 차단 사유, 보안 경고 메시지 등을 사용자에게 제공하여 파일 업로드 과정에서 발생할 수 있는 보안 위협을 감소시키는 것을 목표로 한다.

Safile은 Flask 기반 웹 애플리케이션으로 구현되며, 로그인 시스템, 파일 업로드 기능, 업로드 기록 관리, 보안 정책 확인 기능 등을 포함한다. 또한 보안 중심의 대시보드 UI를 통해 사용자 친화적이면서도 실제 보안 서비스와 유사한 환경을 제공하도록 설계하였다.




# 2. Class Diagram

<p align="center">
  <img src="/images/class.png" width="100%">
</p>

## 1) AuthenticationService

### Description

AuthenticationService는 사용자 인증 및 회원가입 기능을 담당하는 클래스이다. 사용자가 시스템에 접근할 때 입력한 계정 정보를 검증하며, 회원가입 시 사용자 정보를 데이터베이스에 저장하는 역할을 수행한다. 비밀번호는 보안을 위해 암호화하여 저장한다.

### Operations

**register_user(username : String, password : String) : Boolean**

새로운 사용자를 등록하는 메소드이다. 입력받은 비밀번호를 암호화한 후 데이터베이스에 저장하며, 이미 존재하는 사용자 이름인 경우 등록을 거부한다. 등록 성공 시 true를 반환하고 실패 시 false를 반환한다.

**authenticate(username : String, password : String) : User**

로그인 시 사용되는 메소드이다. 데이터베이스에 저장된 사용자 정보를 조회하고 입력된 비밀번호와 비교하여 인증을 수행한다. 인증에 성공하면 User 객체를 반환하며, 실패 시 null 또는 오류를 반환한다.

---

## 2) User

### Description

User는 시스템 사용자 정보를 저장하는 클래스이다. 로그인, 회원가입 및 세션 관리 과정에서 사용되며 사용자 식별에 필요한 정보를 보관한다.

### Attributes

| Attribute | Type | Description |
|------------|------|-------------|
| id | int | 사용자의 고유 번호 |
| username | String | 로그인에 사용하는 사용자 아이디 |
| password | String | 암호화된 비밀번호 |

### Operations

**User(id : int, username : String, password : String)**

사용자 객체를 생성하는 생성자이다.

---

## 3) FileUpload

### Description

FileUpload는 사용자가 업로드한 파일의 정보를 저장하는 클래스이다. 파일명, 파일 형식(MIME Type), 파일 크기 등을 관리하며 보안 검사 과정에서 활용된다.

### Attributes

| Attribute | Type | Description |
|------------|------|-------------|
| file_name | String | 업로드된 파일명 |
| file_type | String | 파일의 MIME 타입 |
| file_size | int | 파일의 크기 |

### Operations

**FileUpload(file_name : String, file_type : String, file_size : int)**

파일 정보를 초기화하는 생성자이다.

---

## 4) SecurityPolicy

### Description

SecurityPolicy는 파일 보안 정책을 정의하는 클래스이다. 시스템에서 위험하다고 판단하는 확장자 목록을 관리하며 보안 검사의 기준으로 사용된다.

### Attributes

| Attribute | Type | Description |
|------------|------|-------------|
| blocked_extensions | List | 업로드를 차단할 위험 확장자 목록 (exe, bat, cmd, sh, msi 등) |

### Operations

**SecurityPolicy()**

보안 정책을 초기화하는 생성자이다.

---

## 5) SecurityScanService

### Description

SecurityScanService는 SAFILE 시스템의 핵심 보안 검사 클래스이다. 사용자가 업로드한 파일을 분석하여 악성 파일 여부를 검사하고 결과를 반환한다. 일반 확장자 검사뿐 아니라 이중 확장자 위장 공격(Double Extension Attack) 탐지 기능도 수행한다.

### Operations

**evaluate(filename : String, policy : SecurityPolicy) : ScanResult**

파일명을 분석하여 보안 검사를 수행하는 메소드이다. 정책에 정의된 위험 확장자를 탐지하며, 이중 확장자 위장 공격 여부를 확인한다. 검사 결과는 ScanResult 객체로 반환된다.

---

## 6) ScanResult

### Description

ScanResult는 파일 검사 결과를 저장하는 클래스이다. 보안 검사 이후 파일의 상태, 위험도, 차단 사유 등을 관리한다.

### Attributes

| Attribute | Type | Description |
|------------|------|-------------|
| status | String | 검사 상태 (SAFE, WARNING, BLOCKED) |
| risk_level | String | 파일의 위험도 (LOW, MEDIUM, HIGH) |
| blocked_reason | String | 차단 또는 경고가 발생한 이유 |

### Operations

**ScanResult(status : String, risk_level : String, blocked_reason : String)**

검사 결과 객체를 생성하는 생성자이다.

---

## 7) SecurityAlert

### Description

SecurityAlert는 보안 검사 결과를 사용자에게 알리는 클래스이다. 검사 결과에 따라 적절한 경고 메시지 또는 안내 메시지를 생성한다.

### Operations

**generate_alert(status : String, reason : String) : String**

검사 결과를 기반으로 사용자에게 표시할 메시지를 생성한다. 차단 파일은 경고 메시지를 출력하고, 안전한 파일은 정상 안내 메시지를 출력한다.

---

## 8) UploadRecord

### Description

UploadRecord는 업로드 이력을 저장하는 클래스이다. 사용자가 업로드한 파일의 검사 결과를 기록하며, History 기능에서 조회된다.

### Attributes

| Attribute | Type | Description |
|------------|------|-------------|
| id | int | 업로드 기록 번호 |
| filename | String | 업로드된 파일명 |
| status | String | 검사 결과 상태 |
| risk | String | 위험도 |
| reason | String | 검사 결과 사유 |
| timestamp | DateTime | 업로드 시각 |

### Operations

**UploadRecord(id : int, filename : String, status : String, risk : String, reason : String, timestamp : DateTime)**

업로드 기록 객체를 생성하는 생성자이다.

---

## 9) HistorySearch

### Description

HistorySearch는 업로드 기록 검색 기능을 담당하는 클래스이다. 사용자가 이전 검사 결과를 조회하거나 특정 파일명을 검색할 때 사용된다.

### Operations

**get_all_history() : List**

저장된 모든 업로드 기록을 조회하는 메소드이다.

**search_by_filename(keyword : String) : List**

파일명을 기준으로 업로드 기록을 검색하는 메소드이다.

---

## 10) FileFilter

### Description

FileFilter는 업로드 기록을 상태별로 조회하는 클래스이다. 사용자가 SAFE, WARNING, BLOCKED 상태에 따라 기록을 분류하여 확인할 수 있도록 지원한다.

### Operations

**filter_by_status(status_criterion : String) : List**

지정된 상태값을 기준으로 업로드 기록을 필터링하는 메소드이다.

---

## 11) FileDeletion

### Description

FileDeletion은 업로드 기록 삭제 기능을 담당하는 클래스이다. 사용자가 더 이상 필요하지 않은 업로드 기록을 삭제할 수 있도록 지원한다.

### Operations

**delete_record(record_id : int) : Boolean**

지정된 업로드 기록을 삭제하는 메소드이다. 삭제 성공 시 true를 반환하며 실패 시 false를 반환한다.

---

### Class Relationship Summary

- AuthenticationService는 User 객체를 생성하고 인증한다.
- FileUpload는 업로드된 파일 정보를 저장하며 SecurityScanService에 전달된다.
- SecurityScanService는 SecurityPolicy를 참조하여 파일을 검사한다.
- 검사 결과는 ScanResult 객체로 생성된다.
- SecurityAlert는 ScanResult 정보를 이용하여 사용자에게 알림 메시지를 생성한다.
- 검사 결과는 UploadRecord에 저장된다.
- HistorySearch는 UploadRecord를 조회 및 검색한다.
- FileFilter는 UploadRecord를 상태별로 필터링한다.
- FileDeletion은 UploadRecord를 삭제한다.  
  



---

# 3. Sequence Diagram

## 1. User Signup Process

<p align="center">
  <img src="./images/s1.png" width="100%">
</p>

* **설명**: 사용자가 회원가입 요청을 보내면 `AuthenticationService`가 `Database`를 조회하여 ID 중복 여부를 확인합니다.
* **핵심 로직**: ID가 존재하지 않을 경우에만 가입이 진행되며, `CombinedFragment1`을 통해 비밀번호 길이 제한(8자 미만 오류) 검증 후, 비밀번호를 해싱(HashPassword)하여 데이터베이스에 저장합니다.

---

## 2. User Login Process

<p align="center">
  <img src="/images/s2.png" width="100%">
</p>

* **설명**: 사용자가 인증을 요청하면 `AuthenticationService`는 사용자 정보를 조회하여 유효성을 검증합니다.
* **핵심 로직**: `Login Checkout` 프래그먼트를 통해 사용자 존재 여부 및 비밀번호 일치를 확인하며, 검증 성공 시 `User Object`를 반환하여 로그인 상태를 유지합니다.


---

## 3. File Upload Process

<p align="center">
  <img src="./images/s3.png" width="100%">
</p>

* **설명**: `:FileUpload` 객체가 `:SecurityScanService`에 파일 평가를 요청하면 확장자 검사(checkExtension)를 수행합니다.
* **핵심 로직**: 검사 결과(`Process`)에 따라 상태가 `.OK`일 경우 기록을 저장하고, `Block`일 경우 에러를 반환하여 보안 정책을 준수합니다.

---

## 4. Security Scan Process

<p align="center">
  <img src="./images/s4.png" width="100%">
</p>

* **설명**: 파일 업로드 시 수행되는 상세 보안 검사 흐름입니다.
* **핵심 로직**: `SecurityPolicy`를 참조하여 차단된 확장자인지 먼저 판단하며(break block), 추가적으로 이중 확장자 검사 및 보안 경고 생성을 수행하여 파일의 안전성을 검증합니다.

---

## 5. Record Deletion Process

<p align="center">
  <img src="./images/s5.png" width="100%">
</p>

* **설명**: 사용자가 `:WebUI`를 통해 기록 삭제를 요청하면 `:HistoryService`가 데이터베이스를 제어합니다.
* **핵심 로직**: `alt` 프래그먼트를 통해 기록 존재 여부를 확인합니다. 기록이 존재하면 삭제를 수행하고 성공 메시지를, 존재하지 않으면 에러 메시지를 UI에 전달합니다.
---

## 6. History Search Process

<p align="center">
  <img src="./images/s6.jpeg" width="100%">
</p>

* **설명**: 사용자가 :WebUI를 통해 기록 삭제를 요청하면 :HistoryService가 데이터베이스를 제어합니다.
핵심 로직: alt 프래그먼트를 통해 기록 존재 여부를 확인합니다. 기록이 존재하면 삭제를 수행하고 성공 메시지를, 존재하지 않으면 에러 메시지를 UI에 전달합니다.
* **핵심 로직**: 기록 존재 여부를 확인합니다. 기록이 존재하면 삭제를 수행하고 성공 메시지를, 존재하지 않으면 에러 메시지를 UI에 전달합니다.



------

# 4. State Machine Diagram

<p align="center">
  <img src="./images/state.png" width="100%">
</p>

### Description

State Machine Diagram은 시스템의 상태 변화 과정을 나타낸다.

### State Transition

1. 사용자는 로그인 또는 회원가입 상태로 진입한다.
2. 인증 성공 후 메인 화면으로 이동한다.
3. 파일 업로드를 수행한다.
4. 보안 검사를 수행한다.
5. 검사 결과를 저장한다.
6. 사용자는 이력을 조회하거나 삭제할 수 있다.
7. 로그아웃 후 시스템을 종료한다.

---

# 5. Implementation Requirements

## Hardware Requirements

| Component | Requirement |
|------------|------------|
| CPU | Dual-Core Processor 2.0GHz 이상 |
| RAM | 2GB 이상 (권장 4GB 이상) |
| Storage | 10GB 이상 |

## Software Requirements

| Component | Requirement |
|------------|------------|
| Operating System | Windows 10/11, Linux, macOS |
| Language | Python 3.9 이상 |
| Framework | Flask 2.0 이상 |
| Database | SQLite3 |
| Package Manager | pip |

---

# 6. Glossary

| Term | Description |
|--------|-------------|
| Attribute | 클래스 내부에 정의된 데이터 변수 |
| Class Diagram | 시스템의 정적 구조를 표현하는 UML 다이어그램 |
| Method | 클래스 내부 기능을 수행하는 함수 |
| Operation | 객체가 수행하는 동작 |
| Database | 데이터를 저장하고 관리하는 시스템 |
| Flask | Python 기반 웹 프레임워크 |
| Sequence Diagram | 객체 간 상호작용을 시간 순서로 표현한 UML 다이어그램 |
| Session | 사용자 로그인 상태를 유지하기 위한 저장 공간 |
| Security Policy | 파일 검사를 위한 보안 규칙 |
| Double Extension Attack | 이중 확장자를 이용한 파일 위장 공격 |
| Scan Result | 파일 검사 결과 |

---

# 7. References

1. Ian Sommerville, *Software Engineering*, 10th Edition, Pearson.

2. Roger S. Pressman, *Software Engineering: A Practitioner's Approach*, McGraw-Hill.

3. Flask Documentation  
   https://flask.palletsprojects.com

4. Python Documentation  
   https://docs.python.org

5. SQLite Documentation  
   https://sqlite.org

6. OWASP File Upload Security Cheat Sheet  
   https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html

7. UML Specification (OMG)  
   https://www.omg.org/spec/UML/