# Backend API 문서

## 개요

**프로젝트**: Containerization Solution (Dockerfile Generator)
**백엔드**: FastAPI 0.115.0
**베이스 URL**: `http://localhost:8000/api`
**총 엔드포인트 수**: 13개

---

## 목차

1. [파일 업로드 & 분석](#1-파일-업로드--분석)
2. [Dockerfile 생성](#2-dockerfile-생성)
3. [Jenkins CI/CD 통합](#3-jenkins-cicd-통합)
4. [Setup 기능 (Jenkins & Harbor)](#4-setup-기능-jenkins--harbor)

---

## 1. 파일 업로드 & 분석

### 1.1 Java JAR 파일 업로드

**엔드포인트**: `POST /api/upload/java`

**설명**: Java JAR/WAR 파일을 업로드하고 메타데이터를 추출합니다.

**Request**:
- Content-Type: `multipart/form-data`
- Body:
  - `file`: JAR/WAR 파일 (최대 500MB)

**Response** (200):
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "app.jar",
  "size": 15728640,
  "project_info": {
    "language": "java",
    "framework": "spring-boot",
    "detected_version": "17",
    "build_tool": "jar",
    "main_class": "com.example.Application",
    "dependencies": [],
    "metadata": {
      "jar_file_name": "app.jar"
    }
  }
}
```

**에러**:
- `400`: 지원하지 않는 파일 형식
- `413`: 파일 크기 초과

**파일 위치**: `backend/app/api/endpoints.py:37`

---

### 1.2 Python 프로젝트 분석

**엔드포인트**: `POST /api/analyze/python`

**설명**: Python 프로젝트 정보를 분석합니다.

**Request**:
```json
{
  "framework": "fastapi",
  "runtime_version": "3.11"
}
```

**Response** (200):
```json
{
  "project_info": {
    "language": "python",
    "framework": "fastapi",
    "detected_version": "3.11",
    "build_tool": null,
    "main_class": null,
    "dependencies": [],
    "metadata": {}
  },
  "session_id": null,
  "suggestions": {}
}
```

**파일 위치**: `backend/app/api/endpoints.py:78`

---

### 1.3 Node.js 프로젝트 분석

**엔드포인트**: `POST /api/analyze/nodejs`

**설명**: Node.js 프로젝트 정보를 분석합니다.

**Request**:
```json
{
  "framework": "express",
  "runtime_version": "20"
}
```

**Response** (200):
```json
{
  "project_info": {
    "language": "nodejs",
    "framework": "express",
    "detected_version": "20",
    "build_tool": null,
    "main_class": null,
    "dependencies": [],
    "metadata": {}
  },
  "session_id": null,
  "suggestions": {}
}
```

**파일 위치**: `backend/app/api/endpoints.py:112`

---

## 2. Dockerfile 생성

### 2.1 Dockerfile 생성

**엔드포인트**: `POST /api/generate`

**설명**: 설정을 기반으로 최적화된 Dockerfile을 생성합니다.

**Request** (Python FastAPI 예시):
```json
{
  "project_info": {
    "language": "python",
    "framework": "fastapi",
    "detected_version": "3.11"
  },
  "config": {
    "language": "python",
    "framework": "fastapi",
    "runtime_version": "3.11",
    "port": 8000,
    "package_manager": "pip",
    "server": "uvicorn",
    "requirements_content": "fastapi==0.115.0\nuvicorn[standard]==0.32.0",
    "entrypoint_file": "main.py",
    "environment_vars": {
      "ENV": "production"
    },
    "health_check_path": "/health",
    "user": "appuser",
    "system_dependencies": []
  }
}
```

**Response** (200):
```json
{
  "dockerfile": "FROM python:3.11-slim\n\nWORKDIR /app\n...",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "metadata": {
    "language": "python",
    "framework": "fastapi",
    "runtime_version": "3.11"
  }
}
```

**지원 언어**:
- Python: FastAPI, Flask, Django, Generic
- Node.js: Express, NestJS, Next.js, Generic
- Java: Spring Boot (JAR)

**파일 위치**: `backend/app/api/endpoints.py:150`

---

### 2.2 Dockerfile 다운로드

**엔드포인트**: `GET /api/download/{session_id}`

**설명**: 생성된 Dockerfile을 다운로드합니다.

**Path Parameters**:
- `session_id`: UUID 형식의 세션 ID

**Response** (200):
- Content-Type: `application/octet-stream`
- Content-Disposition: `attachment; filename=Dockerfile`
- Body: Dockerfile 내용

**에러**:
- `404`: Dockerfile을 찾을 수 없음

**파일 위치**: `backend/app/api/endpoints.py:200`

---

### 2.3 템플릿 목록 조회

**엔드포인트**: `GET /api/templates`

**설명**: 지원하는 Dockerfile 템플릿 목록을 조회합니다.

**Response** (200):
```json
{
  "templates": [
    {
      "language": "python",
      "frameworks": ["fastapi", "flask", "django", "generic"]
    },
    {
      "language": "nodejs",
      "frameworks": ["express", "nestjs", "nextjs", "generic"]
    },
    {
      "language": "java",
      "frameworks": ["spring-boot"]
    }
  ]
}
```

**파일 위치**: `backend/app/api/endpoints.py:237`

---

## 3. Jenkins CI/CD 통합

### 3.1 Pipeline 스크립트 미리보기

**엔드포인트**: `POST /api/preview/pipeline`

**설명**: Jenkins Pipeline 스크립트를 생성하여 미리보기를 제공합니다.

**Request**:
```json
{
  "git_url": "https://github.com/user/repo.git",
  "git_branch": "main",
  "git_credential_id": "github-credentials",
  "image_name": "my-app",
  "image_tag": "latest",
  "use_kubernetes": false,
  "use_kaniko": false,
  "harbor_url": "harbor.example.com/myproject",
  "harbor_credential_id": "harbor-credentials"
}
```

**Response** (200):
```json
{
  "pipeline_script": "pipeline {\n  agent any\n  stages {\n    ...\n  }\n}",
  "message": "Pipeline script generated successfully"
}
```

**Pipeline 타입**:
- **Docker-in-Docker (DinD)**: `use_kubernetes=false, use_kaniko=false`
- **Kaniko**: `use_kaniko=true` (권장 - 보안, 안정성, 속도 우수)
- **Kubernetes Pod**: `use_kubernetes=true`

**파일 위치**: `backend/app/api/endpoints.py:253`

---

### 3.2 커스텀 스크립트로 Jenkins 빌드

**엔드포인트**: `POST /api/build/jenkins/custom`

**설명**: 사용자가 편집한 Pipeline 스크립트로 Jenkins 빌드를 트리거합니다.

**Request**:
```json
{
  "config": {
    "language": "python",
    "framework": "fastapi",
    "port": 8000
  },
  "jenkins_url": "http://jenkins.example.com:8080",
  "jenkins_job": "dockerfile-builder",
  "jenkins_token": "11234567890abcdef",
  "jenkins_username": "admin",
  "custom_pipeline_script": "pipeline { ... }"
}
```

**Response** (200):
```json
{
  "job_name": "dockerfile-builder",
  "queue_id": "123",
  "queue_url": "http://jenkins.example.com:8080/queue/item/123/",
  "job_url": "http://jenkins.example.com:8080/job/dockerfile-builder/",
  "build_number": 42,
  "build_url": "http://jenkins.example.com:8080/job/dockerfile-builder/42",
  "status": "BUILDING",
  "message": "Build triggered successfully"
}
```

**파일 위치**: `backend/app/api/endpoints.py:323`

---

### 3.3 자동 생성 스크립트로 Jenkins 빌드

**엔드포인트**: `POST /api/build/jenkins`

**설명**: 자동 생성된 Pipeline 스크립트로 Jenkins 빌드를 트리거합니다.

**Request**:
```json
{
  "config": {
    "language": "python",
    "framework": "generic",
    "port": 8000,
    "base_image": "python:3.11-slim"
  },
  "jenkins_url": "http://jenkins.example.com:8080",
  "jenkins_job": "dockerfile-builder",
  "jenkins_token": "11234567890abcdef",
  "jenkins_username": "admin",
  "git_url": "https://github.com/user/repo.git",
  "git_branch": "main",
  "git_credential_id": "github-credentials",
  "image_name": "my-app",
  "image_tag": "v1.0.0",
  "use_kubernetes": false,
  "use_kaniko": true,
  "harbor_url": "harbor.example.com/myproject",
  "harbor_credential_id": "harbor-credentials"
}
```

**Response** (200):
```json
{
  "job_name": "dockerfile-builder",
  "queue_id": "124",
  "queue_url": "http://jenkins.example.com:8080/queue/item/124/",
  "job_url": "http://jenkins.example.com:8080/job/dockerfile-builder/",
  "build_number": 43,
  "build_url": "http://jenkins.example.com:8080/job/dockerfile-builder/43",
  "status": "BUILDING",
  "message": "Build triggered successfully with auto-generated pipeline"
}
```

**특징**:
- Dockerfile 자동 생성
- Pipeline 스크립트 자동 생성
- Jenkins Job 업데이트 및 빌드 트리거
- Base64 인코딩으로 안전한 전송
- CSRF 토큰 자동 처리

**파일 위치**: `backend/app/api/endpoints.py:373`

---

## 4. Setup 기능 (Jenkins & Harbor)

### 4.1 Jenkins Job 존재 확인

**엔드포인트**: `POST /api/setup/jenkins/check-job`

**설명**: Jenkins에 특정 Job이 존재하는지 확인합니다.

**Request**:
```json
{
  "jenkins_url": "http://jenkins.example.com:8080",
  "jenkins_username": "admin",
  "jenkins_token": "11234567890abcdef",
  "job_name": "dockerfile-builder"
}
```

**Response** (200):
```json
{
  "exists": true,
  "job_name": "dockerfile-builder",
  "job_url": "http://jenkins.example.com:8080/job/dockerfile-builder"
}
```

**파일 위치**: `backend/app/api/endpoints.py:489`

---

### 4.2 Jenkins Job 생성

**엔드포인트**: `POST /api/setup/jenkins/create-job`

**설명**: Jenkins에 새로운 Pipeline Job을 생성합니다.

**Request**:
```json
{
  "jenkins_url": "http://jenkins.example.com:8080",
  "jenkins_username": "admin",
  "jenkins_token": "11234567890abcdef",
  "job_name": "dockerfile-builder",
  "description": "Auto-generated Pipeline job for containerization"
}
```

**Response** (200):
```json
{
  "job_name": "dockerfile-builder",
  "job_url": "http://jenkins.example.com:8080/job/dockerfile-builder",
  "status": "created",
  "message": "Job 'dockerfile-builder' created successfully"
}
```

**생성되는 Job 설정**:
- Job 타입: Pipeline Job
- 빌드 파라미터:
  - `IMAGE_NAME` (기본값: myapp)
  - `IMAGE_TAG` (기본값: latest)
- Pipeline 스크립트: 빈 템플릿 (나중에 업데이트됨)
- Sandbox 모드: 활성화

**파일 위치**: `backend/app/api/endpoints.py:536`

---

### 4.3 Harbor Project 존재 확인

**엔드포인트**: `POST /api/setup/harbor/check-project`

**설명**: Harbor에 특정 Project가 존재하는지 확인합니다.

**Request**:
```json
{
  "harbor_url": "https://harbor.example.com",
  "harbor_username": "admin",
  "harbor_password": "Harbor12345",
  "project_name": "myproject"
}
```

**Response** (200):
```json
{
  "exists": true,
  "project_name": "myproject",
  "project_url": "https://harbor.example.com/harbor/projects"
}
```

**파일 위치**: `backend/app/api/endpoints.py:592`

---

### 4.4 Harbor Project 생성

**엔드포인트**: `POST /api/setup/harbor/create-project`

**설명**: Harbor에 새로운 Project를 생성합니다.

**Request**:
```json
{
  "harbor_url": "https://harbor.example.com",
  "harbor_username": "admin",
  "harbor_password": "Harbor12345",
  "project_name": "myproject",
  "public": false,
  "enable_content_trust": false,
  "auto_scan": true,
  "severity": "high",
  "prevent_vul": false
}
```

**Response** (200):
```json
{
  "project_name": "myproject",
  "project_url": "https://harbor.example.com/harbor/projects",
  "status": "created",
  "message": "Project 'myproject' created successfully",
  "settings": {
    "public": false,
    "auto_scan": true,
    "severity": "high",
    "content_trust": false,
    "prevent_vulnerable": false
  }
}
```

**Project 설정 옵션**:
- `public`: Public 프로젝트 여부 (누구나 이미지 pull 가능)
- `enable_content_trust`: Docker Content Trust (이미지 서명)
- `auto_scan`: 이미지 Push 시 자동 취약점 스캔 (Trivy)
- `severity`: 취약점 심각도 기준 (critical/high/medium/low)
- `prevent_vul`: 취약점 있는 이미지 Pull 차단

**Project 이름 규칙**:
- 소문자만 사용
- 영문자, 숫자, 하이픈(-), 언더스코어(_) 허용
- 시작은 영문자 또는 숫자

**파일 위치**: `backend/app/api/endpoints.py:643`

---

## 기술 스택

### Backend
- **프레임워크**: FastAPI 0.115.0
- **웹 서버**: Uvicorn 0.32.0
- **검증**: Pydantic 2.10.0
- **템플릿**: Jinja2 3.1.4
- **HTTP 클라이언트**: Requests 2.31.0
- **파일 처리**: Python-magic 0.4.27, Aiofiles 24.1.0
- **보안**: Werkzeug 3.1.3

### 특징
- ✅ **Stateless 아키텍처**: DB 없이 파일 기반 처리
- ✅ **비동기 처리**: AsyncIO 지원
- ✅ **자동 API 문서**: Swagger UI (`/docs`)
- ✅ **보안**: 파일 검증, Non-root 사용자, 자동 파일 정리
- ✅ **Jenkins/Harbor 통합**: REST API 기반 자동화
- ✅ **Kaniko 지원**: 특권 모드 없이 안전한 이미지 빌드

---

## 보안 고려사항

### 1. 파일 업로드 보안
- 다층 검증: 확장자 + Content-Type + Magic Number
- 파일 크기 제한: 최대 500MB
- 파일명 Sanitization: 경로 탐색 공격 방지
- 자동 정리: 1시간 후 임시 파일 자동 삭제

### 2. 외부 시스템 인증
- Jenkins: API Token (Basic Auth)
- Harbor: Username + Password (Basic Auth)
- **주의**: 인증 정보는 저장되지 않으며, 요청 시에만 사용

### 3. CSRF 보호
- Jenkins: Crumb 토큰 자동 처리
- Harbor: Cookieless 방식으로 CSRF 우회

### 4. SSL 지원
- 자체 서명 인증서 지원 (`verify_ssl=False`)
- 프로덕션 환경에서는 정식 인증서 사용 권장

---

## 에러 처리

### HTTP 상태 코드
- `200`: 성공
- `400`: 잘못된 요청 (유효성 검증 실패)
- `404`: 리소스를 찾을 수 없음
- `413`: 파일 크기 초과
- `500`: 서버 내부 오류

### 에러 응답 형식
```json
{
  "detail": "Error message here"
}
```

---

## 환경 변수

```bash
ENVIRONMENT=development          # development 또는 production
LOG_LEVEL=INFO                  # 로그 레벨
MAX_UPLOAD_SIZE=524288000       # 최대 업로드 크기 (500MB)
```

---

## API 사용 예시

### 전체 워크플로우: Python FastAPI 프로젝트

```bash
# 1. Dockerfile 생성
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "language": "python",
      "framework": "fastapi",
      "runtime_version": "3.11",
      "port": 8000,
      "requirements_content": "fastapi==0.115.0\nuvicorn[standard]==0.32.0"
    }
  }'

# 2. Jenkins Job 생성 (없는 경우)
curl -X POST http://localhost:8000/api/setup/jenkins/create-job \
  -H "Content-Type: application/json" \
  -d '{
    "jenkins_url": "http://jenkins.example.com:8080",
    "jenkins_username": "admin",
    "jenkins_token": "your-api-token",
    "job_name": "dockerfile-builder"
  }'

# 3. Harbor Project 생성 (없는 경우)
curl -X POST http://localhost:8000/api/setup/harbor/create-project \
  -H "Content-Type: application/json" \
  -d '{
    "harbor_url": "https://harbor.example.com",
    "harbor_username": "admin",
    "harbor_password": "your-password",
    "project_name": "myproject",
    "auto_scan": true
  }'

# 4. Jenkins 빌드 트리거
curl -X POST http://localhost:8000/api/build/jenkins \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "language": "python",
      "framework": "fastapi"
    },
    "jenkins_url": "http://jenkins.example.com:8080",
    "jenkins_job": "dockerfile-builder",
    "jenkins_token": "your-api-token",
    "git_url": "https://github.com/user/repo.git",
    "image_name": "my-app",
    "use_kaniko": true,
    "harbor_url": "harbor.example.com/myproject"
  }'
```

---

## 참고 문서

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Jenkins REST API](https://www.jenkins.io/doc/book/using/remote-access-api/)
- [Harbor REST API v2.0](https://goharbor.io/docs/2.0.0/working-with-projects/working-with-projects/)
- [Kaniko](https://github.com/GoogleContainerTools/kaniko)

---

**문서 버전**: 1.0.0
**최종 업데이트**: 2026-02-06
**작성자**: Claude (Anthropic)
