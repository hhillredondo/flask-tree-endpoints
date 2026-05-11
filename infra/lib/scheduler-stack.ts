import * as cdk from 'aws-cdk-lib';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as neptune from 'aws-cdk-lib/aws-neptune';
import * as scheduler from 'aws-cdk-lib/aws-scheduler';

export interface TreesSchedulerStackProps extends cdk.StackProps {
  clusterProd: ecs.CfnCluster;
  serviceProd: ecs.CfnService;
  neptuneClusterProd: neptune.CfnDBCluster;
}

export class TreesSchedulerStack extends cdk.Stack {
  public constructor(scope: cdk.App, id: string, props: TreesSchedulerStackProps) {
    super(scope, id, props);

    const neptuneClusterArn = cdk.Fn.join(':', [
      'arn:aws:rds',
      this.region,
      this.account,
      cdk.Fn.join('', ['cluster:', props.neptuneClusterProd.ref]),
    ]);
    const ecsServiceArn = cdk.Fn.join('/', [
      cdk.Fn.join(':', ['arn:aws:ecs', this.region, this.account, 'service']),
      props.clusterProd.ref,
      props.serviceProd.attrName,
    ]);

    const schedulerRole = new iam.CfnRole(this, 'TreesSchedulerRole', {
      roleName: 'trees-scheduler-prod',
      assumeRolePolicyDocument: {
        Version: '2012-10-17',
        Statement: [{
          Effect: 'Allow',
          Principal: { Service: 'scheduler.amazonaws.com' },
          Action: 'sts:AssumeRole',
          Condition: { StringEquals: { 'aws:SourceAccount': this.account } },
        }],
      },
      policies: [{
        policyName: 'scheduler-actions',
        policyDocument: {
          Version: '2012-10-17',
          Statement: [
            {
              Effect: 'Allow',
              Action: ['neptune:StartDBCluster', 'neptune:StopDBCluster'],
              Resource: neptuneClusterArn,
            },
            {
              Effect: 'Allow',
              Action: 'ecs:UpdateService',
              Resource: ecsServiceArn,
            },
          ],
        },
      }],
    });

    const ecsUpdatePayload = (desiredCount: number) => cdk.Fn.sub(
      '{"Cluster":"${ClusterName}","Service":"${ServiceName}","DesiredCount":' + desiredCount + '}',
      { ClusterName: props.clusterProd.ref, ServiceName: props.serviceProd.attrName },
    );

    const neptuneClusterPayload = cdk.Fn.sub(
      '{"DbClusterIdentifier":"${ClusterName}"}',
      { ClusterName: props.neptuneClusterProd.ref },
    );

    const baseTarget = (arn: string, input: string) => ({
      arn,
      input,
      roleArn: schedulerRole.attrArn,
      retryPolicy: { maximumEventAgeInSeconds: 86400, maximumRetryAttempts: 185 },
    });

    new scheduler.CfnSchedule(this, 'NeptuneStart', {
      name: 'trees-prod-neptune-start',
      groupName: 'default',
      state: 'ENABLED',
      scheduleExpression: 'cron(0 9 * * ? *)',
      scheduleExpressionTimezone: 'Europe/Madrid',
      flexibleTimeWindow: { mode: 'OFF' },
      target: baseTarget('arn:aws:scheduler:::aws-sdk:neptune:startDBCluster', neptuneClusterPayload),
    });

    new scheduler.CfnSchedule(this, 'EcsStart', {
      name: 'trees-prod-ecs-start',
      groupName: 'default',
      state: 'ENABLED',
      scheduleExpression: 'cron(5 9 * * ? *)',
      scheduleExpressionTimezone: 'Europe/Madrid',
      flexibleTimeWindow: { mode: 'OFF' },
      target: baseTarget('arn:aws:scheduler:::aws-sdk:ecs:updateService', ecsUpdatePayload(1)),
    });

    new scheduler.CfnSchedule(this, 'EcsStop', {
      name: 'trees-prod-ecs-stop',
      groupName: 'default',
      state: 'ENABLED',
      scheduleExpression: 'cron(0 23 * * ? *)',
      scheduleExpressionTimezone: 'Europe/Madrid',
      flexibleTimeWindow: { mode: 'OFF' },
      target: baseTarget('arn:aws:scheduler:::aws-sdk:ecs:updateService', ecsUpdatePayload(0)),
    });

    new scheduler.CfnSchedule(this, 'NeptuneStop', {
      name: 'trees-prod-neptune-stop',
      groupName: 'default',
      state: 'ENABLED',
      scheduleExpression: 'cron(5 23 * * ? *)',
      scheduleExpressionTimezone: 'Europe/Madrid',
      flexibleTimeWindow: { mode: 'OFF' },
      target: baseTarget('arn:aws:scheduler:::aws-sdk:neptune:stopDBCluster', neptuneClusterPayload),
    });
  }
}
