terraform {
  required_version = ">= 1.5, < 2.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.70"
    }
  }

  backend "s3" {
    # Backend config supplied at init time:
    # terraform init -backend-config="key=<env>/<app>/terraform.tfstate" ...
    key = "dev/bedrock-chat/terraform.tfstate"
  }
}

provider "aws" {
  region = "eu-central-1"

  default_tags {
    tags = {
      Environment = "dev"
      Application = "bedrock-chat"
      ManagedBy   = "terraform"
    }
  }
}
