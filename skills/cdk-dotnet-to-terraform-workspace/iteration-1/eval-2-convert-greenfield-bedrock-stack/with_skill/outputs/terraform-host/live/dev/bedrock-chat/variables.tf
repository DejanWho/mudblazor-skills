variable "environment" {
  description = "Environment name (dev / stg / prd)."
  type        = string
  default     = "dev"
}

variable "application" {
  description = "Application name — drives resource naming and tagging."
  type        = string
  default     = "bedrock-chat"
}

variable "cost_center" {
  description = "Cost center tag."
  type        = string
}

variable "region" {
  description = "AWS region — matches the CDK stack's region (from cdk.json context)."
  type        = string
  default     = "eu-central-1"
}

variable "vpc_cidr" {
  description = "VPC CIDR block. Matches CDK context key `vpc-cidr`."
  type        = string
  default     = "10.30.0.0/16"
}

variable "availability_zones" {
  description = "AZs to spread subnets across. CDK sets MaxAzs = 3 / NatGateways = 3; mirror that with three AZs."
  type        = list(string)
  default     = ["eu-central-1a", "eu-central-1b", "eu-central-1c"]
}

variable "certificate_arn" {
  description = "ACM certificate ARN for the ALB HTTPS listener. Provisioned out-of-stack (CDK imports it)."
  type        = string
  default     = "arn:aws:acm:eu-central-1:000000000000:certificate/00000000-0000-0000-0000-000000000000"
}

variable "api_image" {
  description = "Container image URI for the chat API. CDK default is `public.ecr.aws/nginx/nginx:stable`."
  type        = string
  default     = "public.ecr.aws/nginx/nginx:stable"
}

variable "task_cpu" {
  description = "Fargate task CPU units. CDK sets 1024."
  type        = number
  default     = 1024
}

variable "task_memory" {
  description = "Fargate task memory (MiB). CDK sets 2048."
  type        = number
  default     = 2048
}

variable "desired_count" {
  description = "Desired service task count. CDK sets DesiredCount = 2."
  type        = number
  default     = 2
}

variable "claude_sonnet_model_id" {
  description = "Bedrock model ID for Claude 3.5 Sonnet. Matches CDK context key `claude-sonnet-model-id`."
  type        = string
  default     = "anthropic.claude-3-5-sonnet-20241022-v2:0"
}

variable "claude_haiku_model_id" {
  description = "Bedrock model ID for Claude 3 Haiku. Matches CDK context key `claude-haiku-model-id`."
  type        = string
  default     = "anthropic.claude-3-haiku-20240307-v1:0"
}
