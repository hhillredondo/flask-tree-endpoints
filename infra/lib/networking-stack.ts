import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';

export class TreesNetworkingStack extends cdk.Stack {
  public readonly vpc: ec2.CfnVPC;
  public readonly publicSubnetA: ec2.CfnSubnet;
  public readonly publicSubnetB: ec2.CfnSubnet;
  public readonly privateSubnetA: ec2.CfnSubnet;
  public readonly privateSubnetB: ec2.CfnSubnet;
  public readonly taskSg: ec2.CfnSecurityGroup;
  public readonly neptuneSg: ec2.CfnSecurityGroup;

  public constructor(scope: cdk.App, id: string, props: cdk.StackProps = {}) {
    super(scope, id, props);

    this.vpc = new ec2.CfnVPC(this, 'TreesVpc', {
      cidrBlock: '10.0.0.0/16',
      enableDnsSupport: true,
      enableDnsHostnames: true,
      instanceTenancy: 'default',
      tags: [{ key: 'Name', value: 'trees-vpc-vpc' }],
    });

    const igw = new ec2.CfnInternetGateway(this, 'TreesIgw', {
      tags: [{ key: 'Name', value: 'trees-vpc-igw' }],
    });

    new ec2.CfnVPCGatewayAttachment(this, 'TreesIgwAttachment', {
      vpcId: this.vpc.ref,
      internetGatewayId: igw.ref,
    });

    this.publicSubnetA = new ec2.CfnSubnet(this, 'PublicSubnetA', {
      vpcId: this.vpc.ref,
      availabilityZone: 'eu-central-1a',
      cidrBlock: '10.0.0.0/20',
      mapPublicIpOnLaunch: false,
      tags: [{ key: 'Name', value: 'trees-vpc-subnet-public1-eu-central-1a' }],
    });

    this.publicSubnetB = new ec2.CfnSubnet(this, 'PublicSubnetB', {
      vpcId: this.vpc.ref,
      availabilityZone: 'eu-central-1b',
      cidrBlock: '10.0.16.0/20',
      mapPublicIpOnLaunch: false,
      tags: [{ key: 'Name', value: 'trees-vpc-subnet-public2-eu-central-1b' }],
    });

    this.privateSubnetA = new ec2.CfnSubnet(this, 'PrivateSubnetA', {
      vpcId: this.vpc.ref,
      availabilityZone: 'eu-central-1a',
      cidrBlock: '10.0.128.0/20',
      mapPublicIpOnLaunch: false,
      tags: [{ key: 'Name', value: 'trees-vpc-subnet-private1-eu-central-1a' }],
    });

    this.privateSubnetB = new ec2.CfnSubnet(this, 'PrivateSubnetB', {
      vpcId: this.vpc.ref,
      availabilityZone: 'eu-central-1b',
      cidrBlock: '10.0.144.0/20',
      mapPublicIpOnLaunch: false,
      tags: [{ key: 'Name', value: 'trees-vpc-subnet-private2-eu-central-1b' }],
    });

    const publicRouteTable = new ec2.CfnRouteTable(this, 'PublicRouteTable', {
      vpcId: this.vpc.ref,
      tags: [{ key: 'Name', value: 'trees-vpc-rtb-public' }],
    });

    const privateRouteTableA = new ec2.CfnRouteTable(this, 'PrivateRouteTableA', {
      vpcId: this.vpc.ref,
      tags: [{ key: 'Name', value: 'trees-vpc-rtb-private1-eu-central-1a' }],
    });

    const privateRouteTableB = new ec2.CfnRouteTable(this, 'PrivateRouteTableB', {
      vpcId: this.vpc.ref,
      tags: [{ key: 'Name', value: 'trees-vpc-rtb-private2-eu-central-1b' }],
    });

    new ec2.CfnRoute(this, 'PublicDefaultRoute', {
      routeTableId: publicRouteTable.ref,
      destinationCidrBlock: '0.0.0.0/0',
      gatewayId: igw.ref,
    });

    new ec2.CfnSubnetRouteTableAssociation(this, 'PublicSubnetAAssoc', {
      routeTableId: publicRouteTable.ref,
      subnetId: this.publicSubnetA.ref,
    });

    new ec2.CfnSubnetRouteTableAssociation(this, 'PublicSubnetBAssoc', {
      routeTableId: publicRouteTable.ref,
      subnetId: this.publicSubnetB.ref,
    });

    new ec2.CfnSubnetRouteTableAssociation(this, 'PrivateSubnetAAssoc', {
      routeTableId: privateRouteTableA.ref,
      subnetId: this.privateSubnetA.ref,
    });

    new ec2.CfnSubnetRouteTableAssociation(this, 'PrivateSubnetBAssoc', {
      routeTableId: privateRouteTableB.ref,
      subnetId: this.privateSubnetB.ref,
    });

    this.taskSg = new ec2.CfnSecurityGroup(this, 'TaskSg', {
      groupName: 'task-sg',
      groupDescription: 'Security group for trees-api Task',
      vpcId: this.vpc.ref,
      securityGroupIngress: [
        {
          ipProtocol: 'tcp',
          fromPort: 5000,
          toPort: 5000,
          cidrIp: '10.0.0.0/16',
          description: 'API Gateway VPC Link to ECS task',
        },
      ],
      securityGroupEgress: [
        {
          ipProtocol: '-1',
          fromPort: -1,
          toPort: -1,
          cidrIp: '0.0.0.0/0',
        },
      ],
      tags: [{ key: 'Name', value: 'trees-task-sg' }],
    });

    this.neptuneSg = new ec2.CfnSecurityGroup(this, 'NeptuneSg', {
      groupName: 'neptune-sg',
      groupDescription: 'security group for trees project neptune db',
      vpcId: this.vpc.ref,
      securityGroupEgress: [
        {
          ipProtocol: '-1',
          fromPort: -1,
          toPort: -1,
          cidrIp: '0.0.0.0/0',
        },
      ],
      tags: [{ key: 'Name', value: 'trees-neptune-sg' }],
    });

    new ec2.CfnSecurityGroupIngress(this, 'NeptuneIngressFromTaskSg', {
      groupId: this.neptuneSg.ref,
      ipProtocol: 'tcp',
      fromPort: 8182,
      toPort: 8182,
      sourceSecurityGroupId: this.taskSg.ref,
    });

    new ec2.CfnSecurityGroupEgress(this, 'TaskSgEgressToNeptune', {
      groupId: this.taskSg.ref,
      ipProtocol: 'tcp',
      fromPort: 8182,
      toPort: 8182,
      destinationSecurityGroupId: this.neptuneSg.ref,
    });
  }
}
