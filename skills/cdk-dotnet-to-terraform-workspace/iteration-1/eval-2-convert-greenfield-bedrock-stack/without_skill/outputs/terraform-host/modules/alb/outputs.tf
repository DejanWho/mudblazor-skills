output "alb_arn" {
  description = "ARN of the ALB."
  value       = aws_lb.this.arn
}

output "alb_dns_name" {
  description = "ALB DNS name."
  value       = aws_lb.this.dns_name
}

output "alb_zone_id" {
  description = "Route53 zone ID the ALB can alias from."
  value       = aws_lb.this.zone_id
}

output "https_listener_arn" {
  description = "ARN of the HTTPS listener. Attach target groups / listener rules here."
  value       = aws_lb_listener.https.arn
}

output "security_group_id" {
  description = "Security group in front of the ALB. Services behind the ALB should allow ingress from this SG."
  value       = aws_security_group.this.id
}
