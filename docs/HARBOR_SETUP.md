# Harbor Registry 연동 가이드

## 개요

이 가이드는 Kaniko를 사용하여 Jenkins에서 빌드한 Docker 이미지를 Harbor Registry에 푸시하는 방법을 설명합니다.

## Harbor란?

Harbor는 오픈소스 컨테이너 이미지 레지스트리로, Docker Hub의 프라이빗 대안입니다.

- ✅ Role-based access control (RBAC)
- ✅ 이미지 취약점 스캐닝
- ✅ 이미지 서명 및 검증
- ✅ 복제 및 동기화

## 사전 준비사항

### 1. Harbor 접속 정보

- **Harbor URL**: 예) `harbor.example.com` 또는 `harbor.example.com/myproject`
- **Harbor Username**: 예) `admin` 또는 `robot$myrobot`
- **Harbor Password**: 사용자 비밀번호 또는 Robot Account 토큰

### 2. Kubernetes Secret 생성

Jenkins가 Harbor에 인증하려면 Docker registry secret이 필요합니다.

#### 방법 1: kubectl로 secret 생성 (권장)

```bash
kubectl create secret docker-registry harbor-credentials \
  --docker-server=harbor.example.com \
  --docker-username=admin \
  --docker-password=Harbor12345 \
  --docker-email=admin@example.com \
  -n devops-toolchain
```

**파라미터 설명:**
- `harbor-credentials`: Secret 이름 (Jenkins에서 사용할 ID)
- `harbor.example.com`: Harbor 서버 주소 (프로토콜 제외)
- `admin`: Harbor 사용자명
- `Harbor12345`: Harbor 비밀번호
- `devops-toolchain`: Jenkins가 실행되는 네임스페이스

#### 방법 2: YAML 파일로 secret 생성

먼저 Docker config.json 생성:

```bash
# Docker 로그인으로 config.json 생성
docker login harbor.example.com
Username: admin
Password: Harbor12345

# config.json을 base64로 인코딩
cat ~/.docker/config.json | base64
```

그 다음 Secret YAML 생성:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: harbor-credentials
  namespace: devops-toolchain
type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: <base64-encoded-config.json>
```

적용:

```bash
kubectl apply -f harbor-secret.yaml
```

#### Secret 확인

```bash
kubectl get secret harbor-credentials -n devops-toolchain
kubectl describe secret harbor-credentials -n devops-toolchain
```

### 3. Harbor Robot Account 생용 (권장)

개인 계정 대신 Robot Account를 사용하는 것이 보안상 좋습니다.

Harbor UI에서:
1. Project 선택
2. Robot Accounts 탭
3. "New Robot Account" 클릭
4. 이름 입력 (예: `jenkins-builder`)
5. 권한 선택:
   - ✅ Push Artifact
   - ✅ Pull Artifact
6. 생성된 토큰 복사 (한 번만 표시됨!)

Robot Account 이름은 `robot$jenkins-builder` 형식입니다.

```bash
kubectl create secret docker-registry harbor-credentials \
  --docker-server=harbor.example.com \
  --docker-username=robot\$jenkins-builder \
  --docker-password=<ROBOT_TOKEN> \
  -n devops-toolchain
```

## 웹 UI에서 사용하기

### 1. 기본 설정

1. **언어 선택** 및 **Dockerfile 설정** 완료
2. **Jenkins 설정** 섹션에서:
   - ✅ "Jenkins 빌드 자동화" 체크
   - Jenkins URL, Job 이름, API Token 입력
   - Git Repository 정보 입력
   - Docker 이미지 이름 및 태그 입력

### 2. Kubernetes 환경 설정

3. ✅ **"🚢 Kubernetes 환경용 Pipeline 생성"** 체크
4. ✅ **"🔧 Kaniko 사용 (권장 - privileged 모드 불필요)"** 체크

### 3. Harbor Registry 설정

5. **Harbor Registry 설정** 섹션에서:
   - **Harbor Registry URL**: `harbor.example.com/myproject`
     - 프로젝트 이름까지 포함
     - 프로토콜(`https://`) 제외
   - **Jenkins Credential ID**: `harbor-credentials`
     - 위에서 생성한 Kubernetes Secret 이름

### 4. Pipeline 미리보기 및 빌드

6. **"Pipeline 미리보기"** 버튼 클릭하여 생성된 스크립트 확인
7. **"Jenkins에서 빌드하기"** 또는 미리보기 모달에서 **"이 Pipeline으로 빌드하기"** 클릭

## 생성되는 Pipeline

### Harbor 푸시 포함 Pipeline

```groovy
pipeline {
    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: kaniko
    image: gcr.io/kaniko-project/executor:debug
    command:
    - /busybox/cat
    tty: true
    volumeMounts:
    - name: docker-config
      mountPath: /kaniko/.docker
  volumes:
  - name: docker-config
    secret:
      secretName: harbor-credentials
      items:
      - key: .dockerconfigjson
        path: config.json
'''
        }
    }

    parameters {
        string(name: 'IMAGE_NAME', defaultValue: 'myapp', description: 'Docker image name')
        string(name: 'IMAGE_TAG', defaultValue: 'latest', description: 'Docker image tag')
        string(name: 'REGISTRY_URL', defaultValue: 'harbor.example.com/myproject', description: 'Harbor registry URL')
    }

    stages {
        stage('Build Docker Image with Kaniko') {
            steps {
                container('kaniko') {
                    script {
                        def destination = params.REGISTRY_URL + "/" + params.IMAGE_NAME + ":" + params.IMAGE_TAG
                        sh """/kaniko/executor --context=$(pwd) --dockerfile=Dockerfile --destination=${destination} --cache=true --cache-repo=${params.REGISTRY_URL}/cache"""
                    }
                }
            }
        }
    }

    post {
        success {
            echo 'Docker image built and pushed to Harbor successfully!'
            echo "Image: ${params.REGISTRY_URL}/${params.IMAGE_NAME}:${params.IMAGE_TAG}"
        }
    }
}
```

### 로컬 빌드만 (Harbor 미사용)

Harbor URL을 비워두면 이미지를 tar 파일로만 저장합니다:

```groovy
sh """/kaniko/executor --context=$(pwd) --dockerfile=Dockerfile --no-push --destination=${params.IMAGE_NAME}:${params.IMAGE_TAG} --tar-path=image.tar"""
```

## Harbor에서 이미지 확인

빌드 후 Harbor UI에서 확인:

1. Harbor 웹 UI 접속
2. 프로젝트 선택 (예: `myproject`)
3. Repositories 탭에서 이미지 확인
4. 태그 목록에서 방금 푸시한 태그 확인

또는 CLI로 확인:

```bash
# Harbor에서 이미지 목록 확인 (curl 사용)
curl -u "admin:Harbor12345" https://harbor.example.com/api/v2.0/projects/myproject/repositories

# Docker로 이미지 pull 테스트
docker pull harbor.example.com/myproject/myapp:latest
```

## 트러블슈팅

### 1. "UNAUTHORIZED: authentication required"

**원인**: Harbor 인증 실패

**해결**:
```bash
# Secret이 제대로 생성되었는지 확인
kubectl get secret harbor-credentials -n devops-toolchain -o yaml

# Secret 데이터 디코딩 확인
kubectl get secret harbor-credentials -n devops-toolchain -o jsonpath='{.data.\.dockerconfigjson}' | base64 -d

# 필요시 Secret 재생성
kubectl delete secret harbor-credentials -n devops-toolchain
kubectl create secret docker-registry harbor-credentials \
  --docker-server=harbor.example.com \
  --docker-username=admin \
  --docker-password=Harbor12345 \
  -n devops-toolchain
```

### 2. "x509: certificate signed by unknown authority"

**원인**: Harbor가 자체 서명 인증서(self-signed certificate) 사용

**해결**: Kaniko에 insecure registry 옵션 추가 (권장하지 않음)

또는 Harbor 인증서를 ConfigMap으로 마운트:

```yaml
volumeMounts:
- name: harbor-ca
  mountPath: /kaniko/ssl/certs/
volumes:
- name: harbor-ca
  configMap:
    name: harbor-ca-cert
```

### 3. "denied: requested access to the resource is denied"

**원인**: Harbor 프로젝트 권한 부족

**해결**:
- Harbor UI에서 프로젝트 멤버십 확인
- Push 권한이 있는지 확인
- Robot Account 권한 확인 (Push Artifact)

### 4. "NAME_UNKNOWN: project myproject not found"

**원인**: Harbor 프로젝트가 존재하지 않음

**해결**:
- Harbor UI에서 프로젝트 생성
- 프로젝트 이름 철자 확인

### 5. Secret을 찾을 수 없음

**원인**: Secret이 다른 네임스페이스에 생성됨

**해결**:
```bash
# Jenkins Pod가 실행 중인 네임스페이스 확인
kubectl get pods -A | grep jenkins

# 해당 네임스페이스에 Secret 생성
kubectl create secret docker-registry harbor-credentials \
  --docker-server=harbor.example.com \
  --docker-username=admin \
  --docker-password=Harbor12345 \
  -n <JENKINS_NAMESPACE>
```

## 보안 모범 사례

### 1. Robot Account 사용

개인 계정 대신 Robot Account 사용:
- ✅ 토큰 만료 설정 가능
- ✅ 제한된 권한만 부여
- ✅ 감사 로그에서 명확히 식별

### 2. RBAC 설정

Harbor 프로젝트에 최소 권한만 부여:
- Developer: Pull + Push
- Guest: Pull only

### 3. 이미지 취약점 스캔

Harbor의 Trivy 스캔 활성화:
```yaml
# Harbor project 설정
vulnerability_severity: high
auto_scan: true
prevent_vulnerable_images: true
```

### 4. Secret 암호화

Kubernetes Secret은 기본적으로 base64 인코딩만 되어 있습니다.

실제 암호화를 위해 Sealed Secrets 또는 External Secrets Operator 사용 권장.

## 참고 자료

- [Harbor 공식 문서](https://goharbor.io/docs/)
- [Kaniko 문서](https://github.com/GoogleContainerTools/kaniko)
- [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)
- [Harbor Robot Accounts](https://goharbor.io/docs/2.0.0/working-with-projects/project-configuration/create-robot-accounts/)

## 요약

### Harbor 푸시 활성화 시:
- ✅ 이미지가 Harbor Registry에 푸시됨
- ✅ 레이어 캐싱으로 빌드 속도 향상
- ✅ 팀 전체가 이미지 공유 가능
- ❌ tar 파일 생성 안 됨

### Harbor 푸시 비활성화 시 (URL 비움):
- ✅ 이미지가 `image.tar` 파일로 저장됨
- ✅ Registry 인증 불필요
- ❌ 다른 환경에서 사용하려면 tar 파일 전송 필요
- ❌ 빌드 캐싱 안 됨

**프로덕션 환경에서는 Harbor 푸시 사용을 권장합니다!**
