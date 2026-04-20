output "endpoint_id" {
  description = "ID of the Bedrock runtime VPC interface endpoint."
  value       = aws_vpc_endpoint.bedrock_runtime.id
}

output "endpoint_arn" {
  description = "ARN of the Bedrock runtime VPC interface endpoint."
  value       = aws_vpc_endpoint.bedrock_runtime.arn
}

output "endpoint_dns_entries" {
  description = "DNS entries for the interface endpoint (private DNS is enabled by default)."
  value       = aws_vpc_endpoint.bedrock_runtime.dns_entry
}

output "security_group_id" {
  description = "Security group guarding the Bedrock interface endpoint."
  value       = aws_security_group.this.id
}
