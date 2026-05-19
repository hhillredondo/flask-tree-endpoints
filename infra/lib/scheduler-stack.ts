import * as cdk from 'aws-cdk-lib';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as neptune from 'aws-cdk-lib/aws-neptune';
import * as scheduler from 'aws-cdk-lib/aws-scheduler';

export interface TreesSchedulerStackProps extends cdk.StackProps {
  clusterProd: ecs.CfnCluster;
  serviceProd: ecs.CfnService;
  neptuneClusterProd: neptune.CfnDBCluster;
  clusterDev: ecs.CfnCluster;
  serviceDev: ecs.CfnService;
  neptuneClusterDev: neptune.CfnDBCluster;
}

export class TreesSchedulerStack extends cdk.Stack {
  public constructor(scope: cdk.App, id: string, props: TreesSchedulerStackProps) {
    super(scope, id, props);

    const neptuneClusterArn = (clusterRef: string) => cdk.Fn.join(':', [
      'arn:aws:rds',
      this.region,
      this.account,
      cdk.Fn.join('', ['cluster:', clusterRef]),
    ]);
    const ecsServiceArn = (clusterRef: string, serviceName: string) => cdk.Fn.join('/', [
      cdk.Fn.join(':', ['arn:aws:ecs', this.region, this.account, 'service']),
      clusterRef,
      serviceName,
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
              Action: ['rds:StartDBCluster', 'rds:StopDBCluster'],
              Resource: [
                neptuneClusterArn(props.neptuneClusterProd.ref),
                neptuneClusterArn(props.neptuneClusterDev.ref),
              ],
            },
            {
              Effect: 'Allow',
              Action: 'ecs:UpdateService',
              Resource: [
                ecsServiceArn(props.clusterProd.ref, props.serviceProd.attrName),
                ecsServiceArn(props.clusterDev.ref, props.serviceDev.attrName),
              ],
            },
          ],
        },
      }],
    });

    const ecsUpdatePayload = (clusterRef: string, serviceName: string, desiredCount: number) => cdk.Fn.sub(
      '{"Cluster":"${ClusterName}","Service":"${ServiceName}","DesiredCount":' + desiredCount + '}',
      { ClusterName: clusterRef, ServiceName: serviceName },
    );

    const neptuneClusterPayload = (clusterRef: string) => cdk.Fn.sub(
      '{"DbClusterIdentifier":"${ClusterName}"}',
      { ClusterName: clusterRef },
    );

    const baseTarget = (arn: string, input: string) => ({
      arn,
      input,
      roleArn: schedulerRole.attrArn,
      retryPolicy: { maximumEventAgeInSeconds: 86400, maximumRetryAttempts: 185 },
    });

    const neptuneStartTarget = 'arn:aws:scheduler:::aws-sdk:neptune:startDBCluster';
    const neptuneStopTarget = 'arn:aws:scheduler:::aws-sdk:neptune:stopDBCluster';
    const ecsUpdateTarget = 'arn:aws:scheduler:::aws-sdk:ecs:updateService';

    const prodNeptunePayload = neptuneClusterPayload(props.neptuneClusterProd.ref);
    const devNeptunePayload = neptuneClusterPayload(props.neptuneClusterDev.ref);

    // Prod: available 12:00–22:00 Europe/Madrid (10 hours/day).
    // Neptune starts 5 min before ECS so the cluster is ready when tasks come up,
    // and stops 5 min after ECS so in-flight requests can drain.
    new scheduler.CfnSchedule(this, 'NeptuneStart', {
      name: 'trees-prod-neptune-start',
      groupName: 'default',
      state: 'ENABLED',
      scheduleExpression: 'cron(55 11 * * ? *)',
      scheduleExpressionTimezone: 'Europe/Madrid',
      flexibleTimeWindow: { mode: 'OFF' },
      target: baseTarget(neptuneStartTarget, prodNeptunePayload),
    });

    new scheduler.CfnSchedule(this, 'EcsStart', {
      name: 'trees-prod-ecs-start',
      groupName: 'default',
      state: 'ENABLED',
      scheduleExpression: 'cron(0 12 * * ? *)',
      scheduleExpressionTimezone: 'Europe/Madrid',
      flexibleTimeWindow: { mode: 'OFF' },
      target: baseTarget(ecsUpdateTarget, ecsUpdatePayload(props.clusterProd.ref, props.serviceProd.attrName, 1)),
    });

    new scheduler.CfnSchedule(this, 'EcsStop', {
      name: 'trees-prod-ecs-stop',
      groupName: 'default',
      state: 'ENABLED',
      scheduleExpression: 'cron(0 22 * * ? *)',
      scheduleExpressionTimezone: 'Europe/Madrid',
      flexibleTimeWindow: { mode: 'OFF' },
      target: baseTarget(ecsUpdateTarget, ecsUpdatePayload(props.clusterProd.ref, props.serviceProd.attrName, 0)),
    });

    new scheduler.CfnSchedule(this, 'NeptuneStop', {
      name: 'trees-prod-neptune-stop',
      groupName: 'default',
      state: 'ENABLED',
      scheduleExpression: 'cron(5 22 * * ? *)',
      scheduleExpressionTimezone: 'Europe/Madrid',
      flexibleTimeWindow: { mode: 'OFF' },
      target: baseTarget(neptuneStopTarget, prodNeptunePayload),
    });

    // Dev: off by default. No start schedule — start manually when developing.
    // Stop fires every 6 hours (00/06/12/18 Madrid) as a safety net.
    new scheduler.CfnSchedule(this, 'EcsStopDev', {
      name: 'trees-dev-ecs-stop',
      groupName: 'default',
      state: 'ENABLED',
      scheduleExpression: 'cron(0 0/6 * * ? *)',
      scheduleExpressionTimezone: 'Europe/Madrid',
      flexibleTimeWindow: { mode: 'OFF' },
      target: baseTarget(ecsUpdateTarget, ecsUpdatePayload(props.clusterDev.ref, props.serviceDev.attrName, 0)),
    });

    new scheduler.CfnSchedule(this, 'NeptuneStopDev', {
      name: 'trees-dev-neptune-stop',
      groupName: 'default',
      state: 'ENABLED',
      scheduleExpression: 'cron(5 0/6 * * ? *)',
      scheduleExpressionTimezone: 'Europe/Madrid',
      flexibleTimeWindow: { mode: 'OFF' },
      target: baseTarget(neptuneStopTarget, devNeptunePayload),
    });
  }
}
