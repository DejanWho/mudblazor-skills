variable "environment" {
  description = "Environment name (dev / stg / prd)."
  type        = string
  default     = "dev"
}

variable "application" {
  description = "Application name - drives resource naming."
  type        = string
  default     = "bedrock-chat"
}

variable "cost_center" {
  description = "Cost center tag."
  type        = string
  default     = "ai-platform"
}

variable "region" {
  description = "AWS region."
  type        = string
  default     = "eu-central-1"
}

variable "vpc_cidr" {
  description = "CIDR block of the already-deployed VPC. Must match the real VPC so `terraform import` yields a clean plan."
  type        = string
  default     = "10.30.0.0/16"
}

variable "availability_zones" {
  description = "AZs to spread subnets across. CDK used MaxAzs=3 in eu-central-1."
  type        = list(string)
  default     = ["eu-central-1a", "eu-central-1b", "eu-central-1c"]
}

variable "certificate_arn" {
  description = "ACM cert ARN for the ALB HTTPS listener (matches CDK-imported cert)."
  type        = string
  default     = "arn:aws:acm:eu-central-1:000000000000:certificate/00000000-0000-0000-0000-000000000000"
}

variable "container_image" {
  description = "Container image URI for the chat service."
  type        = string
  default     = "public.ecr.aws/nginx/nginx:stable"
}

variable "container_port" {
  description = "Port the app listens on inside the container."
  type        = number
  default     = 8080
}

variable "desired_count" {
  description = "Desired Fargate task count."
  type        = number
  default     = 2
}

variable "task_cpu" {
  description = "Fargate task CPU units."
  type        = number
  default     = 1024
}

variable "task_memory" {
  description = "Fargate task memory (MiB)."
  type        = number
  default     = 2048
}

variable "log_retention_days" {
  description = "CloudWatch log retention for the task log group."
  type        = number
  default     = 30
}

variable "claude_sonnet_model_id" {
  description = "Bedrock foundation model ID for Claude 3.5 Sonnet."
  type        = string
  default     = "anthropic.claude-3-5-sonnet-20241022-v2:0"
}

variable "claude_haiku_model_id" {
  description = "Bedrock foundation model ID for Claude 3 Haiku."
  type        = string
  default     = "anthropic.claude-3-haiku-20240307-v1:0"
}
