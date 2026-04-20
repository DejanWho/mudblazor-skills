# alb

Application load balancer with HTTPS listener (default 404), HTTP→HTTPS redirect, and a front security group. Target groups and listener rules are intentionally outside this module — services wire their own.

## Inputs

- `name` (string, required) — ALB name and tag base.
- `vpc_id` (string, required) — VPC the ALB lives in.
- `public_subnet_ids` (list(string), required) — public subnets the ALB attaches to.
- `certificate_arn` (string, required) — ACM cert for the HTTPS listener.
- `allowed_cidr_blocks` (list(string), default `["0.0.0.0/0"]`) — client CIDR blocks allowed in.
- `internal` (bool, default `false`) — set `true` for private ALBs.
- `idle_timeout` (number, default `60`) — ALB idle timeout.
- `enable_deletion_protection` (bool, default `false`) — set `true` for prod.
- `tags` (map(string), default `{}`) — extra tags merged with module common tags.

## Outputs

- `alb_arn`, `alb_dns_name`, `alb_zone_id` — ALB identifiers.
- `https_listener_arn` — listener ARN; attach target groups here.
- `security_group_id` — ALB's SG. Services allow ingress from this SG.
