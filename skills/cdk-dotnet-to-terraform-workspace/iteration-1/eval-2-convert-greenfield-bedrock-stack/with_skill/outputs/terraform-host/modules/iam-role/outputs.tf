output "role_arn" {
  description = "ARN of the role."
  value       = aws_iam_role.this.arn
}

output "role_name" {
  description = "Name of the role."
  value       = aws_iam_role.this.name
}

output "role_id" {
  description = "ID of the role."
  value       = aws_iam_role.this.id
}
