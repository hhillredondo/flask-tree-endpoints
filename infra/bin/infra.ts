#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { TreesPersistentStack } from "../lib/persistent-stack";
import { TreesNetworkingStack } from "../lib/networking-stack";
import { TreesDataStack } from "../lib/data-stack";
import { TreesComputeStack } from "../lib/compute-stack";
import { TreesSchedulerStack } from "../lib/scheduler-stack";
import { TreesEdgeStack } from "../lib/edge-stack";

const app = new cdk.App();

cdk.Tags.of(app).add("Project", "flask-tree-endpoints", {
  excludeResourceTypes: [
    "AWS::CertificateManager::Certificate",
    "AWS::WAFv2::WebACL",
    "AWS::ApiGatewayV2::Stage",
  ],
});

// Account is supplied by the environment, not hardcoded: an account id in a public
// repo is free reconnaissance, and a literal here silently targets the wrong
// account for anyone else deploying this stack.
const account = process.env.CDK_DEFAULT_ACCOUNT ?? process.env.AWS_ACCOUNT_ID;
if (!account) {
  throw new Error(
    "Set CDK_DEFAULT_ACCOUNT (or AWS_ACCOUNT_ID) before synthesising this app."
  );
}
const env = { account, region: "eu-central-1" };
const usEast1Env = { account, region: "us-east-1" };

const persistent = new TreesPersistentStack(app, "TreesPersistentStack", { env });

const edge = new TreesEdgeStack(app, "TreesEdgeStack", {
  env: usEast1Env,
  crossRegionReferences: true,
  synthesizer: new cdk.CliCredentialsStackSynthesizer(),
});

const networking = new TreesNetworkingStack(app, "TreesNetworkingStack", { env });

const data = new TreesDataStack(app, "TreesDataStack", {
  env,
  privateSubnets: [networking.privateSubnetA, networking.privateSubnetB],
  neptuneSg: networking.neptuneSg,
});

const compute = new TreesComputeStack(app, "TreesComputeStack", {
  env,
  crossRegionReferences: true,
  vpc: networking.vpc,
  publicSubnets: [networking.publicSubnetA, networking.publicSubnetB],
  privateSubnets: [networking.privateSubnetA, networking.privateSubnetB],
  taskSg: networking.taskSg,
  clusterDev: data.clusterDev,
  clusterProd: data.clusterProd,
  hostedZone: persistent.hostedZone,
  ecrRepository: persistent.ecrRepository,
  certApiProdArn: edge.certApiProd.ref,
  certApiDevArn: edge.certApiDev.ref,
  webAclArn: edge.webAcl.attrArn,
});

new TreesSchedulerStack(app, "TreesSchedulerStack", {
  env,
  clusterProd: compute.clusterProd,
  serviceProd: compute.serviceProd,
  neptuneClusterProd: data.clusterProd,
  clusterDev: compute.clusterDev,
  serviceDev: compute.serviceDev,
  neptuneClusterDev: data.clusterDev,
});
