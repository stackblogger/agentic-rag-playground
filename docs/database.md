# Database

Postgres with the pgvector extension. Tables are SQLAlchemy models in `src/agentic_rag/db/models.py`, and they are created by Alembic migrations in `migrations/versions/`.

## documents

One row for each uploaded file.

| Column | What it is |
| --- | --- |
| `id` | Primary key |
| `filename` | Original file name |
| `file_path` | Where the file is saved in `UPLOAD_DIR` |
| `content_type` | File type sent by the client |
| `size_bytes` | File size |
| `page_count` | Number of pages |
| `extracted_text` | Full text from the PDF |
| `status` | `uploaded`, `processed` or `failed` |
| `created_at` | Upload time |

## chunks

Small pieces of a document's text. Search runs on this table.

| Column | What it is |
| --- | --- |
| `id` | Primary key |
| `document_id` | The document it belongs to |
| `chunk_index` | Order of the chunk in the document |
| `page_number` | Page the chunk came from |
| `content` | Text of the chunk |
| `embedding` | Vector of the text (pgvector) |
| `created_at` | Creation time |

Deleting a document also deletes its chunks (`ON DELETE CASCADE`).

## Embedding size

The `embedding` column has 1536 dimensions, which matches the default `EMBEDDING_MODEL` (`text-embedding-3-small`). The size is `EMBEDDING_DIMENSIONS` in `models.py`. A model with a different size needs a new value there and a new migration.

## Migrations

```bash
alembic upgrade head                                # apply all migrations
alembic revision --autogenerate -m "short message"  # make a new one after changing a model
alembic downgrade -1                                # undo the last one
```

Read a generated migration before applying it. The database URL is taken from `DATABASE_URL`, not from `alembic.ini`.
