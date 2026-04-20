output "alb_dns_name" {
  description = "Public ALB DNS name."
  value       = module.alb.alb_dns_name
}

output "alb_zone_id" {
  description = "ALB Route53 zone ID — alias target for the public hostname."
  value       = module.alb.alb_zone_id
}

output "ecs_cluster_arn" {
  description = "ECS cluster ARN."
  value       = aws_ecs_cluster.this.arn
}

output "service_arn" {
  description = "ECS service ARN."
  value       = module.app_service.service_arn
}

output "task_role_arn" {
  description = "Task role ARN used by the Fargate tasks."
  value       = module.app_service.task_role_arn
}

output "bedrock_runtime_endpoint_id" {
  description = "VPC interface endpoint ID for Bedrock runtime."
  value       = aws_vpc_endpoint.bedrock_runtime.id
}

output "bedrock_runtime_endpoint_security_group_id" {
  description = "Security group ID guarding the Bedrock runtime interface endpoint."
  value       = aws_security_group.bedrock_endpoint.id
}
