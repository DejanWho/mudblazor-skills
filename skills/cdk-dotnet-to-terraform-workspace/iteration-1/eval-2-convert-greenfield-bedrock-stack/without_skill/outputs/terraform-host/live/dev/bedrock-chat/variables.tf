variable "environment" {
  description = "Environment name (dev / stg / prd)."
  type        = string
  default     = "dev"
}

variable "application" {
  description = "Application name — drives resource naming."
  type        = string
  default     = "bedrock-chat"
}

variable "cost_center" {
  description = "Cost center tag."
  type        = string
}

variable "region" {
  description = "AWS region the stack is deployed into."
  type        = string
  default     = "eu-central-1"
}

variable "vpc_cidr" {
  description = "VPC CIDR block."
  type        = string
  default     = "10.30.0.0/16"
}

variable "availability_zones" {
  description = "AZs to spread subnets across."
  type        = list(string)
  default     = ["eu-central-1a", "eu-central-1b", "eu-central-1c"]
}

variable "certificate_arn" {
  description = "ACM certificate ARN for the ALB HTTPS listener."
  type        = string
}

variable "container_image" {
  description = "Container image URI for the chat API service."
  type        = string
  default     = "public.ecr.aws/nginx/nginx:stable"
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

variable "container_port" {
  description = "Container port the service listens on."
  type        = number
  default     = 8080
}

variable "claude_sonnet_model_id" {
  description = "Anthropic Claude 3.5 Sonnet model id the service invokes."
  type        = string
  default     = "anthropic.claude-3-5-sonnet-20241022-v2:0"
}

variable "claude_haiku_model_id" {
  description = "Anthropic Claude 3 Haiku model id the service invokes."
  type        = string
  default     = "anthropic.claude-3-haiku-20240307-v1:0"
}
