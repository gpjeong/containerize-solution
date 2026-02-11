# Dockerfile Generator - Project Hub

웹 서비스용 Dockerfile을 자동으로 생성하는 도구입니다. 소스코드나 빌드된 아티팩트를 분석하고, 사용자 설정을 결합하여 프로덕션에 최적화된 Dockerfile을 생성합니다.

## Repository 구조

이 프로젝트는 3개의 Git 레포지토리로 구성됩니다:

| 레포 | 설명 | 기술 스택 |
|------|------|-----------|
| [**containerize-backend**](https://github.com/gpjeong/containerize-backend) | 백엔드 API 서버 | Java 17 + Spring Boot 3.3.5 |
| [**containerize-frontend**](https://github.com/gpjeong/containerize-frontend) | 프론트엔드 웹 앱 | React 19 + TypeScript + Vite 7 |
| **containerize-tool** (이 레포) | 프로젝트 허브 + 통합 실행 + 문서 | docker-compose + 레거시 코드 |

## 빠른 시작

### 사전 준비

3개 레포를 형제 디렉토리로 클론합니다:

```
workspace/
├── containerize-tool/         ← docker-compose 실행 (이 레포)
├── containerize-backend/      ← 백엔드 코드
└── containerize-frontend/     ← 프론트엔드 코드
```

### 풀스택 실행 (Docker Compose)

```bash
cd containerize-tool
docker-compose up --build
```

- 프론트엔드: http://localhost:4000
- 백엔드 API: http://localhost:8000
- API 문서: http://localhost:8000/api/docs

### 백엔드만 실행

```bash
cd containerize-backend
./gradlew bootRun
```

### 프론트엔드만 실행

```bash
cd containerize-frontend
npm install
npm run dev
```

> 프론트엔드는 백엔드 API(`http://localhost:8000`)가 실행 중이어야 정상 동작합니다.

### 프로덕션 실행

```bash
cd containerize-tool
docker-compose -f docker-compose.prod.yml up -d
```

## 지원하는 기술 스택

| 언어 | 프레임워크 |
|------|-----------|
| Python | FastAPI, Flask, Django |
| Node.js | Express, NestJS, Next.js |
| Java | Spring Boot (JAR/Gradle/Maven) |

## 주요 기능

- **Dockerfile 자동 생성**: 소스 코드 분석 기반 최적화된 Dockerfile 생성
- **JAR 파일 분석**: Java JAR/WAR 업로드 시 자동 분석 (파일명, Spring Boot 감지)
- **멀티 스테이지 빌드**: 모든 템플릿이 최적화된 멀티 스테이지 빌드 사용
- **보안 기본값**: Non-root 사용자, Health Check 자동 설정
- **CodeMirror 에디터**: 실시간 미리보기 및 편집
- **Jenkins CI/CD 통합**: 생성된 Dockerfile로 Jenkins 자동 빌드
- **Harbor 통합**: 컨테이너 이미지 레지스트리 연동

## 문서

| 문서 | 설명 |
|------|------|
| [API Documentation](docs/API_DOCUMENTATION.md) | API 엔드포인트 상세 문서 |
| [Features](docs/FEATURES.md) | 기능 목록 및 상세 설명 |
| [Harbor Setup](docs/HARBOR_SETUP.md) | Harbor 레지스트리 설정 가이드 |
| [Harbor + Kaniko Guide](docs/HARBOR_KANIKO_GUIDE.md) | Harbor와 Kaniko 통합 가이드 |
| [Kaniko Integration](docs/KANIKO_INTEGRATION.md) | Kaniko 빌드 통합 |
| [Kubernetes + Jenkins](docs/KUBERNETES_JENKINS.md) | K8s 및 Jenkins 설정 |
| [Solution Report](docs/SOLUTION_REPORT.md) | 종합 솔루션 보고서 |
| [QA Test Report](docs/QA-TEST-REPORT.md) | QA 테스트 결과 |

## 레거시 코드

`backend/`와 `frontend/` 디렉토리는 v1.0 레거시 구현(Python FastAPI + Vanilla JS)입니다. 참고용으로 보존하며, 신규 개발은 위의 별도 레포에서 진행합니다.

레거시 코드는 `v1.0.0-legacy` 태그에서 확인할 수 있습니다.

## 라이센스

MIT License
