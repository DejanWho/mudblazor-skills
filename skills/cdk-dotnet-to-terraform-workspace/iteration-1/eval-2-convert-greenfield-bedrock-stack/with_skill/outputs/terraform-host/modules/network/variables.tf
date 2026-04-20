variable "name" {
  description = "Base name used for resource naming and tagging."
  type        = string
}

variable "cidr_block" {
  description = "IPv4 CIDR block for the VPC."
  type        = string
}

variable "availability_zones" {
  description = "List of AZ names to spread public + private subnets across."
  type        = list(string)
}

variable "tags" {
  description = "Extra tags merged with the module-managed common_tags."
  type        = map(string)
  default     = {}
}
