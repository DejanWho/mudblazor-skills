locals {
  common_tags = merge(
    var.tags,
    {
      Module = "bedrock-vpc-endpoint"
      Name   = var.name
    }
  )
}

data "aws_region" "current" {}

resource "aws_security_group" "this" {
  name        = "${var.name}-bedrock-endpoint"
  description = "Allow private clients to reach the Bedrock runtime interface endpoint"
  vpc_id      = var.vpc_id
  tags        = local.common_tags
}

resource "aws_vpc_security_group_ingress_rule" "client" {
  for_each                     = toset(var.client_security_group_ids)
  security_group_id            = aws_security_group.this.id
  ip_protocol                  = "tcp"
  from_port                    = 443
  to_port                      = 443
  referenced_security_group_id = each.value
  description                  = "HTTPS from client SG ${each.value}"
}

resource "aws_vpc_endpoint" "bedrock_runtime" {
  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.bedrock-runtime"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = var.subnet_ids
  security_group_ids  = [aws_security_group.this.id]
  private_dns_enabled = true

  tags = merge(local.common_tags, { Name = "${var.name}-bedrock-runtime" })
}
