output "alb_dns_name" {
  description = "Public ALB DNS name. Maps to CDK CfnOutput `AlbDnsName`."
  value       = module.alb.alb_dns_name
}

output "ecs_cluster_arn" {
  description = "ECS cluster ARN."
  value       = aws_ecs_cluster.this.arn
}

output "service_arn" {
  description = "ECS service ARN. Maps to CDK CfnOutput `ServiceArn`."
  value       = module.api_service.service_arn
}

output "vpc_id" {
  description = "VPC ID (useful for downstream configs that share the network)."
  value       = module.network.vpc_id
}

output "bedrock_runtime_endpoint_id" {
  description = "Interface VPC endpoint ID for bedrock-runtime."
  value       = aws_vpc_endpoint.bedrock_runtime.id
}

output "task_role_arn" {
  description = "Task role ARN with bedrock:InvokeModel / InvokeModelWithResponseStream inline."
  value       = module.api_service.task_role_arn
}
