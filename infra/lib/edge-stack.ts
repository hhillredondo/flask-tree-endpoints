import * as cdk from 'aws-cdk-lib';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as wafv2 from 'aws-cdk-lib/aws-wafv2';

export class TreesEdgeStack extends cdk.Stack {
  public constructor(scope: cdk.App, id: string, props: cdk.StackProps) {
    super(scope, id, props);

    const treesLabZoneId = 'Z09589371W719DJ1ZRGSQ';

    // ACM certs: AWS::CertificateManager::Certificate is NOT importable. The two
    // certs below match the live console-created certs by domain. On a clean-slate
    // deploy in a fresh account, CDK will create them and CFN auto-validates via DNS
    // against the hosted zone above. In the *current* account they coexist with the
    // already-live console certs (no harm — ACM is free) until Phase B/C swaps
    // CloudFront's viewerCertificate to these CDK-managed cert ARNs.
    const certApi = new acm.CfnCertificate(this, 'CertApi', {
      domainName: 'api.trees-lab.com',
      subjectAlternativeNames: ['api.trees-lab.com', 'dev-api.trees-lab.com'],
      validationMethod: 'DNS',
      domainValidationOptions: [
        { domainName: 'api.trees-lab.com', hostedZoneId: treesLabZoneId },
        { domainName: 'dev-api.trees-lab.com', hostedZoneId: treesLabZoneId },
      ],
    });
    certApi.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const certApiDev = new acm.CfnCertificate(this, 'CertApiDev', {
      domainName: 'dev-api.trees-lab.com',
      subjectAlternativeNames: ['dev-api.trees-lab.com'],
      validationMethod: 'DNS',
      domainValidationOptions: [
        { domainName: 'dev-api.trees-lab.com', hostedZoneId: treesLabZoneId },
      ],
    });
    certApiDev.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const webAcl = new wafv2.CfnWebACL(this, 'CloudFrontWebAcl', {
      name: 'CreatedByCloudFront-0ac1ed8d',
      defaultAction: { allow: {} },
      scope: 'CLOUDFRONT',
      visibilityConfig: {
        sampledRequestsEnabled: true,
        cloudWatchMetricsEnabled: true,
        metricName: 'CreatedByCloudFront-0ac1ed8d',
      },
      rules: [
        {
          name: 'AWS-AWSManagedRulesAmazonIpReputationList',
          priority: 0,
          statement: {
            managedRuleGroupStatement: {
              vendorName: 'AWS',
              name: 'AWSManagedRulesAmazonIpReputationList',
            },
          },
          overrideAction: { none: {} },
          visibilityConfig: {
            sampledRequestsEnabled: true,
            cloudWatchMetricsEnabled: true,
            metricName: 'AWS-AWSManagedRulesAmazonIpReputationList',
          },
        },
        {
          name: 'AWS-AWSManagedRulesCommonRuleSet',
          priority: 1,
          statement: {
            managedRuleGroupStatement: {
              vendorName: 'AWS',
              name: 'AWSManagedRulesCommonRuleSet',
              ruleActionOverrides: [
                { name: 'SizeRestrictions_BODY', actionToUse: { count: {} } },
                { name: 'CrossSiteScripting_BODY', actionToUse: { count: {} } },
              ],
            },
          },
          overrideAction: { none: {} },
          visibilityConfig: {
            sampledRequestsEnabled: true,
            cloudWatchMetricsEnabled: true,
            metricName: 'AWS-AWSManagedRulesCommonRuleSet',
          },
        },
        {
          name: 'AWS-AWSManagedRulesKnownBadInputsRuleSet',
          priority: 2,
          statement: {
            managedRuleGroupStatement: {
              vendorName: 'AWS',
              name: 'AWSManagedRulesKnownBadInputsRuleSet',
            },
          },
          overrideAction: { none: {} },
          visibilityConfig: {
            sampledRequestsEnabled: true,
            cloudWatchMetricsEnabled: true,
            metricName: 'AWS-AWSManagedRulesKnownBadInputsRuleSet',
          },
        },
      ],
    });
    webAcl.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;
  }
}
