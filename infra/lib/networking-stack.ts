import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';

export interface TreesNetworkingStackProps extends cdk.StackProps {
}

export class TreesNetworkingStack extends cdk.Stack {
  public constructor(scope: cdk.App, id: string, props: TreesNetworkingStackProps = {}) {
    super(scope, id, props);

    // Resources
    const neptuneSg = new ec2.CfnSecurityGroup(this, 'NeptuneSg', {
      groupDescription: 'security group for trees project neptune db',
      groupName: 'neptune-sg',
      vpcId: 'vpc-080e46790f33279a6',
      securityGroupIngress: [
        {
          ipProtocol: 'tcp',
          fromPort: 8182,
          sourceSecurityGroupId: 'sg-015635a1eae8dcd12',
          toPort: 8182,
          sourceSecurityGroupOwnerId: 'AWS_ACCOUNT_ID',
        },
      ],
      securityGroupEgress: [
        {
          cidrIp: '0.0.0.0/0',
          ipProtocol: '-1',
          fromPort: -1,
          toPort: -1,
        },
      ],
      tags: [
        {
          value: 'trees-neptune-sg',
          key: 'Name',
        },
      ],
    });
    neptuneSg.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const privateRouteTableA = new ec2.CfnRouteTable(this, 'PrivateRouteTableA', {
      vpcId: 'vpc-080e46790f33279a6',
      tags: [
        {
          value: 'trees-vpc-rtb-private1-eu-central-1a',
          key: 'Name',
        },
      ],
    });
    privateRouteTableA.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const privateRouteTableB = new ec2.CfnRouteTable(this, 'PrivateRouteTableB', {
      vpcId: 'vpc-080e46790f33279a6',
      tags: [
        {
          value: 'trees-vpc-rtb-private2-eu-central-1b',
          key: 'Name',
        },
      ],
    });
    privateRouteTableB.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const privateSubnetA = new ec2.CfnSubnet(this, 'PrivateSubnetA', {
      mapPublicIpOnLaunch: false,
      enableDns64: false,
      vpcId: 'vpc-080e46790f33279a6',
      availabilityZoneId: 'euc1-az2',
      privateDnsNameOptionsOnLaunch: {
        EnableResourceNameDnsARecord: false,
        HostnameType: 'ip-name',
        EnableResourceNameDnsAAAARecord: false,
      },
      availabilityZone: 'eu-central-1a',
      cidrBlock: '10.0.128.0/20',
      ipv6Native: false,
      tags: [
        {
          value: 'trees-vpc-subnet-private1-eu-central-1a',
          key: 'Name',
        },
      ],
    });
    privateSubnetA.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const privateSubnetAAssoc = new ec2.CfnSubnetRouteTableAssociation(this, 'PrivateSubnetAAssoc', {
      routeTableId: 'rtb-065ea90d8e970649c',
      subnetId: 'subnet-0b0add3a8dbedf82e',
    });
    privateSubnetAAssoc.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const privateSubnetB = new ec2.CfnSubnet(this, 'PrivateSubnetB', {
      mapPublicIpOnLaunch: false,
      enableDns64: false,
      vpcId: 'vpc-080e46790f33279a6',
      availabilityZoneId: 'euc1-az3',
      privateDnsNameOptionsOnLaunch: {
        EnableResourceNameDnsARecord: false,
        HostnameType: 'ip-name',
        EnableResourceNameDnsAAAARecord: false,
      },
      availabilityZone: 'eu-central-1b',
      cidrBlock: '10.0.144.0/20',
      ipv6Native: false,
      tags: [
        {
          value: 'trees-vpc-subnet-private2-eu-central-1b',
          key: 'Name',
        },
      ],
    });
    privateSubnetB.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const privateSubnetBAssoc = new ec2.CfnSubnetRouteTableAssociation(this, 'PrivateSubnetBAssoc', {
      routeTableId: 'rtb-075c3837928f1ab09',
      subnetId: 'subnet-01e3a267b85c87b0c',
    });
    privateSubnetBAssoc.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const publicDefaultRoute = new ec2.CfnRoute(this, 'PublicDefaultRoute', {
      routeTableId: 'rtb-06c2e161bdc980d47',
      destinationCidrBlock: '0.0.0.0/0',
      gatewayId: 'igw-0a9fea932f581ac84',
    });
    publicDefaultRoute.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const publicRouteTable = new ec2.CfnRouteTable(this, 'PublicRouteTable', {
      vpcId: 'vpc-080e46790f33279a6',
      tags: [
        {
          value: 'trees-vpc-rtb-public',
          key: 'Name',
        },
      ],
    });
    publicRouteTable.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const publicSubnetA = new ec2.CfnSubnet(this, 'PublicSubnetA', {
      mapPublicIpOnLaunch: false,
      enableDns64: false,
      vpcId: 'vpc-080e46790f33279a6',
      availabilityZoneId: 'euc1-az2',
      privateDnsNameOptionsOnLaunch: {
        EnableResourceNameDnsARecord: false,
        HostnameType: 'ip-name',
        EnableResourceNameDnsAAAARecord: false,
      },
      availabilityZone: 'eu-central-1a',
      cidrBlock: '10.0.0.0/20',
      ipv6Native: false,
      tags: [
        {
          value: 'trees-vpc-subnet-public1-eu-central-1a',
          key: 'Name',
        },
      ],
    });
    publicSubnetA.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const publicSubnetAAssoc = new ec2.CfnSubnetRouteTableAssociation(this, 'PublicSubnetAAssoc', {
      routeTableId: 'rtb-06c2e161bdc980d47',
      subnetId: 'subnet-05d121fe8f18d0bcc',
    });
    publicSubnetAAssoc.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const publicSubnetB = new ec2.CfnSubnet(this, 'PublicSubnetB', {
      mapPublicIpOnLaunch: false,
      enableDns64: false,
      vpcId: 'vpc-080e46790f33279a6',
      availabilityZoneId: 'euc1-az3',
      privateDnsNameOptionsOnLaunch: {
        EnableResourceNameDnsARecord: false,
        HostnameType: 'ip-name',
        EnableResourceNameDnsAAAARecord: false,
      },
      availabilityZone: 'eu-central-1b',
      cidrBlock: '10.0.16.0/20',
      ipv6Native: false,
      tags: [
        {
          value: 'trees-vpc-subnet-public2-eu-central-1b',
          key: 'Name',
        },
      ],
    });
    publicSubnetB.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const publicSubnetBAssoc = new ec2.CfnSubnetRouteTableAssociation(this, 'PublicSubnetBAssoc', {
      routeTableId: 'rtb-06c2e161bdc980d47',
      subnetId: 'subnet-01bd80a2fb4ed4cc3',
    });
    publicSubnetBAssoc.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const taskSg = new ec2.CfnSecurityGroup(this, 'TaskSg', {
      groupDescription: 'Security group for trees-api Task',
      groupName: 'task-sg',
      vpcId: 'vpc-080e46790f33279a6',
      securityGroupIngress: [
        {
          cidrIp: '10.0.0.0/16',
          ipProtocol: 'tcp',
          description: 'API Gateway VPC Link to ECS task',
          fromPort: 5000,
          toPort: 5000,
        },
      ],
      securityGroupEgress: [
        {
          cidrIp: '0.0.0.0/0',
          ipProtocol: '-1',
          fromPort: -1,
          toPort: -1,
        },
        {
          ipProtocol: 'tcp',
          destinationSecurityGroupId: 'sg-0229c88c446cba89c',
          fromPort: 8182,
          toPort: 8182,
        },
      ],
      tags: [
        {
          value: 'trees-task-sg',
          key: 'Name',
        },
      ],
    });
    taskSg.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const treesIgw = new ec2.CfnInternetGateway(this, 'TreesIgw', {
      tags: [
        {
          value: 'trees-vpc-igw',
          key: 'Name',
        },
      ],
    });
    treesIgw.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const treesIgwAttachment = new ec2.CfnVPCGatewayAttachment(this, 'TreesIgwAttachment', {
      internetGatewayId: 'igw-0a9fea932f581ac84',
      vpcId: 'vpc-080e46790f33279a6',
    });
    treesIgwAttachment.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const treesVpc = new ec2.CfnVPC(this, 'TreesVpc', {
      cidrBlock: '10.0.0.0/16',
      enableDnsSupport: true,
      instanceTenancy: 'default',
      enableDnsHostnames: true,
      tags: [
        {
          value: 'trees-vpc-vpc',
          key: 'Name',
        },
      ],
    });
    treesVpc.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;
  }
}
