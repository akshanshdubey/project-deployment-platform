FROM python:3.12

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    docker.io \
    postgresql-client

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD sh -c "until pg_isready -h postgres -p 5432 -U admin; do echo waiting for postgres; sleep 2; done; python app.py"