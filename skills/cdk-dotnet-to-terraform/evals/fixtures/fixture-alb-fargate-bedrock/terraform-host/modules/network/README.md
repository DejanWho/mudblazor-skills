# network

VPC with public + private subnets across configurable AZs. One NAT gateway per AZ (HA by default).

## Inputs

- `name` (string, required) — base name used in resource naming and tags.
- `cidr_block` (string, required) — VPC IPv4 CIDR.
- `availability_zones` (list(string), required) — AZ names, one subnet of each tier per AZ.
- `tags` (map(string), default `{}`) — extra tags merged with module-managed common tags.

## Outputs

- `vpc_id` — VPC ID.
- `vpc_cidr_block` — VPC CIDR.
- `public_subnet_ids` — list of public subnet IDs.
- `private_subnet_ids` — list of private subnet IDs.
- `default_security_group_id` — VPC default SG ID.
