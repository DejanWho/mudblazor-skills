variable "name" {
  description = "ALB name and base for tagging/naming dependent resources."
  type        = string
}

variable "vpc_id" {
  description = "VPC the ALB lives in."
  type        = string
}

variable "public_subnet_ids" {
  description = "Public subnet IDs the ALB attaches to."
  type        = list(string)
}

variable "certificate_arn" {
  description = "ACM certificate ARN for the HTTPS listener."
  type        = string
}

variable "allowed_cidr_blocks" {
  description = "Client CIDR blocks allowed to reach the ALB."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "internal" {
  description = "Whether the ALB is internal (vs internet-facing)."
  type        = bool
  default     = false
}

variable "idle_timeout" {
  description = "ALB idle timeout seconds."
  type        = number
  default     = 60
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection on the ALB."
  type        = bool
  default     = false
}

variable "tags" {
  description = "Extra tags merged with the module-managed common_tags."
  type        = map(string)
  default     = {}
}
