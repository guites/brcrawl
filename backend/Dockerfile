# ---- Base image ----
FROM python:3.10-slim

# ---- Install uv ----
RUN pip install --no-cache-dir uv

# ---- Build args
ARG UID=1000
ARG GID=1000

# Create group and user matching host
RUN groupadd -g ${GID} appgroup \
    && useradd -m -u ${UID} -g appgroup appuser

# ---- Set workdir ----
WORKDIR /app

# ---- Copy dependency files first (better caching) ----
COPY pyproject.toml uv.lock* ./

# ---- Install dependencies (no dev dependencies) ----
RUN uv sync --frozen --no-dev

# ---- Copy project files ----
COPY . .

# ---- Switch to non-root user ----
USER appuser

# ---- Expose internal port ----
EXPOSE 8000

# ---- Run with gunicorn ----
CMD ["uv", "run", "gunicorn", "-b", "0.0.0.0:8000", "app:app"]
