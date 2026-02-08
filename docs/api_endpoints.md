## API Endpoints

### Common Headers
- `Authorization: Bearer <JWT>`
- `X-Partition-Key: <userId_treeId>` for partitioned endpoints

### Health / Auth
- `GET /`  
  Health check (no auth). Verifies Gremlin connectivity.
- `GET /auth/debug`  
  Debug auth header (no auth).
- `GET /auth/me`  
  Returns current user info (auth required).
- `DELETE /account`  
  Delete current user account, owned trees, and roles (auth required).

### Trees
- `GET /trees`  
  List trees current user can access (auth required).
- `GET /myTrees`  
  List trees owned by current user (legacy, auth required).
- `POST /trees`  
  Create tree and seed owner role (auth required).  
  Body: member fields + `tree_id`.
- `DELETE /trees`  
  Delete entire tree (owner only, partition required).  
  If `S3_MEDIA_BUCKET` is unset, media deletion is skipped and the tree still deletes.

### Roles (Owner-only)
- `GET /roles`  
  List ACL for tree (owner only).
- `POST /roles`  
  Add editor/viewer by email (owner only).  
  Body: `{ "email": "...", "role": "editor" | "viewer" }`
- `DELETE /roles`  
  Remove editor/viewer (owner only).  
  Body: `{ "email": "..." }` or `{ "user_id": "..." }`

### Editor Lock
- `GET /editor-lock`  
  Get lock status (owner/editor).
- `POST /editor-lock`  
  Acquire lock (owner/editor).
- `DELETE /editor-lock`  
  Release lock (owner/editor, must own lock).
- `POST /editor-lock/force`  
  Force release lock (owner only).

### Members
All member/relationship write operations require editor lock.

- `GET /member`  
  Fetch member (auth + partition + role).
- `PUT /member`  
  Update member (auth + partition + role + lock).
- `DELETE /member`  
  Delete member (auth + partition + role + lock).  
  If this is the last member in the tree, it deletes the tree (roles/media/graph).  
  If `S3_MEDIA_BUCKET` is set, member media is deleted.
- `GET /members`  
  List all members in tree (auth + partition + role).
- `GET /memberDirectRelations`  
  Direct relations for a member (auth + partition + role).

### Composed member endpoints
- `POST /child`  
  Create child (auth + partition + role + lock).
- `POST /parent`  
  Create parent relation (auth + partition + role + lock).
- `POST /spouse`  
  Create spouse relation (auth + partition + role + lock).
- `PUT /spouse`  
  Update spouse relation (auth + partition + role + lock).

### Media (S3)
- `POST /member/pic`  
  Upload member pic (multipart form; `member_id`, `file`).
- `POST /member/photos`  
  Upload member photos (multipart form; `member_id`, `file` or `files[]`).
- `GET /member/pic-url`  
  Get presigned URL for pic (`member_id`, optional `expires_in`).
- `GET /member/photos-urls`  
  Get presigned URLs for photos (`member_id`, optional `expires_in`).

### Metrics
- `GET /metrics`  
  In-memory auth/role counters (auth required).



