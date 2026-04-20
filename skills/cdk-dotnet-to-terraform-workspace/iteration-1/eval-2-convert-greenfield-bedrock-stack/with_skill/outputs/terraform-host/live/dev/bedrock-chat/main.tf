locals {
  common_tags = {
    Environment = var.environment
    Application = var.application
    CostCenter  = var.cost_center
    ManagedBy   = "terraform"
  }

  name_prefix = "${var.application}-${var.environment}"

  # Bedrock foundation-model ARNs. Region segment is populated; the account segment is
  # intentionally empty because foundation models are AWS-owned.
  # Source: CDK BedrockChatStack.cs `taskRole.AddToPolicy(...)` Resources array.
  bedrock_model_arns = [
    "arn:aws:bedrock:${var.region}::foundation-model/${var.claude_sonnet_model_id}",
    "arn:aws:bedrock:${var.region}::foundation-model/${var.claude_haiku_model_id}",
  ]
}

data "aws_region" "current" {}

# ---- Networking ----

module "network" {
  source = "../../../modules/network"

  name               = local.name_prefix
  cidr_block         = var.vpc_cidr
  availability_zones = var.availability_zones

  tags = local.common_tags
}

# ---- Bedrock runtime VPC endpoint ----
# Raw resources: the network module doesn't accept a variadic list of endpoints, so the
# bedrock-runtime interface endpoint and its security group live at the call site.
# Maps to CDK: vpc.AddInterfaceEndpoint("BedrockRuntimeEndpoint", ...) + BedrockEndpointSg.

resource "aws_security_group" "bedrock_endpoint" {
  name        = "${local.name_prefix}-bedrock-endpoint"
  description = "Allow Fargate tasks to reach the Bedrock runtime interface endpoint"
  vpc_id      = module.network.vpc_id
  tags        = merge(local.common_tags, { Name = "${local.name_prefix}-bedrock-endpoint" })
}

resource "aws_vpc_security_group_ingress_rule" "bedrock_endpoint_from_tasks" {
  security_group_id            = aws_security_group.bedrock_endpoint.id
  ip_protocol                  = "tcp"
  from_port                    = 443
  to_port                      = 443
  referenced_security_group_id = module.api_service.security_group_id
  description                  = "Fargate -> Bedrock endpoint"
}

resource "aws_vpc_endpoint" "bedrock_runtime" {
  vpc_id              = module.network.vpc_id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.bedrock-runtime"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = module.network.private_subnet_ids
  security_group_ids  = [aws_security_group.bedrock_endpoint.id]
  private_dns_enabled = true

  tags = merge(local.common_tags, { Name = "${local.name_prefix}-bedrock-runtime" })
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

resource "aws_lb_target_group" "api" {
  name        = "${local.name_prefix}-api"
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
# ECS cluster stays inline (matches the reference-service pattern). Container insights is
# set to "enhanced" to match the CDK stack's ContainerInsightsV2 = ContainerInsights.ENABLED.
# TODO: if cluster creation ever moves into a module, expose this as a variable there.

resource "aws_ecs_cluster" "this" {
  name = local.name_prefix

  setting {
    name  = "containerInsights"
    value = "enhanced"
  }

  tags = local.common_tags
}

module "api_service" {
  source = "../../../modules/ecs-service"

  service_name          = "${local.name_prefix}-api"
  cluster_arn           = aws_ecs_cluster.this.arn
  image                 = var.api_image
  cpu                   = var.task_cpu
  memory                = var.task_memory
  desired_count         = var.desired_count
  vpc_id                = module.network.vpc_id
  subnet_ids            = module.network.private_subnet_ids
  alb_security_group_id = module.alb.security_group_id
  target_group_arn      = aws_lb_target_group.api.arn
  container_port        = 8080

  environment_variables = {
    ASPNETCORE_ENVIRONMENT  = var.environment
    LOG_LEVEL               = "Information"
    BEDROCK_SONNET_MODEL_ID = var.claude_sonnet_model_id
    BEDROCK_HAIKU_MODEL_ID  = var.claude_haiku_model_id
  }

  tags = local.common_tags
}

# ---- Bedrock IAM policy on the task role ----
# CDK called taskRole.AddToPolicy(...) which CloudFormation rendered as an AWS::IAM::Policy
# attached to the task role. We attach the equivalent as an aws_iam_role_policy against the
# ecs-service module's task role (option 2 from the module's README).

data "aws_iam_policy_document" "bedrock_invoke" {
  statement {
    sid    = "InvokeClaudeModels"
    effect = "Allow"
    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream",
    ]
    resources = local.bedrock_model_arns
  }
}

resource "aws_iam_role_policy" "task_bedrock_invoke" {
  name   = "bedrock-invoke"
  role   = module.api_service.task_role_name
  policy = data.aws_iam_policy_document.bedrock_invoke.json
}
