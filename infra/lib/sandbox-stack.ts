import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import { Construct } from 'constructs';

export class SandboxStack extends cdk.Stack {
  public readonly vpc: ec2.IVpc;
  public readonly repository: ecr.IRepository;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create an isolated VPC (no internet gateway, no NAT gateway)
    this.vpc = new ec2.Vpc(this, 'SandboxVpc', {
      maxAzs: 2,
      subnetConfiguration: [
        {
          name: 'Isolated',
          subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
        },
      ],
    });

    // Create ECR repository for the sandbox Lambda image
    this.repository = new ecr.Repository(this, 'SandboxRepository', {
      repositoryName: 'prompt-arena-sandbox',
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteImages: true,
    });
  }
}
