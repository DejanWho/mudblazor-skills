output "alb_dns_name" {
  description = "Public ALB DNS name."
  value       = module.alb.alb_dns_name
}

output "ecs_cluster_arn" {
  description = "ECS cluster ARN."
  value       = aws_ecs_cluster.this.arn
}

output "api_service_arn" {
  description = "API service ARN."
  value       = module.api_service.service_arn
}
