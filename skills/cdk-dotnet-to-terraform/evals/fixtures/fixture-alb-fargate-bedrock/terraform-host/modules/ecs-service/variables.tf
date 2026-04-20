variable "service_name" {
  description = "Service name — used for naming resources and tagging."
  type        = string
}

variable "cluster_arn" {
  description = "ARN of the ECS cluster to run the service in."
  type        = string
}

variable "image" {
  description = "Container image URI."
  type        = string
}

variable "cpu" {
  description = "Fargate task CPU units."
  type        = number
  default     = 512
}

variable "memory" {
  description = "Fargate task memory (MiB)."
  type        = number
  default     = 1024
}

variable "desired_count" {
  description = "Desired task count. Autoscaler may override (ignored in lifecycle)."
  type        = number
  default     = 2
}

variable "vpc_id" {
  description = "VPC ID the service lives in."
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs for the Fargate tasks (typically private)."
  type        = list(string)
}

variable "alb_security_group_id" {
  description = "ALB security group ID. Task SG ingress allows traffic from this SG."
  type        = string
}

variable "target_group_arn" {
  description = "Target group ARN the service registers against."
  type        = string
}

variable "container_port" {
  description = "Container port the service listens on."
  type        = number
  default     = 8080
}

variable "environment_variables" {
  description = "Environment variables for the container (key → value)."
  type        = map(string)
  default     = {}
}

variable "secret_arns" {
  description = "Secret env vars (key → Secrets Manager ARN or SSM parameter ARN)."
  type        = map(string)
  default     = {}
}

variable "additional_task_role_policy_arns" {
  description = "Additional managed/customer policy ARNs attached to the task role."
  type        = list(string)
  default     = []
}

variable "log_retention_days" {
  description = "CloudWatch log group retention (days)."
  type        = number
  default     = 30
}

variable "tags" {
  description = "Extra tags merged with module common_tags."
  type        = map(string)
  default     = {}
}
