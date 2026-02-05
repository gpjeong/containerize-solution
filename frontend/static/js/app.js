// Global state
let currentLanguage = null;
let currentSessionId = null;
let currentJarFileName = null;
let editor = null;
let pipelineEditor = null;
let cachedPipelineScript = null;

// Show/hide loading
function showLoading() {
  document.getElementById('loading').classList.remove('hidden');
}

function hideLoading() {
  document.getElementById('loading').classList.add('hidden');
}

// Show/hide alert modal
function showAlert(message, type = 'error', isHtml = false) {
  const iconElement = document.getElementById('alertIcon');
  const titleElement = document.getElementById('alertTitle');
  const messageElement = document.getElementById('alertMessage');

  if (type === 'success') {
    iconElement.textContent = '✅';
    titleElement.textContent = '완료';
    // Hide title for success messages
    titleElement.classList.add('hidden');
    iconElement.classList.add('hidden');
  } else {
    iconElement.textContent = '⚠️';
    titleElement.textContent = '입력 오류';
    // Show title for error messages
    titleElement.classList.remove('hidden');
    iconElement.classList.remove('hidden');
  }

  if (isHtml) {
    messageElement.innerHTML = message;
  } else {
    messageElement.textContent = message;
  }

  document.getElementById('alertModal').classList.remove('hidden');
}

function closeAlert() {
  document.getElementById('alertModal').classList.add('hidden');
}

// Language selection
function selectLanguage(language) {
  currentLanguage = language;

  // Hide preview step
  document.getElementById('step-preview').classList.add('hidden');

  // Reset all input fields
  resetInputFields();

  // Update language button styles
  updateLanguageButtonStyles(language);

  // For Python/Node.js: skip input step and go directly to config
  if (language === 'python' || language === 'nodejs') {
    document.getElementById('step-input').classList.add('hidden');
    document.getElementById('step-config').classList.remove('hidden');

    // Show simple language fields, hide Java fields
    document.getElementById('simple-lang-fields').classList.remove('hidden');
    document.getElementById('java-lang-fields').classList.add('hidden');

    // Update step number
    document.getElementById('config-step-number').textContent = '2';

    // Update placeholders based on language
    updatePlaceholders(language);

    // Scroll to config section
    document
      .getElementById('step-config')
      .scrollIntoView({ behavior: 'smooth' });
  }
  // For Java: show input step
  else if (language === 'java') {
    document.getElementById('step-input').classList.remove('hidden');
    document.getElementById('step-config').classList.add('hidden');

    // Hide all input sections first
    document.querySelectorAll('.input-section').forEach((el) => {
      el.classList.add('hidden');
    });

    // Show Java input section
    document.getElementById('input-java').classList.remove('hidden');

    // Scroll to input section
    document
      .getElementById('step-input')
      .scrollIntoView({ behavior: 'smooth' });
  }
}

// Update placeholders based on selected language
function updatePlaceholders(language) {
  const baseImageInput = document.getElementById('baseImage');
  const portInput = document.getElementById('port');
  const startCommandInput = document.getElementById('startCommand');

  if (language === 'python') {
    baseImageInput.placeholder = '예: python:3.11-slim';
    portInput.placeholder = '예: 8000';
    startCommandInput.placeholder =
      '예: uvicorn main:app --host 0.0.0.0 --port 8000';
  } else if (language === 'nodejs') {
    baseImageInput.placeholder = '예: node:20-alpine';
    portInput.placeholder = '예: 3000';
    startCommandInput.placeholder = '예: node server.js';
  }
}

// Update language button styles to show selected state
function updateLanguageButtonStyles(selectedLanguage) {
  // Reset all buttons to default state
  const pythonBtn = document.getElementById('lang-btn-python');
  const nodejsBtn = document.getElementById('lang-btn-nodejs');
  const javaBtn = document.getElementById('lang-btn-java');

  // Remove active classes from all buttons
  pythonBtn.className =
    'lang-btn p-6 border-2 border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition';
  nodejsBtn.className =
    'lang-btn p-6 border-2 border-gray-300 rounded-lg hover:border-green-500 hover:bg-green-50 transition';
  javaBtn.className =
    'lang-btn p-6 border-2 border-gray-300 rounded-lg hover:border-red-500 hover:bg-red-50 transition';

  // Add active class to selected button
  if (selectedLanguage === 'python') {
    pythonBtn.className =
      'lang-btn p-6 border-2 border-blue-500 bg-blue-50 rounded-lg transition';
  } else if (selectedLanguage === 'nodejs') {
    nodejsBtn.className =
      'lang-btn p-6 border-2 border-green-500 bg-green-50 rounded-lg transition';
  } else if (selectedLanguage === 'java') {
    javaBtn.className =
      'lang-btn p-6 border-2 border-red-500 bg-red-50 rounded-lg transition';
  }
}

// Reset all input fields
function resetInputFields() {
  // Python/Node.js fields
  document.getElementById('baseImage').value = '';
  document.getElementById('port').value = '';
  document.getElementById('serviceUrl').value = '';
  document.getElementById('startCommand').value = '';

  // Java fields
  document.getElementById('javaPort').value = '';
  document.getElementById('javaBaseImage').value = '';
  document.getElementById('javaServiceUrl').value = '';
  document.getElementById('javaStartCommand').value = '';
  document.getElementById('jarFile').value = '';
  currentJarFileName = null;

  // Common optional fields
  document.getElementById('envVars').value = '';
  document.getElementById('healthCheck').value = '/health';
  document.getElementById('systemDeps').value = '';

  // Reset checkboxes and hide inputs
  document.getElementById('enableEnvVars').checked = false;
  document.getElementById('envVarsInput').classList.add('hidden');

  document.getElementById('enableHealthCheck').checked = false;
  document.getElementById('healthCheckInput').classList.add('hidden');

  document.getElementById('enableSystemDeps').checked = false;
  document.getElementById('systemDepsInput').classList.add('hidden');

  // Jenkins fields
  document.getElementById('jenkinsUrl').value = '';
  document.getElementById('jenkinsJob').value = '';
  document.getElementById('jenkinsUsername').value = '';
  document.getElementById('jenkinsToken').value = '';
  document.getElementById('gitUrl').value = '';
  document.getElementById('gitBranch').value = 'main';
  document.getElementById('gitCredentialId').value = '';
  document.getElementById('imageName').value = '';
  document.getElementById('imageTag').value = 'latest';

  // Reset Jenkins checkbox and hide config
  document.getElementById('enableJenkins').checked = false;
  document.getElementById('jenkinsConfig').classList.add('hidden');

  // Hide Jenkins step
  document.getElementById('step-jenkins').classList.add('hidden');

  // Clear editor if exists
  if (editor) {
    editor.setValue('');
  }

  // Reset session
  currentSessionId = null;
}

// Toggle Java input type (JAR vs Source)
// Toggle Environment Variables input
function toggleEnvVars() {
  const checkbox = document.getElementById('enableEnvVars');
  const input = document.getElementById('envVarsInput');

  if (checkbox.checked) {
    input.classList.remove('hidden');
  } else {
    input.classList.add('hidden');
  }
}

// Toggle Health Check input
function toggleHealthCheck() {
  const checkbox = document.getElementById('enableHealthCheck');
  const input = document.getElementById('healthCheckInput');

  if (checkbox.checked) {
    input.classList.remove('hidden');
  } else {
    input.classList.add('hidden');
  }
}

// Toggle System Dependencies input
function toggleSystemDeps() {
  const checkbox = document.getElementById('enableSystemDeps');
  const input = document.getElementById('systemDepsInput');

  if (checkbox.checked) {
    input.classList.remove('hidden');
  } else {
    input.classList.add('hidden');
  }
}

// Move to configuration step (Java only)
async function nextToConfig() {
  // Only for Java - check if file uploaded and analyze
  if (currentLanguage === 'java') {
    const fileInput = document.getElementById('jarFile');

    // Check if JAR file is uploaded
    if (fileInput.files.length === 0) {
      showAlert('JAR 파일을 업로드해주세요.');
      return;
    }

    await uploadJavaFile(fileInput.files[0]);
  }

  // Show config step
  document.getElementById('step-config').classList.remove('hidden');

  // Show Java fields, hide simple fields
  document.getElementById('java-lang-fields').classList.remove('hidden');
  document.getElementById('simple-lang-fields').classList.add('hidden');

  // Update step number
  document.getElementById('config-step-number').textContent = '3';

  document.getElementById('step-config').scrollIntoView({ behavior: 'smooth' });
}

// Upload Java JAR file
async function uploadJavaFile(file) {
  showLoading();

  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch('/api/upload/java', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Upload failed');
    }

    const data = await response.json();
    currentSessionId = data.session_id;
    currentJarFileName = file.name;

    showAlert('Jar 파일 확인 완료', 'success');
    console.log('Analysis result:', data.project_info);
  } catch (error) {
    showAlert('파일 업로드 실패: ' + error.message);
    console.error('Upload error:', error);
  } finally {
    hideLoading();
  }
}

// Parse environment variables
function parseEnvVars(envText) {
  const envVars = {};
  if (!envText) return envVars;

  envText.split('\n').forEach((line) => {
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
  return depsText
    .trim()
    .split(/\s+/)
    .filter((d) => d);
}

// Validate required fields for Python/Node.js
function validateSimpleLanguageFields() {
  const baseImage = document.getElementById('baseImage').value.trim();
  const port = document.getElementById('port').value.trim();
  const serviceUrl = document.getElementById('serviceUrl').value.trim();
  const startCommand = document.getElementById('startCommand').value.trim();

  if (!baseImage) {
    showAlert('Base Image를 입력해주세요.');
    return false;
  }

  if (!port) {
    showAlert('포트를 입력해주세요.');
    return false;
  }

  if (!serviceUrl) {
    showAlert('서비스 URL을 입력해주세요.');
    return false;
  }

  if (!startCommand) {
    showAlert('실행 명령어를 입력해주세요.');
    return false;
  }

  return true;
}

// Validate required fields for Java
function validateJavaFields() {
  const baseImage = document.getElementById('javaBaseImage').value.trim();
  const port = document.getElementById('javaPort').value.trim();
  const serviceUrl = document.getElementById('javaServiceUrl').value.trim();
  const startCommand = document.getElementById('javaStartCommand').value.trim();

  if (!baseImage) {
    showAlert('Base Image를 입력해주세요.');
    return false;
  }

  if (!port) {
    showAlert('포트를 입력해주세요.');
    return false;
  }

  if (!serviceUrl) {
    showAlert('서비스 URL을 입력해주세요.');
    return false;
  }

  if (!startCommand) {
    showAlert('실행 명령어를 입력해주세요.');
    return false;
  }

  return true;
}

// Generate Dockerfile
async function generateDockerfile() {
  showLoading();

  try {
    let config;

    // Build configuration based on language
    if (currentLanguage === 'python' || currentLanguage === 'nodejs') {
      // Validate required fields
      if (!validateSimpleLanguageFields()) {
        hideLoading();
        return;
      }

      // Build config for Python/Node.js
      const enableEnvVars = document.getElementById('enableEnvVars').checked;
      const enableHealthCheck =
        document.getElementById('enableHealthCheck').checked;
      const enableSystemDeps =
        document.getElementById('enableSystemDeps').checked;

      config = {
        language: currentLanguage,
        framework: 'generic', // Use generic framework
        runtime_version: '', // Not needed for simple languages
        port: parseInt(document.getElementById('port').value),
        environment_vars: enableEnvVars
          ? parseEnvVars(document.getElementById('envVars').value)
          : {},
        health_check_path: enableHealthCheck
          ? document.getElementById('healthCheck').value
          : null,
        system_dependencies: enableSystemDeps
          ? parseSystemDeps(document.getElementById('systemDeps').value)
          : [],
        base_image: document.getElementById('baseImage').value,
        user: 'appuser',
        service_url: document.getElementById('serviceUrl').value,
        custom_start_command: document.getElementById('startCommand').value,
      };

      // Add language-specific defaults
      if (currentLanguage === 'python') {
        config.package_manager = 'pip';
        config.entrypoint_file = 'main.py';
      } else if (currentLanguage === 'nodejs') {
        config.package_manager = 'npm';
        config.start_command = config.custom_start_command;
      }
    } else if (currentLanguage === 'java') {
      // Validate required fields
      if (!validateJavaFields()) {
        hideLoading();
        return;
      }

      // Build config for Java
      const enableEnvVars = document.getElementById('enableEnvVars').checked;
      const enableHealthCheck =
        document.getElementById('enableHealthCheck').checked;
      const enableSystemDeps =
        document.getElementById('enableSystemDeps').checked;

      config = {
        language: currentLanguage,
        framework: 'spring-boot',
        port: parseInt(document.getElementById('javaPort').value),
        environment_vars: enableEnvVars
          ? parseEnvVars(document.getElementById('envVars').value)
          : {},
        health_check_path: enableHealthCheck
          ? document.getElementById('healthCheck').value
          : null,
        system_dependencies: enableSystemDeps
          ? parseSystemDeps(document.getElementById('systemDeps').value)
          : [],
        base_image: document.getElementById('javaBaseImage').value,
        user: 'appuser',
        service_url: document.getElementById('javaServiceUrl').value,
        custom_start_command: document.getElementById('javaStartCommand').value,
      };

      // JAR file (already uploaded)
      config.build_tool = 'jar';
      config.jar_file_name = currentJarFileName || 'app.jar';
      config.jvm_options = '-Xmx512m';
    }

    // Make API request
    const response = await fetch('/api/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        config: config,
      }),
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
    showAlert('Dockerfile 생성 실패: ' + error.message);
    console.error('Generation error:', error);
  } finally {
    hideLoading();
  }
}

// Show Dockerfile preview
function showPreview(dockerfileContent) {
  // Show preview step
  document.getElementById('step-preview').classList.remove('hidden');
  document
    .getElementById('step-preview')
    .scrollIntoView({ behavior: 'smooth' });

  // Initialize CodeMirror editor if not already done
  if (!editor) {
    const textarea = document.getElementById('dockerfileEditor');
    editor = CodeMirror.fromTextArea(textarea, {
      mode: 'dockerfile',
      theme: 'monokai',
      lineNumbers: true,
      lineWrapping: true,
      readOnly: false,
    });
    editor.setSize(null, 400);
  }

  // Set content
  editor.setValue(dockerfileContent);

  // Show Jenkins build section
  document.getElementById('step-jenkins').classList.remove('hidden');
}

// Download Dockerfile
function downloadDockerfile() {
  if (!editor) {
    showAlert('Dockerfile이 생성되지 않았습니다.');
    return;
  }

  try {
    // Get current content from editor (including any edits)
    const content = editor.getValue();

    // Create blob and download
    const blob = new Blob([content], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'Dockerfile';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);

    showAlert('Dockerfile이 다운로드되었습니다!', 'success');
  } catch (error) {
    showAlert('다운로드 실패: ' + error.message);
    console.error('Download error:', error);
  }
}

// Copy to clipboard
function copyToClipboard() {
  if (!editor) return;

  const content = editor.getValue();
  navigator.clipboard
    .writeText(content)
    .then(() => {
      showAlert('클립보드에 복사되었습니다!', 'success');
    })
    .catch((err) => {
      showAlert('복사 실패: ' + err.message);
    });
}

// Show reset confirmation modal
function showResetConfirmation() {
  document.getElementById('resetConfirmModal').classList.remove('hidden');
}

// Cancel reset
function cancelReset() {
  document.getElementById('resetConfirmModal').classList.add('hidden');
}

// Confirm reset
function confirmReset() {
  // Hide modal
  document.getElementById('resetConfirmModal').classList.add('hidden');

  // Reset state
  currentLanguage = null;
  currentSessionId = null;

  // Hide all steps except language selection
  document.getElementById('step-input').classList.add('hidden');
  document.getElementById('step-config').classList.add('hidden');
  document.getElementById('step-preview').classList.add('hidden');

  // Clear all inputs
  document.getElementById('runtimeVersion').value = '';
  document.getElementById('javaPort').value = '';
  document.getElementById('javaBaseImage').value = '';
  document.getElementById('javaServiceUrl').value = '';
  document.getElementById('javaStartCommand').value = '';
  document.getElementById('baseImage').value = '';
  document.getElementById('port').value = '';
  document.getElementById('serviceUrl').value = '';
  document.getElementById('startCommand').value = '';
  document.getElementById('envVars').value = '';
  document.getElementById('healthCheck').value = '/health';
  document.getElementById('systemDeps').value = '';

  document.getElementById('jarFile').value = '';

  // Reset checkboxes and hide inputs
  document.getElementById('enableEnvVars').checked = false;
  document.getElementById('envVarsInput').classList.add('hidden');

  document.getElementById('enableHealthCheck').checked = false;
  document.getElementById('healthCheckInput').classList.add('hidden');

  document.getElementById('enableSystemDeps').checked = false;
  document.getElementById('systemDepsInput').classList.add('hidden');

  // Reset language button styles
  const pythonBtn = document.getElementById('lang-btn-python');
  const nodejsBtn = document.getElementById('lang-btn-nodejs');
  const javaBtn = document.getElementById('lang-btn-java');

  if (pythonBtn)
    pythonBtn.className =
      'lang-btn p-6 border-2 border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition';
  if (nodejsBtn)
    nodejsBtn.className =
      'lang-btn p-6 border-2 border-gray-300 rounded-lg hover:border-green-500 hover:bg-green-50 transition';
  if (javaBtn)
    javaBtn.className =
      'lang-btn p-6 border-2 border-gray-300 rounded-lg hover:border-red-500 hover:bg-red-50 transition';

  // Scroll to top
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Legacy function (kept for compatibility)
function resetForm() {
  showResetConfirmation();
}

// ============================================
// Jenkins Build Functions
// ============================================

// Toggle Jenkins configuration section
function toggleJenkins() {
  const checkbox = document.getElementById('enableJenkins');
  const config = document.getElementById('jenkinsConfig');

  if (checkbox.checked) {
    config.classList.remove('hidden');
  } else {
    config.classList.add('hidden');
  }
}

// Toggle Kaniko option visibility
function toggleKanikoOption() {
  const k8sCheckbox = document.getElementById('useKubernetes');
  const kanikoOption = document.getElementById('kanikoOption');

  if (k8sCheckbox.checked) {
    kanikoOption.classList.remove('hidden');
  } else {
    kanikoOption.classList.add('hidden');
    document.getElementById('useKaniko').checked = false;
  }
}

// Get current Dockerfile configuration
function getCurrentDockerConfig() {
  if (currentLanguage === 'python' || currentLanguage === 'nodejs') {
    const enableEnvVars = document.getElementById('enableEnvVars').checked;
    const enableHealthCheck =
      document.getElementById('enableHealthCheck').checked;
    const enableSystemDeps =
      document.getElementById('enableSystemDeps').checked;

    const config = {
      language: currentLanguage,
      framework: 'generic',
      runtime_version: '',
      port: parseInt(document.getElementById('port').value),
      environment_vars: enableEnvVars
        ? parseEnvVars(document.getElementById('envVars').value)
        : {},
      health_check_path: enableHealthCheck
        ? document.getElementById('healthCheck').value
        : null,
      system_dependencies: enableSystemDeps
        ? parseSystemDeps(document.getElementById('systemDeps').value)
        : [],
      base_image: document.getElementById('baseImage').value,
      user: 'appuser',
      service_url: document.getElementById('serviceUrl').value,
      custom_start_command: document.getElementById('startCommand').value,
    };

    if (currentLanguage === 'python') {
      config.package_manager = 'pip';
      config.entrypoint_file = 'main.py';
    } else if (currentLanguage === 'nodejs') {
      config.package_manager = 'npm';
      config.start_command = config.custom_start_command;
    }

    return config;
  } else if (currentLanguage === 'java') {
    const enableEnvVars = document.getElementById('enableEnvVars').checked;
    const enableHealthCheck =
      document.getElementById('enableHealthCheck').checked;
    const enableSystemDeps =
      document.getElementById('enableSystemDeps').checked;

    const config = {
      language: currentLanguage,
      framework: 'spring-boot',
      port: parseInt(document.getElementById('javaPort').value),
      environment_vars: enableEnvVars
        ? parseEnvVars(document.getElementById('envVars').value)
        : {},
      health_check_path: enableHealthCheck
        ? document.getElementById('healthCheck').value
        : null,
      system_dependencies: enableSystemDeps
        ? parseSystemDeps(document.getElementById('systemDeps').value)
        : [],
      base_image: document.getElementById('javaBaseImage').value,
      user: 'appuser',
      service_url: document.getElementById('javaServiceUrl').value,
      custom_start_command: document.getElementById('javaStartCommand').value,
      build_tool: 'jar',
      jar_file_name: currentJarFileName || 'app.jar',
      jvm_options: '-Xmx512m',
    };

    return config;
  }

  return null;
}

// Preview Jenkins Pipeline
async function previewPipeline() {
  showLoading();

  try {
    // Validate Jenkins fields
    const jenkinsUrl = document.getElementById('jenkinsUrl').value.trim();
    const jenkinsJob = document.getElementById('jenkinsJob').value.trim();
    const gitUrl = document.getElementById('gitUrl').value.trim();
    const imageName = document.getElementById('imageName').value.trim();

    if (!jenkinsUrl) {
      showAlert('Jenkins URL을 입력해주세요.');
      hideLoading();
      return;
    }

    if (!jenkinsJob) {
      showAlert('Jenkins Job 이름을 입력해주세요.');
      hideLoading();
      return;
    }

    if (!gitUrl) {
      showAlert('Git Repository URL을 입력해주세요.');
      hideLoading();
      return;
    }

    if (!imageName) {
      showAlert('Docker 이미지 이름을 입력해주세요.');
      hideLoading();
      return;
    }

    // Get current Dockerfile config
    const config = getCurrentDockerConfig();
    if (!config) {
      showAlert('Dockerfile 설정을 먼저 완료해주세요.');
      hideLoading();
      return;
    }

    // Build request payload
    const payload = {
      config: config,
      jenkins_url: jenkinsUrl,
      jenkins_job: jenkinsJob,
      jenkins_token: 'dummy-token', // Not used for preview
      jenkins_username: 'dummy-user', // Not used for preview
      git_url: gitUrl,
      git_branch: document.getElementById('gitBranch').value.trim() || 'main',
      git_credential_id:
        document.getElementById('gitCredentialId').value.trim() || null,
      image_name: imageName,
      image_tag: document.getElementById('imageTag').value.trim() || 'latest',
      use_kubernetes: document.getElementById('useKubernetes').checked,
      use_kaniko: document.getElementById('useKaniko').checked,
      harbor_url: document.getElementById('harborUrl').value.trim() || null,
      harbor_credential_id: document.getElementById('harborCredentialId').value.trim() || null,
    };

    console.log('Requesting pipeline preview:', payload);

    // Call API
    const response = await fetch('/api/preview/pipeline', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Pipeline 미리보기 실패');
    }

    const data = await response.json();
    cachedPipelineScript = data.pipeline_script;

    console.log('Pipeline preview received');

    // Initialize pipeline editor if not already done
    if (!pipelineEditor) {
      const textarea = document.getElementById('pipelineEditor');
      pipelineEditor = CodeMirror.fromTextArea(textarea, {
        mode: 'groovy',
        theme: 'monokai',
        lineNumbers: true,
        lineWrapping: true,
        readOnly: false,
        indentUnit: 2,
        tabSize: 2,
      });
      pipelineEditor.setSize(null, 500);
    }

    // Set pipeline content
    pipelineEditor.setValue(data.pipeline_script);

    // Show modal
    document.getElementById('pipelinePreviewModal').classList.remove('hidden');

    hideLoading();
  } catch (error) {
    console.error('Pipeline preview error:', error);
    showAlert('Pipeline 미리보기 실패: ' + error.message);
    hideLoading();
  }
}

// Close pipeline preview modal
function closePipelinePreview() {
  document.getElementById('pipelinePreviewModal').classList.add('hidden');
}

// Build with edited pipeline script
async function buildWithEditedPipeline() {
  if (!pipelineEditor) {
    showAlert('Pipeline 스크립트가 없습니다.');
    return;
  }

  // Close preview modal
  closePipelinePreview();

  showLoading();

  try {
    // Validate Jenkins fields
    const jenkinsUrl = document.getElementById('jenkinsUrl').value.trim();
    const jenkinsJob = document.getElementById('jenkinsJob').value.trim();
    const jenkinsToken = document.getElementById('jenkinsToken').value.trim();
    const jenkinsUsername =
      document.getElementById('jenkinsUsername').value.trim() || 'admin';

    if (!jenkinsToken) {
      showAlert('Jenkins API Token을 입력해주세요.');
      hideLoading();
      return;
    }

    // Get edited pipeline script
    const editedPipelineScript = pipelineEditor.getValue();

    // Call backend to update pipeline and trigger build
    const response = await fetch('/api/build/jenkins/custom', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        jenkins_url: jenkinsUrl,
        jenkins_job: jenkinsJob,
        jenkins_token: jenkinsToken,
        jenkins_username: jenkinsUsername,
        pipeline_script: editedPipelineScript,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Jenkins 빌드 실패');
    }

    const data = await response.json();

    console.log('Jenkins build with custom pipeline response:', data);

    // Show success message
    const message = `
      <div class="space-y-4">
        <div class="text-lg font-semibold text-green-600">
          🚀 Jenkins 빌드가 시작되었습니다!
        </div>

        <div class="bg-gray-50 p-4 rounded-lg text-left space-y-2">
          <div class="flex items-center">
            <span class="font-medium text-gray-700 mr-2">Job Name:</span>
            <span class="text-gray-900 font-mono">${data.job_name}</span>
          </div>
          ${data.build_number ? `
          <div class="flex items-center">
            <span class="font-medium text-gray-700 mr-2">Build Number:</span>
            <span class="text-blue-600 font-mono font-semibold">#${data.build_number}</span>
          </div>
          ` : data.queue_id ? `
          <div class="flex items-center">
            <span class="font-medium text-gray-700 mr-2">Queue ID:</span>
            <span class="text-orange-600 font-mono">#${data.queue_id}</span>
            <span class="text-xs text-gray-500 ml-2">(빌드 대기 중)</span>
          </div>
          ` : ''}
        </div>

        <div class="pt-2">
          <a href="${data.job_url}" target="_blank" rel="noopener noreferrer"
             class="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors">
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
            </svg>
            Jenkins에서 빌드 확인하기
          </a>
        </div>
      </div>
    `;

    showAlert(message, 'success', true);
  } catch (error) {
    console.error('Jenkins build with custom pipeline error:', error);
    showAlert('Jenkins 빌드 실패: ' + error.message);
  } finally {
    hideLoading();
  }
}

// Build with Jenkins
async function buildWithJenkins() {
  showLoading();

  try {
    // Validate Jenkins fields
    const jenkinsUrl = document.getElementById('jenkinsUrl').value.trim();
    const jenkinsJob = document.getElementById('jenkinsJob').value.trim();
    const jenkinsToken = document.getElementById('jenkinsToken').value.trim();
    const jenkinsUsername =
      document.getElementById('jenkinsUsername').value.trim() || 'admin';
    const gitUrl = document.getElementById('gitUrl').value.trim();
    const imageName = document.getElementById('imageName').value.trim();

    if (!jenkinsUrl) {
      showAlert('Jenkins URL을 입력해주세요.');
      hideLoading();
      return;
    }

    if (!jenkinsJob) {
      showAlert('Jenkins Job 이름을 입력해주세요.');
      hideLoading();
      return;
    }

    if (!jenkinsToken) {
      showAlert('Jenkins API Token을 입력해주세요.');
      hideLoading();
      return;
    }

    if (!gitUrl) {
      showAlert('Git Repository URL을 입력해주세요.');
      hideLoading();
      return;
    }

    if (!imageName) {
      showAlert('Docker 이미지 이름을 입력해주세요.');
      hideLoading();
      return;
    }

    // Get current Dockerfile config
    const config = getCurrentDockerConfig();
    if (!config) {
      showAlert('Dockerfile 설정을 먼저 완료해주세요.');
      hideLoading();
      return;
    }

    // Build request payload
    const payload = {
      config: config,
      jenkins_url: jenkinsUrl,
      jenkins_job: jenkinsJob,
      jenkins_token: jenkinsToken,
      jenkins_username: jenkinsUsername,
      git_url: gitUrl,
      git_branch: document.getElementById('gitBranch').value.trim() || 'main',
      git_credential_id:
        document.getElementById('gitCredentialId').value.trim() || null,
      image_name: imageName,
      image_tag: document.getElementById('imageTag').value.trim() || 'latest',
      use_kubernetes: document.getElementById('useKubernetes').checked,
      use_kaniko: document.getElementById('useKaniko').checked,
      harbor_url: document.getElementById('harborUrl').value.trim() || null,
      harbor_credential_id: document.getElementById('harborCredentialId').value.trim() || null,
    };

    console.log('Sending Jenkins build request:', payload);

    // Call API
    const response = await fetch('/api/build/jenkins', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Jenkins 빌드 실패');
    }

    const data = await response.json();

    console.log('Jenkins build response:', data);

    // Show success message with clickable URL and better formatting
    const message = `
      <div class="space-y-4">
        <div class="text-lg font-semibold text-green-600">
          🚀 Jenkins 빌드가 시작되었습니다!
        </div>

        <div class="bg-gray-50 p-4 rounded-lg text-left space-y-2">
          <div class="flex items-center">
            <span class="font-medium text-gray-700 mr-2">Job Name:</span>
            <span class="text-gray-900 font-mono">${data.job_name}</span>
          </div>
          ${data.build_number ? `
          <div class="flex items-center">
            <span class="font-medium text-gray-700 mr-2">Build Number:</span>
            <span class="text-blue-600 font-mono font-semibold">#${data.build_number}</span>
          </div>
          ` : data.queue_id ? `
          <div class="flex items-center">
            <span class="font-medium text-gray-700 mr-2">Queue ID:</span>
            <span class="text-orange-600 font-mono">#${data.queue_id}</span>
            <span class="text-xs text-gray-500 ml-2">(빌드 대기 중)</span>
          </div>
          ` : ''}
        </div>

        <div class="pt-2">
          <a href="${data.job_url}" target="_blank" rel="noopener noreferrer"
             class="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors">
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
            </svg>
            Jenkins에서 빌드 확인하기
          </a>
        </div>
      </div>
    `;

    showAlert(message, 'success', true);
  } catch (error) {
    console.error('Jenkins build error:', error);
    showAlert('Jenkins 빌드 실패: ' + error.message);
  } finally {
    hideLoading();
  }
}
