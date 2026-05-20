terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = "dev"
      ManagedBy   = "terraform"
    }
  }
}

module "iceguard" {
  source = "../../modules/iceguard_stack"

  name_prefix            = var.project_name
  aws_region             = var.aws_region
  checkpoint_bucket_name = var.checkpoint_bucket_name
  data_lake_bucket_name  = var.data_lake_bucket_name
  enable_kms             = var.enable_kms
  enable_alarms          = var.enable_alarms
  sns_alert_topic_arn    = var.sns_alert_topic_arn
  deploy_lambda          = var.deploy_lambda
  lambda_artifact_bucket = var.lambda_artifact_bucket
  lambda_artifact_key    = var.lambda_artifact_key
  lambda_layer_artifact_key = var.lambda_layer_artifact_key

  tags = {
    Environment = "dev"
    Project     = var.project_name
  }
}
