# trees-api infra (CDK)

CDK app for the AWS resources behind the Trees API. The resources predate the
CDK app: they were built in the console, then adopted into CloudFormation in May
2026 via the IaC Generator and `cdk migrate`, one stack at a time. That import is
finished, so day-to-day work is ordinary `cdk deploy`.

Region is `eu-central-1`, except where noted. The account is read from
`CDK_DEFAULT_ACCOUNT`, and synth fails with a clear message if it is unset.

## Stacks

`bin/infra.ts` instantiates all five.

| Stack | Region | Resources |
| ----- | ------ | --------- |
| `TreesNetworkingStack` | eu-central-1 | VPC, 4 subnets, IGW, route tables, routes, subnet associations, `task-sg`, `neptune-sg` |
| `TreesDataStack`       | eu-central-1 | Neptune subnet group, 2 Neptune clusters + instances (db.t4g.medium), 2 SSM params (`GREMLIN_ENDPOINT_*`) |
| `TreesComputeStack`    | eu-central-1 | ECR, 2 ECS clusters/services/task-defs, log groups, VPC Link, 2 HTTP APIs + stages + deployments, 2 CloudFront distros, hosted zone, 2 R53 ALIAS records, 3 IAM roles |
| `TreesSchedulerStack`  | eu-central-1 | 4 EventBridge schedules + scheduler IAM role |
| `TreesEdgeStack`       | us-east-1    | CloudFront WAFv2 WebACL; 2 ACM certs defined in code but not deployed in the current account |

## Deploying

```bash
export CDK_DEFAULT_ACCOUNT=<account-id>
export CDK_DEFAULT_REGION=eu-central-1

npm install
npx cdk diff <Stack>     # always read this first
npx cdk deploy <Stack>
```

Deploy one stack at a time and check `cdk diff` in between. `TreesComputeStack`
is the one to be careful with: it owns the ECS services and the Route 53 records,
so a bad change there takes the API down.

The Cognito ids, table and bucket names and the Gremlin endpoints are not in this
app. They resolve from SSM through the task definition's `secrets:` block at task
start, so changing one needs a new task, not a redeploy. Every parameter named
there must exist, or the task fails to start.

`deploy.yml` only pushes an image and forces a new deployment, which reuses the
registered task definition. Changes to task definitions reach AWS only through
`cdk deploy TreesComputeStack`.

## What is not in IaC, and why

- **ACM certificates** in `us-east-1`. `AWS::CertificateManager::Certificate` is
  not importable into CloudFormation. They are defined in `TreesEdgeStack` so a
  clean rebuild would create them through DNS validation against the hosted zone,
  but the certificates production CloudFront actually uses are still
  console-managed.
- **Cloud Map** (the `internal.trees-lab.com` namespace and its `prod-api` /
  `dev-api` services). `AWS::ServiceDiscovery::*` is not importable either, and
  both the ECS service registry and the HTTP API integration URI reference those
  ARNs. Adopting them means replacing the ECS service and updating the
  integration in one coordinated change.

`TreesEdgeStack` uses `CliCredentialsStackSynthesizer` rather than the default.
The IAM user used for deploys lacks `ecr:CreateRepository`, so a normal
`cdk bootstrap` in `us-east-1` rolls back; that synthesizer skips the bootstrap
version parameter and lets the stack deploy without it.

## Known quirks from the import

These came out of `cdk migrate` and are worth knowing before you touch them:

- The Neptune cluster has `enableCloudwatchLogsExports: []`. An empty array and
  an unset property behave differently in CloudFormation. Leave it unless drift
  shows up.
- Write-only properties such as master passwords are stripped from import
  templates. Not a problem here, since Neptune uses IAM auth.
