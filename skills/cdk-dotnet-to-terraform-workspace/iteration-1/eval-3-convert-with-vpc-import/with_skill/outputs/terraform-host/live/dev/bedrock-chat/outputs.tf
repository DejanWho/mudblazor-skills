output "alb_dns_name" {
  description = "Public ALB DNS name."
  value       = module.alb.alb_dns_name
}

output "ecs_cluster_arn" {
  description = "ECS cluster ARN."
  value       = aws_ecs_cluster.this.arn
}

output "api_service_arn" {
  description = "Bedrock chat API ECS service ARN."
  value       = module.api_service.service_arn
}

output "vpc_id" {
  description = "VPC ID (adopted via imports.tf)."
  value       = module.network.vpc_id
}

output "bedrock_runtime_endpoint_id" {
  description = "Bedrock runtime interface VPC endpoint ID."
  value       = aws_vpc_endpoint.bedrock_runtime.id
}
