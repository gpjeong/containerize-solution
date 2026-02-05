# 기능 설명서 (Features Documentation)

## 목차
- [개요](#개요)
- [지원 기술 스택](#지원-기술-스택)
- [주요 기능](#주요-기능)
- [사용 시나리오](#사용-시나리오)
- [생성되는 Dockerfile 특징](#생성되는-dockerfile-특징)
- [API 명세](#api-명세)

---

## 개요

**Dockerfile Generator**는 웹 서비스용 Dockerfile을 자동으로 생성하는 웹 애플리케이션입니다.
소스코드나 빌드된 아티팩트를 분석하고, 사용자의 설정을 결합하여 프로덕션에 최적화된 Dockerfile을 생성합니다.

### 핵심 가치
- ⚡ **빠른 컨테이너화**: 복잡한 Dockerfile 작성 없이 몇 번의 클릭으로 생성
- 🔒 **보안 모범 사례**: Non-root 사용자, Health Check 자동 포함
- 🎯 **멀티스테이지 빌드**: 최적화된 이미지 크기
- 🛠️ **커스터마이징**: 모든 설정을 사용자가 제어 가능

---

## 지원 기술 스택

### Python
| 프레임워크 | 서버 | 특징 |
|-----------|------|------|
| **FastAPI** | uvicorn | 고성능 비동기 API 프레임워크 |
| **Flask** | gunicorn | 경량 마이크로 프레임워크 |
| **Django** | gunicorn | 풀스택 웹 프레임워크 |

**자동 감지 기능:**
- requirements.txt 파싱
- 프레임워크 자동 감지 (dependencies 분석)
- 적절한 서버 자동 선택

### Node.js
| 프레임워크 | 패키지 매니저 | 특징 |
|-----------|-------------|------|
| **Express** | npm/yarn/pnpm | 미니멀 웹 프레임워크 |
| **NestJS** | npm/yarn/pnpm | TypeScript 기반 프로그레시브 프레임워크 |
| **Next.js** | npm/yarn/pnpm | React 기반 풀스택 프레임워크 |

**자동 감지 기능:**
- package.json 파싱
- 프레임워크 자동 감지
- 패키지 매니저 감지 (npm, yarn, pnpm)
- 빌드/시작 명령어 추출

### Java
| 입력 방식 | 특징 |
|----------|------|
| **JAR 파일** | 빌드된 Fat JAR 파일 업로드 |

**자동 감지 기능:**
- JAR 파일에서 MANIFEST.MF 추출
- Spring Boot 버전 감지
- Main Class 자동 탐지
- Fat JAR vs Thin JAR 구분
- 업로드한 파일명 자동 반영

---

## 주요 기능

### 1. 언어 및 프레임워크 선택

#### 1.1 Python
**입력 방식:**
- 프레임워크 선택 (FastAPI/Flask/Django)
- requirements.txt 내용 붙여넣기 (선택사항)

**자동 처리:**
```python
# requirements.txt 예시
fastapi==0.115.0
uvicorn[standard]==0.32.0
pydantic==2.10.0

→ FastAPI 자동 감지
→ uvicorn 서버 자동 선택
→ 의존성 자동 설치
```

#### 1.2 Node.js
**입력 방식:**
- 프레임워크 선택 (Express/NestJS/Next.js)
- package.json 내용 붙여넣기 (선택사항)

**자동 처리:**
```json
{
  "dependencies": {
    "next": "^14.0.0"
  },
  "packageManager": "pnpm@8.0.0"
}

→ Next.js 자동 감지
→ pnpm 패키지 매니저 자동 선택
→ 빌드 명령어 추출
```

#### 1.3 Java
**입력 방식:**

**JAR 파일 업로드**
```
app.jar 업로드
→ MANIFEST.MF 분석
→ Spring Boot 감지
→ Main Class 추출
→ 실제 파일명 자동 반영
```

**특징:**
- 업로드한 JAR 파일의 실제 파일명이 Dockerfile에 자동으로 반영됩니다
- 예: `my-spring-app-2.0.0.jar` 업로드 시 → `COPY my-spring-app-2.0.0.jar app.jar`

### 2. Docker 설정

#### 2.1 필수 설정 (Python/Node.js)
| 설정 항목 | 설명 | 예시 |
|----------|------|------|
| **Base Image** | Docker 베이스 이미지 | python:3.11-slim, node:20-alpine |
| **포트** | 서비스 포트 | Python: 8000, Node: 3000 |
| **서비스 URL** | 배포될 서비스 URL | https://api.example.com |
| **실행 명령어** | 컨테이너 시작 명령어 | uvicorn main:app --host 0.0.0.0 --port 8000 |

#### 2.2 필수 설정 (Java)
| 설정 항목 | 설명 | 예시 |
|----------|------|------|
| **Base Image** | Docker 베이스 이미지 | eclipse-temurin:17-jre-alpine |
| **포트** | 서비스 포트 | 8080 |
| **서비스 URL** | 배포될 서비스 URL | https://api.example.com |
| **실행 명령어** | 컨테이너 시작 명령어 | java -jar app.jar |

#### 2.3 선택 설정

**모든 언어에서 다음 설정은 선택사항입니다:**
- **환경 변수**: 체크박스로 활성화
- **Health Check**: 체크박스로 활성화
- **시스템 의존성 패키지**: 체크박스로 활성화

#### 2.4 환경 변수 (선택사항)
**입력 형식:**
```
ENV=production
DEBUG=false
DATABASE_URL=postgresql://localhost/mydb
API_KEY=your-api-key
```

**Dockerfile 변환:**
```dockerfile
ENV ENV="production"
ENV DEBUG="false"
ENV DATABASE_URL="postgresql://localhost/mydb"
ENV API_KEY="your-api-key"
```

#### 2.5 Health Check (선택사항)
**기본값:**
```
/health
```

**커스터마이징 가능:**
```
/actuator/health  # Spring Boot
/api/health       # 커스텀 경로
```

#### 2.6 시스템 의존성 (선택사항)
**입력 형식:**
```
curl wget git
```

**Dockerfile 변환 (Python/Java):**
```dockerfile
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*
```

**Dockerfile 변환 (Node.js):**
```dockerfile
RUN apk add --no-cache curl wget git
```

#### 2.7 UI 개선사항

**언어 선택:**
- 각 언어별 실제 로고 아이콘 표시 (Python, Node.js, Java)
- 선택된 언어 시각적 표시 (색상 하이라이트)
- 폐쇄망에서도 작동 (로컬 SVG 파일 사용)

**입력 플레이스홀더:**
- 언어별 맞춤형 예시 표시
- Python: `uvicorn main:app --host 0.0.0.0 --port 8000`
- Node.js: `node server.js`

**알림:**
- 커스텀 모달 팝업 (브라우저 기본 alert 대체)
- 성공/오류 구분 표시 (✅/⚠️)

**재생성:**
- "🔄 Dockerfile 재생성" 버튼
- 커스텀 확인 모달

### 3. Dockerfile 생성 및 미리보기

#### 3.1 실시간 미리보기
- **신택스 하이라이팅**: CodeMirror 에디터 사용
- **편집 가능**: 생성 후 수정 가능
- **라인 넘버**: 코드 라인 번호 표시

#### 3.2 다운로드 옵션
- **파일 다운로드**: "Dockerfile" 이름으로 저장
- **클립보드 복사**: 원클릭으로 복사

#### 3.3 세션 관리
- 생성된 Dockerfile은 1시간 동안 저장
- 세션 ID로 관리
- 자동 정리 (1시간 후)

### 4. Jenkins 통합 (자동 빌드)

#### 4.1 개요
생성된 Dockerfile을 Jenkins API를 통해 자동으로 빌드할 수 있습니다. 사용자가 Jenkins에서 Pipeline Job을 미리 생성해두면, 이 솔루션이 자동으로 Pipeline 스크립트를 생성하고 Jenkins에 전달하여 Docker 이미지를 빌드합니다.

#### 4.2 주요 기능
- **Pipeline 스크립트 자동 생성**: Dockerfile 기반으로 Groovy Pipeline 스크립트 자동 생성
- **Jenkins API 통합**: CSRF 토큰 자동 처리 및 인증
- **Git 통합**: Git 저장소에서 소스코드 체크아웃
- **자동 빌드 트리거**: Pipeline 업데이트 및 빌드 자동 실행
- **Base64 인코딩**: Dockerfile 내용을 안전하게 Jenkins에 전달

#### 4.3 필수 설정
| 설정 항목 | 설명 | 예시 |
|----------|------|------|
| **Jenkins URL** | Jenkins 서버 주소 | https://jenkins.example.com |
| **Jenkins Job 이름** | 미리 생성된 Pipeline Job 이름 | my-docker-build-job |
| **Jenkins 사용자명** | Jenkins 사용자 계정 | admin |
| **Jenkins API 토큰** | Jenkins API Token | 11abcd1234567890abcdef |
| **Git Repository URL** | 소스코드 저장소 URL | https://github.com/user/repo.git |
| **Git Branch** | Git 브랜치 이름 | main |
| **Git Credential ID** | Jenkins에 등록된 Git 인증 정보 ID (선택) | git-credentials |
| **Docker Image 이름** | 빌드할 이미지 이름 | my-app |
| **Docker Image 태그** | 이미지 태그 | latest |

#### 4.4 동작 방식
```
1. 사용자가 Dockerfile 생성 완료
2. Jenkins 빌드 섹션에서 설정 입력
3. "Jenkins에서 빌드하기" 버튼 클릭
4. 백엔드에서 처리:
   a. Dockerfile 생성
   b. Pipeline 스크립트 생성 (Base64 인코딩)
   c. Jenkins Crumb(CSRF 토큰) 가져오기
   d. Jenkins Job의 config.xml 업데이트
   e. 빌드 트리거
5. Jenkins에서 자동 실행:
   a. Git Repository 체크아웃
   b. Dockerfile 생성 (Base64 디코딩)
   c. Docker 이미지 빌드
   d. 이미지 검증
```

#### 4.5 생성되는 Pipeline 스크립트 구조
```groovy
pipeline {
    agent any

    parameters {
        string(name: 'IMAGE_NAME', defaultValue: 'my-app')
        string(name: 'IMAGE_TAG', defaultValue: 'latest')
    }

    stages {
        stage('Checkout') {
            // Git 저장소에서 소스코드 체크아웃
        }

        stage('Create Dockerfile') {
            // Base64로 인코딩된 Dockerfile 디코딩 및 생성
        }

        stage('Build Docker Image') {
            // Docker 이미지 빌드
        }

        stage('Verify Image') {
            // 빌드된 이미지 검증
        }
    }

    post {
        success { /* 빌드 성공 메시지 */ }
        failure { /* 빌드 실패 메시지 */ }
    }
}
```

#### 4.6 보안 기능
- **SSL 인증서 검증**: 자체 서명 인증서 지원 (SSL 검증 비활성화 옵션)
- **CSRF 보호**: Jenkins Crumb 자동 처리
- **API Token 인증**: HTTPBasicAuth 사용
- **안전한 데이터 전송**: Base64 인코딩으로 특수문자 처리
- **CDATA 섹션**: XML 파싱 문제 방지

#### 4.7 에러 처리
| 에러 | 원인 | 해결 방법 |
|------|------|----------|
| SSL 인증 실패 | 자체 서명 인증서 | SSL 검증 자동 비활성화 |
| CSRF 토큰 오류 | Jenkins CSRF 보호 활성화 | Crumb 자동 가져오기 |
| 인증 실패 | API 토큰 오류 | 올바른 사용자명/토큰 확인 |
| Job 없음 | Jenkins Job 미생성 | Pipeline Job 먼저 생성 |
| 500 서버 오류 | Pipeline 스크립트 오류 | Jenkins 로그 확인 |

---

## 사용 시나리오

### 시나리오 1: Python 프로젝트

**입력:**
```
언어: Python
Base Image: python:3.11-slim
포트: 8000
서비스 URL: https://api.example.com
실행 명령어: uvicorn main:app --host 0.0.0.0 --port 8000
환경 변수 (선택): ENV=production
Health Check (선택): /health
```

**생성되는 Dockerfile:**
```dockerfile
FROM python:3.11-slim AS base

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R appuser:appuser /app

USER appuser

ENV ENV="production"
ENV SERVICE_URL="https://api.example.com"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=40s \
  CMD curl --fail http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 시나리오 2: Node.js 프로젝트

**입력:**
```
언어: Node.js
Base Image: node:20-alpine
포트: 3000
서비스 URL: https://api.example.com
실행 명령어: node server.js
시스템 의존성 (선택): curl
```

**생성되는 Dockerfile:**
```dockerfile
FROM node:20-alpine AS base

# Install system dependencies
RUN apk add --no-cache curl

RUN addgroup -S appuser && adduser -S appuser -G appuser

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN chown -R appuser:appuser /app

USER appuser

ENV SERVICE_URL="https://api.example.com"

EXPOSE 3000

CMD ["node", "server.js"]
```

### 시나리오 3: Java Spring Boot JAR 프로젝트

**입력:**
```
언어: Java
JAR 파일 업로드: my-spring-app-2.0.0.jar
Base Image: eclipse-temurin:17-jre-alpine
포트: 8080
서비스 URL: https://api.example.com
실행 명령어: java -jar app.jar
JVM 옵션: -Xmx1024m
```

**생성되는 Dockerfile:**
```dockerfile
# Spring Boot JAR Application Dockerfile
# Generated by Dockerfile Generator

FROM eclipse-temurin:17-jre-alpine AS runtime

# Create non-root user
RUN addgroup -S appuser && adduser -S appuser -G appuser

WORKDIR /app

# Copy JAR file (실제 업로드한 파일명 반영)
COPY --chown=appuser:appuser my-spring-app-2.0.0.jar app.jar

# Switch to non-root user
USER appuser

# Set environment variables
ENV SERVICE_URL="https://api.example.com"

# Expose port
EXPOSE 8080

# Run Spring Boot application (ENTRYPOINT 사용)
ENTRYPOINT ["java", "-jar", "app.jar"]
```

---

## 생성되는 Dockerfile 특징

### 1. 멀티스테이지 빌드 (Node.js, Java)

**장점:**
- 최종 이미지 크기 감소 (빌드 도구 제외)
- 보안 향상 (공격 표면 축소)
- 빌드 캐싱 최적화

**구조:**
```
Stage 1: Dependencies (의존성 설치)
  → 의존성 파일만 복사
  → 캐싱 최대 활용

Stage 2: Builder (빌드 실행)
  → 소스 코드 복사
  → 빌드 수행

Stage 3: Runtime (실행 환경)
  → 빌드 결과물만 복사
  → 최소한의 런타임만 포함
```

### 2. 레이어 캐싱 최적화

**순서:**
```dockerfile
1. Base image + 시스템 의존성
2. 패키지 매니저 파일 (requirements.txt, package.json, pom.xml)
3. 의존성 설치
4. 소스 코드 복사
5. 빌드/컴파일
6. 런타임 설정
```

**효과:**
- 소스 코드만 변경 시 → 1-3단계 캐싱 활용
- 의존성 추가 시 → 1-2단계 캐싱 활용

### 3. 보안 모범 사례

#### 3.1 Non-root 사용자
```dockerfile
# 사용자 생성
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 권한 설정
RUN chown -R appuser:appuser /app

# 사용자 전환
USER appuser
```

#### 3.2 Health Check
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s \
  CMD [health check command] || exit 1
```

**효과:**
- 컨테이너 상태 모니터링
- 자동 재시작 트리거
- 로드밸런서 통합

#### 3.3 최소 이미지
- Python: `python:3.11-slim` (Debian slim)
- Node.js: `node:20-alpine` (Alpine Linux)
- Java: `eclipse-temurin:17-jre-alpine` (JRE only)

### 4. 프로덕션 최적화

#### 4.1 이미지 크기
```
일반 이미지: 1.5GB
멀티스테이지 빌드: 300MB
Alpine 기반: 150MB
```

#### 4.2 빌드 시간
```
캐싱 없이: 5분
캐싱 활용: 30초
```

---

## API 명세

### 1. 파일 업로드 (Java)

**Endpoint:**
```
POST /api/upload/java
```

**Request:**
```http
Content-Type: multipart/form-data

file: [JAR/WAR file]
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "app.jar",
  "size": 52428800,
  "project_info": {
    "language": "java",
    "framework": "spring-boot",
    "detected_version": "17",
    "build_tool": "jar",
    "main_class": "com.example.Application",
    "metadata": {
      "spring_boot_version": "3.2.0",
      "fat_jar": "true",
      "jar_filename": "app.jar"
    }
  }
}
```

### 2. Python 프로젝트 분석

**Endpoint:**
```
POST /api/analyze/python
```

**Request:**
```json
{
  "language": "python",
  "framework": "fastapi",
  "runtime_version": "3.11",
  "port": 8000,
  "package_manager": "pip",
  "requirements_content": "fastapi==0.115.0\nuvicorn[standard]==0.32.0",
  "entrypoint_file": "main.py"
}
```

**Response:**
```json
{
  "project_info": {
    "language": "python",
    "framework": "fastapi",
    "dependencies": ["fastapi", "uvicorn"],
    "metadata": {
      "server": "uvicorn",
      "package_count": "2"
    }
  },
  "suggestions": {
    "server": "Recommended server: uvicorn"
  }
}
```

### 3. Node.js 프로젝트 분석

**Endpoint:**
```
POST /api/analyze/nodejs
```

**Request:**
```json
{
  "language": "nodejs",
  "framework": "nextjs",
  "runtime_version": "20",
  "port": 3000,
  "package_json": {
    "dependencies": {
      "next": "^14.0.0"
    },
    "packageManager": "pnpm@8.0.0"
  }
}
```

**Response:**
```json
{
  "project_info": {
    "language": "nodejs",
    "framework": "nextjs",
    "dependencies": ["next"],
    "metadata": {
      "package_manager": "pnpm",
      "build_command": "npm run build",
      "start_command": "npm start",
      "dependency_count": "1"
    }
  },
  "suggestions": {
    "package_manager": "Detected package manager: pnpm",
    "build_command": "Build command: npm run build"
  }
}
```

### 4. Dockerfile 생성

**Endpoint:**
```
POST /api/generate
```

**Request:**
```json
{
  "config": {
    "language": "python",
    "framework": "fastapi",
    "runtime_version": "3.11",
    "port": 8000,
    "environment_vars": {
      "ENV": "production",
      "DEBUG": "false"
    },
    "health_check_path": "/health",
    "system_dependencies": ["curl", "wget"],
    "base_image": null,
    "user": "appuser",
    "service_url": "https://api.example.com",
    "custom_start_command": null,
    "requirements_content": "fastapi==0.115.0",
    "package_manager": "pip",
    "entrypoint_file": "main.py"
  }
}
```

**Response:**
```json
{
  "dockerfile": "FROM python:3.11-slim AS base\n...",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "metadata": {
    "language": "python",
    "framework": "fastapi",
    "template": "python/fastapi"
  }
}
```

### 5. Dockerfile 다운로드

**Endpoint:**
```
GET /api/download/{session_id}
```

**Response:**
```http
Content-Type: text/plain
Content-Disposition: attachment; filename=Dockerfile

[Dockerfile content]
```

### 6. 템플릿 목록 조회

**Endpoint:**
```
GET /api/templates
```

**Response:**
```json
{
  "templates": {
    "python": ["fastapi", "flask", "django"],
    "nodejs": ["express", "nestjs", "nextjs"],
    "java": ["spring-boot"]
  }
}
```

### 7. Jenkins 빌드 트리거

**Endpoint:**
```
POST /api/build/jenkins
```

**Request:**
```json
{
  "config": {
    "language": "python",
    "framework": "fastapi",
    "runtime_version": "3.11",
    "port": 8000,
    "base_image": "python:3.11-slim",
    "service_url": "https://api.example.com",
    "custom_start_command": "uvicorn main:app --host 0.0.0.0 --port 8000"
  },
  "jenkins_url": "https://jenkins.example.com",
  "jenkins_job": "my-docker-build-job",
  "jenkins_username": "admin",
  "jenkins_token": "11abcd1234567890abcdef",
  "git_url": "https://github.com/user/repo.git",
  "git_branch": "main",
  "git_credential_id": "git-credentials",
  "image_name": "my-app",
  "image_tag": "latest"
}
```

**Response:**
```json
{
  "job_name": "my-docker-build-job",
  "queue_id": "123",
  "queue_url": "https://jenkins.example.com/queue/item/123/",
  "job_url": "https://jenkins.example.com/job/my-docker-build-job",
  "status": "QUEUED",
  "message": "Jenkins build triggered successfully"
}
```

**에러 응답:**
```json
{
  "detail": "Jenkins job 'my-docker-build-job' not found. Please create the job first."
}
```

---

## 에러 처리

### 파일 업로드 에러

| 상태 코드 | 에러 | 원인 | 해결 방법 |
|----------|------|------|----------|
| 400 | Invalid file type | 허용되지 않은 확장자 | .jar, .war 파일만 업로드 |
| 400 | Invalid content type | Content-Type 불일치 | application/java-archive 확인 |
| 400 | File is not a valid JAR | Magic number 불일치 | 올바른 JAR 파일인지 확인 |
| 413 | File too large | 파일 크기 초과 | 500MB 이하로 제한 |

### 생성 에러

| 상태 코드 | 에러 | 원인 | 해결 방법 |
|----------|------|------|----------|
| 400 | Invalid configuration | 필수 필드 누락 | 모든 필수 설정 입력 |
| 404 | Template not found | 지원하지 않는 프레임워크 | 지원 프레임워크 확인 |
| 500 | Generation failed | 템플릿 렌더링 실패 | 설정 값 확인 |

---

## 제한사항

### 파일 업로드
- 최대 파일 크기: **500MB**
- 허용 확장자: **.jar, .war**
- 세션 유효기간: **1시간**

### 지원 범위
- Python: FastAPI, Flask, Django (추가 프레임워크 확장 가능)
- Node.js: Express, NestJS, Next.js
- Java: Spring Boot (Maven, Gradle, JAR)

### 브라우저 지원
- Chrome/Edge: 최신 버전
- Firefox: 최신 버전
- Safari: 최신 버전

---

## 향후 계획

### Phase 10: 추가 기능
- [x] Jenkins CI/CD 통합 (자동 빌드)
- [ ] Docker Registry Push 기능
- [ ] Docker Compose 생성
- [ ] Kubernetes manifest 생성
- [ ] .dockerignore 파일 생성
- [ ] CI/CD 파이프라인 템플릿 (GitHub Actions, GitLab CI)
- [ ] 이미지 크기 예측
- [ ] 보안 스캐닝 통합 (Trivy, Grype)
- [ ] 템플릿 커스터마이징 UI
- [ ] 설정 프로필 저장/로드
- [ ] 추가 Python 프레임워크 (Tornado, Sanic, Falcon 등)
- [ ] Go, Rust, PHP 언어 지원

---

## 문의 및 지원

- **문서**: README.md, CLAUDE.md
- **API 문서**: http://localhost:8000/api/docs
- **이슈 리포트**: GitHub Issues
- **기여**: Pull Requests 환영

---

---

## 최근 업데이트

### v1.2.0 (2026-02-05) - Jenkins 통합

#### 새로운 기능
- ✅ **Jenkins CI/CD 통합**: Dockerfile 생성 후 Jenkins에서 자동 빌드
- ✅ **Pipeline 스크립트 자동 생성**: Groovy Pipeline 스크립트 자동 생성 및 전달
- ✅ **Git 통합**: Git 저장소에서 소스코드 자동 체크아웃
- ✅ **CSRF 보호**: Jenkins Crumb 자동 처리
- ✅ **Base64 인코딩**: Dockerfile 안전한 전송
- ✅ **SSL 지원**: 자체 서명 인증서 지원

#### Jenkins 관련 추가 파일
- `backend/app/services/jenkins_client.py`: Jenkins REST API 클라이언트
- `backend/app/services/pipeline_generator.py`: Pipeline 스크립트 생성기
- `backend/app/models/schemas.py`: JenkinsBuildRequest/Response 스키마
- API Endpoint: `POST /api/build/jenkins`

#### 기술적 개선
- ✅ Jenkins API 인증 (HTTPBasicAuth)
- ✅ CSRF 토큰 자동 관리
- ✅ SSL 인증서 검증 옵션
- ✅ Job 존재 여부 사전 확인
- ✅ 상세한 에러 로깅 및 처리
- ✅ CDATA 섹션으로 XML 파싱 문제 방지

### v1.1.0 (2025-02-05)

#### UI/UX 개선
- ✅ Python/Node.js 워크플로우 단순화 (프레임워크 선택 제거)
- ✅ 필수 설정 명확화 (Base Image, 포트, 서비스 URL, 실행 명령어)
- ✅ 선택적 기능 체크박스화 (환경변수, Health Check, 시스템 의존성)
- ✅ 실제 언어 로고 아이콘 표시 (폐쇄망 지원)
- ✅ 선택된 언어 시각적 하이라이트
- ✅ 언어별 맞춤형 플레이스홀더
- ✅ 커스텀 알림 모달 (브라우저 alert 대체)
- ✅ 재생성 버튼 및 확인 모달

#### Java 개선
- ✅ Maven/Gradle 소스 프로젝트 옵션 제거 (JAR만 지원)
- ✅ 런타임 버전 필드 제거
- ✅ 업로드한 JAR 파일의 실제 파일명 자동 반영
- ✅ Java 실행 명령어 ENTRYPOINT 방식으로 변경 (CMD → ENTRYPOINT)
- ✅ Java 필수 필드 추가 (Base Image, 포트, 서비스 URL, 실행 명령어)

#### 기술적 개선
- ✅ CMD 명령어 JSON 배열 형식으로 통일
- ✅ 언어 전환 시 입력값 자동 초기화
- ✅ 동적 JAR 파일명 처리

---

**Version**: 1.2.0
**Last Updated**: 2026-02-05
