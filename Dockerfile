FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY user_invoice_db ./user_invoice_db
COPY scripts ./scripts

RUN pip install --no-cache-dir -e .

ENV USERDB_PATH=/data/userdb.sqlite

ENTRYPOINT ["userdb"]
CMD ["--help"]