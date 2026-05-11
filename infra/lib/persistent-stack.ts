import * as cdk from 'aws-cdk-lib';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as route53 from 'aws-cdk-lib/aws-route53';

export class TreesPersistentStack extends cdk.Stack {
  public readonly hostedZone: route53.CfnHostedZone;
  public readonly ecrRepository: ecr.CfnRepository;

  public constructor(scope: cdk.App, id: string, props: cdk.StackProps) {
    super(scope, id, props);

    this.hostedZone = new route53.CfnHostedZone(this, 'TreesLabZone', {
      name: 'trees-lab.com.',
      hostedZoneConfig: { comment: 'HostedZone created by Route53 Registrar' },
    });
    this.hostedZone.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    this.ecrRepository = new ecr.CfnRepository(this, 'FlaskTreeApiEcr', {
      repositoryName: 'flask-tree-api',
      imageScanningConfiguration: { scanOnPush: true },
      encryptionConfiguration: { encryptionType: 'AES256' },
      imageTagMutability: 'MUTABLE',
    });
    this.ecrRepository.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    new iam.CfnRole(this, 'GithubActionsFlaskDeployRole', {
      roleName: 'github-actions-flask-trees-deploy',
      assumeRolePolicyDocument: {
        Version: '2012-10-17',
        Statement: [{
          Effect: 'Allow',
          Principal: { Federated: `arn:aws:iam::${this.account}:oidc-provider/token.actions.githubusercontent.com` },
          Action: 'sts:AssumeRoleWithWebIdentity',
          Condition: {
            StringEquals: { 'token.actions.githubusercontent.com:aud': 'sts.amazonaws.com' },
            StringLike: { 'token.actions.githubusercontent.com:sub': 'repo:AlphaAnimal/flask-tree-endpoints:ref:refs/heads/main' },
          },
        }],
      },
      policies: [{
        policyName: 'ecr-push-ecs-deploy',
        policyDocument: {
          Version: '2012-10-17',
          Statement: [
            {
              Sid: 'ECRPush',
              Effect: 'Allow',
              Action: [
                'ecr:GetAuthorizationToken', 'ecr:BatchCheckLayerAvailability', 'ecr:BatchGetImage',
                'ecr:CompleteLayerUpload', 'ecr:GetDownloadUrlForLayer', 'ecr:InitiateLayerUpload',
                'ecr:PutImage', 'ecr:UploadLayerPart',
              ],
              Resource: '*',
            },
            {
              Sid: 'ECSDeploy',
              Effect: 'Allow',
              Action: ['ecs:UpdateService', 'ecs:DescribeServices'],
              Resource: `arn:aws:ecs:${this.region}:${this.account}:service/trees-api-*/trees-api-svc-*`,
            },
          ],
        },
      }],
    });
  }
}
