import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';

export class SandboxStack extends cdk.Stack {
  public readonly vpc: ec2.IVpc;
  public readonly repository: ecr.IRepository;
  public readonly sandboxFunction: lambda.DockerImageFunction;

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

    // Create a dedicated IAM Role assumed by lambda.amazonaws.com
    const executionRole = new iam.Role(this, 'SandboxLambdaExecutionRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaVPCAccessExecutionRole'),
      ],
    });

    // Create the Lambda function using the Docker image from ECR
    this.sandboxFunction = new lambda.DockerImageFunction(this, 'SandboxLambdaFunction', {
      code: lambda.DockerImageCode.fromEcr(this.repository),
      timeout: cdk.Duration.seconds(5),
      vpc: this.vpc,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
      },
      role: executionRole,
    });
  }
}
