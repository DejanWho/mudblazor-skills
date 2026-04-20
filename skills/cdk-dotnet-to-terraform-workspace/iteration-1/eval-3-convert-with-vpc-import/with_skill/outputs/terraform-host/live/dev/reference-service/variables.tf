variable "environment" {
  description = "Environment name (dev / stg / prd)."
  type        = string
  default     = "dev"
}

variable "application" {
  description = "Application name — drives resource naming."
  type        = string
  default     = "reference"
}

variable "cost_center" {
  description = "Cost center tag."
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR block."
  type        = string
  default     = "10.20.0.0/16"
}

variable "availability_zones" {
  description = "AZs to spread subnets across."
  type        = list(string)
  default     = ["eu-central-1a", "eu-central-1b", "eu-central-1c"]
}

variable "certificate_arn" {
  description = "ACM cert ARN for the ALB HTTPS listener."
  type        = string
}

variable "api_image" {
  description = "Container image URI for the API service."
  type        = string
}
