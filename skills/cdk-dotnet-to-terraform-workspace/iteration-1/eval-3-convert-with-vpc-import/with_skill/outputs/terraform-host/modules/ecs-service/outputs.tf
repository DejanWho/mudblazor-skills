output "service_arn" {
  description = "ARN of the ECS service."
  value       = aws_ecs_service.this.id
}

output "service_name" {
  description = "Name of the ECS service."
  value       = aws_ecs_service.this.name
}

output "task_definition_arn" {
  description = "ARN of the task definition (specific revision)."
  value       = aws_ecs_task_definition.this.arn
}

output "task_role_arn" {
  description = "Task role ARN — attach extra policies via additional_task_role_policy_arns or inline at the caller."
  value       = aws_iam_role.task.arn
}

output "task_role_name" {
  description = "Task role name — useful for aws_iam_role_policy attachment at the caller."
  value       = aws_iam_role.task.name
}

output "execution_role_arn" {
  description = "Execution role ARN."
  value       = aws_iam_role.execution.arn
}

output "log_group_name" {
  description = "CloudWatch log group name."
  value       = aws_cloudwatch_log_group.this.name
}

output "security_group_id" {
  description = "Service task security group ID."
  value       = aws_security_group.this.id
}
