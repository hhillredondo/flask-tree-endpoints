import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as scheduler from 'aws-cdk-lib/aws-scheduler';

export interface TreesSchedulerStackProps extends cdk.StackProps {
}

export class TreesSchedulerStack extends cdk.Stack {
  public constructor(scope: cdk.App, id: string, props: TreesSchedulerStackProps = {}) {
    super(scope, id, props);

    // Resources
    const ecsStart = new scheduler.CfnSchedule(this, 'EcsStart', {
      groupName: 'default',
      scheduleExpression: 'cron(5 9 * * ? *)',
      target: {
        input: '{\"Cluster\":\"trees-api-prod\",\"Service\":\"trees-api-svc-prod\",\"DesiredCount\":1}',
        arn: 'arn:aws:scheduler:::aws-sdk:ecs:updateService',
        retryPolicy: {
          maximumEventAgeInSeconds: 86400,
          maximumRetryAttempts: 185,
        },
        roleArn: cdk.Lazy.string({ produce: () => treesSchedulerRole.attrArn }),
      },
      state: 'ENABLED',
      flexibleTimeWindow: {
        mode: 'OFF',
      },
      scheduleExpressionTimezone: 'Europe/Madrid',
      name: 'trees-prod-ecs-start',
    });
    ecsStart.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const ecsStop = new scheduler.CfnSchedule(this, 'EcsStop', {
      groupName: 'default',
      scheduleExpression: 'cron(0 23 * * ? *)',
      target: {
        input: '{\"Cluster\":\"trees-api-prod\",\"Service\":\"trees-api-svc-prod\",\"DesiredCount\":0}',
        arn: 'arn:aws:scheduler:::aws-sdk:ecs:updateService',
        retryPolicy: {
          maximumEventAgeInSeconds: 86400,
          maximumRetryAttempts: 185,
        },
        roleArn: cdk.Lazy.string({ produce: () => treesSchedulerRole.attrArn }),
      },
      state: 'ENABLED',
      flexibleTimeWindow: {
        mode: 'OFF',
      },
      scheduleExpressionTimezone: 'Europe/Madrid',
      name: 'trees-prod-ecs-stop',
    });
    ecsStop.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const neptuneStart = new scheduler.CfnSchedule(this, 'NeptuneStart', {
      groupName: 'default',
      scheduleExpression: 'cron(0 9 * * ? *)',
      target: {
        input: '{\"DbClusterIdentifier\":\"trees-neptune-prod\"}',
        arn: 'arn:aws:scheduler:::aws-sdk:neptune:startDBCluster',
        retryPolicy: {
          maximumEventAgeInSeconds: 86400,
          maximumRetryAttempts: 185,
        },
        roleArn: cdk.Lazy.string({ produce: () => treesSchedulerRole.attrArn }),
      },
      state: 'ENABLED',
      flexibleTimeWindow: {
        mode: 'OFF',
      },
      scheduleExpressionTimezone: 'Europe/Madrid',
      name: 'trees-prod-neptune-start',
    });
    neptuneStart.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const neptuneStop = new scheduler.CfnSchedule(this, 'NeptuneStop', {
      groupName: 'default',
      scheduleExpression: 'cron(5 23 * * ? *)',
      target: {
        input: '{\"DbClusterIdentifier\":\"trees-neptune-prod\"}',
        arn: 'arn:aws:scheduler:::aws-sdk:neptune:stopDBCluster',
        retryPolicy: {
          maximumEventAgeInSeconds: 86400,
          maximumRetryAttempts: 185,
        },
        roleArn: cdk.Lazy.string({ produce: () => treesSchedulerRole.attrArn }),
      },
      state: 'ENABLED',
      flexibleTimeWindow: {
        mode: 'OFF',
      },
      scheduleExpressionTimezone: 'Europe/Madrid',
      name: 'trees-prod-neptune-stop',
    });
    neptuneStop.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const treesSchedulerRole = new iam.CfnRole(this, 'TreesSchedulerRole', {
      path: '/',
      maxSessionDuration: 3600,
      roleName: 'trees-scheduler-prod',
      policies: [
        {
          policyDocument: {
            Version: '2012-10-17',
            Statement: [
              {
                Resource: 'arn:aws:rds:eu-central-1:AWS_ACCOUNT_ID:cluster:trees-neptune-prod',
                Action: [
                  'neptune:StartDBCluster',
                  'neptune:StopDBCluster',
                ],
                Effect: 'Allow',
              },
              {
                Resource: 'arn:aws:ecs:eu-central-1:AWS_ACCOUNT_ID:service/trees-api-prod/trees-api-svc-prod',
                Action: 'ecs:UpdateService',
                Effect: 'Allow',
              },
            ],
          },
          policyName: 'scheduler-actions',
        },
      ],
      assumeRolePolicyDocument: {
        Version: '2012-10-17',
        Statement: [
          {
            Condition: {
              StringEquals: {
                'aws:SourceAccount': 'AWS_ACCOUNT_ID',
              },
            },
            Action: 'sts:AssumeRole',
            Effect: 'Allow',
            Principal: {
              Service: 'scheduler.amazonaws.com',
            },
          },
        ],
      },
    });
    treesSchedulerRole.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;
  }
}
