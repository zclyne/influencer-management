# Backend Dev Data

`mock_data.sql` is the persistent local seed dataset for frontend testing and backend
e2e-style smoke tests.

Run from `backend/`:

```bash
uv run python -m app.dev.seed_mock_data
```

The default command runs Alembic migrations first, then applies the SQL seed to the
configured `DATABASE_URL`.

Useful options:

```bash
uv run python -m app.dev.seed_mock_data --skip-migrations
uv run python -m app.dev.seed_mock_data --database-url sqlite:////tmp/desktop_irm_seed.db
uv run python -m app.dev.seed_mock_data --sql-path dev/mock_data.sql
```

The seed is idempotent. It uses fixed IDs and upserts seeded rows without deleting
unrelated local data.
