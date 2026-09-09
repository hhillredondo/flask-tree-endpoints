# trees-api infra (CDK)

CDK app that imports the AWS resources backing `https://api.trees-lab.com/`. Generated via the CloudFormation IaC Generator → `cdk migrate` workflow on 2026-05-10.

Region `eu-central-1`. The account comes from `CDK_DEFAULT_ACCOUNT`.

## Stacks

| Stack | Region | Resources |
| ----- | ------ | --------- |
| `TreesNetworkingStack` | eu-central-1 | VPC, 4 subnets, IGW, route tables, routes, subnet associations, `task-sg`, `neptune-sg` |
| `TreesDataStack`       | eu-central-1 | Neptune subnet group, 2 Neptune clusters + instances (db.t4g.medium), 2 SSM params (`GREMLIN_ENDPOINT_*`) |
| `TreesComputeStack`    | eu-central-1 | ECR, 2 ECS clusters/services/task-defs, log groups, VPC Link, 2 HTTP APIs + stages + deployments, 2 CloudFront distros, hosted zone, 2 R53 ALIAS records, 3 IAM roles |
| `TreesSchedulerStack`  | eu-central-1 | 4 EventBridge schedules + scheduler IAM role |
| `TreesEdgeStack`       | us-east-1    | CloudFront WAFv2 WebACL (imported); 2 ACM certs (in code, not deployed in current account — see below) |

`bin/infra.ts` instantiates all five.

## What's NOT in IaC (and why)

- **ACM certs** in `us-east-1` — `AWS::CertificateManager::Certificate` is not CFN-importable. The certs are defined in `TreesEdgeStack` (so a clean-slate-rebuild creates them via DNS validation against the hosted zone), but the *live* certs the production CloudFront uses are still console-managed. Phase B/C will swap CloudFront's `viewerCertificate` to the CDK-managed cert ARNs via cross-region references.
- **Cloud Map** (`internal.trees-lab.com.` namespace + `prod-api`/`dev-api` services) — `AWS::ServiceDiscovery::*` isn't importable. ECS service registry and HTTP API `integrationUri` reference these ARNs, so adopting them requires a coordinated swap (ECS service replacement + integration update). Deferred to Phase B/C alongside the refs refactor.

## Deploying with import

The `migrate/<slice>.migrate.json` files map logical IDs to physical resource IDs for each stack. Per-stack import workflow (do one stack at a time, sanity-check between):

```bash
# 0) build & synth so cdk.out/ is up to date
npm run build && AWS_PROFILE=admin-1 npx cdk synth --all

# 1) import slice A
aws cloudformation create-change-set \
  --profile admin-1 \
  --stack-name TreesNetworkingStack \
  --change-set-name InitialImport \
  --change-set-type IMPORT \
  --resources-to-import file://migrate/networking.migrate.json \
  --template-body file://cdk.out/TreesNetworkingStack.template.json \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM

aws cloudformation describe-change-set \
  --profile admin-1 \
  --stack-name TreesNetworkingStack \
  --change-set-name InitialImport

# review, then execute:
aws cloudformation execute-change-set \
  --profile admin-1 \
  --stack-name TreesNetworkingStack \
  --change-set-name InitialImport

# 2) repeat for TreesDataStack, TreesComputeStack, TreesSchedulerStack
```

After each stack's IMPORT completes, run `cdk diff <Stack>` to confirm there's no drift before moving to the next.

## After all stacks are imported

- Future changes: edit the stack `.ts` files, run `cdk deploy <Stack>` (no `--import-existing-resources`).
- Refactor the auto-generated `Cfn*` constructs to L2 constructs incrementally if desired.

## Phase A history (2026-05-10)

Closed the smaller IaC gaps after the initial 51-resource import:

- **R53 ALIAS records** (`api.trees-lab.com`, `dev-api.trees-lab.com`) — `AWS::Route53::RecordSet` is not importable, so we deleted the live records and let `cdk deploy TreesComputeStack` create them. Brief NXDOMAIN window during deploy, full restore in <1 min.
- **HTTP API `$default` stages + initial deployments** — `AWS::ApiGatewayV2::Stage` is not importable. Same approach: deleted live stages, `cdk deploy` recreated them with explicit `CfnDeployment` resources (`autoDeploy: true` alone won't seed a deployment for a freshly-created stage).
- **WAFv2 WebACL (prod CloudFront)** — `AWS::WAFv2::WebACL` IS importable. Created `TreesEdgeStack` in `us-east-1` and ran `create-change-set --change-set-type IMPORT` for it.
- **us-east-1 nuance**: `TreesEdgeStack` uses `cdk.CliCredentialsStackSynthesizer()` because the `Hugo-Amplify` IAM user lacks `ecr:CreateRepository`, so a normal `cdk bootstrap` rolls back. The synthesizer skips the bootstrap version parameter, letting raw `aws cloudformation create-change-set` run without bootstrap.

## Caveats from the migrate generator

These come from `aws-cdk migrate` and need a human eye:

- Neptune cluster `enableCloudwatchLogsExports: []` is an empty array — fine, but the empty array vs unset has subtle CFN behavior. Leave as-is unless drift appears.
- Some "write-only" properties (e.g. master passwords) are stripped from the import template. Not an issue for Neptune with IAM auth.
- `vpcEndpointId` was incorrectly populated on `PublicDefaultRoute` — already removed.
