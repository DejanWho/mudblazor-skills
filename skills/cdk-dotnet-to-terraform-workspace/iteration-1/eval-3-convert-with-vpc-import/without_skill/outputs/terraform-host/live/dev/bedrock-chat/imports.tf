# Import the already-deployed VPC shell so that Terraform manages it
# without recreating it. The VPC was provisioned out-of-band (pre-existing
# from another team/stack); subnets, NAT, IGW, and route tables inside it
# are greenfield and managed by the `network-imported` module.
#
# Requires Terraform >= 1.5 for the `import` block syntax. After the first
# successful `terraform apply` (or `terraform plan -generate-config-out=...`
# if desired), this block may be removed; the resource will remain in state.
import {
  to = module.network.aws_vpc.this
  id = "vpc-0a1b2c3d4e5f6a7b8"
}
