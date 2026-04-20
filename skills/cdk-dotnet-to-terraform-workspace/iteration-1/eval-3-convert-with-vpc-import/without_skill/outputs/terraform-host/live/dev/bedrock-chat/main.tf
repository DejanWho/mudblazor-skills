data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}
data "aws_region" "current" {}

locals {
  name_prefix = "${var.application}-${var.environment}"

  common_tags = {
    Environment = var.environment
    Application = var.application
    CostCenter  = var.cost_center
    ManagedBy   = "terraform"
  }

  # Bedrock foundation-model ARNs scoped to the current region and partition.
  # Foundation-model ARNs are account-less (no account segment).
  claude_sonnet_arn = "arn:${data.aws_partition.current.partition}:bedrock:${data.aws_region.current.name}::foundation-model/${var.claude_sonnet_model_id}"
  claude_haiku_arn  = "arn:${data.aws_partition.current.partition}:bedrock:${data.aws_region.current.name}::foundation-model/${var.claude_haiku_model_id}"
}

# ---- Networking ----
# The VPC shell is already deployed; it is adopted via imports.tf. Subnets,
# IGW, NAT, and route tables are greenfield inside it.
module "network" {
  source = "../../../modules/network-imported"

  name               = local.name_prefix
  cidr_block         = var.vpc_cidr
  availability_zones = var.availability_zones

  tags = local.common_tags
}

# ---- ECS cluster ----
# CDK sets ContainerInsightsV2 = ENABLED (synthesised as "enhanced").
resource "aws_ecs_cluster" "this" {
  name = local.name_prefix

  setting {
    name  = "containerInsights"
    value = "enhanced"
  }

  tags = local.common_tags
}

# ---- ALB ----
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
    protocol            = "HTTP"
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

# ---- Fargate service ----
# Uses the shared ecs-service module. The module creates the task/exec roles
# and the task SG; we attach a Bedrock inline policy to the task role below.
module "api_service" {
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
  log_retention_days    = var.log_retention_days

  environment_variables = {
    ASPNETCORE_ENVIRONMENT  = var.environment
    LOG_LEVEL               = "Information"
    BEDROCK_SONNET_MODEL_ID = var.claude_sonnet_model_id
    BEDROCK_HAIKU_MODEL_ID  = var.claude_haiku_model_id
  }

  tags = local.common_tags
}

# Bedrock invocation permissions for the task role.
# The CDK stack attached these as a default inline policy on the task role.
data "aws_iam_policy_document" "bedrock_invoke" {
  statement {
    sid    = "InvokeClaudeModels"
    effect = "Allow"
    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream",
    ]
    resources = [
      local.claude_sonnet_arn,
      local.claude_haiku_arn,
    ]
  }
}

resource "aws_iam_role_policy" "task_bedrock" {
  name   = "bedrock-invoke"
  role   = module.api_service.task_role_name
  policy = data.aws_iam_policy_document.bedrock_invoke.json
}

# ---- Bedrock runtime VPC endpoint ----
# Keeps Bedrock traffic off the NAT gateways. The endpoint SG allows ingress
# from the Fargate task SG on 443.
module "bedrock_endpoint" {
  source = "../../../modules/bedrock-vpc-endpoint"

  name                      = local.name_prefix
  vpc_id                    = module.network.vpc_id
  subnet_ids                = module.network.private_subnet_ids
  client_security_group_ids = [module.api_service.security_group_id]

  tags = local.common_tags
}
