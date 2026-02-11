# Harbor Registry 연동 및 Kaniko 빌드 완벽 가이드

## 목차
1. [개요](#개요)
2. [Kubernetes Jenkins에서 Docker 빌드 문제](#kubernetes-jenkins에서-docker-빌드-문제)
3. [Kaniko 솔루션](#kaniko-솔루션)
4. [Harbor Registry 연동](#harbor-registry-연동)
5. [사용 방법](#사용-방법)
6. [트러블슈팅](#트러블슈팅)
7. [캐시 관리](#캐시-관리)

---

## 개요

이 문서는 Kubernetes 환경의 Jenkins에서 Kaniko를 사용하여 Docker 이미지를 빌드하고 Harbor Registry에 푸시하는 전체 과정을 설명합니다.

### 주요 기능
- ✅ Kubernetes 환경에서 Docker 빌드 (privileged 모드 불필요)
- ✅ Harbor Private Registry에 이미지 푸시
- ✅ Jenkins Credential을 통한 안전한 인증
- ✅ 빌드 캐시로 속도 향상
- ✅ Self-signed 인증서 지원

---

## Kubernetes Jenkins에서 Docker 빌드 문제

### 문제 1: docker not found

Jenkins가 Kubernetes 클러스터에서 실행 중일 때:

```bash
docker: not found
```

**원인**: Jenkins agent Pod에 Docker가 설치되어 있지 않음

### 문제 2: Docker-in-Docker (DinD) 문제

DinD를 사용하면:

```bash
[Running][ContainersNotReady] containers with unready status: [docker]
Cannot connect to the Docker daemon at unix:///var/run/docker.sock
```

**원인**:
- DinD는 `privileged: true` 필요
- Pod Security Policy에서 차단될 수 있음
- 컨테이너가 Ready 상태가 되지 않음

---

## Kaniko 솔루션

### Kaniko란?

Google의 컨테이너 이미지 빌드 도구로, **Docker daemon 없이** 이미지를 빌드합니다.

### Kaniko vs Docker-in-Docker

| 항목 | Docker-in-Docker | Kaniko |
|------|------------------|--------|
| **Privileged 모드** | ✅ 필요 | ❌ 불필요 |
| **보안** | ⚠️ 낮음 | ✅ 높음 |
| **시작 속도** | 🐌 느림 (daemon 초기화) | ⚡ 빠름 |
| **안정성** | ⚠️ Pod ready 이슈 | ✅ 안정적 |
| **캐싱** | ✅ Docker 레이어 캐시 | ✅ Remote 캐시 |
| **멀티스테이지 빌드** | ✅ 완벽 지원 | ✅ 완벽 지원 |

### Kaniko 동작 원리

```
┌─────────────────────────────────────┐
│   Jenkins Pipeline (Kubernetes)     │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  Kaniko Container            │  │
│  │  - No Docker daemon          │  │
│  │  - Reads Dockerfile          │  │
│  │  - Builds layer by layer     │  │
│  │  - Pushes to Harbor          │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
           │
           ▼
   ┌───────────────────┐
   │  Harbor Registry  │
   │  - Image storage  │
   │  - Cache storage  │
   └───────────────────┘
```

---

## Harbor Registry 연동

### 1. Harbor 준비

#### Harbor 정보 확인
- **Harbor URL**: `harbor.devops.cicd.test`
- **Project**: `python`
- **Image Path**: `harbor.devops.cicd.test/python/python-app`

#### Harbor 사용자 또는 Robot Account

**옵션 A: 기존 사용자**
```
Username: admin
Password: Harbor12345
```

**옵션 B: Robot Account (권장)**

Harbor UI에서:
1. Projects → python → Robot Accounts
2. "New Robot Account" 클릭
3. Name: `jenkins-builder`
4. Permissions: Push Artifact, Pull Artifact
5. 생성된 토큰 복사 (한 번만 표시!)

```
Username: robot$jenkins-builder
Password: <GENERATED_TOKEN>
```

### 2. Jenkins Credential 생성

**Jenkins UI에서:**

1. **Manage Jenkins** → **Credentials**
2. **Global credentials** → **Add Credentials**
3. 설정:
   - **Kind**: `Username with password`
   - **Scope**: `Global`
   - **Username**: `admin` (또는 `robot$jenkins-builder`)
   - **Password**: Harbor 비밀번호 (또는 Robot 토큰)
   - **ID**: `harbor-credentials` ← **웹 UI에 입력할 이름**
   - **Description**: `Harbor Registry Credentials`
4. **OK** 클릭

#### Credential 확인

```bash
# Jenkins Script Console에서 확인 (선택사항)
println(com.cloudbees.plugins.credentials.CredentialsProvider.lookupCredentials(
    com.cloudbees.plugins.credentials.common.StandardUsernamePasswordCredentials.class
).collect { it.id })
```

---

## 사용 방법

### 웹 UI에서 설정

#### 1. Dockerfile 설정 (기존 방식)

1. 언어 선택: Python / Node.js / Java
2. Dockerfile 옵션 설정
3. Dockerfile 생성 확인

#### 2. Jenkins 빌드 설정

**기본 설정:**
- ✅ **Jenkins 빌드 자동화** 체크
- Jenkins URL: `http://jenkins.devops.cicd.test:8080`
- Jenkins Job: `containerize-pipeline-test`
- API Token: `11234567890abcdef`
- Git Repository URL: `https://github.com/user/repo.git`
- Git Branch: `main`
- Docker 이미지 이름: `python-app`
- Docker 이미지 태그: `latest`

**Kubernetes 환경 설정:**
- ✅ **🚢 Kubernetes 환경용 Pipeline 생성** 체크
- ✅ **🔧 Kaniko 사용 (권장 - privileged 모드 불필요)** 체크

**Harbor Registry 설정:**
- **Harbor Registry URL**: `harbor.devops.cicd.test/python`
  - ⚠️ 프로토콜(`https://`) 제외
  - ✅ 프로젝트 이름 포함
- **Jenkins Credential ID**: `harbor-credentials`
  - Jenkins에 등록한 Credential ID

#### 3. Pipeline 미리보기

"**Pipeline 미리보기**" 버튼을 클릭하여 생성된 Groovy 스크립트 확인

#### 4. 빌드 실행

"**Jenkins에서 빌드하기**" 또는 미리보기 모달에서 "**이 Pipeline으로 빌드하기**" 클릭

---

## 생성되는 Pipeline

### Kubernetes + Kaniko + Harbor Pipeline

```groovy
pipeline {
    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
metadata:
  labels:
    jenkins: agent
spec:
  containers:
  - name: kaniko
    image: gcr.io/kaniko-project/executor:debug
    command:
    - /busybox/cat
    tty: true
'''
        }
    }

    parameters {
        string(name: 'IMAGE_NAME', defaultValue: 'python-app', description: 'Docker image name')
        string(name: 'IMAGE_TAG', defaultValue: 'latest', description: 'Docker image tag')
        string(name: 'REGISTRY_URL', defaultValue: 'harbor.devops.cicd.test/python', description: 'Harbor registry URL')
    }

    stages {
        stage('Checkout') {
            steps {
                container('kaniko') {
                    echo 'Cloning repository...'
                    git url: 'https://github.com/user/repo.git',
                        branch: 'main'
                }
            }
        }

        stage('Create Dockerfile') {
            steps {
                container('kaniko') {
                    echo 'Creating Dockerfile from generated content...'
                    script {
                        def dockerfileContent = """
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
"""
                        writeFile file: 'Dockerfile', text: dockerfileContent
                        echo 'Dockerfile created successfully'
                        sh 'cat Dockerfile'
                    }
                }
            }
        }

        stage('Build Docker Image with Kaniko') {
            steps {
                container('kaniko') {
                    echo "Building Docker image with Kaniko: ${params.IMAGE_NAME}:${params.IMAGE_TAG}"
                    script {
                        def destination = params.REGISTRY_URL + "/" + params.IMAGE_NAME + ":" + params.IMAGE_TAG
                        echo "Destination: ${destination}"
                        def cacheRepo = params.REGISTRY_URL + "/cache"

                        withCredentials([usernamePassword(credentialsId: 'harbor-credentials',
                                                           usernameVariable: 'HARBOR_USER',
                                                           passwordVariable: 'HARBOR_PASS')]) {
                            sh """
                                mkdir -p /kaniko/.docker
                                cat > /kaniko/.docker/config.json << EOF
{"auths":{"${params.REGISTRY_URL}":{"username":"${HARBOR_USER}","password":"${HARBOR_PASS}"}}}
EOF
                                /kaniko/executor \\
                                  --context=\$(pwd) \\
                                  --dockerfile=Dockerfile \\
                                  --destination=${destination} \\
                                  --cache=true \\
                                  --cache-repo=${cacheRepo} \\
                                  --skip-tls-verify
                            """
                        }
                    }
                    echo 'Image built and pushed to Harbor successfully!'
                }
            }
        }
    }

    post {
        success {
            echo 'Docker image built and pushed to Harbor successfully!'
            echo "Image: ${params.REGISTRY_URL}/${params.IMAGE_NAME}:${params.IMAGE_TAG}"
        }
        failure {
            echo 'Build failed!'
            echo 'Check the console output for details'
        }
        always {
            echo 'Build completed'
        }
    }
}
```

### Kaniko 명령어 상세

```bash
/kaniko/executor \
  --context=$(pwd)                                    # 빌드 컨텍스트 (현재 디렉토리)
  --dockerfile=Dockerfile                             # Dockerfile 경로
  --destination=harbor.devops.cicd.test/python/python-app:latest  # 푸시할 이미지
  --cache=true                                        # 캐시 활성화
  --cache-repo=harbor.devops.cicd.test/python/cache   # 캐시 저장소
  --skip-tls-verify                                   # TLS 인증서 검증 건너뛰기
```

#### 옵션 설명

| 옵션 | 설명 |
|------|------|
| `--context` | 빌드 컨텍스트 경로 |
| `--dockerfile` | Dockerfile 경로 |
| `--destination` | 푸시할 이미지 전체 경로 (registry/project/image:tag) |
| `--cache` | 빌드 캐시 사용 여부 |
| `--cache-repo` | 캐시를 저장할 레지스트리 경로 |
| `--skip-tls-verify` | Self-signed 인증서 사용 시 필요 |
| `--no-push` | 로컬 빌드만 (tar 파일로 저장) |
| `--tar-path` | tar 파일 저장 경로 |

---

## 트러블슈팅

### 1. `secret "xxx" not found`

**에러:**
```
MountVolume.SetUp failed for volume "docker-config" : secret "harborUser" not found
```

**원인**: Kubernetes Secret을 찾으려고 시도

**해결**: 이 솔루션은 Jenkins Credential을 사용하므로 별도의 Kubernetes Secret 불필요. Pipeline 스크립트가 `withCredentials` 블록을 사용하는지 확인.

### 2. `certificate signed by unknown authority`

**에러:**
```
error checking push permissions: creating push check transport for harbor.devops.cicd.test failed:
Get "https://harbor.devops.cicd.test/v2/": tls: failed to verify certificate: x509: certificate signed by unknown authority
```

**원인**: Harbor가 자체 서명 인증서(self-signed certificate) 사용

**해결**: ✅ **이미 적용됨** - Pipeline에 `--skip-tls-verify` 옵션 포함됨

**프로덕션 환경에서는**:
1. Harbor에 신뢰할 수 있는 인증서 설치 (Let's Encrypt 등)
2. 또는 Harbor CA 인증서를 ConfigMap으로 마운트

### 3. `UNAUTHORIZED: authentication required`

**에러:**
```
error checking push permissions: UNAUTHORIZED: authentication required
```

**원인**: Harbor 인증 실패

**해결**:
1. Jenkins Credential 확인:
   ```bash
   # Jenkins → Credentials → Global → harbor-credentials 확인
   ```
2. Harbor에서 사용자 권한 확인:
   - Harbor UI → Projects → python → Members
   - Push Artifact 권한 필요
3. Credential ID가 Pipeline과 일치하는지 확인

### 4. `denied: requested access to the resource is denied`

**에러:**
```
denied: requested access to the resource is denied
```

**원인**: Harbor 프로젝트 권한 부족

**해결**:
- Harbor UI → Projects → python → Members
- 사용자에게 Developer 또는 Maintainer 역할 부여

### 5. Pipeline 미리보기 에러: `f-string expression part cannot include a backslash`

**에러:**
```
Preview generation failed: f-string expression part cannot include a backslash
```

**원인**: Python f-string에서 백슬래시 사용 불가

**해결**: ✅ **이미 해결됨** - raw string과 heredoc 사용

### 6. 환경변수가 치환되지 않음

**증상:**
```
echo '{"auths":{"${REGISTRY_URL}":...}}'
# 출력: {"auths":{"${REGISTRY_URL}":...}}  (변수 그대로)
```

**원인**: Groovy single quote (`'''`)는 변수 치환 안 함

**해결**: ✅ **이미 해결됨** - triple double quote (`"""`) 사용

### 7. `a repository name must be specified`

**에러:**
```
error pushing image: getting tag for destination: a repository name must be specified
```

**원인**: `--destination` 파라미터가 비어있음

**해결**: ✅ **이미 해결됨** - 변수가 제대로 치환되도록 수정

---

## 캐시 관리

### 캐시란?

Kaniko는 빌드 속도를 높이기 위해 Dockerfile의 각 레이어를 캐시합니다.

```
harbor.devops.cicd.test/python/
├── python-app:latest          ← 실제 애플리케이션 이미지
├── cache:<hash1>               ← 레이어 1 캐시 (base image)
├── cache:<hash2>               ← 레이어 2 캐시 (dependencies)
└── cache:<hash3>               ← 레이어 3 캐시 (application code)
```

### 캐시의 장점

✅ **빌드 속도 향상**
- 첫 빌드: 5분
- 캐시 사용 시: 30초~1분

✅ **네트워크 트래픽 절감**
- pip/npm 패키지를 매번 다운로드하지 않음

✅ **리소스 절약**
- 변경되지 않은 레이어는 재사용

### 캐시 동작 방식

```
빌드 1 (첫 빌드):
FROM python:3.11-slim           → 캐시에 저장
COPY requirements.txt .         → 캐시에 저장
RUN pip install -r requirements → 캐시에 저장 (시간 소요)
COPY . .                        → 캐시에 저장

빌드 2 (코드만 변경):
FROM python:3.11-slim           → 캐시에서 가져옴 ⚡
COPY requirements.txt .         → 캐시에서 가져옴 ⚡
RUN pip install -r requirements → 캐시에서 가져옴 ⚡ (빠름!)
COPY . .                        → 새로 빌드
```

### Harbor에서 캐시 확인

**Harbor UI:**
1. Projects → python → Repositories
2. `cache` 레포지토리 확인
3. 여러 개의 태그(해시값) 확인

**CLI:**
```bash
# Harbor에서 캐시 이미지 목록 확인
curl -u "admin:Harbor12345" https://harbor.devops.cicd.test/api/v2.0/projects/python/repositories/cache/artifacts

# 캐시 이미지 삭제 (수동)
docker rmi harbor.devops.cicd.test/python/cache:<hash>
```

### 캐시 자동 정리

오래된 캐시를 자동으로 정리하려면:

#### Harbor Tag Retention Rule 설정

1. **Harbor UI → Projects → python → Policy**
2. **Tag Retention** 탭
3. **Add Rule** 클릭
4. 설정:
   - **Repository**: `cache`
   - **Retain**: `most recently pushed # artifacts`
   - **Count**: `10` (최근 10개만 유지)
   - **Schedule**: `Daily at 2:00 AM`
5. **Save**

#### 효과
- 최근 10개 캐시만 유지
- 매일 자동으로 오래된 캐시 삭제
- Harbor 저장소 공간 절약

### 캐시 비활성화 (권장하지 않음)

캐시를 사용하지 않으려면:

```groovy
// 현재 (캐시 사용)
/kaniko/executor --context=$(pwd) --dockerfile=Dockerfile --destination=${destination} --cache=true --cache-repo=${cacheRepo}

// 캐시 비활성화
/kaniko/executor --context=$(pwd) --dockerfile=Dockerfile --destination=${destination}
```

**⚠️ 주의**: 캐시 비활성화 시 매 빌드마다 모든 레이어를 처음부터 빌드하므로 시간이 오래 걸립니다.

---

## 로컬 빌드 (Harbor 푸시 없이)

Harbor에 푸시하지 않고 로컬에서만 빌드하려면:

### 웹 UI 설정
- **Harbor Registry URL**: 비워두기 ← 중요!
- **Harbor Credential ID**: 비워두기

### 생성되는 Pipeline

```groovy
stage('Build Docker Image with Kaniko') {
    steps {
        container('kaniko') {
            script {
                def destination = params.IMAGE_NAME + ":" + params.IMAGE_TAG
                echo "Destination: ${destination}"
                sh "/kaniko/executor --context=\$(pwd) --dockerfile=Dockerfile --no-push --destination=${destination} --tar-path=image.tar"
            }
            echo 'Image built successfully and saved as image.tar'
        }
    }
}

stage('Verify Image') {
    steps {
        container('kaniko') {
            echo 'Verifying built image tarball...'
            sh 'ls -lh image.tar'
        }
    }
}
```

### 빌드 결과

```bash
# Jenkins 워크스페이스에 image.tar 생성
-rw-r--r-- 1 jenkins jenkins 150M Jan 01 12:00 image.tar
```

### tar 파일 사용

```bash
# 로컬 Docker에 로드
docker load < image.tar

# 이미지 확인
docker images | grep python-app

# 실행
docker run -p 8080:8080 python-app:latest
```

---

## 비교표

### Harbor 푸시 vs 로컬 빌드

| 항목 | Harbor 푸시 | 로컬 빌드 (tar) |
|------|------------|----------------|
| **Harbor URL 설정** | ✅ 필요 | ❌ 비워둠 |
| **Jenkins Credential** | ✅ 필요 | ❌ 불필요 |
| **결과물** | Harbor에 이미지 푸시 | tar 파일 생성 |
| **캐싱** | ✅ 가능 | ❌ 불가능 |
| **팀 공유** | ✅ 가능 | ❌ 수동 전송 필요 |
| **배포** | ✅ Harbor에서 pull | ❌ tar 파일 전송 필요 |
| **권장 용도** | 프로덕션, 개발 환경 | 테스트, 로컬 개발 |

---

## 보안 권장사항

### 1. Robot Account 사용

개인 계정 대신 Robot Account 사용:
- ✅ 토큰 만료 설정 가능
- ✅ 제한된 권한만 부여
- ✅ 감사 로그에서 명확히 식별

### 2. Jenkins Credential 보안

- ✅ Jenkins Credentials Plugin 사용 (암호화 저장)
- ❌ Pipeline 스크립트에 평문 비밀번호 금지
- ✅ Credential ID만 사용

### 3. RBAC 설정

Harbor 프로젝트에 최소 권한 부여:
- **Developer**: Pull + Push (빌드용)
- **Guest**: Pull only (배포용)
- **Maintainer**: 전체 관리

### 4. TLS 인증서

프로덕션 환경:
- ✅ 신뢰할 수 있는 인증서 사용 (Let's Encrypt)
- ❌ `--skip-tls-verify` 사용 금지

개발/테스트 환경:
- ⚠️ `--skip-tls-verify` 허용

### 5. 이미지 취약점 스캔

Harbor의 Trivy 스캔 활성화:
```yaml
# Harbor project 설정
vulnerability_severity: high
auto_scan: true
prevent_vulnerable_images: true
```

---

## 성능 최적화

### 1. Dockerfile 최적화

```dockerfile
# ❌ 나쁜 예 - 캐시 활용 불가
FROM python:3.11-slim
COPY . .
RUN pip install -r requirements.txt

# ✅ 좋은 예 - 캐시 활용
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt  # ← 캐시됨 (requirements 변경 시만 재실행)
COPY . .                             # ← 코드 변경 시만 재실행
```

### 2. 멀티스테이지 빌드

```dockerfile
# Build stage
FROM python:3.11 as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 3. 캐시 워밍

첫 빌드를 미리 실행하여 캐시 생성:
```bash
# Jenkins에서 첫 빌드 실행
# 이후 빌드는 캐시 덕분에 빠름
```

---

## 참고 자료

### 공식 문서
- [Kaniko 공식 문서](https://github.com/GoogleContainerTools/kaniko)
- [Harbor 공식 문서](https://goharbor.io/docs/)
- [Jenkins Kubernetes Plugin](https://plugins.jenkins.io/kubernetes/)

### 관련 문서
- `KANIKO_INTEGRATION.md`: Kaniko 상세 가이드
- `HARBOR_SETUP.md`: Harbor 초기 설정 가이드
- `KUBERNETES_JENKINS.md`: Kubernetes Jenkins 설정

---

## 요약

### ✅ 이 솔루션으로 해결된 문제들

1. ❌ `docker: not found` → ✅ Kaniko 사용
2. ❌ `ContainersNotReady` (DinD) → ✅ Kaniko (privileged 불필요)
3. ❌ `certificate signed by unknown authority` → ✅ `--skip-tls-verify`
4. ❌ Kubernetes Secret 복잡도 → ✅ Jenkins Credential 사용
5. ❌ 느린 빌드 속도 → ✅ Remote 캐시

### 🚀 주요 장점

- **보안**: Privileged 모드 불필요, Jenkins Credential 암호화
- **속도**: Remote 캐시로 빌드 시간 단축 (5분 → 30초)
- **안정성**: Pod 시작 문제 없음
- **편의성**: 웹 UI에서 간단히 설정

### 🎯 권장 설정

**프로덕션 환경:**
```
✅ Kubernetes 환경용 Pipeline
✅ Kaniko 사용
✅ Harbor 푸시
✅ Robot Account
✅ Tag Retention (캐시 정리)
⚠️ 신뢰할 수 있는 TLS 인증서
```

**개발/테스트 환경:**
```
✅ Kubernetes 환경용 Pipeline
✅ Kaniko 사용
✅ Harbor 푸시
✅ --skip-tls-verify (self-signed cert)
✅ 캐시 활성화
```

**로컬 테스트:**
```
✅ Kubernetes 환경용 Pipeline
✅ Kaniko 사용
❌ Harbor URL 비우기 (tar 파일로 저장)
```

---

## 체크리스트

빌드 전 확인사항:

- [ ] Jenkins Credential 생성 (`harbor-credentials`)
- [ ] Harbor 프로젝트 권한 확인 (Push Artifact)
- [ ] Jenkins Job 생성 (Pipeline 타입)
- [ ] Git Repository 접근 가능
- [ ] Kubernetes 환경 체크 ✅
- [ ] Kaniko 사용 체크 ✅
- [ ] Harbor URL 입력 (`harbor.devops.cicd.test/python`)
- [ ] Harbor Credential ID 입력 (`harbor-credentials`)
- [ ] Pipeline 미리보기로 스크립트 확인
- [ ] 빌드 실행 및 결과 확인

빌드 후 확인:

- [ ] Jenkins 콘솔 로그 확인
- [ ] Harbor에서 이미지 확인 (`python/python-app:latest`)
- [ ] Harbor에서 캐시 확인 (`python/cache`)
- [ ] 이미지 pull 테스트: `docker pull harbor.devops.cicd.test/python/python-app:latest`
- [ ] 컨테이너 실행 테스트: `docker run -p 8080:8080 harbor.devops.cicd.test/python/python-app:latest`

---

**문서 버전**: 1.0
**최종 수정일**: 2026-02-05
**작성자**: Containerization Solution Team
