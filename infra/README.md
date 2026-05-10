# trees-api infra (CDK)

CDK app that imports the AWS resources backing `https://api.trees-lab.com/`. Generated via the CloudFormation IaC Generator → `cdk migrate` workflow on 2026-05-10.

Region `eu-central-1`, account `AWS_ACCOUNT_ID`.

## Stacks

| Stack | Resources | Slice |
| ----- | --------- | ----- |
| `TreesNetworkingStack` | VPC, 4 subnets, IGW, route tables, routes, subnet associations, `task-sg`, `neptune-sg` | A |
| `TreesDataStack`       | Neptune subnet group, 2 Neptune clusters + instances (db.t4g.medium), 2 SSM params (`GREMLIN_ENDPOINT_*`) | B |
| `TreesComputeStack`    | ECR, 2 ECS clusters/services/task-defs, log groups, VPC Link, 2 HTTP APIs, 2 CloudFront distros, hosted zone, 3 IAM roles | C |
| `TreesSchedulerStack`  | 4 EventBridge schedules + scheduler IAM role | D |

`bin/infra.ts` instantiates all four against `eu-central-1`.

## What's NOT in IaC (and why)

These don't have CFN-importable types, so they remain console-managed:

- **AWS Cloud Map** (`internal.trees-lab.com.` namespace + `prod-api`/`dev-api` services) — `AWS::ServiceDiscovery::*` isn't supported by IaC Generator. The underlying R53 hosted zone (`Z005424127FR8DAXCLUAZ`) is auto-created by Cloud Map.
- **API Gateway HTTP API stages** (`$default` for both APIs) — `AWS::ApiGatewayV2::Stage` not picked up by the scan.
- **ACM certs** for CloudFront live in `us-east-1`. Cross-region resources require a separate stack (deferred).
- **WAFv2 WebACL** (`CreatedByCloudFront-0ac1ed8d`) — auto-created by CloudFront console, console-managed.
- **Route 53 record sets** for `api.trees-lab.com` and `dev-api.trees-lab.com` — only the hosted zone itself is imported; the ALIAS records can be added as `CfnRecordSet` constructs in a follow-up.

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

## After all four stacks are imported

- Future changes: edit the stack `.ts` files, run `cdk deploy <Stack>` (no `--import-existing-resources`).
- Add the missing pieces (Cloud Map, ACM us-east-1, R53 records) as fresh CDK resources in a new follow-up stack — no import dance needed for those since they're create-not-import.
- Refactor the auto-generated `Cfn*` constructs to L2 constructs incrementally if desired.

## Caveats from the migrate generator

These come from `aws-cdk migrate` and need a human eye:

- Neptune cluster `enableCloudwatchLogsExports: []` is an empty array — fine, but the empty array vs unset has subtle CFN behavior. Leave as-is unless drift appears.
- Some "write-only" properties (e.g. master passwords) are stripped from the import template. Not an issue for Neptune with IAM auth.
- `vpcEndpointId` was incorrectly populated on `PublicDefaultRoute` — already removed.
