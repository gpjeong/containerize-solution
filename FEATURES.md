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
| 빌드 도구 | 특징 |
|----------|------|
| **Maven** | pom.xml 기반 빌드 |
| **Gradle** | build.gradle 기반 빌드 |
| **JAR** | 빌드된 Fat JAR 파일 |

**자동 감지 기능:**
- JAR 파일에서 MANIFEST.MF 추출
- Spring Boot 버전 감지
- Main Class 자동 탐지
- Fat JAR vs Thin JAR 구분

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
**입력 방식 (3가지):**

**방식 1: JAR 파일 업로드**
```
app.jar 업로드
→ MANIFEST.MF 분석
→ Spring Boot 감지
→ Main Class 추출
```

**방식 2: Maven 소스 프로젝트**
```
빌드 도구: Maven 선택
pom.xml 내용 붙여넣기
→ 의존성 분석
→ 멀티스테이지 빌드 생성
```

**방식 3: Gradle 소스 프로젝트**
```
빌드 도구: Gradle 선택
build.gradle 내용 붙여넣기
→ 의존성 분석
→ 멀티스테이지 빌드 생성
```

### 2. Docker 설정

#### 2.1 기본 설정
| 설정 항목 | 설명 | 기본값 | 예시 |
|----------|------|--------|------|
| **런타임 버전** | 언어 런타임 버전 | 자동 | Python: 3.11, Node: 20, Java: 17 |
| **포트** | 서비스 포트 | 8000 | Python: 8000, Node: 3000, Java: 8080 |
| **Health Check 경로** | 헬스체크 엔드포인트 | /health | /actuator/health, /api/health |

#### 2.2 환경 변수
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

#### 2.3 시스템 의존성
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

#### 2.4 고급 설정

**Base Image (선택사항):**
```
python:3.11-alpine
node:20-slim
eclipse-temurin:17-jre
```

**서비스 URL (선택사항):**
```
https://api.example.com
→ ENV SERVICE_URL="https://api.example.com"
```

**커스텀 실행 명령어 (선택사항):**
```
Python: python main.py --reload
Node.js: node server.js --port 3000
Java: java -jar app.jar --spring.profiles.active=prod
```

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

---

## 사용 시나리오

### 시나리오 1: Python FastAPI 프로젝트

**입력:**
```
언어: Python
프레임워크: FastAPI
런타임 버전: 3.11
포트: 8000
requirements.txt:
  fastapi==0.115.0
  uvicorn[standard]==0.32.0
환경 변수:
  ENV=production
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

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=40s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 시나리오 2: Node.js Next.js 프로젝트 (멀티스테이지)

**입력:**
```
언어: Node.js
프레임워크: Next.js
런타임 버전: 20
포트: 3000
패키지 매니저: pnpm (자동 감지)
```

**생성되는 Dockerfile:**
```dockerfile
# Stage 1: Dependencies
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
COPY pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile

# Stage 2: Builder
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Stage 3: Runtime
FROM node:20-alpine AS runtime
RUN addgroup -S appuser && adduser -S appuser -G appuser
WORKDIR /app
COPY --from=builder --chown=appuser /app/.next/standalone ./
COPY --from=builder --chown=appuser /app/.next/static ./.next/static
COPY --from=builder --chown=appuser /app/public ./public
USER appuser
EXPOSE 3000
CMD ["node", "server.js"]
```

### 시나리오 3: Java Spring Boot Maven 프로젝트

**입력:**
```
언어: Java
프로젝트 타입: Maven 소스 프로젝트
빌드 도구: Maven
런타임 버전: 17
포트: 8080
JVM 옵션: -Xmx1024m
```

**생성되는 Dockerfile:**
```dockerfile
# Stage 1: Build
FROM maven:3.9-eclipse-temurin-17-alpine AS build
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline -B
COPY src ./src
RUN mvn clean package -DskipTests

# Stage 2: Runtime
FROM eclipse-temurin:17-jre-alpine AS runtime
RUN addgroup -S appuser && adduser -S appuser -G appuser
WORKDIR /app
COPY --from=build --chown=appuser /app/target/*.jar app.jar
USER appuser
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/actuator/health || exit 1
ENTRYPOINT ["java", "-Xmx1024m", "-jar", "app.jar"]
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

**Version**: 1.0.0
**Last Updated**: 2025-02-04
