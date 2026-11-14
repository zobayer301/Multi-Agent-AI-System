"""
Comprehensive Unit & Integration Tests for Phase 10:
Deployment Configuration, Dockerfile, Docker Compose, Environment Security, and Documentation.
"""

from pathlib import Path
import yaml


def test_dockerfile_structure_and_security():
    """Verify Dockerfile presence, Python 3.12 base image, non-root security, and exposed ports."""
    dockerfile_path = Path("Dockerfile")
    assert dockerfile_path.exists(), "Dockerfile must exist in the project root."

    content = dockerfile_path.read_text(encoding="utf-8")

    # Base image check
    assert "FROM python:3.12-slim" in content, "Must use python:3.12-slim base image."

    # Security: Non-root user check
    assert "useradd" in content or "adduser" in content, "Must create a dedicated non-root user."
    assert "USER appuser" in content or "USER 10000" in content, "Must switch to non-root user."

    # Exposed ports (Backend 8000 and Frontend 8501)
    assert "EXPOSE 8000 8501" in content or ("8000" in content and "8501" in content), "Must expose ports 8000 and 8501."

    # Health check definition
    assert "HEALTHCHECK" in content, "Dockerfile should define a container HEALTHCHECK."
    assert "CMD" in content, "Dockerfile must define a default CMD instruction."


def test_docker_compose_validity():
    """Verify docker-compose.yml YAML syntax, multi-service setup, ports, and healthcheck dependencies."""
    compose_path = Path("docker-compose.yml")
    assert compose_path.exists(), "docker-compose.yml must exist in the project root."

    data = yaml.safe_load(compose_path.read_text(encoding="utf-8"))

    # Check top-level keys
    assert "services" in data, "docker-compose.yml must define 'services'."
    services = data["services"]

    # Backend service
    assert "backend" in services, "Service 'backend' must be configured."
    backend = services["backend"]
    assert any("8000:8000" in str(p) for p in backend.get("ports", [])), "Backend must expose port 8000:8000."
    assert "healthcheck" in backend, "Backend service must declare a healthcheck."
    assert any("shared-data" in str(v) for v in backend.get("volumes", [])), "Backend must mount shared-data volume."

    # Frontend service
    assert "frontend" in services, "Service 'frontend' must be configured."
    frontend = services["frontend"]
    assert any("8501:8501" in str(p) for p in frontend.get("ports", [])), "Frontend must expose port 8501:8501."
    assert any("shared-data" in str(v) for v in frontend.get("volumes", [])), "Frontend must mount shared-data volume."
    assert "depends_on" in frontend, "Frontend must depend on backend."
    assert "backend" in frontend["depends_on"], "Frontend must depend on backend service."

    # Volumes check
    assert "volumes" in data, "docker-compose.yml must define named volumes."
    assert "shared-data" in data["volumes"], "Must define 'shared-data' persistent volume."


def test_dockerignore_exclusions():
    """Verify .dockerignore prevents sensitive or unnecessary files from being copied into the image."""
    dockerignore_path = Path(".dockerignore")
    assert dockerignore_path.exists(), ".dockerignore must exist in the project root."

    content = dockerignore_path.read_text(encoding="utf-8")
    critical_exclusions = [".venv", "__pycache__", ".env", "data/", ".git"]
    for exclusion in critical_exclusions:
        assert exclusion in content, f".dockerignore must exclude '{exclusion}'."


def test_env_example_completeness():
    """Verify .env.example contains all required configuration parameters and documentation."""
    env_path = Path(".env.example")
    assert env_path.exists(), ".env.example must exist in the project root."

    content = env_path.read_text(encoding="utf-8")
    required_keys = [
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
        "SQLITE_DB_PATH",
        "CHROMA_PERSIST_DIRECTORY",
        "API_PORT",
        "STREAMLIT_PORT",
        "VERIFICATION_THRESHOLD",
        "MAX_REVISION_ITERATIONS",
    ]
    for key in required_keys:
        assert key in content, f".env.example must define configuration key '{key}'."


def test_gitignore_completeness():
    """Verify .gitignore properly excludes virtual environments, caches, local data, and secrets."""
    gitignore_path = Path(".gitignore")
    assert gitignore_path.exists(), ".gitignore must exist in the project root."

    content = gitignore_path.read_text(encoding="utf-8")
    assert ".venv" in content
    assert "__pycache__" in content
    assert ".env" in content
    assert "data/" in content


def test_readme_completeness():
    """Verify README.md contains architectural diagrams, quickstart instructions, and API references."""
    readme_path = Path("README.md")
    assert readme_path.exists(), "README.md must exist in the project root."

    content = readme_path.read_text(encoding="utf-8")
    assert "flowchart TD" in content, "README must include a Mermaid architecture diagram."
    assert "Supervisor Agent" in content
    assert "Research Agent" in content
    assert "Analysis Agent" in content
    assert "Verification Agent" in content
    assert "Report Agent" in content
    assert "docker compose up --build" in content
    assert "/api/research" in content
