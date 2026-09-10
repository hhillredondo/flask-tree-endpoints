## Smoke Tests (Manual)

### Health
- `GET /` returns `{"status": "healthy"}` when Gremlin is reachable, and
  `{"status": "unhealthy"}` with a 503 when it is not. Nothing else is in the body.

### Auth
- `GET /auth/me` without token → `401`.
- `GET /auth/me` with valid token → `200` and user payload.

### Tree & Roles
- `POST /trees` creates tree and returns `partition_key`.
- `GET /roles` as owner returns owner entry.
- `POST /roles` add editor + viewer by email.
- `DELETE /roles` removes editor/viewer.

### Editor Lock
- `GET /editor-lock` shows unlocked.
- `POST /editor-lock` by editor → lock acquired.
- Writer call without lock → `409 Editor lock required`.
- Writer call by non-owner lock holder → `409 Editor locked`.
- `DELETE /editor-lock` by owner/editor (lock owner) → released.
- `POST /editor-lock/force` by owner → lock released.

### Member CRUD

Members are created through `POST /trees` (the first member) and the relation
endpoints below; there is no `POST /member`.

- `PUT /member` as editor with lock → `200`.
- `GET /member` and `GET /members` as viewer → `200`.
- `DELETE /member` as viewer → `403`.
- `DELETE /member` as editor with lock → `200`.

### Relations
- Create child/parent/spouse as editor with lock → `200`.
- Attempt write without lock → `409`.

### Media (S3)
- `POST /member/pic` (image) → returns `pic` + `pic_url`.
- `POST /member/photos` (1+ images) → returns `photos` + `uploaded` list.
- `GET /member/pic-url` → presigned URL is valid.
- `GET /member/photos-urls` → presigned URLs list.

### Metrics
- Trigger a few `401/403` failures and confirm `GET /metrics` increments.



