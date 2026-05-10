import * as cdk from 'aws-cdk-lib';
import * as apigatewayv2 from 'aws-cdk-lib/aws-apigatewayv2';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as route53 from 'aws-cdk-lib/aws-route53';

export interface TreesComputeStackProps extends cdk.StackProps {
}

export class TreesComputeStack extends cdk.Stack {
  public constructor(scope: cdk.App, id: string, props: TreesComputeStackProps = {}) {
    super(scope, id, props);

    // Resources
    const cloudFrontDev = new cloudfront.CfnDistribution(this, 'CloudFrontDev', {
      distributionConfig: {
        comment: 'trees-api dev CloudFront',
        defaultRootObject: '',
        origins: [
          {
            domainName: 'xhstoutar6.execute-api.eu-central-1.amazonaws.com',
            id: 'trees-api-dev-httpapi',
            customOriginConfig: {
              originKeepaliveTimeout: 5,
              originReadTimeout: 30,
              originSslProtocols: [
                'TLSv1.2',
              ],
              httpsPort: 443,
              httpPort: 80,
              originProtocolPolicy: 'https-only',
            },
          },
        ],
        viewerCertificate: {
          minimumProtocolVersion: 'TLSv1.2_2021',
          sslSupportMethod: 'sni-only',
          acmCertificateArn: 'arn:aws:acm:us-east-1:AWS_ACCOUNT_ID:certificate/e07cbf90-e3d6-4e7d-b79b-23b6374aab8b',
        },
        priceClass: 'PriceClass_All',
        defaultCacheBehavior: {
          compress: true,
          targetOriginId: 'trees-api-dev-httpapi',
          viewerProtocolPolicy: 'redirect-to-https',
          responseHeadersPolicyId: '5cc3b908-e619-4b99-88e5-2cf7f45965bd',
          allowedMethods: [
            'HEAD',
            'DELETE',
            'POST',
            'GET',
            'OPTIONS',
            'PUT',
            'PATCH',
          ],
          originRequestPolicyId: 'b689b0a8-53d0-40ab-baf2-68738e2966ac',
          cachePolicyId: '4135ea2d-6df8-44a3-9df3-4b5a84be39ad',
        },
        staging: false,
        enabled: true,
        aliases: [
          'dev-api.trees-lab.com',
        ],
        ipv6Enabled: true,
        webAclId: '',
        httpVersion: 'http2',
        restrictions: {
          geoRestriction: {
            restrictionType: 'none',
          },
        },
      },
    });
    cloudFrontDev.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const cloudFrontProd = new cloudfront.CfnDistribution(this, 'CloudFrontProd', {
      distributionConfig: {
        comment: '',
        defaultRootObject: '',
        origins: [
          {
            domainName: '68e9c5mnsa.execute-api.eu-central-1.amazonaws.com',
            id: 'trees-api-prod-httpapi',
            customOriginConfig: {
              originKeepaliveTimeout: 5,
              originReadTimeout: 30,
              originSslProtocols: [
                'TLSv1.2',
              ],
              httpsPort: 443,
              httpPort: 80,
              originProtocolPolicy: 'https-only',
            },
          },
        ],
        viewerCertificate: {
          minimumProtocolVersion: 'TLSv1.2_2021',
          sslSupportMethod: 'sni-only',
          acmCertificateArn: 'arn:aws:acm:us-east-1:AWS_ACCOUNT_ID:certificate/ce3af368-4996-4ecc-984e-79f692ae7576',
        },
        priceClass: 'PriceClass_All',
        defaultCacheBehavior: {
          compress: true,
          targetOriginId: 'trees-api-prod-httpapi',
          viewerProtocolPolicy: 'redirect-to-https',
          responseHeadersPolicyId: '5cc3b908-e619-4b99-88e5-2cf7f45965bd',
          allowedMethods: [
            'HEAD',
            'DELETE',
            'POST',
            'GET',
            'OPTIONS',
            'PUT',
            'PATCH',
          ],
          originRequestPolicyId: 'b689b0a8-53d0-40ab-baf2-68738e2966ac',
          cachePolicyId: '4135ea2d-6df8-44a3-9df3-4b5a84be39ad',
        },
        staging: false,
        enabled: true,
        aliases: [
          'api.trees-lab.com',
        ],
        ipv6Enabled: true,
        webAclId: 'arn:aws:wafv2:us-east-1:AWS_ACCOUNT_ID:global/webacl/CreatedByCloudFront-0ac1ed8d/8ebafa67-15c3-4a10-967e-c67c83e6826c',
        httpVersion: 'http2',
        restrictions: {
          geoRestriction: {
            restrictionType: 'none',
          },
        },
      },
      tags: [
        {
          value: 'trees-api-cloudfront',
          key: 'Name',
        },
      ],
    });
    cloudFrontProd.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const ecsClusterDev = new ecs.CfnCluster(this, 'EcsClusterDev', {
      clusterName: 'trees-api-dev',
      clusterSettings: [
        {
          value: 'disabled',
          name: 'containerInsights',
        },
      ],
      tags: [
        {
          value: 'dev',
          key: 'Env',
        },
        {
          value: 'trees-api-dev',
          key: 'Name',
        },
      ],
    });
    ecsClusterDev.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const ecsClusterProd = new ecs.CfnCluster(this, 'EcsClusterProd', {
      clusterName: 'trees-api-prod',
      clusterSettings: [
        {
          value: 'disabled',
          name: 'containerInsights',
        },
      ],
      tags: [
        {
          value: 'prod',
          key: 'Env',
        },
        {
          value: 'trees-api-prod',
          key: 'Name',
        },
      ],
    });
    ecsClusterProd.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const ecsLogGroupDev = new logs.CfnLogGroup(this, 'EcsLogGroupDev', {
      retentionInDays: 7,
      logGroupClass: 'STANDARD',
      logGroupName: '/ecs/trees-api-dev',
    });
    ecsLogGroupDev.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const ecsLogGroupProd = new logs.CfnLogGroup(this, 'EcsLogGroupProd', {
      retentionInDays: 14,
      logGroupClass: 'STANDARD',
      logGroupName: '/ecs/trees-api-prod',
    });
    ecsLogGroupProd.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const ecsServiceDev = new ecs.CfnService(this, 'EcsServiceDev', {
      platformVersion: 'LATEST',
      healthCheckGracePeriodSeconds: 0,
      enableEcsManagedTags: false,
      enableExecuteCommand: false,
      cluster: ecsClusterDev.ref,
      desiredCount: 0,
      deploymentController: {
        type: 'ECS',
      },
      serviceRegistries: [
        {
          containerPort: 5000,
          registryArn: 'arn:aws:servicediscovery:eu-central-1:AWS_ACCOUNT_ID:service/srv-apsql6xdfn7a3jtp',
          containerName: 'trees-api',
        },
      ],
      launchType: 'FARGATE',
      availabilityZoneRebalancing: 'ENABLED',
      role: 'arn:aws:iam::AWS_ACCOUNT_ID:role/aws-service-role/ecs.amazonaws.com/AWSServiceRoleForECS',
      schedulingStrategy: 'REPLICA',
      taskDefinition: cdk.Lazy.string({ produce: () => ecsTaskDefDev.ref }),
      serviceName: 'trees-api-svc-dev',
      networkConfiguration: {
        awsvpcConfiguration: {
          securityGroups: [
            'sg-015635a1eae8dcd12',
          ],
          subnets: [
            'subnet-01bd80a2fb4ed4cc3',
            'subnet-05d121fe8f18d0bcc',
          ],
          assignPublicIp: 'ENABLED',
        },
      },
      deploymentConfiguration: {
        strategy: 'ROLLING',
        bakeTimeInMinutes: 0,
        deploymentCircuitBreaker: {
          enable: false,
          rollback: false,
        },
        maximumPercent: 200,
        minimumHealthyPercent: 0,
      },
    });
    ecsServiceDev.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const ecsServiceProd = new ecs.CfnService(this, 'EcsServiceProd', {
      platformVersion: 'LATEST',
      healthCheckGracePeriodSeconds: 0,
      enableEcsManagedTags: false,
      enableExecuteCommand: false,
      cluster: ecsClusterProd.ref,
      desiredCount: 1,
      deploymentController: {
        type: 'ECS',
      },
      serviceRegistries: [
        {
          containerPort: 5000,
          registryArn: 'arn:aws:servicediscovery:eu-central-1:AWS_ACCOUNT_ID:service/srv-we3dm4um3mwub62m',
          containerName: 'trees-api',
        },
      ],
      launchType: 'FARGATE',
      availabilityZoneRebalancing: 'ENABLED',
      role: 'arn:aws:iam::AWS_ACCOUNT_ID:role/aws-service-role/ecs.amazonaws.com/AWSServiceRoleForECS',
      schedulingStrategy: 'REPLICA',
      taskDefinition: cdk.Lazy.string({ produce: () => ecsTaskDefProd.ref }),
      serviceName: 'trees-api-svc-prod',
      networkConfiguration: {
        awsvpcConfiguration: {
          securityGroups: [
            'sg-015635a1eae8dcd12',
          ],
          subnets: [
            'subnet-01bd80a2fb4ed4cc3',
            'subnet-05d121fe8f18d0bcc',
          ],
          assignPublicIp: 'ENABLED',
        },
      },
      deploymentConfiguration: {
        strategy: 'ROLLING',
        bakeTimeInMinutes: 0,
        deploymentCircuitBreaker: {
          enable: false,
          rollback: false,
        },
        maximumPercent: 200,
        minimumHealthyPercent: 0,
      },
    });
    ecsServiceProd.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const ecsTaskDefDev = new ecs.CfnTaskDefinition(this, 'EcsTaskDefDev', {
      taskRoleArn: cdk.Lazy.string({ produce: () => ecsTaskRoleNeptuneConnect.attrArn }),
      memory: '1024',
      cpu: '256',
      requiresCompatibilities: [
        'FARGATE',
      ],
      networkMode: 'awsvpc',
      executionRoleArn: cdk.Lazy.string({ produce: () => ecsTaskExecutionRole.attrArn }),
      runtimePlatform: {
        operatingSystemFamily: 'LINUX',
        cpuArchitecture: 'X86_64',
      },
      containerDefinitions: [
        {
          secrets: [
            {
              valueFrom: '/amplify/sandbox/sandbox/TreeAclTableName',
              name: 'ACL_TABLE_NAME',
            },
            {
              valueFrom: '/amplify/sandbox/sandbox/UserPoolId',
              name: 'AMPLIFY_USER_POOL_ID',
            },
            {
              valueFrom: '/trees/api/GREMLIN_ENDPOINT_DEV',
              name: 'GREMLIN_ENDPOINT',
            },
            {
              valueFrom: '/amplify/sandbox/sandbox/TreeEditorLocksTableName',
              name: 'LOCK_TABLE_NAME',
            },
            {
              valueFrom: '/amplify/sandbox/sandbox/MediaBucketName',
              name: 'S3_MEDIA_BUCKET',
            },
            {
              valueFrom: '/amplify/sandbox/sandbox/TreeTableName',
              name: 'TREE_TABLE_NAME',
            },
          ],
          cpu: 0,
          image: cdk.Lazy.string({ produce: () => `${flaskTreeApiEcr.attrRepositoryUri}:latest` }),
          essential: true,
          logConfiguration: {
            options: {
              'awslogs-group': ecsLogGroupDev.ref,
              'awslogs-create-group': 'true',
              'awslogs-region': 'eu-central-1',
              'awslogs-stream-prefix': 'ecs',
            },
            logDriver: 'awslogs',
          },
          name: 'trees-api',
          portMappings: [
            {
              containerPort: 5000,
              appProtocol: 'http',
              protocol: 'tcp',
              hostPort: 5000,
              name: 'trees-api-5000-tcp',
            },
          ],
          command: [
            'gunicorn',
            '--bind',
            '0.0.0.0:5000',
            'app:app',
          ],
          environment: [
            {
              value: 'eu-central-1',
              name: 'AWS_REGION',
            },
            {
              value: '30',
              name: 'ROLE_CACHE_TTL_SECONDS',
            },
            {
              value: '8182',
              name: 'GREMLIN_PORT',
            },
            {
              value: 'REDACTED_ROTATED_SECRET',
              name: 'FLASK_SECRET_KEY',
            },
            {
              value: 'true',
              name: 'GREMLIN_SSL',
            },
            {
              value: 'development',
              name: 'FLASK_ENV',
            },
            {
              value: 'http://localhost:5173,http://localhost:5174,https://master.d32mgf3rp8n1oh.amplifyapp.com',
              name: 'CORS_ORIGINS',
            },
            {
              value: 'true',
              name: 'GREMLIN_IAM_AUTH',
            },
            {
              value: 'INFO',
              name: 'LOG_LEVEL',
            },
            {
              value: '300',
              name: 'LOCK_TTL_SECONDS',
            },
            {
              value: 'true',
              name: 'ENFORCE_LIMITS',
            },
            {
              value: 'True',
              name: 'FLASK_DEBUG',
            },
          ],
        },
      ],
      family: 'trees-api-task-dev',
    });
    ecsTaskDefDev.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const ecsTaskDefProd = new ecs.CfnTaskDefinition(this, 'EcsTaskDefProd', {
      taskRoleArn: cdk.Lazy.string({ produce: () => ecsTaskRoleNeptuneConnect.attrArn }),
      memory: '1024',
      cpu: '256',
      requiresCompatibilities: [
        'FARGATE',
      ],
      networkMode: 'awsvpc',
      executionRoleArn: cdk.Lazy.string({ produce: () => ecsTaskExecutionRole.attrArn }),
      runtimePlatform: {
        operatingSystemFamily: 'LINUX',
        cpuArchitecture: 'X86_64',
      },
      containerDefinitions: [
        {
          secrets: [
            {
              valueFrom: '/amplify/d32mgf3rp8n1oh/master/TreeAclTableName',
              name: 'ACL_TABLE_NAME',
            },
            {
              valueFrom: '/amplify/d32mgf3rp8n1oh/master/UserPoolId',
              name: 'AMPLIFY_USER_POOL_ID',
            },
            {
              valueFrom: '/trees/api/GREMLIN_ENDPOINT_PROD',
              name: 'GREMLIN_ENDPOINT',
            },
            {
              valueFrom: '/amplify/d32mgf3rp8n1oh/master/TreeEditorLocksTableName',
              name: 'LOCK_TABLE_NAME',
            },
            {
              valueFrom: '/amplify/d32mgf3rp8n1oh/master/MediaBucketName',
              name: 'S3_MEDIA_BUCKET',
            },
            {
              valueFrom: '/amplify/d32mgf3rp8n1oh/master/TreeTableName',
              name: 'TREE_TABLE_NAME',
            },
          ],
          cpu: 0,
          image: cdk.Lazy.string({ produce: () => `${flaskTreeApiEcr.attrRepositoryUri}:latest` }),
          essential: true,
          logConfiguration: {
            options: {
              'awslogs-group': ecsLogGroupProd.ref,
              'awslogs-create-group': 'true',
              'awslogs-region': 'eu-central-1',
              'awslogs-stream-prefix': 'ecs',
            },
            logDriver: 'awslogs',
          },
          name: 'trees-api',
          portMappings: [
            {
              containerPort: 5000,
              appProtocol: 'http',
              protocol: 'tcp',
              hostPort: 5000,
              name: 'trees-api-5000-tcp',
            },
          ],
          command: [
            'gunicorn',
            '--bind',
            '0.0.0.0:5000',
            'app:app',
          ],
          environment: [
            {
              value: 'eu-central-1',
              name: 'AWS_REGION',
            },
            {
              value: 'production',
              name: 'FLASK_ENV',
            },
            {
              value: '30',
              name: 'ROLE_CACHE_TTL_SECONDS',
            },
            {
              value: '8182',
              name: 'GREMLIN_PORT',
            },
            {
              value: 'REDACTED_ROTATED_SECRET',
              name: 'FLASK_SECRET_KEY',
            },
            {
              value: 'False',
              name: 'FLASK_DEBUG',
            },
            {
              value: 'true',
              name: 'GREMLIN_SSL',
            },
            {
              value: 'WARNING',
              name: 'LOG_LEVEL',
            },
            {
              value: 'true',
              name: 'GREMLIN_IAM_AUTH',
            },
            {
              value: 'http://localhost:5173,http://localhost:5174,https://master.d32mgf3rp8n1oh.amplifyapp.com,https://trees-lab.com,https://www.trees-lab.com',
              name: 'CORS_ORIGINS',
            },
            {
              value: '300',
              name: 'LOCK_TTL_SECONDS',
            },
            {
              value: 'true',
              name: 'ENFORCE_LIMITS',
            },
          ],
        },
      ],
      family: 'trees-api-task-prod',
    });
    ecsTaskDefProd.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const ecsTaskExecutionRole = new iam.CfnRole(this, 'EcsTaskExecutionRole', {
      path: '/',
      managedPolicyArns: [
        'arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy',
      ],
      maxSessionDuration: 3600,
      roleName: 'ecsTaskExecutionRole',
      policies: [
        {
          policyDocument: {
            Version: '2012-10-17',
            Statement: [
              {
                Resource: [
                  'arn:aws:ssm:eu-central-1:AWS_ACCOUNT_ID:parameter/trees/api/*',
                  'arn:aws:ssm:eu-central-1:AWS_ACCOUNT_ID:parameter/amplify/sandbox/sandbox/*',
                  'arn:aws:ssm:eu-central-1:AWS_ACCOUNT_ID:parameter/amplify/d32mgf3rp8n1oh/master/*',
                ],
                Action: [
                  'ssm:GetParameter',
                  'ssm:GetParameters',
                  'ssm:GetParametersByPath',
                ],
                Effect: 'Allow',
              },
              {
                Resource: '*',
                Action: 'kms:Decrypt',
                Effect: 'Allow',
              },
            ],
          },
          policyName: 'ecs-task-ssm-read',
        },
      ],
      assumeRolePolicyDocument: {
        Version: '2008-10-17',
        Statement: [
          {
            Action: 'sts:AssumeRole',
            Effect: 'Allow',
            Principal: {
              Service: 'ecs-tasks.amazonaws.com',
            },
            Sid: '',
          },
        ],
      },
    });
    ecsTaskExecutionRole.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const ecsTaskRoleNeptuneConnect = new iam.CfnRole(this, 'EcsTaskRoleNeptuneConnect', {
      path: '/',
      maxSessionDuration: 3600,
      roleName: 'ecsTaskRoleNeptuneConnect',
      description: 'Allows ECS tasks to call AWS services on your behalf.',
      policies: [
        {
          policyDocument: {
            Version: '2012-10-17',
            Statement: [
              {
                Resource: 'arn:aws:dynamodb:eu-central-1:AWS_ACCOUNT_ID:table/Tree-*',
                Action: [
                  'dynamodb:BatchGetItem',
                  'dynamodb:GetItem',
                ],
                Effect: 'Allow',
              },
            ],
          },
          policyName: 'AmplifyTableReadAccess',
        },
        {
          policyDocument: {
            Version: '2012-10-17',
            Statement: [
              {
                Resource: 'arn:aws:cognito-idp:eu-central-1:AWS_ACCOUNT_ID:userpool/*',
                Action: [
                  'cognito-idp:AdminGetUser',
                  'cognito-idp:ListUsers',
                  'cognito-idp:AdminDeleteUser',
                ],
                Effect: 'Allow',
                Sid: 'AllowAdminDeleteUser',
              },
            ],
          },
          policyName: 'CognitoDeleteUsers',
        },
        {
          policyDocument: {
            Version: '2012-10-17',
            Statement: [
              {
                Resource: '*',
                Action: [
                  'ssmmessages:CreateControlChannel',
                  'ssmmessages:CreateDataChannel',
                  'ssmmessages:OpenControlChannel',
                  'ssmmessages:OpenDataChannel',
                ],
                Effect: 'Allow',
              },
            ],
          },
          policyName: 'ECSExecSSMMessages',
        },
        {
          policyDocument: {
            Version: '2012-10-17',
            Statement: [
              {
                Resource: 'arn:aws:neptune-db:eu-central-1:AWS_ACCOUNT_ID:cluster-*/*',
                Action: [
                  'neptune-db:connect',
                  'neptune-db:GetEngineStatus',
                  'neptune-db:ReadDataViaQuery',
                  'neptune-db:WriteDataViaQuery',
                  'neptune-db:DeleteDataViaQuery',
                ],
                Effect: 'Allow',
              },
            ],
          },
          policyName: 'neptune-db-connect',
        },
        {
          policyDocument: {
            Version: '2012-10-17',
            Statement: [
              {
                Resource: 'arn:aws:s3:::amplify-*/*',
                Action: [
                  's3:PutObject',
                  's3:GetObject',
                  's3:DeleteObject',
                ],
                Effect: 'Allow',
                Sid: 'S3PutObject',
              },
              {
                Condition: {
                  StringLike: {
                    's3:prefix': [
                      'trees/*',
                    ],
                  },
                },
                Resource: 'arn:aws:s3:::amplify-*',
                Action: 's3:ListBucket',
                Effect: 'Allow',
                Sid: 'S3ListBucketForMedia',
              },
            ],
          },
          policyName: 'trees-media-S3',
        },
        {
          policyDocument: {
            Version: '2012-10-17',
            Statement: [
              {
                Resource: [
                  'arn:aws:dynamodb:eu-central-1:AWS_ACCOUNT_ID:table/custom-resources-*',
                  'arn:aws:dynamodb:eu-central-1:AWS_ACCOUNT_ID:table/amplify-*',
                ],
                Action: [
                  'dynamodb:GetItem',
                  'dynamodb:PutItem',
                  'dynamodb:UpdateItem',
                  'dynamodb:DeleteItem',
                  'dynamodb:BatchGetItem',
                  'dynamodb:BatchWriteItem',
                  'dynamodb:Query',
                  'dynamodb:Scan',
                  'dynamodb:ConditionCheckItem',
                ],
                Effect: 'Allow',
                Sid: 'DynamoDBCustomResourcesTables',
              },
              {
                Resource: 'arn:aws:dynamodb:eu-central-1:AWS_ACCOUNT_ID:table/Tree-*',
                Action: [
                  'dynamodb:GetItem',
                  'dynamodb:BatchGetItem',
                  'dynamodb:Query',
                ],
                Effect: 'Allow',
                Sid: 'DynamoDBTreeTable',
              },
              {
                Resource: 'arn:aws:cognito-idp:eu-central-1:AWS_ACCOUNT_ID:userpool/*',
                Action: 'cognito-idp:ListUsers',
                Effect: 'Allow',
                Sid: 'CognitoListUsers',
              },
              {
                Resource: 'arn:aws:cognito-idp:eu-central-1:AWS_ACCOUNT_ID:userpool/*',
                Action: 'cognito-idp:AdminDeleteUser',
                Effect: 'Allow',
                Sid: 'CognitoAdminDeleteUser',
              },
            ],
          },
          policyName: 'TreesApiAclAccess',
        },
      ],
      assumeRolePolicyDocument: {
        Version: '2012-10-17',
        Statement: [
          {
            Action: 'sts:AssumeRole',
            Effect: 'Allow',
            Principal: {
              Service: 'ecs-tasks.amazonaws.com',
            },
            Sid: '',
          },
        ],
      },
    });
    ecsTaskRoleNeptuneConnect.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const flaskTreeApiEcr = new ecr.CfnRepository(this, 'FlaskTreeApiEcr', {
      imageScanningConfiguration: {
        scanOnPush: true,
      },
      repositoryName: 'flask-tree-api',
      encryptionConfiguration: {
        encryptionType: 'AES256',
      },
      imageTagMutability: 'MUTABLE',
    });
    flaskTreeApiEcr.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const githubActionsFlaskDeployRole = new iam.CfnRole(this, 'GithubActionsFlaskDeployRole', {
      path: '/',
      maxSessionDuration: 3600,
      roleName: 'github-actions-flask-trees-deploy',
      description: '',
      policies: [
        {
          policyDocument: {
            Version: '2012-10-17',
            Statement: [
              {
                Resource: '*',
                Action: [
                  'ecr:GetAuthorizationToken',
                  'ecr:BatchCheckLayerAvailability',
                  'ecr:BatchGetImage',
                  'ecr:CompleteLayerUpload',
                  'ecr:GetDownloadUrlForLayer',
                  'ecr:InitiateLayerUpload',
                  'ecr:PutImage',
                  'ecr:UploadLayerPart',
                ],
                Effect: 'Allow',
                Sid: 'ECRPush',
              },
              {
                Resource: 'arn:aws:ecs:eu-central-1:AWS_ACCOUNT_ID:service/trees-api-dev/trees-api-svc',
                Action: [
                  'ecs:UpdateService',
                  'ecs:DescribeServices',
                ],
                Effect: 'Allow',
                Sid: 'ECSDeploy',
              },
            ],
          },
          policyName: 'ecr-push-ecs-deploy',
        },
      ],
      assumeRolePolicyDocument: {
        Version: '2012-10-17',
        Statement: [
          {
            Condition: {
              StringEquals: {
                'token.actions.githubusercontent.com:aud': 'sts.amazonaws.com',
              },
              StringLike: {
                'token.actions.githubusercontent.com:sub': 'repo:AlphaAnimal/flask-tree-endpoints:ref:refs/heads/main',
              },
            },
            Action: 'sts:AssumeRoleWithWebIdentity',
            Effect: 'Allow',
            Principal: {
              Federated: 'arn:aws:iam::AWS_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com',
            },
          },
        ],
      },
    });
    githubActionsFlaskDeployRole.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const treesVpcLink = new apigatewayv2.CfnVpcLink(this, 'TreesVpcLink', {
      subnetIds: [
        'subnet-0b0add3a8dbedf82e',
        'subnet-01e3a267b85c87b0c',
      ],
      securityGroupIds: [
        'sg-015635a1eae8dcd12',
      ],
      name: 'trees-vpc-link',
    });
    treesVpcLink.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const httpApiDev = new apigatewayv2.CfnApi(this, 'HttpApiDev', {
      routeSelectionExpression: '$request.method $request.path',
      disableExecuteApiEndpoint: false,
      protocolType: 'HTTP',
      name: 'trees-api-dev',
    });
    httpApiDev.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const httpApiDevIntegration = new apigatewayv2.CfnIntegration(this, 'HttpApiDevIntegration', {
      apiId: httpApiDev.ref,
      connectionId: treesVpcLink.ref,
      integrationUri: 'arn:aws:servicediscovery:eu-central-1:AWS_ACCOUNT_ID:service/srv-apsql6xdfn7a3jtp',
      payloadFormatVersion: '1.0',
      connectionType: 'VPC_LINK',
      timeoutInMillis: 30000,
      integrationMethod: 'ANY',
      integrationType: 'HTTP_PROXY',
    });
    httpApiDevIntegration.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const httpApiDevRoute = new apigatewayv2.CfnRoute(this, 'HttpApiDevRoute', {
      apiId: httpApiDev.ref,
      target: cdk.Fn.join('/', ['integrations', httpApiDevIntegration.ref]),
      apiKeyRequired: false,
      routeKey: 'ANY /{proxy+}',
      authorizationType: 'NONE',
    });
    httpApiDevRoute.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const httpApiProd = new apigatewayv2.CfnApi(this, 'HttpApiProd', {
      routeSelectionExpression: '$request.method $request.path',
      disableExecuteApiEndpoint: false,
      protocolType: 'HTTP',
      name: 'trees-api-prod',
    });
    httpApiProd.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const httpApiProdIntegration = new apigatewayv2.CfnIntegration(this, 'HttpApiProdIntegration', {
      apiId: httpApiProd.ref,
      connectionId: treesVpcLink.ref,
      integrationUri: 'arn:aws:servicediscovery:eu-central-1:AWS_ACCOUNT_ID:service/srv-we3dm4um3mwub62m',
      payloadFormatVersion: '1.0',
      connectionType: 'VPC_LINK',
      timeoutInMillis: 30000,
      integrationMethod: 'ANY',
      integrationType: 'HTTP_PROXY',
    });
    httpApiProdIntegration.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const httpApiProdRoute = new apigatewayv2.CfnRoute(this, 'HttpApiProdRoute', {
      apiId: httpApiProd.ref,
      target: cdk.Fn.join('/', ['integrations', httpApiProdIntegration.ref]),
      apiKeyRequired: false,
      routeKey: 'ANY /{proxy+}',
      authorizationType: 'NONE',
    });
    httpApiProdRoute.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const treesLabZone = new route53.CfnHostedZone(this, 'TreesLabZone', {
      hostedZoneConfig: {
        comment: 'HostedZone created by Route53 Registrar',
      },
      name: 'trees-lab.com.',
    });
    treesLabZone.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const httpApiDevDeployment = new apigatewayv2.CfnDeployment(this, 'HttpApiDevDeployment', {
      apiId: httpApiDev.ref,
      description: 'Initial deployment',
    });
    httpApiDevDeployment.addDependency(httpApiDevRoute);
    httpApiDevDeployment.addDependency(httpApiDevIntegration);

    const httpApiDevStage = new apigatewayv2.CfnStage(this, 'HttpApiDevStage', {
      apiId: httpApiDev.ref,
      stageName: '$default',
      autoDeploy: true,
      deploymentId: httpApiDevDeployment.ref,
    });
    httpApiDevStage.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const httpApiProdDeployment = new apigatewayv2.CfnDeployment(this, 'HttpApiProdDeployment', {
      apiId: httpApiProd.ref,
      description: 'Initial deployment',
    });
    httpApiProdDeployment.addDependency(httpApiProdRoute);
    httpApiProdDeployment.addDependency(httpApiProdIntegration);

    const httpApiProdStage = new apigatewayv2.CfnStage(this, 'HttpApiProdStage', {
      apiId: httpApiProd.ref,
      stageName: '$default',
      autoDeploy: true,
      deploymentId: httpApiProdDeployment.ref,
    });
    httpApiProdStage.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const cloudFrontHostedZoneId = 'Z2FDTNDATAQYW2';

    const recordSetApiProd = new route53.CfnRecordSet(this, 'RecordSetApiProd', {
      hostedZoneId: treesLabZone.ref,
      name: 'api.trees-lab.com.',
      type: 'A',
      aliasTarget: {
        hostedZoneId: cloudFrontHostedZoneId,
        dnsName: cloudFrontProd.attrDomainName,
        evaluateTargetHealth: false,
      },
    });
    recordSetApiProd.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const recordSetApiDev = new route53.CfnRecordSet(this, 'RecordSetApiDev', {
      hostedZoneId: treesLabZone.ref,
      name: 'dev-api.trees-lab.com.',
      type: 'A',
      aliasTarget: {
        hostedZoneId: cloudFrontHostedZoneId,
        dnsName: cloudFrontDev.attrDomainName,
        evaluateTargetHealth: false,
      },
    });
    recordSetApiDev.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;
  }
}
