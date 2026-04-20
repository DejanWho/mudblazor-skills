locals {
  common_tags = {
    Environment = var.environment
    Application = var.application
    CostCenter  = var.cost_center
    ManagedBy   = "terraform"
  }

  service_name = "${var.application}-${var.environment}"
}

data "aws_region" "current" {}

# ---- Networking ----
# The VPC already exists and is adopted via imports.tf.
# Subnets / NAT / route tables are provisioned here greenfield unless the user
# adds more import blocks (see imports.tf and SUMMARY.md for guidance).
module "network" {
  source = "../../../modules/network"

  name               = local.service_name
  cidr_block         = var.vpc_cidr
  availability_zones = var.availability_zones

  tags = local.common_tags
}

# Security group for the Bedrock interface endpoint. Fargate tasks reach the
# endpoint on 443; the endpoint does not need outbound rules.
resource "aws_security_group" "bedrock_endpoint" {
  name        = "${local.service_name}-bedrock-endpoint"
  description = "Allow Fargate tasks to reach the Bedrock runtime interface endpoint"
  vpc_id      = module.network.vpc_id
  tags        = merge(local.common_tags, { Name = "${local.service_name}-bedrock-endpoint" })
}

resource "aws_vpc_security_group_ingress_rule" "bedrock_endpoint_from_tasks" {
  security_group_id            = aws_security_group.bedrock_endpoint.id
  ip_protocol                  = "tcp"
  from_port                    = 443
  to_port                      = 443
  referenced_security_group_id = module.api_service.security_group_id
  description                  = "Fargate tasks -> Bedrock endpoint"
}

# Bedrock runtime interface endpoint so traffic stays inside the VPC rather
# than traversing NAT.
resource "aws_vpc_endpoint" "bedrock_runtime" {
  vpc_id              = module.network.vpc_id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.bedrock-runtime"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = module.network.private_subnet_ids
  security_group_ids  = [aws_security_group.bedrock_endpoint.id]
  private_dns_enabled = true

  tags = merge(local.common_tags, { Name = "${local.service_name}-bedrock-runtime" })
}

# ---- Load balancing ----
module "alb" {
  source = "../../../modules/alb"

  name              = local.service_name
  vpc_id            = module.network.vpc_id
  public_subnet_ids = module.network.public_subnet_ids
  certificate_arn   = var.certificate_arn

  tags = local.common_tags
}

resource "aws_lb_target_group" "api" {
  name        = "${local.service_name}-api"
  port        = 8080
  protocol    = "HTTP"
  vpc_id      = module.network.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    path                = "/health"
    matcher             = "200"
    interval            = 30
    timeout             = 10
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }

  tags = local.common_tags
}

resource "aws_lb_listener_rule" "api" {
  listener_arn = module.alb.https_listener_arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }

  condition {
    path_pattern {
      values = ["/*"]
    }
  }

  tags = local.common_tags
}

# ---- Compute ----
resource "aws_ecs_cluster" "this" {
  name = local.service_name

  setting {
    name  = "containerInsights"
    value = "enhanced"
  }

  tags = local.common_tags
}

module "api_service" {
  source = "../../../modules/ecs-service"

  service_name          = local.service_name
  cluster_arn           = aws_ecs_cluster.this.arn
  image                 = var.api_image
  cpu                   = 1024
  memory                = 2048
  vpc_id                = module.network.vpc_id
  subnet_ids            = module.network.private_subnet_ids
  alb_security_group_id = module.alb.security_group_id
  target_group_arn      = aws_lb_target_group.api.arn

  environment_variables = {
    ASPNETCORE_ENVIRONMENT  = var.environment
    LOG_LEVEL               = "Information"
    BEDROCK_SONNET_MODEL_ID = var.claude_sonnet_model_id
    BEDROCK_HAIKU_MODEL_ID  = var.claude_haiku_model_id
  }

  tags = local.common_tags
}

# Task role Bedrock invoke policy. CDK's taskRole.AddToPolicy(...) becomes a
# caller-side aws_iam_role_policy referencing the module's task role.
data "aws_iam_policy_document" "bedrock_invoke" {
  statement {
    effect = "Allow"
    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream",
    ]
    resources = [
      "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/${var.claude_sonnet_model_id}",
      "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/${var.claude_haiku_model_id}",
    ]
  }
}

resource "aws_iam_role_policy" "bedrock_invoke" {
  name   = "bedrock-invoke"
  role   = module.api_service.task_role_name
  policy = data.aws_iam_policy_document.bedrock_invoke.json
}
