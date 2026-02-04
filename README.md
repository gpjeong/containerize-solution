# Dockerfile Generator

웹 서비스용 Dockerfile을 자동으로 생성하는 도구입니다. 소스코드나 빌드된 아티팩트를 분석하고, 사용자 설정을 결합하여 프로덕션에 최적화된 Dockerfile을 생성합니다.

## 지원하는 기술 스택

### Python

- FastAPI (uvicorn)
- Flask (gunicorn)
- Django (gunicorn)

### Node.js

- Express
- NestJS
- Next.js

### Java

- Spring Boot (JAR)

## 주요 기능

- **파일 업로드**: Java JAR 파일을 업로드하여 자동 분석
- **설정 입력**: Python/Node.js는 requirements.txt 또는 package.json 내용 입력
- **커스터마이징**: 런타임 버전, 포트, 환경변수, Health Check 경로 등 설정
- **멀티스테이지 빌드**: 최적화된 Docker 이미지 생성
- **보안**: Non-root 사용자, Health Check 포함
- **미리보기 및 편집**: 생성된 Dockerfile을 CodeMirror 에디터로 확인하고 수정
- **다운로드**: 생성된 Dockerfile 다운로드

## 빠른 시작

### 로컬 개발 (Python)

```bash
# 1. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 의존성 설치
cd backend
pip install -r requirements.txt

# 3. 애플리케이션 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 4. 브라우저에서 열기
# http://localhost:8000
```

### Docker로 실행

```bash
# 1. Docker Compose로 실행
docker-compose up --build

# 2. 브라우저에서 열기
# http://localhost:8000
```

## 사용 방법

### 1. 언어 선택

Python, Node.js, Java 중 선택

### 2. 프레임워크 및 입력

- **Java**: JAR 파일 업로드 (선택사항)
- **Python**: 프레임워크 선택 및 requirements.txt 내용 입력
- **Node.js**: 프레임워크 선택 및 package.json 내용 입력

### 3. Docker 설정

- 런타임 버전 (예: Python 3.11, Node 20, Java 17)
- 포트 번호
- 환경 변수
- Health Check 경로
- 시스템 의존성 패키지
- Base Image (선택사항)

### 4. 생성 및 다운로드

- Dockerfile 생성
- CodeMirror 에디터로 미리보기 및 편집
- 다운로드 또는 클립보드에 복사

## API 엔드포인트

### `POST /api/upload/java`

JAR/WAR 파일 업로드 및 분석

### `POST /api/analyze/python`

Python 프로젝트 설정 분석

### `POST /api/analyze/nodejs`

Node.js 프로젝트 설정 분석

### `POST /api/generate`

Dockerfile 생성

### `GET /api/download/{session_id}`

생성된 Dockerfile 다운로드

### `GET /api/templates`

지원하는 템플릿 목록 조회

### `GET /api/docs`

자동 생성된 API 문서 (Swagger UI)

## 프로젝트 구조

```
containerize-tool/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 애플리케이션
│   │   ├── config.py            # 설정
│   │   ├── models/              # Pydantic 스키마
│   │   ├── services/            # 비즈니스 로직
│   │   │   ├── file_analyzer.py
│   │   │   ├── dockerfile_generator.py
│   │   │   └── template_engine.py
│   │   ├── templates/           # Jinja2 템플릿
│   │   │   ├── python/
│   │   │   ├── nodejs/
│   │   │   └── java/
│   │   ├── api/                 # API 엔드포인트
│   │   └── utils/               # 유틸리티
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html
│   └── js/
│       └── app.js
├── uploads/                     # 임시 파일 저장소
├── docker-compose.yml
└── README.md
```

## 보안 기능

- **다층 파일 검증**: 확장자, Content-Type, Magic Number 검증
- **파일 크기 제한**: 최대 500MB
- **파일명 Sanitization**: 경로 탐색 공격 방지
- **Non-root 사용자**: 생성된 Dockerfile에서 non-root 사용자 사용
- **자동 파일 정리**: 1시간 후 임시 파일 자동 삭제

## 환경 변수

```bash
ENVIRONMENT=development          # development 또는 production
LOG_LEVEL=INFO                  # 로그 레벨
MAX_UPLOAD_SIZE=524288000       # 최대 업로드 크기 (바이트)
```

## 개발

### 테스트 실행

```bash
cd backend
pytest
```

### 새로운 템플릿 추가

1. `backend/app/templates/{language}/` 디렉터리에 `.dockerfile.j2` 파일 추가
2. `dockerfile_generator.py`의 `template_map`에 매핑 추가
3. 필요한 경우 `file_analyzer.py`에 분석 로직 추가

## 라이센스

MIT License

## 기여

이슈와 풀 리퀘스트를 환영합니다!
