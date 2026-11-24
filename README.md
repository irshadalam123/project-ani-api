# Instagram Comment-to-DM Automation Platform

Backend for a multi-tenant SaaS that connects Instagram professional accounts, receives comment webhooks from Meta, matches automation rules, and sends a public comment reply plus a private reply.

The API is intentionally persistence-agnostic. Repositories are in-memory today. PostgreSQL can replace them later without rewriting routes, services, the automation engine, or the Meta client.

This repository is a tested foundation, not a production deployment. There is no database, tokens are not encrypted at rest, and a separate Celery worker cannot see records created in the API process until a shared repository exists.

## Architecture

```
HTTP route
  -> service
    -> domain / automation engine
      -> repository interface
        -> in-memory repository (PostgreSQL later)

Webhook
  -> signature check and normalization
    -> store event
      -> queue (inline background task, or Celery)
        -> comment worker
          -> automation engine
            -> messaging service
              -> Instagram client
                -> Meta Graph API (or the mock client)
```

Routes validate input, resolve dependencies, call a service, and return an envelope. They do not call Meta and they do not construct repositories.

Every workspace-owned record carries `workspace_id`. A user can only read and write workspaces they belong to.

## Technology stack

- Python 3.12+ (developed and tested on 3.13)
- FastAPI, Pydantic v2, Pydantic Settings
- httpx
- PyJWT and pwdlib (Argon2) for application login
- structlog
- Redis and Celery
- pytest, pytest-asyncio, ruff, mypy
- SQLAlchemy and Alembic are installed for the future database. The running app does not create an engine. `alembic upgrade` exits before connecting.

## Directory structure

```
api/
  app/
    main.py
    api/                  HTTP routes
    core/                 settings, security, DI, errors, middleware
    schemas/              request and response models
    models/domain/        persistence-agnostic records
    repositories/
      interfaces/         ports services depend on
      memory/             current implementations
      postgres/           placeholder for SQLAlchemy repositories
    services/
    integrations/
      instagram/          the only Meta-specific code
      llm/                unused by the engine until AI replies exist
    automation/           trigger matching and action execution
    workers/              Celery app, tasks, inline dispatcher
    utils/
  tests/
  scripts/seed_demo_data.py
  alembic/                prepared, not executable
  Dockerfile
  docker-compose.yml
```

## Local setup

From `apps/api`:

```bash
python -m venv .venv
```

Windows:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env
```

macOS and Linux:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Fill `JWT_SECRET` and `SECRET_KEY` with long random values before any shared environment. Leave Meta secrets empty while `MOCK_EXTERNAL_SERVICES=true`.

## Environment variables

| Variable | Purpose |
| --- | --- |
| `APP_NAME` | API title |
| `APP_ENV` | `development`, `test`, or `production` |
| `DEBUG` | Include exception text outside production |
| `API_V1_PREFIX` | Version prefix, default `/api/v1` |
| `SECRET_KEY` | Application secret. Required in production |
| `META_APP_ID` | Meta app id |
| `META_APP_SECRET` | App secret. Also the webhook HMAC key |
| `META_REDIRECT_URI` | OAuth redirect URL |
| `META_API_VERSION` | Graph version segment, for example the version enabled on your app. Required for real calls |
| `META_GRAPH_BASE_URL` | Default `https://graph.instagram.com` |
| `META_OAUTH_AUTHORIZE_URL` | Default Instagram Login authorize URL |
| `META_OAUTH_TOKEN_URL` | Default code-exchange URL |
| `META_OAUTH_SCOPES` | Comma-separated scopes. Confirm them in the App Dashboard |
| `META_WEBHOOK_VERIFY_TOKEN` | Must match the dashboard verify token |
| `META_WEBHOOK_FIELDS` | Subscription fields. Default `comments` |
| `REDIS_URL` | Health check and dead-letter overflow |
| `CELERY_BROKER_URL` | Celery broker |
| `CELERY_RESULT_BACKEND` | Celery results |
| `TASK_EXECUTION_MODE` | `inline` or `celery` |
| `JWT_SECRET` | Access-token signing key |
| `JWT_ALGORITHM` | Default `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access-token lifetime |
| `LOG_LEVEL` | structlog level |
| `LLM_PROVIDER` | Reserved for a future AI reply action |
| `LLM_API_KEY` | Reserved. Never logged |
| `LLM_MODEL` | Reserved |
| `MOCK_EXTERNAL_SERVICES` | Use the mock Instagram client |
| `SEED_DEMO_DATA` | Load demo records on startup |
| `CORS_ORIGINS` | Comma-separated browser origins. `*` is rejected in production |
| `TRUSTED_HOSTS` | Comma-separated Host header allow-list |
| `RATE_LIMIT_ENABLED` | Turn limiting on or off |
| `RATE_LIMIT_BACKEND` | `memory` or `redis` |
| `RATE_LIMIT_AUTH_PER_MINUTE` | Auth route limit |
| `RATE_LIMIT_AUTOMATION_CREATE_PER_MINUTE` | Automation create limit |
| `RATE_LIMIT_INSTAGRAM_PER_MINUTE` | Instagram route limit |
| `RATE_LIMIT_WEBHOOK_PER_MINUTE` | Webhook route limit |
| `RETRY_BASE_SECONDS` | Exponential backoff base |
| `RETRY_MAX_ATTEMPTS` | Attempts for a transient Instagram error |

## Redis

Redis is the Celery broker, the readiness dependency, and a short dead-letter list. It is not the system of record for users, automations, or messages.

```bash
docker run --rm -p 6379:6379 redis:7-alpine
```

`GET /health` does not need Redis. `GET /health/ready` returns 503 until Redis answers `PING`.

## Run the API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Liveness: http://localhost:8000/health

With `TASK_EXECUTION_MODE=inline` (the default), webhook jobs run in the API process after the response is produced. That is what makes the full mock flow work before a database exists.

## Run the Celery worker

Start Redis first, then:

```bash
celery -A app.workers.celery_app:celery_app worker --loglevel=info
```

On Windows use `--pool=solo`.

Set `TASK_EXECUTION_MODE=celery` on the API to enqueue work. The worker process has its own empty in-memory store, so it cannot load automations created by the API until PostgreSQL repositories are bound in `app/core/container.py`. Keep `inline` for local end-to-end tests.

Tasks:

- `process_webhook_event`
- `process_comment`
- `send_public_reply`
- `send_private_reply`

Transient Meta errors retry with exponential backoff. Permanent errors are recorded on the execution and are not retried. Exhausted retries are logged and pushed to a Redis `dead_letter` list when Redis is reachable.

## Docker

`docker-compose.yml` starts `redis`, `api`, and `worker`. It does not start PostgreSQL.

```bash
docker compose up --build
```

The API service uses `TASK_EXECUTION_MODE=inline` and `MOCK_EXTERNAL_SERVICES=true`, so the mock flow runs inside the API container. The worker process is started and idle until you switch the API to Celery and add a shared repository.

## Tests

```bash
pytest
```

```bash
ruff check .
mypy app
```

## Mock mode

`APP_ENV=development` and `MOCK_EXTERNAL_SERVICES=true`.

`InstagramClient` methods return deterministic data and do not call Meta. `send_private_reply` returns a message id shaped like `mock_message_<comment_id>`. Tokens are still stored in `InMemoryTokenManager` and are never returned by the API.

`POST /webhooks/instagram` accepts either:

- a signed Meta webhook body, or
- a simplified local payload when mock mode is on or the app is not in production:

```json
{
  "comment_id": "comment_123",
  "media_id": "media_123",
  "instagram_user_id": "user_456",
  "username": "testuser",
  "text": "GUIDE"
}
```

If that payload does not name the professional account, and exactly one account is connected in the process, the event is attributed to that account.

## Demo data

```bash
python scripts/seed_demo_data.py
```

That command seeds a throwaway process and prints counts. To load the same records into the server, start it with `SEED_DEMO_DATA=true`.

Demo login: `demo@example.com` / `DemoPassword123!`

The seed creates one user, one workspace, one Instagram account, two automations, three contacts, one conversation, and two messages.

## Meta Developer setup

1. Create a Meta app and add the Instagram product with Business Login.
2. Set the OAuth redirect URI to `META_REDIRECT_URI`.
3. Set `META_APP_ID`, `META_APP_SECRET`, and `META_API_VERSION` to the version enabled for that app.
4. Request only scopes your app is allowed to use. The default string matches scopes shown on Meta's Business Login guide: `instagram_business_basic`, `instagram_business_manage_comments`, `instagram_business_manage_messages`. Confirm that list in the dashboard before going live.
5. Set `MOCK_EXTERNAL_SERVICES=false`.

### OAuth flow

1. `GET /api/v1/instagram/connect` returns Meta's authorization URL and a one-time `state`.
2. The professional account approves the request.
3. Meta redirects to `GET /api/v1/instagram/callback` with `code` and `state`.
4. The API checks state, exchanges the code, exchanges the short-lived token for a long-lived token, loads the professional account, stores metadata, stores the token outside the account record, and calls the webhook subscription endpoint.

### Webhooks

1. In the Meta dashboard, set the callback URL to `https://<your-host>/webhooks/instagram`.
2. Set the verify token to `META_WEBHOOK_VERIFY_TOKEN`.
3. Subscribe to the `comments` field.
4. `GET /webhooks/instagram` returns `hub.challenge` when `hub.verify_token` matches.
5. `POST /webhooks/instagram` checks `X-Hub-Signature-256`, stores each comment once, queues processing, and returns immediately.

The same comment is not answered twice by the same automation. Comments from the connected account itself, and replies to comments (`parent_id`), are ignored so a public reply does not loop.

## Keyword matching

`CONTAINS` is case-insensitive and matches a whole keyword. `guide` matches `GUIDE`, `AI GUIDE`, and `send me the guide`. It does not match `guidance`. `EXACT`, `STARTS_WITH`, and `REGEX` are also available. `ANY_COMMENT` matches every top-level comment.

Reply templates support `{{first_name}}` and `{{username}}`. Unknown placeholders are left in place.

## API responses

Success:

```json
{"success": true, "data": {}}
```

Lists add `pagination` with `page`, `page_size` (max 100), and `total`.

Errors:

```json
{"success": false, "error": {"code": "AUTOMATION_NOT_FOUND", "message": "Automation not found", "request_id": "..."}}
```

`GET /health` is the small exception and returns `{"status": "ok"}`.

Send `Authorization: Bearer <token>` and, once a user has more than one workspace, `X-Workspace-Id`.

## API endpoints

| Method | Path |
| --- | --- |
| GET | `/health` |
| GET | `/health/ready` |
| GET | `/docs` |
| GET | `/redoc` |
| POST | `/api/v1/auth/register` |
| POST | `/api/v1/auth/login` |
| GET | `/api/v1/auth/me` |
| GET | `/api/v1/workspaces` |
| POST | `/api/v1/workspaces` |
| GET | `/api/v1/instagram/connect` |
| GET | `/api/v1/instagram/callback` |
| GET | `/api/v1/instagram/accounts` |
| DELETE | `/api/v1/instagram/accounts/{account_id}` |
| POST | `/api/v1/automations` |
| GET | `/api/v1/automations` |
| GET | `/api/v1/automations/{automation_id}` |
| PATCH | `/api/v1/automations/{automation_id}` |
| DELETE | `/api/v1/automations/{automation_id}` |
| POST | `/api/v1/automations/{automation_id}/activate` |
| POST | `/api/v1/automations/{automation_id}/pause` |
| GET | `/api/v1/executions` |
| GET | `/api/v1/executions/{execution_id}` |
| GET | `/api/v1/contacts` |
| GET | `/api/v1/contacts/{contact_id}` |
| GET | `/api/v1/conversations` |
| GET | `/api/v1/conversations/{conversation_id}` |
| GET | `/api/v1/conversations/{conversation_id}/messages` |
| GET | `/api/v1/analytics/overview` |
| GET | `/webhooks/instagram` |
| POST | `/webhooks/instagram` |

## Adding PostgreSQL later

1. Add ORM models under `app/models/orm`. Keep `app/models/domain` as the type services use.
2. Implement each interface in `app/repositories/postgres`.
3. Implement `EncryptedPostgreSQLTokenManager` in place of `InMemoryTokenManager`.
4. Change `build_container` in `app/core/container.py` to construct those classes.
5. Point Alembic at the ORM metadata and remove the guard in `alembic/env.py`.
6. Add Postgres to Compose only at that point.
7. Set `TASK_EXECUTION_MODE=celery` so the worker and API share the database.

Do not put SQL or Meta HTTP calls in routes or in the automation engine.

## Production notes

Production startup refuses mock mode, wildcard CORS, an empty JWT secret, an empty app secret, and an empty webhook verify token.

Still required before a real deployment:

- PostgreSQL (or another shared store) so the worker and API share data
- encrypted token storage
- a public HTTPS webhook URL
- Meta app review for the permissions you request
- refresh of long-lived Instagram tokens (they expire; refresh is not scheduled yet)
- rate-limit backend set to Redis if you run more than one API process
- removal of the development JWT fallback

## What must be verified against current Meta documentation

The integration builds URLs from configuration and follows the published Instagram Login guides. Confirm these against the docs for your app before disabling mock mode:

- Graph version in `META_API_VERSION` (Meta retires versions on a schedule)
- OAuth token JSON shape (flat object versus a `data` array)
- `GET /me` fields: `user_id`, `username`, `name`, `account_type`, `profile_picture_url`
- Long-lived exchange at `graph.instagram.com/access_token` with `grant_type=ig_exchange_token`
- Public reply `POST /{comment-id}/replies?message=`
- Private reply `POST /{ig-user-id}/messages` with `recipient.comment_id`
- Webhook subscribe `POST /me/subscribed_apps`
- Comment webhook shape: `entry.field` / `entry.value` and the older `entry.changes` array are both parsed
- Private-reply rules: one reply per comment, within 7 days, and live comments only during the broadcast
- Permission names for comments versus messaging

Code that depends on those points is marked with `TODO(meta)` in `app/integrations/instagram/`.
