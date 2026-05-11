import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as neptune from 'aws-cdk-lib/aws-neptune';
import * as ssm from 'aws-cdk-lib/aws-ssm';

export interface TreesDataStackProps extends cdk.StackProps {
  privateSubnets: ec2.CfnSubnet[];
  neptuneSg: ec2.CfnSecurityGroup;
}

export class TreesDataStack extends cdk.Stack {
  public readonly clusterDev: neptune.CfnDBCluster;
  public readonly clusterProd: neptune.CfnDBCluster;

  public constructor(scope: cdk.App, id: string, props: TreesDataStackProps) {
    super(scope, id, props);

    const subnetGroup = new neptune.CfnDBSubnetGroup(this, 'NeptuneSubnetGroup', {
      dbSubnetGroupName: 'neptune-subnet-group',
      dbSubnetGroupDescription: 'neptune subnet group for trees project db',
      subnetIds: props.privateSubnets.map((s) => s.ref),
    });

    const clusterDefaults = {
      engineVersion: '1.4.7.0',
      iamAuthEnabled: true,
      dbPort: 8182,
      dbClusterParameterGroupName: 'default.neptune1.4',
      dbSubnetGroupName: subnetGroup.ref,
      vpcSecurityGroupIds: [props.neptuneSg.ref],
      backupRetentionPeriod: 1,
      storageEncrypted: true,
      deletionProtection: false,
    };

    this.clusterDev = new neptune.CfnDBCluster(this, 'NeptuneClusterDev', {
      ...clusterDefaults,
      dbClusterIdentifier: 'trees-neptune-dev',
      preferredMaintenanceWindow: 'thu:23:31-fri:00:01',
      preferredBackupWindow: '22:35-23:05',
      tags: [
        { key: 'Name', value: 'trees-neptune-dev' },
        { key: 'Env', value: 'dev' },
      ],
    });

    this.clusterProd = new neptune.CfnDBCluster(this, 'NeptuneClusterProd', {
      ...clusterDefaults,
      dbClusterIdentifier: 'trees-neptune-prod',
      preferredMaintenanceWindow: 'sat:04:10-sat:04:40',
      preferredBackupWindow: '01:54-02:24',
      tags: [
        { key: 'Name', value: 'trees-neptune-prod' },
        { key: 'Env', value: 'prod' },
      ],
    });

    new neptune.CfnDBInstance(this, 'NeptuneInstanceDev', {
      dbClusterIdentifier: this.clusterDev.ref,
      dbInstanceIdentifier: 'trees-neptune-dev-1',
      dbInstanceClass: 'db.t4g.medium',
      dbParameterGroupName: 'default.neptune1.4',
      dbSubnetGroupName: subnetGroup.ref,
      availabilityZone: 'eu-central-1b',
      preferredMaintenanceWindow: 'sun:01:45-sun:02:15',
      autoMinorVersionUpgrade: true,
      tags: [
        { key: 'Name', value: 'trees-neptune-dev-1' },
        { key: 'Env', value: 'dev' },
      ],
    });

    new neptune.CfnDBInstance(this, 'NeptuneInstanceProd', {
      dbClusterIdentifier: this.clusterProd.ref,
      dbInstanceIdentifier: 'trees-neptune-prod-1',
      dbInstanceClass: 'db.t4g.medium',
      dbParameterGroupName: 'default.neptune1.4',
      dbSubnetGroupName: subnetGroup.ref,
      availabilityZone: 'eu-central-1b',
      preferredMaintenanceWindow: 'sat:22:21-sat:22:51',
      autoMinorVersionUpgrade: true,
      tags: [
        { key: 'Name', value: 'trees-neptune-prod-1' },
        { key: 'Env', value: 'prod' },
      ],
    });

    new ssm.CfnParameter(this, 'SsmGremlinEndpointDev', {
      name: '/trees/api/GREMLIN_ENDPOINT_DEV',
      type: 'String',
      dataType: 'text',
      value: this.clusterDev.attrEndpoint,
    });

    new ssm.CfnParameter(this, 'SsmGremlinEndpointProd', {
      name: '/trees/api/GREMLIN_ENDPOINT_PROD',
      type: 'String',
      dataType: 'text',
      value: this.clusterProd.attrEndpoint,
    });
  }
}
