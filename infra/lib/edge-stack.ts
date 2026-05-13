import * as cdk from 'aws-cdk-lib';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as wafv2 from 'aws-cdk-lib/aws-wafv2';

export class TreesEdgeStack extends cdk.Stack {
  public readonly certApiProd: acm.CfnCertificate;
  public readonly certApiDev: acm.CfnCertificate;
  public readonly webAcl: wafv2.CfnWebACL;

  public constructor(scope: cdk.App, id: string, props: cdk.StackProps) {
    super(scope, id, props);

    const treesLabZoneId = 'Z09589371W719DJ1ZRGSQ';

    this.certApiProd = new acm.CfnCertificate(this, 'CertApi', {
      domainName: 'api.trees-lab.com',
      subjectAlternativeNames: ['api.trees-lab.com', 'dev-api.trees-lab.com'],
      validationMethod: 'DNS',
      domainValidationOptions: [
        { domainName: 'api.trees-lab.com', hostedZoneId: treesLabZoneId },
        { domainName: 'dev-api.trees-lab.com', hostedZoneId: treesLabZoneId },
      ],
    });
    this.certApiProd.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    this.certApiDev = new acm.CfnCertificate(this, 'CertApiDev', {
      domainName: 'dev-api.trees-lab.com',
      subjectAlternativeNames: ['dev-api.trees-lab.com'],
      validationMethod: 'DNS',
      domainValidationOptions: [
        { domainName: 'dev-api.trees-lab.com', hostedZoneId: treesLabZoneId },
      ],
    });
    this.certApiDev.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    const cfWafRules: wafv2.CfnWebACL.RuleProperty[] = [
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
    ];

    const legacyWebAcl = new wafv2.CfnWebACL(this, 'CloudFrontWebAcl', {
      name: 'CreatedByCloudFront-0ac1ed8d',
      defaultAction: { allow: {} },
      scope: 'CLOUDFRONT',
      visibilityConfig: {
        sampledRequestsEnabled: true,
        cloudWatchMetricsEnabled: true,
        metricName: 'CreatedByCloudFront-0ac1ed8d',
      },
      rules: cfWafRules,
    });
    legacyWebAcl.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.RETAIN;

    this.webAcl = new wafv2.CfnWebACL(this, 'CloudFrontWebAclV2', {
      name: 'trees-cf-webacl',
      defaultAction: { allow: {} },
      scope: 'CLOUDFRONT',
      visibilityConfig: {
        sampledRequestsEnabled: true,
        cloudWatchMetricsEnabled: true,
        metricName: 'trees-cf-webacl',
      },
      rules: cfWafRules,
    });
  }
}
