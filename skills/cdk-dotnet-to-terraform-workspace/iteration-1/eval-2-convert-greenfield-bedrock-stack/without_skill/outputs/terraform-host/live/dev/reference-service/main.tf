locals {
  common_tags = {
    Environment = var.environment
    Application = var.application
    CostCenter  = var.cost_center
    ManagedBy   = "terraform"
  }
}

module "network" {
  source = "../../../modules/network"

  name               = "${var.application}-${var.environment}"
  cidr_block         = var.vpc_cidr
  availability_zones = var.availability_zones

  tags = local.common_tags
}

module "alb" {
  source = "../../../modules/alb"

  name              = "${var.application}-${var.environment}"
  vpc_id            = module.network.vpc_id
  public_subnet_ids = module.network.public_subnet_ids
  certificate_arn   = var.certificate_arn

  tags = local.common_tags
}

resource "aws_ecs_cluster" "this" {
  name = "${var.application}-${var.environment}"
  tags = local.common_tags
}

resource "aws_lb_target_group" "api" {
  name        = "${var.application}-${var.environment}-api"
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

module "api_service" {
  source = "../../../modules/ecs-service"

  service_name          = "${var.application}-${var.environment}-api"
  cluster_arn           = aws_ecs_cluster.this.arn
  image                 = var.api_image
  vpc_id                = module.network.vpc_id
  subnet_ids            = module.network.private_subnet_ids
  alb_security_group_id = module.alb.security_group_id
  target_group_arn      = aws_lb_target_group.api.arn

  environment_variables = {
    ASPNETCORE_ENVIRONMENT = var.environment
    LOG_LEVEL              = "Information"
  }

  tags = local.common_tags
}
