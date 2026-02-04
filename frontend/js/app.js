// Global state
let currentLanguage = null;
let currentSessionId = null;
let editor = null;

// Show/hide loading
function showLoading() {
    document.getElementById('loading').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading').classList.add('hidden');
}

// Language selection
function selectLanguage(language) {
    currentLanguage = language;

    // Hide config and preview steps (in case user is changing language)
    document.getElementById('step-config').classList.add('hidden');
    document.getElementById('step-preview').classList.add('hidden');

    // Show input step
    document.getElementById('step-input').classList.remove('hidden');

    // Hide all input sections
    document.querySelectorAll('.input-section').forEach(el => {
        el.classList.add('hidden');
    });

    // Show relevant input section
    document.getElementById(`input-${language}`).classList.remove('hidden');

    // Scroll to input section
    document.getElementById('step-input').scrollIntoView({ behavior: 'smooth' });
}

// Toggle Java input type (JAR vs Source)
function toggleJavaInput(type) {
    if (type === 'jar') {
        document.getElementById('java-jar-input').classList.remove('hidden');
        document.getElementById('java-source-input').classList.add('hidden');
    } else {
        document.getElementById('java-jar-input').classList.add('hidden');
        document.getElementById('java-source-input').classList.remove('hidden');
    }
}

// Move to configuration step
async function nextToConfig() {
    // For Java, check if file uploaded and analyze
    if (currentLanguage === 'java') {
        const javaType = document.querySelector('input[name="javaType"]:checked').value;

        if (javaType === 'jar') {
            const fileInput = document.getElementById('jarFile');
            if (fileInput.files.length > 0) {
                await uploadJavaFile(fileInput.files[0]);
            }
        }
        // For source projects, data will be sent during generation
    }

    // Show config step
    document.getElementById('step-config').classList.remove('hidden');
    document.getElementById('step-config').scrollIntoView({ behavior: 'smooth' });

    // Set default runtime version based on language
    const versionInput = document.getElementById('runtimeVersion');
    if (!versionInput.value) {
        const defaults = {
            'python': '3.11',
            'nodejs': '20',
            'java': '17'
        };
        versionInput.value = defaults[currentLanguage];
    }

    // Set default port
    const portInput = document.getElementById('port');
    if (currentLanguage === 'nodejs' && portInput.value === '8000') {
        portInput.value = '3000';
    } else if (currentLanguage === 'java' && portInput.value === '8000') {
        portInput.value = '8080';
    }
}

// Upload Java JAR file
async function uploadJavaFile(file) {
    showLoading();

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/upload/java', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }

        const data = await response.json();
        currentSessionId = data.session_id;

        alert('JAR 파일이 분석되었습니다!');
        console.log('Analysis result:', data.project_info);

    } catch (error) {
        alert('파일 업로드 실패: ' + error.message);
        console.error('Upload error:', error);
    } finally {
        hideLoading();
    }
}

// Parse environment variables
function parseEnvVars(envText) {
    const envVars = {};
    if (!envText) return envVars;

    envText.split('\n').forEach(line => {
        line = line.trim();
        if (line && line.includes('=')) {
            const [key, ...valueParts] = line.split('=');
            envVars[key.trim()] = valueParts.join('=').trim();
        }
    });

    return envVars;
}

// Parse system dependencies
function parseSystemDeps(depsText) {
    if (!depsText) return [];
    return depsText.trim().split(/\s+/).filter(d => d);
}

// Generate Dockerfile
async function generateDockerfile() {
    showLoading();

    try {
        // Build configuration based on language
        const config = {
            language: currentLanguage,
            runtime_version: document.getElementById('runtimeVersion').value,
            port: parseInt(document.getElementById('port').value),
            environment_vars: parseEnvVars(document.getElementById('envVars').value),
            health_check_path: document.getElementById('healthCheck').value,
            system_dependencies: parseSystemDeps(document.getElementById('systemDeps').value),
            base_image: document.getElementById('baseImage').value || null,
            user: 'appuser',
            service_url: document.getElementById('serviceUrl').value || null,
            custom_start_command: document.getElementById('startCommand').value || null
        };

        // Add language-specific config
        if (currentLanguage === 'python') {
            config.framework = document.getElementById('pythonFramework').value;
            config.requirements_content = document.getElementById('pythonRequirements').value || null;
            config.package_manager = 'pip';
            config.entrypoint_file = 'main.py';
        } else if (currentLanguage === 'nodejs') {
            config.framework = document.getElementById('nodejsFramework').value;
            const packageJsonText = document.getElementById('nodejsPackageJson').value;
            if (packageJsonText) {
                try {
                    config.package_json = JSON.parse(packageJsonText);
                } catch (e) {
                    alert('package.json 형식이 올바르지 않습니다.');
                    hideLoading();
                    return;
                }
            }
            config.package_manager = 'npm';
            config.start_command = config.custom_start_command || 'npm start';
        } else if (currentLanguage === 'java') {
            config.framework = 'spring-boot';

            const javaType = document.querySelector('input[name="javaType"]:checked').value;

            if (javaType === 'jar') {
                // JAR file (already uploaded)
                config.build_tool = 'jar';
                config.jar_file_name = 'app.jar';
            } else {
                // Source project (Maven/Gradle)
                config.build_tool = document.getElementById('javaBuildTool').value;
                config.build_file_content = document.getElementById('javaBuildFile').value || null;
                config.main_class = document.getElementById('javaMainClass').value || null;
            }

            config.jvm_options = '-Xmx512m';
        }

        // Make API request
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                config: config
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Generation failed');
        }

        const data = await response.json();
        currentSessionId = data.session_id;

        // Show preview
        showPreview(data.dockerfile);

    } catch (error) {
        alert('Dockerfile 생성 실패: ' + error.message);
        console.error('Generation error:', error);
    } finally {
        hideLoading();
    }
}

// Show Dockerfile preview
function showPreview(dockerfileContent) {
    // Show preview step
    document.getElementById('step-preview').classList.remove('hidden');
    document.getElementById('step-preview').scrollIntoView({ behavior: 'smooth' });

    // Initialize CodeMirror editor if not already done
    if (!editor) {
        const textarea = document.getElementById('dockerfileEditor');
        editor = CodeMirror.fromTextArea(textarea, {
            mode: 'dockerfile',
            theme: 'monokai',
            lineNumbers: true,
            lineWrapping: true,
            readOnly: false
        });
        editor.setSize(null, 400);
    }

    // Set content
    editor.setValue(dockerfileContent);
}

// Download Dockerfile
async function downloadDockerfile() {
    if (!currentSessionId) {
        alert('세션이 만료되었습니다. 다시 생성해주세요.');
        return;
    }

    try {
        const response = await fetch(`/api/download/${currentSessionId}`);

        if (!response.ok) {
            throw new Error('Download failed');
        }

        // Create blob and download
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'Dockerfile';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        alert('Dockerfile이 다운로드되었습니다!');

    } catch (error) {
        alert('다운로드 실패: ' + error.message);
        console.error('Download error:', error);
    }
}

// Copy to clipboard
function copyToClipboard() {
    if (!editor) return;

    const content = editor.getValue();
    navigator.clipboard.writeText(content).then(() => {
        alert('클립보드에 복사되었습니다!');
    }).catch(err => {
        alert('복사 실패: ' + err.message);
    });
}

// Reset form
function resetForm() {
    if (!confirm('처음부터 다시 시작하시겠습니까?')) {
        return;
    }

    // Reset state
    currentLanguage = null;
    currentSessionId = null;

    // Hide all steps except language selection
    document.getElementById('step-input').classList.add('hidden');
    document.getElementById('step-config').classList.add('hidden');
    document.getElementById('step-preview').classList.add('hidden');

    // Clear all inputs
    document.getElementById('runtimeVersion').value = '';
    document.getElementById('port').value = '8000';
    document.getElementById('envVars').value = '';
    document.getElementById('healthCheck').value = '/health';
    document.getElementById('systemDeps').value = '';
    document.getElementById('baseImage').value = '';

    document.getElementById('pythonRequirements').value = '';
    document.getElementById('nodejsPackageJson').value = '';
    document.getElementById('jarFile').value = '';

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
