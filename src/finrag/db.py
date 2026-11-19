import os

import psycopg
from pgvector.psycopg import register_vector

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://finrag:finrag@localhost:5433/finrag")

SCHEMA = """
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS chunks (
    id        bigserial PRIMARY KEY,
    source    text NOT NULL,      -- nombre del archivo en data/raw
    company   text NOT NULL,
    year      int  NOT NULL,
    page      int,                -- NULL en documentos HTML
    section   text NOT NULL,
    kind      text NOT NULL,      -- 'text' | 'table'
    content   text NOT NULL,
    embedding vector(1024) NOT NULL
);
"""


def connect() -> psycopg.Connection:
    conn = psycopg.connect(DATABASE_URL)
    conn.execute(SCHEMA)  # la extensión debe existir antes de registrar el tipo vector
    register_vector(conn)
    return conn
