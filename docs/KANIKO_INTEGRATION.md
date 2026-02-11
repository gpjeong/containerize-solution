# Kaniko Integration for Kubernetes Jenkins

## 개요

Kaniko는 Docker daemon 없이 컨테이너 이미지를 빌드할 수 있는 Google의 도구입니다. Kubernetes 환경의 Jenkins에서 **privileged 모드 없이** 안전하게 Docker 이미지를 빌드할 수 있습니다.

## 문제 해결

### Docker-in-Docker (DinD)의 문제점

기존 Kubernetes 환경에서 Docker 빌드 시 발생하는 문제:

1. **privileged 모드 필요**
   - DinD 컨테이너는 `securityContext.privileged: true` 필요
   - 보안 정책에서 제한될 수 있음

2. **Pod 시작 실패**
   ```
   [Running][ContainersNotReady] containers with unready status: [docker]
   ```
   - DinD 컨테이너가 ready 상태가 되지 않음
   - readinessProbe 실패

3. **Docker daemon 연결 실패**
   ```
   Cannot connect to the Docker daemon at unix:///var/run/docker.sock
   ```

### Kaniko의 장점

✅ **privileged 모드 불필요** - 보안 정책 위반 없음
✅ **빠른 시작** - Docker daemon 초기화 불필요
✅ **안정적** - Pod readiness 문제 없음
✅ **Kubernetes 네이티브** - K8s 환경에 최적화

## 사용 방법

### 1. 웹 UI에서 활성화

Jenkins 설정 섹션에서:

1. ✅ **"🚢 Kubernetes 환경용 Pipeline 생성"** 체크
2. ✅ **"🔧 Kaniko 사용 (권장 - privileged 모드 불필요)"** 체크
3. Jenkins 및 Git 설정 입력
4. "Pipeline 미리보기"로 생성된 스크립트 확인
5. "Jenkins에서 빌드하기" 클릭

### 2. 생성되는 Pipeline 구조

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
    - name: kaniko-cache
      mountPath: /cache
  volumes:
  - name: kaniko-cache
    emptyDir: {}
'''
        }
    }

    stages {
        stage('Build Docker Image with Kaniko') {
            steps {
                container('kaniko') {
                    sh """
                        /kaniko/executor \\
                          --context=\$(pwd) \\
                          --dockerfile=Dockerfile \\
                          --no-push \\
                          --destination=\${IMAGE_NAME}:\${IMAGE_TAG} \\
                          --tar-path=image.tar \\
                          --cache=true \\
                          --cache-dir=/cache
                    """
                }
            }
        }
    }
}
```

### 3. Kaniko 빌드 옵션 설명

| 옵션 | 설명 |
|------|------|
| `--context` | 빌드 컨텍스트 경로 (현재 디렉토리) |
| `--dockerfile` | Dockerfile 경로 |
| `--no-push` | 레지스트리에 푸시하지 않음 (로컬 빌드만) |
| `--destination` | 이미지 이름 및 태그 |
| `--tar-path` | 빌드된 이미지를 tar 파일로 저장 |
| `--cache` | 빌드 캐시 사용 |
| `--cache-dir` | 캐시 디렉토리 경로 |

## 레지스트리에 푸시하기

이미지를 Docker Registry에 푸시하려면:

1. **Docker Registry Secret 생성**

```bash
kubectl create secret docker-registry regcred \
  --docker-server=<your-registry-server> \
  --docker-username=<your-username> \
  --docker-password=<your-password> \
  --docker-email=<your-email> \
  -n devops-toolchain
```

2. **Kaniko Pipeline 수정**

`--no-push` 옵션을 제거하고 registry 경로 포함:

```groovy
sh """
    /kaniko/executor \\
      --context=\$(pwd) \\
      --dockerfile=Dockerfile \\
      --destination=registry.example.com/\${IMAGE_NAME}:\${IMAGE_TAG} \\
      --cache=true \\
      --cache-dir=/cache
"""
```

3. **Pod에 Secret 마운트**

```yaml
spec:
  containers:
  - name: kaniko
    image: gcr.io/kaniko-project/executor:debug
    volumeMounts:
    - name: docker-config
      mountPath: /kaniko/.docker
  volumes:
  - name: docker-config
    secret:
      secretName: regcred
      items:
      - key: .dockerconfigjson
        path: config.json
```

## 비교: DinD vs Kaniko

| 항목 | Docker-in-Docker | Kaniko |
|------|------------------|--------|
| **Privileged 모드** | ✅ 필요 | ❌ 불필요 |
| **보안** | ⚠️ 낮음 | ✅ 높음 |
| **시작 속도** | 🐌 느림 (daemon 초기화) | ⚡ 빠름 |
| **안정성** | ⚠️ Pod ready 이슈 | ✅ 안정적 |
| **캐싱** | ✅ Docker 레이어 캐시 | ✅ Kaniko 캐시 |
| **멀티스테이지 빌드** | ✅ 완벽 지원 | ✅ 완벽 지원 |
| **로컬 이미지** | ✅ docker images로 확인 | ⚠️ tar 파일로 저장 |
| **복잡한 빌드** | ✅ 모든 Docker 기능 | ⚠️ 일부 제약 |

## 트러블슈팅

### 1. "executor: launcher not found" 에러

**원인**: Kaniko executor 이미지가 없음

**해결**:
```yaml
image: gcr.io/kaniko-project/executor:debug  # :latest 대신 :debug 사용
```

### 2. "UNAUTHORIZED: authentication required" 에러

**원인**: Registry 인증 실패

**해결**: Docker registry secret 생성 및 마운트 (위 "레지스트리에 푸시하기" 참조)

### 3. 빌드는 성공하지만 이미지가 없음

**원인**: `--no-push` 옵션 사용 시 이미지가 tar 파일로만 저장됨

**해결**:
- 이미지 확인: `ls -lh image.tar`
- tar에서 로드: `docker load < image.tar` (로컬 환경에서)
- 또는 `--no-push` 제거하고 registry에 푸시

### 4. 캐시가 작동하지 않음

**원인**: 캐시 디렉토리가 휘발성 emptyDir

**해결**: PersistentVolume 사용
```yaml
volumes:
- name: kaniko-cache
  persistentVolumeClaim:
    claimName: kaniko-cache-pvc
```

## 성능 최적화

### 1. PersistentVolume으로 캐시 유지

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: kaniko-cache-pvc
  namespace: devops-toolchain
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

### 2. Kaniko 옵션 최적화

```bash
/kaniko/executor \
  --context=$(pwd) \
  --dockerfile=Dockerfile \
  --destination=${IMAGE_NAME}:${IMAGE_TAG} \
  --cache=true \
  --cache-dir=/cache \
  --cache-repo=registry.example.com/cache \  # Remote cache
  --snapshot-mode=redo \  # 빠른 스냅샷
  --use-new-run        # 최적화된 RUN 명령
```

## 참고 자료

- [Kaniko 공식 문서](https://github.com/GoogleContainerTools/kaniko)
- [Kaniko vs Docker-in-Docker](https://github.com/GoogleContainerTools/kaniko#comparison-with-other-tools)
- [Jenkins Kubernetes Plugin](https://plugins.jenkins.io/kubernetes/)

## 요약

**Kubernetes 환경의 Jenkins라면 Kaniko 사용을 권장합니다!**

장점:
- ✅ Privileged 모드 불필요 (보안 강화)
- ✅ Pod 시작 및 빌드 안정성 향상
- ✅ 빠른 빌드 시작
- ✅ Kubernetes 네이티브

단점:
- ⚠️ 로컬에서 바로 이미지 실행 불가 (tar 또는 registry 필요)
- ⚠️ 일부 Docker 고급 기능 미지원

**이 도구에서는 체크박스 두 개로 자동 전환됩니다!**
