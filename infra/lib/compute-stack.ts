import * as cdk from 'aws-cdk-lib';
import * as apigatewayv2 from 'aws-cdk-lib/aws-apigatewayv2';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as neptune from 'aws-cdk-lib/aws-neptune';
import * as route53 from 'aws-cdk-lib/aws-route53';
import * as servicediscovery from 'aws-cdk-lib/aws-servicediscovery';

export interface TreesComputeStackProps extends cdk.StackProps {
  vpc: ec2.CfnVPC;
  publicSubnets: ec2.CfnSubnet[];
  privateSubnets: ec2.CfnSubnet[];
  taskSg: ec2.CfnSecurityGroup;
  clusterDev: neptune.CfnDBCluster;
  clusterProd: neptune.CfnDBCluster;
  hostedZone: route53.CfnHostedZone;
  ecrRepository: ecr.CfnRepository;
  certApiProdArn: string;
  certApiDevArn: string;
  webAclArn: string;
}

export class TreesComputeStack extends cdk.Stack {
  public readonly serviceProd: ecs.CfnService;
  public readonly serviceDev: ecs.CfnService;
  public readonly clusterDev: ecs.CfnCluster;
  public readonly clusterProd: ecs.CfnCluster;

  public constructor(scope: cdk.App, id: string, props: TreesComputeStackProps) {
    super(scope, id, props);

    const ecrRepository = props.ecrRepository;
    const treesLabZone = props.hostedZone;

    const internalNamespace = new servicediscovery.CfnPrivateDnsNamespace(this, 'InternalNamespace', {
      name: 'internal.trees-lab.com',
      vpc: props.vpc.ref,
      description: 'Private DNS namespace for trees backend services',
    });

    const cloudMapDev = new servicediscovery.CfnService(this, 'CloudMapServiceDev', {
      name: 'dev-api',
      namespaceId: internalNamespace.ref,
      dnsConfig: {
        namespaceId: internalNamespace.ref,
        routingPolicy: 'MULTIVALUE',
        dnsRecords: [
          { type: 'A', ttl: 60 },
          { type: 'SRV', ttl: 60 },
        ],
      },
    });

    const cloudMapProd = new servicediscovery.CfnService(this, 'CloudMapServiceProd', {
      name: 'prod-api',
      namespaceId: internalNamespace.ref,
      dnsConfig: {
        namespaceId: internalNamespace.ref,
        routingPolicy: 'MULTIVALUE',
        dnsRecords: [
          { type: 'A', ttl: 60 },
          { type: 'SRV', ttl: 60 },
        ],
      },
    });

    const taskExecutionRole = new iam.CfnRole(this, 'EcsTaskExecutionRole', {
      roleName: 'ecsTaskExecutionRole',
      managedPolicyArns: ['arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy'],
      assumeRolePolicyDocument: {
        Version: '2008-10-17',
        Statement: [{
          Effect: 'Allow',
          Principal: { Service: 'ecs-tasks.amazonaws.com' },
          Action: 'sts:AssumeRole',
        }],
      },
      policies: [{
        policyName: 'ecs-task-ssm-read',
        policyDocument: {
          Version: '2012-10-17',
          Statement: [
            {
              Effect: 'Allow',
              Action: ['ssm:GetParameter', 'ssm:GetParameters', 'ssm:GetParametersByPath'],
              Resource: [
                `arn:aws:ssm:${this.region}:${this.account}:parameter/trees/api/*`,
                `arn:aws:ssm:${this.region}:${this.account}:parameter/amplify/sandbox/sandbox/*`,
                `arn:aws:ssm:${this.region}:${this.account}:parameter/amplify/d32mgf3rp8n1oh/master/*`,
              ],
            },
            {
              // Needed to decrypt SecureString parameters. Constrained so the role
              // cannot decrypt arbitrary ciphertext elsewhere in the account.
              Effect: 'Allow',
              Action: 'kms:Decrypt',
              Resource: '*',
              Condition: {
                StringEquals: { 'kms:ViaService': `ssm.${this.region}.amazonaws.com` },
              },
            },
          ],
        },
      }],
    });

    const taskRole = new iam.CfnRole(this, 'EcsTaskRoleNeptuneConnect', {
      roleName: 'ecsTaskRoleNeptuneConnect',
      description: 'Allows ECS tasks to call AWS services on your behalf.',
      assumeRolePolicyDocument: {
        Version: '2012-10-17',
        Statement: [{
          Effect: 'Allow',
          Principal: { Service: 'ecs-tasks.amazonaws.com' },
          Action: 'sts:AssumeRole',
        }],
      },
      policies: [
        {
          policyName: 'AmplifyTableReadAccess',
          policyDocument: {
            Version: '2012-10-17',
            Statement: [{
              Effect: 'Allow',
              Action: ['dynamodb:BatchGetItem', 'dynamodb:GetItem'],
              Resource: `arn:aws:dynamodb:${this.region}:${this.account}:table/Tree-*`,
            }],
          },
        },
        {
          policyName: 'CognitoDeleteUsers',
          policyDocument: {
            Version: '2012-10-17',
            Statement: [{
              Sid: 'AllowAdminDeleteUser',
              Effect: 'Allow',
              Action: ['cognito-idp:AdminGetUser', 'cognito-idp:ListUsers', 'cognito-idp:AdminDeleteUser'],
              Resource: `arn:aws:cognito-idp:${this.region}:${this.account}:userpool/*`,
            }],
          },
        },
        {
          policyName: 'ECSExecSSMMessages',
          policyDocument: {
            Version: '2012-10-17',
            Statement: [{
              Effect: 'Allow',
              Action: [
                'ssmmessages:CreateControlChannel',
                'ssmmessages:CreateDataChannel',
                'ssmmessages:OpenControlChannel',
                'ssmmessages:OpenDataChannel',
              ],
              Resource: '*',
            }],
          },
        },
        {
          policyName: 'neptune-db-connect',
          policyDocument: {
            Version: '2012-10-17',
            Statement: [{
              Effect: 'Allow',
              Action: [
                'neptune-db:connect',
                'neptune-db:GetEngineStatus',
                'neptune-db:ReadDataViaQuery',
                'neptune-db:WriteDataViaQuery',
                'neptune-db:DeleteDataViaQuery',
              ],
              Resource: `arn:aws:neptune-db:${this.region}:${this.account}:cluster-*/*`,
            }],
          },
        },
        {
          policyName: 'trees-media-S3',
          policyDocument: {
            Version: '2012-10-17',
            Statement: [
              {
                Sid: 'S3PutObject',
                Effect: 'Allow',
                Action: ['s3:PutObject', 's3:GetObject', 's3:DeleteObject'],
                Resource: 'arn:aws:s3:::amplify-*/*',
              },
              {
                Sid: 'S3ListBucketForMedia',
                Effect: 'Allow',
                Action: 's3:ListBucket',
                Resource: 'arn:aws:s3:::amplify-*',
                Condition: { StringLike: { 's3:prefix': ['trees/*'] } },
              },
            ],
          },
        },
        {
          policyName: 'TreesApiAclAccess',
          policyDocument: {
            Version: '2012-10-17',
            Statement: [
              {
                Sid: 'DynamoDBCustomResourcesTables',
                Effect: 'Allow',
                Action: [
                  'dynamodb:GetItem', 'dynamodb:PutItem', 'dynamodb:UpdateItem', 'dynamodb:DeleteItem',
                  'dynamodb:BatchGetItem', 'dynamodb:BatchWriteItem', 'dynamodb:Query', 'dynamodb:Scan',
                  'dynamodb:ConditionCheckItem',
                ],
                Resource: [
                  `arn:aws:dynamodb:${this.region}:${this.account}:table/custom-resources-*`,
                  `arn:aws:dynamodb:${this.region}:${this.account}:table/amplify-*`,
                ],
              },
              {
                Sid: 'DynamoDBTreeTable',
                Effect: 'Allow',
                Action: ['dynamodb:GetItem', 'dynamodb:BatchGetItem', 'dynamodb:Query'],
                Resource: `arn:aws:dynamodb:${this.region}:${this.account}:table/Tree-*`,
              },
              {
                Sid: 'CognitoListUsers',
                Effect: 'Allow',
                Action: 'cognito-idp:ListUsers',
                Resource: `arn:aws:cognito-idp:${this.region}:${this.account}:userpool/*`,
              },
              {
                Sid: 'CognitoAdminDeleteUser',
                Effect: 'Allow',
                Action: 'cognito-idp:AdminDeleteUser',
                Resource: `arn:aws:cognito-idp:${this.region}:${this.account}:userpool/*`,
              },
            ],
          },
        },
      ],
    });

    this.clusterDev = new ecs.CfnCluster(this, 'EcsClusterDev', {
      clusterName: 'trees-api-dev',
      clusterSettings: [{ name: 'containerInsights', value: 'disabled' }],
      tags: [{ key: 'Name', value: 'trees-api-dev' }, { key: 'Env', value: 'dev' }],
    });

    this.clusterProd = new ecs.CfnCluster(this, 'EcsClusterProd', {
      clusterName: 'trees-api-prod',
      clusterSettings: [{ name: 'containerInsights', value: 'disabled' }],
      tags: [{ key: 'Name', value: 'trees-api-prod' }, { key: 'Env', value: 'prod' }],
    });

    const logGroupDev = new logs.CfnLogGroup(this, 'EcsLogGroupDev', {
      logGroupName: '/ecs/trees-api-dev',
      retentionInDays: 7,
    });

    const logGroupProd = new logs.CfnLogGroup(this, 'EcsLogGroupProd', {
      logGroupName: '/ecs/trees-api-prod',
      retentionInDays: 14,
    });

    // NOTE: everything here lands in the task definition in plaintext, readable by
    // anyone with ecs:DescribeTaskDefinition. Secrets belong in the `secrets:`
    // block below, which resolves from SSM/Secrets Manager at task start.
    const sharedContainerEnv = (env: 'development' | 'production') => [
      { name: 'AWS_REGION', value: this.region },
      { name: 'FLASK_ENV', value: env },
      { name: 'ROLE_CACHE_TTL_SECONDS', value: '30' },
      { name: 'GREMLIN_PORT', value: '8182' },
      { name: 'FLASK_DEBUG', value: env === 'development' ? 'True' : 'False' },
      { name: 'GREMLIN_SSL', value: 'true' },
      { name: 'LOG_LEVEL', value: env === 'development' ? 'INFO' : 'WARNING' },
      { name: 'GREMLIN_IAM_AUTH', value: 'true' },
      { name: 'CORS_ORIGINS', value: env === 'development'
        ? 'http://localhost:5173,http://localhost:5174,https://master.d32mgf3rp8n1oh.amplifyapp.com'
        : 'http://localhost:5173,http://localhost:5174,https://master.d32mgf3rp8n1oh.amplifyapp.com,https://trees-lab.com,https://www.trees-lab.com' },
      { name: 'LOCK_TTL_SECONDS', value: '300' },
      { name: 'ENFORCE_LIMITS', value: 'true' },
    ];

    const taskDefDev = new ecs.CfnTaskDefinition(this, 'EcsTaskDefDev', {
      family: 'trees-api-task-dev',
      requiresCompatibilities: ['FARGATE'],
      networkMode: 'awsvpc',
      cpu: '256',
      memory: '1024',
      runtimePlatform: { operatingSystemFamily: 'LINUX', cpuArchitecture: 'X86_64' },
      taskRoleArn: taskRole.attrArn,
      executionRoleArn: taskExecutionRole.attrArn,
      containerDefinitions: [{
        name: 'trees-api',
        image: `${ecrRepository.attrRepositoryUri}:latest`,
        essential: true,
        cpu: 0,
        portMappings: [{ name: 'trees-api-5000-tcp', containerPort: 5000, hostPort: 5000, protocol: 'tcp', appProtocol: 'http' }],
        command: ['gunicorn', '--bind', '0.0.0.0:5000', 'app:app'],
        logConfiguration: {
          logDriver: 'awslogs',
          options: {
            'awslogs-group': logGroupDev.ref,
            'awslogs-region': this.region,
            'awslogs-stream-prefix': 'ecs',
            'awslogs-create-group': 'true',
          },
        },
        environment: sharedContainerEnv('development'),
        secrets: [
          { name: 'ACL_TABLE_NAME', valueFrom: '/amplify/sandbox/sandbox/TreeAclTableName' },
          { name: 'AMPLIFY_USER_POOL_ID', valueFrom: '/amplify/sandbox/sandbox/UserPoolId' },
          { name: 'AMPLIFY_USER_POOL_CLIENT_ID', valueFrom: '/amplify/sandbox/sandbox/UserPoolClientId' },
          { name: 'GREMLIN_ENDPOINT', valueFrom: '/trees/api/GREMLIN_ENDPOINT_DEV' },
          { name: 'LOCK_TABLE_NAME', valueFrom: '/amplify/sandbox/sandbox/TreeEditorLocksTableName' },
          { name: 'S3_MEDIA_BUCKET', valueFrom: '/amplify/sandbox/sandbox/MediaBucketName' },
          { name: 'TREE_TABLE_NAME', valueFrom: '/amplify/sandbox/sandbox/TreeTableName' },
        ],
      }],
    });

    const taskDefProd = new ecs.CfnTaskDefinition(this, 'EcsTaskDefProd', {
      family: 'trees-api-task-prod',
      requiresCompatibilities: ['FARGATE'],
      networkMode: 'awsvpc',
      cpu: '256',
      memory: '1024',
      runtimePlatform: { operatingSystemFamily: 'LINUX', cpuArchitecture: 'X86_64' },
      taskRoleArn: taskRole.attrArn,
      executionRoleArn: taskExecutionRole.attrArn,
      containerDefinitions: [{
        name: 'trees-api',
        image: `${ecrRepository.attrRepositoryUri}:latest`,
        essential: true,
        cpu: 0,
        portMappings: [{ name: 'trees-api-5000-tcp', containerPort: 5000, hostPort: 5000, protocol: 'tcp', appProtocol: 'http' }],
        command: ['gunicorn', '--bind', '0.0.0.0:5000', 'app:app'],
        logConfiguration: {
          logDriver: 'awslogs',
          options: {
            'awslogs-group': logGroupProd.ref,
            'awslogs-region': this.region,
            'awslogs-stream-prefix': 'ecs',
            'awslogs-create-group': 'true',
          },
        },
        environment: sharedContainerEnv('production'),
        secrets: [
          { name: 'ACL_TABLE_NAME', valueFrom: '/amplify/d32mgf3rp8n1oh/master/TreeAclTableName' },
          { name: 'AMPLIFY_USER_POOL_ID', valueFrom: '/amplify/d32mgf3rp8n1oh/master/UserPoolId' },
          { name: 'AMPLIFY_USER_POOL_CLIENT_ID', valueFrom: '/amplify/d32mgf3rp8n1oh/master/UserPoolClientId' },
          { name: 'GREMLIN_ENDPOINT', valueFrom: '/trees/api/GREMLIN_ENDPOINT_PROD' },
          { name: 'LOCK_TABLE_NAME', valueFrom: '/amplify/d32mgf3rp8n1oh/master/TreeEditorLocksTableName' },
          { name: 'S3_MEDIA_BUCKET', valueFrom: '/amplify/d32mgf3rp8n1oh/master/MediaBucketName' },
          { name: 'TREE_TABLE_NAME', valueFrom: '/amplify/d32mgf3rp8n1oh/master/TreeTableName' },
        ],
      }],
    });

    const sharedServiceProps: Partial<ecs.CfnServiceProps> = {
      launchType: 'FARGATE',
      platformVersion: 'LATEST',
      schedulingStrategy: 'REPLICA',
      availabilityZoneRebalancing: 'ENABLED',
      deploymentController: { type: 'ECS' },
      deploymentConfiguration: {
        strategy: 'ROLLING',
        bakeTimeInMinutes: 0,
        maximumPercent: 200,
        minimumHealthyPercent: 0,
        deploymentCircuitBreaker: { enable: false, rollback: false },
      },
    };

    this.serviceDev = new ecs.CfnService(this, 'EcsServiceDev', {
      ...sharedServiceProps,
      serviceName: 'trees-api-svc-dev',
      cluster: this.clusterDev.ref,
      taskDefinition: taskDefDev.ref,
      desiredCount: 0,
      networkConfiguration: {
        awsvpcConfiguration: {
          subnets: props.publicSubnets.map((s) => s.ref),
          securityGroups: [props.taskSg.ref],
          assignPublicIp: 'ENABLED',
        },
      },
      serviceRegistries: [{
        registryArn: cloudMapDev.attrArn,
        containerName: 'trees-api',
        containerPort: 5000,
      }],
    });

    this.serviceProd = new ecs.CfnService(this, 'EcsServiceProd', {
      ...sharedServiceProps,
      serviceName: 'trees-api-svc-prod',
      cluster: this.clusterProd.ref,
      taskDefinition: taskDefProd.ref,
      desiredCount: 1,
      networkConfiguration: {
        awsvpcConfiguration: {
          subnets: props.publicSubnets.map((s) => s.ref),
          securityGroups: [props.taskSg.ref],
          assignPublicIp: 'ENABLED',
        },
      },
      serviceRegistries: [{
        registryArn: cloudMapProd.attrArn,
        containerName: 'trees-api',
        containerPort: 5000,
      }],
    });

    const vpcLink = new apigatewayv2.CfnVpcLink(this, 'TreesVpcLink', {
      name: 'trees-vpc-link',
      subnetIds: props.privateSubnets.map((s) => s.ref),
      securityGroupIds: [props.taskSg.ref],
    });

    const httpApiDev = new apigatewayv2.CfnApi(this, 'HttpApiDev', {
      name: 'trees-api-dev',
      protocolType: 'HTTP',
      routeSelectionExpression: '$request.method $request.path',
      disableExecuteApiEndpoint: false,
    });

    const httpApiProd = new apigatewayv2.CfnApi(this, 'HttpApiProd', {
      name: 'trees-api-prod',
      protocolType: 'HTTP',
      routeSelectionExpression: '$request.method $request.path',
      disableExecuteApiEndpoint: false,
    });

    const integrationDev = new apigatewayv2.CfnIntegration(this, 'HttpApiDevIntegration', {
      apiId: httpApiDev.ref,
      integrationType: 'HTTP_PROXY',
      integrationMethod: 'ANY',
      connectionType: 'VPC_LINK',
      connectionId: vpcLink.ref,
      integrationUri: cloudMapDev.attrArn,
      payloadFormatVersion: '1.0',
      timeoutInMillis: 30000,
    });

    const integrationProd = new apigatewayv2.CfnIntegration(this, 'HttpApiProdIntegration', {
      apiId: httpApiProd.ref,
      integrationType: 'HTTP_PROXY',
      integrationMethod: 'ANY',
      connectionType: 'VPC_LINK',
      connectionId: vpcLink.ref,
      integrationUri: cloudMapProd.attrArn,
      payloadFormatVersion: '1.0',
      timeoutInMillis: 30000,
    });

    const routeDev = new apigatewayv2.CfnRoute(this, 'HttpApiDevRoute', {
      apiId: httpApiDev.ref,
      routeKey: 'ANY /{proxy+}',
      target: cdk.Fn.join('/', ['integrations', integrationDev.ref]),
      authorizationType: 'NONE',
      apiKeyRequired: false,
    });

    const routeProd = new apigatewayv2.CfnRoute(this, 'HttpApiProdRoute', {
      apiId: httpApiProd.ref,
      routeKey: 'ANY /{proxy+}',
      target: cdk.Fn.join('/', ['integrations', integrationProd.ref]),
      authorizationType: 'NONE',
      apiKeyRequired: false,
    });

    const deploymentDev = new apigatewayv2.CfnDeployment(this, 'HttpApiDevDeployment', {
      apiId: httpApiDev.ref,
      description: 'Initial deployment',
    });
    deploymentDev.addDependency(routeDev);
    deploymentDev.addDependency(integrationDev);

    new apigatewayv2.CfnStage(this, 'HttpApiDevStage', {
      apiId: httpApiDev.ref,
      stageName: '$default',
      autoDeploy: true,
      deploymentId: deploymentDev.ref,
    });

    const deploymentProd = new apigatewayv2.CfnDeployment(this, 'HttpApiProdDeployment', {
      apiId: httpApiProd.ref,
      description: 'Initial deployment',
    });
    deploymentProd.addDependency(routeProd);
    deploymentProd.addDependency(integrationProd);

    new apigatewayv2.CfnStage(this, 'HttpApiProdStage', {
      apiId: httpApiProd.ref,
      stageName: '$default',
      autoDeploy: true,
      deploymentId: deploymentProd.ref,
    });

    const responseHeadersPolicyId = '5cc3b908-e619-4b99-88e5-2cf7f45965bd';
    const originRequestPolicyId = 'b689b0a8-53d0-40ab-baf2-68738e2966ac';
    const cachePolicyId = '4135ea2d-6df8-44a3-9df3-4b5a84be39ad';
    const cloudFrontHostedZoneId = 'Z2FDTNDATAQYW2';

    const cloudFrontDev = new cloudfront.CfnDistribution(this, 'CloudFrontDev', {
      distributionConfig: {
        comment: 'trees-api dev CloudFront',
        enabled: true,
        ipv6Enabled: true,
        httpVersion: 'http2',
        priceClass: 'PriceClass_All',
        aliases: ['dev-api.trees-lab.com'],
        viewerCertificate: {
          acmCertificateArn: props.certApiDevArn,
          minimumProtocolVersion: 'TLSv1.2_2021',
          sslSupportMethod: 'sni-only',
        },
        origins: [{
          id: 'trees-api-dev-httpapi',
          domainName: cdk.Fn.join('', [httpApiDev.ref, '.execute-api.', this.region, '.amazonaws.com']),
          customOriginConfig: {
            originProtocolPolicy: 'https-only',
            httpPort: 80,
            httpsPort: 443,
            originSslProtocols: ['TLSv1.2'],
            originKeepaliveTimeout: 5,
            originReadTimeout: 30,
          },
        }],
        defaultCacheBehavior: {
          targetOriginId: 'trees-api-dev-httpapi',
          viewerProtocolPolicy: 'redirect-to-https',
          allowedMethods: ['HEAD', 'DELETE', 'POST', 'GET', 'OPTIONS', 'PUT', 'PATCH'],
          compress: true,
          cachePolicyId: cachePolicyId,
          originRequestPolicyId: originRequestPolicyId,
          responseHeadersPolicyId: responseHeadersPolicyId,
        },
        restrictions: { geoRestriction: { restrictionType: 'none' } },
      },
    });

    const cloudFrontProd = new cloudfront.CfnDistribution(this, 'CloudFrontProd', {
      tags: [{ key: 'Name', value: 'trees-api-cloudfront' }],
      distributionConfig: {
        enabled: true,
        ipv6Enabled: true,
        httpVersion: 'http2',
        priceClass: 'PriceClass_All',
        aliases: ['api.trees-lab.com'],
        webAclId: props.webAclArn,
        viewerCertificate: {
          acmCertificateArn: props.certApiProdArn,
          minimumProtocolVersion: 'TLSv1.2_2021',
          sslSupportMethod: 'sni-only',
        },
        origins: [{
          id: 'trees-api-prod-httpapi',
          domainName: cdk.Fn.join('', [httpApiProd.ref, '.execute-api.', this.region, '.amazonaws.com']),
          customOriginConfig: {
            originProtocolPolicy: 'https-only',
            httpPort: 80,
            httpsPort: 443,
            originSslProtocols: ['TLSv1.2'],
            originKeepaliveTimeout: 5,
            originReadTimeout: 30,
          },
        }],
        defaultCacheBehavior: {
          targetOriginId: 'trees-api-prod-httpapi',
          viewerProtocolPolicy: 'redirect-to-https',
          allowedMethods: ['HEAD', 'DELETE', 'POST', 'GET', 'OPTIONS', 'PUT', 'PATCH'],
          compress: true,
          cachePolicyId: cachePolicyId,
          originRequestPolicyId: originRequestPolicyId,
          responseHeadersPolicyId: responseHeadersPolicyId,
        },
        restrictions: { geoRestriction: { restrictionType: 'none' } },
      },
    });

    new route53.CfnRecordSet(this, 'RecordSetApiProd', {
      hostedZoneId: treesLabZone.ref,
      name: 'api.trees-lab.com.',
      type: 'A',
      aliasTarget: {
        hostedZoneId: cloudFrontHostedZoneId,
        dnsName: cloudFrontProd.attrDomainName,
        evaluateTargetHealth: false,
      },
    });

    new route53.CfnRecordSet(this, 'RecordSetApiDev', {
      hostedZoneId: treesLabZone.ref,
      name: 'dev-api.trees-lab.com.',
      type: 'A',
      aliasTarget: {
        hostedZoneId: cloudFrontHostedZoneId,
        dnsName: cloudFrontDev.attrDomainName,
        evaluateTargetHealth: false,
      },
    });
  }
}
