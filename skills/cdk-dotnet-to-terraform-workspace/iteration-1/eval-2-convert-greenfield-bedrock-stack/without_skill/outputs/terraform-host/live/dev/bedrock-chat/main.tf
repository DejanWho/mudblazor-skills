locals {
  name_prefix = "${var.application}-${var.environment}"

  common_tags = {
    Environment = var.environment
    Application = var.application
    CostCenter  = var.cost_center
    ManagedBy   = "terraform"
  }

  claude_sonnet_model_arn = "arn:aws:bedrock:${var.region}::foundation-model/${var.claude_sonnet_model_id}"
  claude_haiku_model_arn  = "arn:aws:bedrock:${var.region}::foundation-model/${var.claude_haiku_model_id}"
}

# ---- Networking ----
module "network" {
  source = "../../../modules/network"

  name               = local.name_prefix
  cidr_block         = var.vpc_cidr
  availability_zones = var.availability_zones

  tags = local.common_tags
}

# ---- Load balancing ----
module "alb" {
  source = "../../../modules/alb"

  name              = local.name_prefix
  vpc_id            = module.network.vpc_id
  public_subnet_ids = module.network.public_subnet_ids
  certificate_arn   = var.certificate_arn

  tags = local.common_tags
}

resource "aws_lb_target_group" "app" {
  name        = "${local.name_prefix}-app"
  port        = var.container_port
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

resource "aws_lb_listener_rule" "app" {
  listener_arn = module.alb.https_listener_arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
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
  name = local.name_prefix

  setting {
    name  = "containerInsights"
    value = "enhanced"
  }

  tags = local.common_tags
}

module "app_service" {
  source = "../../../modules/ecs-service"

  service_name          = local.name_prefix
  cluster_arn           = aws_ecs_cluster.this.arn
  image                 = var.container_image
  cpu                   = var.task_cpu
  memory                = var.task_memory
  desired_count         = var.desired_count
  vpc_id                = module.network.vpc_id
  subnet_ids            = module.network.private_subnet_ids
  alb_security_group_id = module.alb.security_group_id
  target_group_arn      = aws_lb_target_group.app.arn
  container_port        = var.container_port

  environment_variables = {
    ASPNETCORE_ENVIRONMENT  = var.environment
    LOG_LEVEL               = "Information"
    BEDROCK_SONNET_MODEL_ID = var.claude_sonnet_model_id
    BEDROCK_HAIKU_MODEL_ID  = var.claude_haiku_model_id
  }

  tags = local.common_tags
}

# ---- Bedrock runtime VPC interface endpoint ----
# Keep Bedrock traffic inside the VPC so it doesn't traverse the NAT gateway.
resource "aws_security_group" "bedrock_endpoint" {
  name        = "${local.name_prefix}-bedrock-endpoint"
  description = "Allow Fargate tasks to reach the Bedrock runtime interface endpoint"
  vpc_id      = module.network.vpc_id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-bedrock-endpoint"
  })
}

resource "aws_vpc_security_group_ingress_rule" "bedrock_endpoint_from_tasks" {
  security_group_id            = aws_security_group.bedrock_endpoint.id
  ip_protocol                  = "tcp"
  from_port                    = 443
  to_port                      = 443
  referenced_security_group_id = module.app_service.security_group_id
  description                  = "Fargate tasks → Bedrock runtime endpoint"
}

resource "aws_vpc_endpoint" "bedrock_runtime" {
  vpc_id              = module.network.vpc_id
  service_name        = "com.amazonaws.${var.region}.bedrock-runtime"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = module.network.private_subnet_ids
  security_group_ids  = [aws_security_group.bedrock_endpoint.id]
  private_dns_enabled = true

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-bedrock-runtime"
  })
}

# ---- Task role: Bedrock invoke permissions ----
# Scoped to Claude 3.5 Sonnet and Claude 3 Haiku foundation models. Attached
# to the task role created by the ecs-service module.
data "aws_iam_policy_document" "bedrock_invoke" {
  statement {
    sid    = "InvokeClaudeModels"
    effect = "Allow"
    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream",
    ]
    resources = [
      local.claude_sonnet_model_arn,
      local.claude_haiku_model_arn,
    ]
  }
}

resource "aws_iam_role_policy" "bedrock_invoke" {
  name   = "bedrock-invoke"
  role   = module.app_service.task_role_name
  policy = data.aws_iam_policy_document.bedrock_invoke.json
}
