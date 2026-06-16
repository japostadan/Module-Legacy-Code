FROM python:3.12-slim

# psycopg2 builds from source, so it needs a C toolchain with the libc
# headers (build-essential) and the Postgres client headers (libpq-dev,
# which also provides pg_config + the runtime libpq).
RUN apt-get update \
    && apt-get install --yes --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3000

CMD ["python", "main.py"]
