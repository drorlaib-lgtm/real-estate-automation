FROM python:3.11-slim

WORKDIR /app

# Python dependencies (lightweight - no crewai/ML packages)
COPY requirements_deploy.txt .
RUN pip install --no-cache-dir -r requirements_deploy.txt

# Copy application code
COPY . .

# Create lightweight crewai stub (avoids installing the 500MB+ crewai package)
# The @tool decorator is only needed for CrewAI pipeline - in our app we call functions directly
RUN mkdir -p /usr/local/lib/python3.11/site-packages/crewai/tools && \
    printf 'def tool(name):\n    def decorator(func):\n        return func\n    return decorator\n' > /usr/local/lib/python3.11/site-packages/crewai/tools/__init__.py && \
    touch /usr/local/lib/python3.11/site-packages/crewai/__init__.py

# Create necessary directories
RUN mkdir -p artifacts submissions contracts

# Environment - Cloud Run sets PORT=8080
ENV PORT=8080
ENV APP_NAME=app_ureca

# Streamlit settings for cloud
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE ${PORT}

CMD streamlit run ${APP_NAME}.py \
    --server.port=${PORT} \
    --server.address=0.0.0.0 \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false
