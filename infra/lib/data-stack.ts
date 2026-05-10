import * as cdk from 'aws-cdk-lib';
import * as neptune from 'aws-cdk-lib/aws-neptune';
import * as ssm from 'aws-cdk-lib/aws-ssm';

export interface TreesDataStackProps extends cdk.StackProps {
}

export class TreesDataStack extends cdk.Stack {
  public constructor(scope: cdk.App, id: string, props: TreesDataStackProps = {}) {
    super(scope, id, props);

    // Resources
    const neptuneClusterDev = new neptune.CfnDBCluster(this, 'NeptuneClusterDev', {
      storageEncrypted: true,
      engineVersion: '1.4.7.0',
      kmsKeyId: 'arn:aws:kms:eu-central-1:AWS_ACCOUNT_ID:key/fd1505d9-aacf-463c-a6ac-4d2106e7b9a3',
      associatedRoles: [
      ],
      availabilityZones: [
        'eu-central-1a',
        'eu-central-1c',
        'eu-central-1b',
      ],
      dbClusterIdentifier: 'trees-neptune-dev',
      preferredMaintenanceWindow: 'thu:23:31-fri:00:01',
      iamAuthEnabled: true,
      dbSubnetGroupName: 'neptune-subnet-group',
      deletionProtection: false,
      preferredBackupWindow: '22:35-23:05',
      dbPort: 8182,
      vpcSecurityGroupIds: [
        'sg-0229c88c446cba89c',
      ],
      copyTagsToSnapshot: false,
      dbClusterParameterGroupName: 'default.neptune1.4',
      backupRetentionPeriod: 1,
      tags: [
        {
          value: 'trees-neptune-dev',
          key: 'Name',
        },
        {
          value: 'dev',
          key: 'Env',
        },
      ],
      enableCloudwatchLogsExports: [
      ],
    });
    neptuneClusterDev.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const neptuneClusterProd = new neptune.CfnDBCluster(this, 'NeptuneClusterProd', {
      storageEncrypted: true,
      engineVersion: '1.4.7.0',
      kmsKeyId: 'arn:aws:kms:eu-central-1:AWS_ACCOUNT_ID:key/fd1505d9-aacf-463c-a6ac-4d2106e7b9a3',
      associatedRoles: [
      ],
      availabilityZones: [
        'eu-central-1a',
        'eu-central-1c',
        'eu-central-1b',
      ],
      dbClusterIdentifier: 'trees-neptune-prod',
      preferredMaintenanceWindow: 'sat:04:10-sat:04:40',
      iamAuthEnabled: true,
      dbSubnetGroupName: 'neptune-subnet-group',
      deletionProtection: false,
      preferredBackupWindow: '01:54-02:24',
      dbPort: 8182,
      vpcSecurityGroupIds: [
        'sg-0229c88c446cba89c',
      ],
      copyTagsToSnapshot: false,
      dbClusterParameterGroupName: 'default.neptune1.4',
      backupRetentionPeriod: 1,
      tags: [
        {
          value: 'trees-neptune-prod',
          key: 'Name',
        },
        {
          value: 'prod',
          key: 'Env',
        },
      ],
      enableCloudwatchLogsExports: [
      ],
    });
    neptuneClusterProd.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const neptuneInstanceDev = new neptune.CfnDBInstance(this, 'NeptuneInstanceDev', {
      dbParameterGroupName: 'default.neptune1.4',
      dbInstanceClass: 'db.t4g.medium',
      dbClusterIdentifier: 'trees-neptune-dev',
      availabilityZone: 'eu-central-1b',
      preferredMaintenanceWindow: 'sun:01:45-sun:02:15',
      autoMinorVersionUpgrade: true,
      dbSubnetGroupName: 'neptune-subnet-group',
      dbInstanceIdentifier: 'trees-neptune-dev-1',
      tags: [
        {
          value: 'trees-neptune-dev-1',
          key: 'Name',
        },
        {
          value: 'dev',
          key: 'Env',
        },
      ],
    });
    neptuneInstanceDev.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const neptuneInstanceProd = new neptune.CfnDBInstance(this, 'NeptuneInstanceProd', {
      dbParameterGroupName: 'default.neptune1.4',
      dbInstanceClass: 'db.t4g.medium',
      dbClusterIdentifier: 'trees-neptune-prod',
      availabilityZone: 'eu-central-1b',
      preferredMaintenanceWindow: 'sat:22:21-sat:22:51',
      autoMinorVersionUpgrade: true,
      dbSubnetGroupName: 'neptune-subnet-group',
      dbInstanceIdentifier: 'trees-neptune-prod-1',
      tags: [
        {
          value: 'trees-neptune-prod-1',
          key: 'Name',
        },
        {
          value: 'prod',
          key: 'Env',
        },
      ],
    });
    neptuneInstanceProd.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const neptuneSubnetGroup = new neptune.CfnDBSubnetGroup(this, 'NeptuneSubnetGroup', {
      dbSubnetGroupDescription: 'neptune subnet group for trees project db',
      subnetIds: [
        'subnet-0b0add3a8dbedf82e',
        'subnet-01e3a267b85c87b0c',
      ],
      dbSubnetGroupName: 'neptune-subnet-group',
    });
    neptuneSubnetGroup.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const ssmGremlinEndpointDev = new ssm.CfnParameter(this, 'SsmGremlinEndpointDev', {
      value: 'trees-neptune-dev.cluster-cluauo8uat5l.eu-central-1.neptune.amazonaws.com',
      dataType: 'text',
      type: 'String',
      name: '/trees/api/GREMLIN_ENDPOINT_DEV',
    });
    ssmGremlinEndpointDev.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const ssmGremlinEndpointProd = new ssm.CfnParameter(this, 'SsmGremlinEndpointProd', {
      value: 'trees-neptune-prod.cluster-cluauo8uat5l.eu-central-1.neptune.amazonaws.com',
      dataType: 'text',
      type: 'String',
      name: '/trees/api/GREMLIN_ENDPOINT_PROD',
    });
    ssmGremlinEndpointProd.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;
  }
}
