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
}

variable "vpc_cidr" {
  description = "VPC CIDR block. Matches the already-deployed VPC's CIDR (imported via imports.tf)."
  type        = string
  default     = "10.30.0.0/16"
}

variable "availability_zones" {
  description = "AZs to spread subnets across. Must match the deployed VPC's AZ layout."
  type        = list(string)
  default     = ["eu-central-1a", "eu-central-1b", "eu-central-1c"]
}

variable "certificate_arn" {
  description = "ACM cert ARN for the ALB HTTPS listener."
  type        = string
}

variable "api_image" {
  description = "Container image URI for the Bedrock chat API service."
  type        = string
  default     = "public.ecr.aws/nginx/nginx:stable"
}

variable "claude_sonnet_model_id" {
  description = "Anthropic Claude Sonnet model ID invoked by the service."
  type        = string
  default     = "anthropic.claude-3-5-sonnet-20241022-v2:0"
}

variable "claude_haiku_model_id" {
  description = "Anthropic Claude Haiku model ID invoked by the service."
  type        = string
  default     = "anthropic.claude-3-haiku-20240307-v1:0"
}
