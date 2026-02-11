# Kubernetes 환경의 Jenkins에서 Docker 빌드하기

Jenkins가 Kubernetes 클러스터에서 실행 중일 때 Docker 이미지를 빌드하는 방법입니다.

## 문제점

Kubernetes 위의 Jenkins에서 일반 Pipeline을 실행하면 다음과 같은 에러가 발생합니다:

```bash
docker: not found
```

이는 Jenkins agent Pod에 Docker가 설치되어 있지 않기 때문입니다.

## 해결 방법

### ✅ 이 도구에서의 자동 해결

Containerization Solution은 Kubernetes 환경을 자동으로 지원합니다:

1. **Jenkins 빌드 설정** 섹션에서
2. **"🚢 Kubernetes 환경용 Pipeline 생성"** 체크박스를 선택
3. Pipeline을 생성하면 자동으로 Kubernetes 호환 Pipeline이 생성됩니다

### 🔧 기술적 세부 사항

Kubernetes 환경용 Pipeline은 다음과 같은 구조를 사용합니다:

#### 1. **podTemplate 사용**

```groovy
agent {
    kubernetes {
        yaml '''
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: docker
    image: docker:24-dind
    securityContext:
      privileged: true
  - name: docker-client
    image: docker:24-cli
    command: [cat]
    tty: true
'''
    }
}
```

#### 2. **Docker-in-Docker (DinD) 컨테이너**

- **docker** 컨테이너: Docker daemon 실행
- **docker-client** 컨테이너: Docker CLI 제공
- 두 컨테이너가 Unix socket을 공유하여 통신

#### 3. **Container 지정**

각 stage에서 사용할 컨테이너를 명시:

```groovy
stage('Build Docker Image') {
    steps {
        container('docker-client') {
            sh "docker build -t ${params.IMAGE_NAME}:${params.IMAGE_TAG} ."
        }
    }
}
```

## 사용 방법

### 웹 UI에서

1. Dockerfile 생성
2. Jenkins 설정 섹션에서:
   - ✅ **"Kubernetes 환경용 Pipeline 생성"** 체크
   - Jenkins URL, Job 이름, API Token 입력
   - Git Repository 정보 입력
   - Docker 이미지 이름 및 태그 입력
3. "Pipeline 미리보기"로 생성된 스크립트 확인
4. "Jenkins에서 빌드하기" 클릭

### 생성되는 Pipeline 구조

```groovy
pipeline {
    agent {
        kubernetes {
            yaml '''
            # Pod 정의 (Docker DinD + Client)
            '''
        }
    }

    stages {
        stage('Checkout') {
            steps {
                container('docker-client') {
                    // Git 체크아웃
                }
            }
        }

        stage('Create Dockerfile') {
            steps {
                container('docker-client') {
                    // Dockerfile 생성
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                container('docker-client') {
                    // Docker 빌드
                    sh "docker build -t ${params.IMAGE_NAME}:${params.IMAGE_TAG} ."
                }
            }
        }

        stage('Verify Image') {
            steps {
                container('docker-client') {
                    // 이미지 확인
                    sh 'docker images | grep ${params.IMAGE_NAME}'
                }
            }
        }
    }
}
```

## Jenkins 사전 요구사항

### 1. **Kubernetes Plugin 설치**

Jenkins → Manage Jenkins → Plugins → Available plugins
- **Kubernetes plugin** 설치

### 2. **Kubernetes 설정**

Jenkins → Manage Jenkins → Configure System → Cloud
- Kubernetes 클라우드 추가
- Kubernetes URL 설정
- Namespace 설정

### 3. **Pod Security**

DinD 사용을 위해 `privileged` 모드가 필요합니다.

#### PodSecurityPolicy (K8s < 1.25)

```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: jenkins-agent-psp
spec:
  privileged: true
  allowPrivilegeEscalation: true
  volumes:
    - 'emptyDir'
  runAsUser:
    rule: 'RunAsAny'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
```

#### PodSecurity (K8s >= 1.25)

Namespace에 `privileged` 레벨 설정:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: jenkins
  labels:
    pod-security.kubernetes.io/enforce: privileged
    pod-security.kubernetes.io/audit: privileged
    pod-security.kubernetes.io/warn: privileged
```

## 대안 방법들

### 방법 1: Kaniko 사용 (권장 - Privileged 불필요)

Docker 대신 Kaniko를 사용하면 `privileged` 모드 없이 빌드 가능:

```groovy
agent {
    kubernetes {
        yaml '''
        containers:
        - name: kaniko
          image: gcr.io/kaniko-project/executor:debug
          command: ["/busybox/cat"]
          tty: true
        '''
    }
}

stage('Build') {
    steps {
        container('kaniko') {
            sh """
            /kaniko/executor \\
              --context=. \\
              --dockerfile=Dockerfile \\
              --destination=${IMAGE_NAME}:${IMAGE_TAG}
            """
        }
    }
}
```

### 방법 2: Buildah 사용

rootless 컨테이너 빌드:

```groovy
containers:
- name: buildah
  image: quay.io/buildah/stable
```

### 방법 3: Docker Socket 마운트 (비권장 - 보안 위험)

호스트의 Docker socket을 마운트:

```yaml
volumeMounts:
- name: docker-sock
  mountPath: /var/run/docker.sock
volumes:
- name: docker-sock
  hostPath:
    path: /var/run/docker.sock
```

**⚠️ 보안 위험**: 호스트 Docker에 직접 접근 가능

## 트러블슈팅

### 1. "docker: not found" 에러

- ✅ **해결**: "Kubernetes 환경용 Pipeline 생성" 체크박스 선택

### 2. "permission denied" 에러

- Namespace에 `privileged` PodSecurity 레벨 설정
- 또는 Kaniko 사용 고려

### 3. "cannot connect to Docker daemon" 에러

- DinD 컨테이너가 제대로 시작되었는지 확인
- `DOCKER_TLS_CERTDIR` 환경변수 설정 확인

### 4. 빌드가 매우 느림

- 각 빌드마다 새 DinD 컨테이너 시작
- 캐싱 전략 고려 (Docker registry 사용)

## 성능 최적화

### 1. **레지스트리 캐시 사용**

빌드한 이미지를 레지스트리에 푸시하고 재사용:

```groovy
stage('Push to Registry') {
    steps {
        container('docker-client') {
            sh """
            docker push ${IMAGE_NAME}:${IMAGE_TAG}
            """
        }
    }
}
```

### 2. **PersistentVolume으로 Docker 캐시**

```yaml
volumes:
- name: docker-cache
  persistentVolumeClaim:
    claimName: docker-cache-pvc
```

### 3. **멀티스테이지 빌드**

Dockerfile에서 멀티스테이지 빌드 사용

## 참고 자료

- [Jenkins Kubernetes Plugin Documentation](https://plugins.jenkins.io/kubernetes/)
- [Docker-in-Docker Best Practices](https://jpetazzo.github.io/2015/09/03/do-not-use-docker-in-docker-for-ci/)
- [Kaniko Documentation](https://github.com/GoogleContainerTools/kaniko)
- [Kubernetes PodSecurity](https://kubernetes.io/docs/concepts/security/pod-security-standards/)

## 요약

| 항목 | 일반 Pipeline | Kubernetes Pipeline |
|------|--------------|-------------------|
| **Agent** | `agent any` | `agent { kubernetes { ... } }` |
| **Docker** | 호스트 Docker 사용 | DinD 컨테이너 사용 |
| **권한** | 일반 | `privileged: true` 필요 |
| **빌드 명령** | `docker.build()` | `sh "docker build ..."` |
| **Container 지정** | 불필요 | `container('docker-client')` 필요 |
| **적용 대상** | VM/물리 서버 Jenkins | Kubernetes Jenkins |

✅ **이 도구는 체크박스 하나로 자동 전환합니다!**
