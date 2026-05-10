#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { TreesNetworkingStack } from "../lib/networking-stack";
import { TreesDataStack } from "../lib/data-stack";
import { TreesComputeStack } from "../lib/compute-stack";
import { TreesSchedulerStack } from "../lib/scheduler-stack";

const app = new cdk.App();

const env = { account: "AWS_ACCOUNT_ID", region: "eu-central-1" };

new TreesNetworkingStack(app, "TreesNetworkingStack", { env });
new TreesDataStack(app, "TreesDataStack", { env });
new TreesComputeStack(app, "TreesComputeStack", { env });
new TreesSchedulerStack(app, "TreesSchedulerStack", { env });
