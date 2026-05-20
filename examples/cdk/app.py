#!/usr/bin/env python3
"""Minimal CDK stack: checkpoint bucket + Lambda IAM role (see terraform modules for full parity)."""

import aws_cdk as cdk
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3


class IceGuardStack(cdk.Stack):
    def __init__(self, scope, construct_id, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        bucket = s3.Bucket(
            self,
            "CheckpointBucket",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )

        role = iam.Role(
            self,
            "LambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
        )
        bucket.grant_read_write(role)

        cdk.CfnOutput(self, "CheckpointBucketName", value=bucket.bucket_name)
        cdk.CfnOutput(self, "LambdaRoleArn", value=role.role_arn)


app = cdk.App()
IceGuardStack(app, "IceGuardCdkSample")
app.synth()
