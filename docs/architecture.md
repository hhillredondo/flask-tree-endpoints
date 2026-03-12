## Architecture Overview

---

### Production Architecture

The production frontend is served over **HTTPS** from Amplify Hosting. Browsers
enforce mixed-content policy and will block requests from an HTTPS page to a
plain HTTP endpoint. To avoid this without requiring a custom domain or an ACM
certificate on the ALB, a **CloudFront distribution** is placed in front of the
ALB. CloudFront terminates HTTPS and forwards traffic to the ALB over HTTP
inside AWS.

```mermaid
flowchart LR
    Browser["Browser\n(HTTPS)"]
    Amplify["Amplify Hosting\nhttps://master.d32mgf3rp8n1oh.amplifyapp.com"]
    CF["CloudFront\nhttps://dxxxx.cloudfront.net"]
    ALB["ALB\nhttp://trees-api-alb-xxx.eu-central-1.elb.amazonaws.com"]
    ECS["ECS Fargate\nFlask API (port 5000)\nPrivate subnet"]
    Cognito[(Cognito)]
    AppSync[(AppSync / Amplify Data)]
    DynamoTrees[(DynamoDB Trees)]
    Neptune[(Neptune / Gremlin)]
    DynamoAcl[(DynamoDB TreeAcl)]
    DynamoLock[(DynamoDB TreeEditorLocks)]
    S3[(S3 Media Bucket)]

    Browser --> Amplify
    Amplify --> Cognito
    Amplify --> AppSync
    AppSync --> DynamoTrees
    Browser -->|HTTPS + JWT| CF
    CF -->|HTTP| ALB
    ALB --> ECS
    ECS --> Cognito
    ECS --> Neptune
    ECS --> DynamoAcl
    ECS --> DynamoLock
    ECS --> S3
```

**Key points:**
- ECS tasks run in **private subnets**; only the ALB can reach them (security group allows port 5000 from the ALB's security group only).
- CloudFront provides the HTTPS endpoint; CORS_ORIGINS on the ECS task must include the Amplify frontend origin (e.g. `https://master.d32mgf3rp8n1oh.amplifyapp.com`).

---

### Development Architecture

There is no ALB in front of the dev ECS service. The dev ECS task runs in a
**public subnet** with a public IP assigned and port 5000 open to the internet,
allowing the sandbox frontend to reach it directly.

```mermaid
flowchart LR
    Browser["Browser\n(Amplify Sandbox / localhost)"]
    Sandbox["Amplify Sandbox\nnpx ampx sandbox"]
    ECS_Dev["ECS Fargate - Dev\nFlask API (port 5000)\nPublic subnet + public IP"]
    Cognito[(Cognito)]
    AppSync[(AppSync / Amplify Data)]
    DynamoTrees[(DynamoDB Trees)]
    Neptune[(Neptune / Gremlin)]
    DynamoAcl[(DynamoDB TreeAcl)]
    DynamoLock[(DynamoDB TreeEditorLocks)]
    S3[(S3 Media Bucket - dev)]

    Browser --> Sandbox
    Sandbox --> Cognito
    Sandbox --> AppSync
    AppSync --> DynamoTrees
    Browser -->|HTTP + JWT| ECS_Dev
    ECS_Dev --> Cognito
    ECS_Dev --> Neptune
    ECS_Dev --> DynamoAcl
    ECS_Dev --> DynamoLock
    ECS_Dev --> S3
```

**Key points:**
- The dev ECS task runs in a **public subnet** with **Assign public IP = ON** and no ALB.
- The task's security group allows inbound TCP 5000 from `0.0.0.0/0` (no ALB SG rule needed).
- The task's public IP is **ephemeral** — it changes when the task is replaced. Update `VITE_FLASK_API_URL` in `.env.local` after each task replacement.
- `VITE_FLASK_API_URL=http://<task-public-ip>:5000` in `.env.local` (not committed).
- CORS_ORIGINS on the dev ECS task must include the sandbox origin (e.g. `http://localhost:5173`).

---

### Request Flow (Protected Endpoints)

Applies to both prod and dev.

```mermaid
sequenceDiagram
    participant Client
    participant API as Flask API
    participant Auth as Auth Middleware
    participant Partition as Partition Middleware
    participant Role as Role Middleware
    participant Lock as Editor Lock Middleware
    participant Handler as Handler

    Client->>API: Request (JWT + X-Partition-Key)
    API->>Auth: Validate JWT (Cognito)
    Auth-->>API: user_id/email in context
    API->>Partition: Parse partition key (userId_treeId)
    Partition-->>API: tree_id in context
    API->>Role: Load role from TreeAcl
    Role-->>API: allow/deny
    API->>Lock: Ensure editor lock for write ops
    Lock-->>API: allow/deny
    API->>Handler: Execute business logic
```

---

### Data Stores

```mermaid
erDiagram
    TreeAcl {
        string treeId PK
        string userId
        string role
        string createdAt
    }
    TreeEditorLocks {
        string treeId PK
        string lockOwner
        string acquiredAt
        int expiresAt
    }
    S3Media {
        string bucket
        string key
    }
```

---

### S3 Media Key Layout

```mermaid
flowchart LR
    Bucket["s3://&lt;bucket&gt;"] --> Prefix["&lt;prefix&gt;"]
    Prefix --> Partition["&lt;partition_key&gt;"]
    Partition --> Members["members"]
    Members --> MemberId["&lt;member_id&gt;"]
    MemberId --> Pic["pic.png"]
    MemberId --> Photos["photos/&lt;uuid&gt;.&lt;ext&gt;"]
```
