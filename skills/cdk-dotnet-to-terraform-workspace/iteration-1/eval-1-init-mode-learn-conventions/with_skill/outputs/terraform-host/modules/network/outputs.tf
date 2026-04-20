output "vpc_id" {
  description = "ID of the created VPC."
  value       = aws_vpc.this.id
}

output "vpc_cidr_block" {
  description = "CIDR block of the created VPC."
  value       = aws_vpc.this.cidr_block
}

output "public_subnet_ids" {
  description = "List of public subnet IDs, one per AZ."
  value       = [for s in aws_subnet.public : s.id]
}

output "private_subnet_ids" {
  description = "List of private subnet IDs, one per AZ."
  value       = [for s in aws_subnet.private : s.id]
}

output "default_security_group_id" {
  description = "VPC default security group ID."
  value       = aws_vpc.this.default_security_group_id
}
