#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { TreesNetworkingStack } from "../lib/networking-stack";
import { TreesDataStack } from "../lib/data-stack";
import { TreesComputeStack } from "../lib/compute-stack";
import { TreesSchedulerStack } from "../lib/scheduler-stack";
import { TreesEdgeStack } from "../lib/edge-stack";

const app = new cdk.App();

const account = "AWS_ACCOUNT_ID";
const env = { account, region: "eu-central-1" };
const usEast1Env = { account, region: "us-east-1" };

new TreesNetworkingStack(app, "TreesNetworkingStack", { env });
new TreesDataStack(app, "TreesDataStack", { env });
new TreesComputeStack(app, "TreesComputeStack", { env });
new TreesSchedulerStack(app, "TreesSchedulerStack", { env });
new TreesEdgeStack(app, "TreesEdgeStack", {
  env: usEast1Env,
  synthesizer: new cdk.CliCredentialsStackSynthesizer(),
});
