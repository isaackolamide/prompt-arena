#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { SandboxStack } from '../lib/sandbox-stack';

export const app = new cdk.App();
new SandboxStack(app, 'SandboxStack');
