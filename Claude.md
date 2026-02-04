# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dockerfile Generator is a web application that automatically generates optimized Dockerfiles for web services. It analyzes user source code or build artifacts and combines this with user input to create production-ready Dockerfiles.

**Supported Stacks**: Python (FastAPI/Flask/Django), Node.js (Express/NestJS/Next.js), Java (Spring Boot)

## Technology Stack

- **Backend**: FastAPI 0.115.0 with Python 3.11
- **Frontend**: Vanilla JavaScript + Tailwind CSS + CodeMirror
- **Template Engine**: Jinja2
- **Deployment**: Docker + docker-compose

## Development Commands

### Local Development (Python)
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Access application at http://localhost:8000
# API docs at http://localhost:8000/api/docs
```

### Docker Development
```bash
# Build and run with docker-compose
docker-compose up --build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Testing
```bash
cd backend
pytest                          # Run all tests
pytest tests/test_analyzer.py  # Run specific test
pytest -v                      # Verbose output
```

## Architecture

### Request Flow

1. **Frontend** (`frontend/index.html`, `frontend/js/app.js`)
   - User selects language and inputs configuration
   - Sends request to FastAPI backend

2. **API Layer** (`app/api/endpoints.py`)
   - Validates requests with Pydantic schemas
   - Routes to appropriate service

3. **Analysis Layer** (`app/services/file_analyzer.py`)
   - For Java: Extracts MANIFEST.MF from JAR, detects Spring Boot
   - For Python: Parses requirements.txt, detects framework from dependencies
   - For Node.js: Parses package.json, detects framework and package manager

4. **Generation Layer** (`app/services/dockerfile_generator.py`)
   - Selects appropriate Jinja2 template
   - Merges project info + user config
   - Applies security defaults (non-root user, health checks)

5. **Template Rendering** (`app/services/template_engine.py`)
   - Renders Dockerfile using Jinja2
   - Applies optimizations (layer caching, multi-stage builds)

### File Upload Security

Multi-layer validation in `app/utils/security.py`:
1. Extension check (.jar, .war only)
2. Content-Type header validation
3. Magic number verification (ZIP header: PK\x03\x04)
4. File size limit (500MB max)
5. Filename sanitization (werkzeug.secure_filename)

Streaming upload with 1MB chunks for memory efficiency.

### Session Management

- Uploads stored in `/uploads/{session_id}/` (UUID-based)
- Automatic cleanup after 1 hour (background task in `app/utils/file_handler.py`)
- Generated Dockerfiles saved to session directory for download

## Key Files

### Backend Core
- `backend/app/main.py` - FastAPI application entry point, middleware, static file serving
- `backend/app/config.py` - Configuration constants (upload limits, paths, CORS)
- `backend/app/models/schemas.py` - Pydantic models for API validation

### Business Logic
- `backend/app/services/file_analyzer.py` - Language/framework detection logic
- `backend/app/services/dockerfile_generator.py` - Template selection and context building
- `backend/app/services/template_engine.py` - Jinja2 rendering

### API & Utils
- `backend/app/api/endpoints.py` - All API routes (upload, analyze, generate, download)
- `backend/app/utils/security.py` - File validation and security
- `backend/app/utils/file_handler.py` - Upload management and session cleanup

### Templates
- `backend/app/templates/{language}/{framework}.dockerfile.j2` - Jinja2 templates for each stack
- All templates use multi-stage builds, non-root users, health checks

### Frontend
- `frontend/index.html` - Single-page application UI
- `frontend/js/app.js` - Frontend application logic, API calls, CodeMirror integration

## Adding New Templates

1. Create template file: `backend/app/templates/{language}/{framework}.dockerfile.j2`
2. Update `dockerfile_generator.py`:
   ```python
   template_map = {
       "python": {
           "your-framework": "python/your-framework.dockerfile.j2"
       }
   }
   ```
3. Add analysis logic in `file_analyzer.py` if needed
4. Update frontend dropdown in `index.html`

## Template Variables

Available in all templates:
- `base_image` - Docker base image
- `runtime_version` - Language runtime version
- `port` - Exposed port
- `environment_vars` - Dict of env vars
- `health_check_path` - Health check endpoint
- `user` - Non-root username
- `system_dependencies` - List of apt/apk packages

Language-specific:
- Python: `server`, `requirements_content`, `entrypoint_file`
- Node.js: `package_manager`, `build_command`, `start_command`
- Java: `jar_file_name`, `jvm_options`, `main_class`

## Common Patterns

### Multi-stage builds
All Node.js and Java templates use multi-stage builds:
1. **deps** stage: Install dependencies
2. **builder** stage: Build application (if needed)
3. **runtime** stage: Copy only necessary artifacts

### Layer optimization
Order layers for cache efficiency:
1. Base image + system dependencies
2. Package manager files (package.json, requirements.txt)
3. Install dependencies
4. Copy source code
5. Build/compile
6. Runtime configuration

### Security best practices
- Always create non-root user
- Use alpine/slim base images
- Include health checks
- Minimize attack surface with multi-stage builds

## Troubleshooting

### "Module not found" errors
- Ensure you're in the backend directory
- Check virtual environment is activated
- Verify all dependencies installed: `pip install -r requirements.txt`

### Frontend not loading
- Check FastAPI is serving static files (see `main.py`)
- Verify `FRONTEND_DIR` path in `config.py`
- Check browser console for JavaScript errors

### Template rendering errors
- Verify template exists in `backend/app/templates/`
- Check template syntax (Jinja2)
- Review context variables passed to template

### File upload fails
- Check file size (<500MB)
- Verify file extension (.jar, .war for Java)
- Check logs for validation errors

## Code Style

- Follow PEP 8 for Python code
- Use type hints for all functions
- Add docstrings to classes and public methods
- Keep functions focused and single-purpose
- Use async/await for I/O operations

## Future Enhancements

Potential additions:
- Docker Compose generation for multi-service projects
- Kubernetes manifest generation
- .dockerignore file generation
- CI/CD pipeline templates
- Image size estimation
- Security scanning integration (Trivy, Grype)
- Template customization UI
- User profiles for saving configurations
