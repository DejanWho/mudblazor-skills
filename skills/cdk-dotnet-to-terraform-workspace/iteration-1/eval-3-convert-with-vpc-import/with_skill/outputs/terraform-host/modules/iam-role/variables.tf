variable "name" {
  description = "Role name."
  type        = string
}

variable "trust_policy_json" {
  description = "Trust policy document as JSON. Use jsonencode() or data.aws_iam_policy_document at the caller."
  type        = string
}

variable "managed_policy_arns" {
  description = "Managed policies to attach."
  type        = list(string)
  default     = []
}

variable "inline_policies" {
  description = "Inline policies, keyed by policy name. Value is the policy JSON."
  type        = map(string)
  default     = {}
}

variable "max_session_duration" {
  description = "Max session duration in seconds."
  type        = number
  default     = 3600
}

variable "tags" {
  description = "Extra tags merged with module common_tags."
  type        = map(string)
  default     = {}
}
