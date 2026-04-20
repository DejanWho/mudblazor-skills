# network-imported

Companion to the `network` module for situations where the VPC shell already
exists (provisioned out-of-band by another team/stack) and must be adopted via
a Terraform `import` block, while subnets / NAT / IGW / route tables are
greenfield inside it.

The VPC is declared as a normal `aws_vpc` resource so the caller can point an
`import` block at `module.<this>.aws_vpc.this`. The remaining networking
(public + private subnets, IGW, NAT per AZ, route tables) is created fresh.

## Inputs

- `name` (string, required) - base name used in resource naming and tags.
- `cidr_block` (string, required) - VPC IPv4 CIDR. Must match the real VPC's
  CIDR so that `terraform import` produces a clean plan.
- `availability_zones` (list(string), required) - AZ names, one subnet of each
  tier per AZ.
- `tags` (map(string), default `{}`) - extra tags merged with module common
  tags.

## Outputs

- `vpc_id` - VPC ID.
- `vpc_cidr_block` - VPC CIDR.
- `public_subnet_ids` - list of public subnet IDs.
- `private_subnet_ids` - list of private subnet IDs.
- `default_security_group_id` - VPC default SG ID.

## Adopting the VPC

In the root config (Terraform 1.5+):

```hcl
import {
  to = module.network.aws_vpc.this
  id = "vpc-0a1b2c3d4e5f6a7b8"
}
```

The first `terraform plan` after adding the import block should show the VPC
as being adopted with no destructive changes. If the plan shows replacement
or significant attribute drift, reconcile the module inputs (most commonly
`cidr_block`, `enable_dns_hostnames`, `enable_dns_support`) with the real
VPC before applying.
