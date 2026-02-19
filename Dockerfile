FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY app/ app/

# Production uniquement (sans extra [dev])
RUN pip install --no-cache-dir .

CMD ["naas-provisioner","--loop"]
