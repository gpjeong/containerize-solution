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

### 핵심 기능

- **JAR 파일 업로드**: Java JAR 파일을 업로드하여 자동 분석 (실제 파일명 자동 반영)
- **간편한 설정**: 필수 설정만 입력하면 바로 생성 가능
- **선택적 기능**: Health Check, 환경변수, 시스템 의존성은 체크박스로 선택
- **보안**: Non-root 사용자 자동 설정
- **미리보기 및 편집**: CodeMirror 에디터로 실시간 확인 및 수정
- **다운로드**: 생성된 Dockerfile 다운로드 또는 클립보드 복사
- **Jenkins 통합**: 생성된 Dockerfile을 Jenkins API를 통해 자동 빌드

### Jenkins CI/CD 통합 (NEW!)

- **자동 빌드**: Dockerfile 생성 후 Jenkins에서 즉시 빌드
- **Pipeline 자동 생성**: Groovy Pipeline 스크립트 자동 생성 및 배포
- **Git 통합**: Git 저장소에서 소스코드 자동 체크아웃
- **안전한 전송**: Base64 인코딩 및 CSRF 토큰 자동 처리
- **SSL 지원**: 자체 서명 인증서 환경 지원
- **가독성 높은 UI**: 빌드 성공 시 클릭 가능한 Jenkins URL 제공
- **스마트 초기화**: 언어 전환 시 모든 입력 필드 자동 초기화

### UI 개선

- **시각적 언어 선택**: 실제 언어 로고 표시 및 선택 상태 하이라이트
- **언어별 맞춤 플레이스홀더**: Python/Node.js 각각에 맞는 예시 표시
- **커스텀 알림 모달**: 브라우저 기본 alert 대체, HTML 형식 지원
- **폐쇄망 지원**: 모든 아이콘 및 리소스 로컬 저장
- **스마트 입력 초기화**: 언어 전환 시 모든 필드 자동 초기화
- **Jenkins 빌드 알림**: 가독성 높은 성공 메시지 및 클릭 가능한 URL

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

Python, Node.js, Java 중 선택 (로고 아이콘으로 시각적 표시)

### 2. 입력 방식

#### Python / Node.js

바로 설정 단계로 이동하여 다음을 입력:

- Base Image (필수)
- 포트 (필수)
- 서비스 URL (필수)
- 실행 명령어 (필수, 언어별 예시 표시)

#### Java

1. JAR 파일 업로드
2. 설정 단계에서 다음을 입력:
   - Base Image (필수)
   - 포트 (필수)
   - 서비스 URL (필수)
   - 실행 명령어 (필수)

### 3. 선택 설정 (모든 언어)

체크박스로 활성화:

- **환경 변수**: KEY=VALUE 형식으로 입력
- **Health Check**: 헬스체크 경로 (기본: /health)
- **시스템 의존성**: 공백으로 구분된 패키지명

### 4. 생성 및 다운로드

- "Dockerfile 생성" 버튼 클릭
- CodeMirror 에디터로 미리보기 및 편집
- "다운로드" 또는 "클립보드에 복사" 선택
- "🔄 Dockerfile 재생성"으로 처음부터 다시 시작

### 5. Jenkins 자동 빌드 (선택사항)

Dockerfile 생성 후 Jenkins에서 자동으로 빌드하려면:

1. **Jenkins 준비사항**
   - Jenkins에서 Pipeline Job 미리 생성
   - Git 저장소에 소스코드 업로드
   - Jenkins API Token 발급

2. **Jenkins 빌드 설정**
   - Jenkins URL 입력
   - Jenkins Job 이름 입력
   - Jenkins 사용자명 및 API 토큰 입력
   - Git Repository URL 및 브랜치 입력
   - Docker Image 이름 및 태그 입력

3. **빌드 실행**
   - "Jenkins에서 빌드하기" 버튼 클릭
   - 빌드 성공 메시지 확인
   - "Jenkins에서 빌드 확인하기" 버튼을 클릭하여 새 탭에서 Jenkins 콘솔 열기
   - Jenkins 콘솔에서 실시간 빌드 진행 상황 확인

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

### `POST /api/build/jenkins`

Jenkins 빌드 트리거 (Dockerfile 자동 빌드)

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
│   │   │   ├── template_engine.py
│   │   │   ├── jenkins_client.py         # Jenkins API 클라이언트
│   │   │   └── pipeline_generator.py     # Pipeline 스크립트 생성
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
│   └── static/
│       ├── js/
│       │   └── app.js
│       └── icons/
│           ├── python.svg
│           ├── nodejs.svg
│           └── java.svg
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
