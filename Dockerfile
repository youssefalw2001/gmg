FROM python:3.11-slim-bookworm

RUN groupadd -r agent && useradd -r -g agent -d /workspace -s /sbin/nologin agent

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip==24.2 && \
    pip install --no-cache-dir -r requirements.txt

COPY agent ./agent
COPY run.py config.yaml ./

RUN mkdir -p /workspace/data && chown -R agent:agent /workspace

USER agent

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random

ENTRYPOINT ["python", "run.py"]
CMD ["preflight"]
