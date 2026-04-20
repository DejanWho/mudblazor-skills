variable "name" {
  description = "Base name used for resource naming and tagging."
  type        = string
}

variable "vpc_id" {
  description = "VPC the interface endpoint is created in."
  type        = string
}

variable "subnet_ids" {
  description = "Private subnet IDs to attach the interface endpoint ENIs to."
  type        = list(string)
}

variable "client_security_group_ids" {
  description = "Security groups whose members are allowed to reach the endpoint on 443."
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Extra tags merged with module common_tags."
  type        = map(string)
  default     = {}
}
