# Terraform >= 1.5 import blocks for pre-deployed resources.
#
# Scope: the VPC is already deployed and must not be recreated. Everything else
# in this stack (ALB, Fargate service, Bedrock IAM, Bedrock VPC endpoint) is
# greenfield and is not imported.
#
# IMPORTANT: the `modules/network` module also creates subnets, an internet
# gateway, per-AZ NAT gateways + EIPs, and public/private route tables with
# associations. The user has said only the VPC is a known pre-existing resource
# with its physical ID; the rest of the networking resources were described as
# "treat as also needing imports OR note that IDs aren't known". The pragmatic
# choice taken here is to ONLY import the VPC and leave the rest as greenfield
# creates inside the module. If the user's deployed VPC already has subnets /
# NAT / route tables attached, the first plan will try to create fresh copies
# of those, which is almost certainly not what they want. See SUMMARY.md for
# the follow-up actions (either fill in physical IDs for the remaining
# networking resources as additional import blocks below, OR decide to let
# Terraform build its own new subnets / NATs and manually detach / clean up the
# originals outside Terraform).
#
# The remaining networking resources inside the `network` module use `for_each`
# keyed by AZ name. If / when the physical IDs are known, the import address
# syntax is e.g.:
#
#   import {
#     to = module.network.aws_subnet.public["eu-central-1a"]
#     id = "subnet-0abc..."
#   }

# From CDK: BedrockChatStack-dev/Vpc
import {
  to = module.network.aws_vpc.this
  id = "vpc-0a1b2c3d4e5f6a7b8"
}

# ---------------------------------------------------------------------------
# Scaffold for the rest of modules/network — uncomment and fill in physical IDs.
# Remove the scaffold once the real IDs are in place.
# ---------------------------------------------------------------------------

# import {
#   to = module.network.aws_subnet.public["eu-central-1a"]
#   id = "subnet-FILL_ME_IN"
# }
# import {
#   to = module.network.aws_subnet.public["eu-central-1b"]
#   id = "subnet-FILL_ME_IN"
# }
# import {
#   to = module.network.aws_subnet.public["eu-central-1c"]
#   id = "subnet-FILL_ME_IN"
# }
# import {
#   to = module.network.aws_subnet.private["eu-central-1a"]
#   id = "subnet-FILL_ME_IN"
# }
# import {
#   to = module.network.aws_subnet.private["eu-central-1b"]
#   id = "subnet-FILL_ME_IN"
# }
# import {
#   to = module.network.aws_subnet.private["eu-central-1c"]
#   id = "subnet-FILL_ME_IN"
# }
#
# import {
#   to = module.network.aws_internet_gateway.this
#   id = "igw-FILL_ME_IN"
# }
#
# import {
#   to = module.network.aws_eip.nat["eu-central-1a"]
#   id = "eipalloc-FILL_ME_IN"
# }
# import {
#   to = module.network.aws_eip.nat["eu-central-1b"]
#   id = "eipalloc-FILL_ME_IN"
# }
# import {
#   to = module.network.aws_eip.nat["eu-central-1c"]
#   id = "eipalloc-FILL_ME_IN"
# }
#
# import {
#   to = module.network.aws_nat_gateway.this["eu-central-1a"]
#   id = "nat-FILL_ME_IN"
# }
# import {
#   to = module.network.aws_nat_gateway.this["eu-central-1b"]
#   id = "nat-FILL_ME_IN"
# }
# import {
#   to = module.network.aws_nat_gateway.this["eu-central-1c"]
#   id = "nat-FILL_ME_IN"
# }
#
# import {
#   to = module.network.aws_route_table.public
#   id = "rtb-FILL_ME_IN"
# }
# import {
#   to = module.network.aws_route_table.private["eu-central-1a"]
#   id = "rtb-FILL_ME_IN"
# }
# import {
#   to = module.network.aws_route_table.private["eu-central-1b"]
#   id = "rtb-FILL_ME_IN"
# }
# import {
#   to = module.network.aws_route_table.private["eu-central-1c"]
#   id = "rtb-FILL_ME_IN"
# }
#
# # Route table associations import by "<subnet-id>/<route-table-id>".
# import {
#   to = module.network.aws_route_table_association.public["eu-central-1a"]
#   id = "subnet-FILL_ME_IN/rtb-FILL_ME_IN"
# }
# ... (repeat per AZ for both public and private associations)
