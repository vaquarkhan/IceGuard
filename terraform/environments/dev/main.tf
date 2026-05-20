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
}

module "checkpoint_bucket" {
  source      = "../../modules/checkpoint_bucket"
  bucket_name = var.checkpoint_bucket_name
  tags = {
    Environment = "dev"
    Project     = var.project_name
  }
}

module "lambda_iam" {
  source                = "../../modules/lambda_iam"
  role_name             = "${var.project_name}-lambda-role"
  checkpoint_bucket_arn = module.checkpoint_bucket.bucket_arn
  data_bucket_arns      = var.data_bucket_arns
  tags = {
    Environment = "dev"
    Project     = var.project_name
  }
}

module "cloudwatch_dashboard" {
  source         = "../../modules/cloudwatch_dashboard"
  dashboard_name = "${var.project_name}-IceGuard"
}
