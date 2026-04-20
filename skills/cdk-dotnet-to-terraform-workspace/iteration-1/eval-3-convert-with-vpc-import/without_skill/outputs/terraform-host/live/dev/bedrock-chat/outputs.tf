output "vpc_id" {
  description = "ID of the (imported) VPC backing the bedrock-chat stack."
  value       = module.network.vpc_id
}

output "alb_dns_name" {
  description = "Public ALB DNS name (Route53 alias target for the chat endpoint)."
  value       = module.alb.alb_dns_name
}

output "alb_zone_id" {
  description = "Route53 zone ID the ALB can alias from."
  value       = module.alb.alb_zone_id
}

output "ecs_cluster_arn" {
  description = "ECS cluster ARN."
  value       = aws_ecs_cluster.this.arn
}

output "service_arn" {
  description = "ECS service ARN."
  value       = module.api_service.service_arn
}

output "task_role_arn" {
  description = "ARN of the Fargate task role (has Bedrock invoke permissions)."
  value       = module.api_service.task_role_arn
}

output "bedrock_endpoint_id" {
  description = "ID of the Bedrock runtime VPC interface endpoint."
  value       = module.bedrock_endpoint.endpoint_id
}
