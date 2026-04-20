# Module Inventory

Catalogue of modules in the host Terraform repo at `terraform-host/modules/`. Convert mode MUST consult this file before deciding to author a new module — if an existing module's inputs/outputs match what a CDK construct needs, reuse it.

Module path convention: `terraform-host/modules/<name>/`, consumed from a root config as `source = "../../../modules/<name>"`.

---

## `modules/network`

- **Purpose:** VPC with one public + one private subnet per AZ, an Internet Gateway, one EIP + NAT gateway per AZ (HA by default), and route tables per tier/AZ wired to IGW (public) or NAT (private).
- **Key inputs:** `name` (string, required), `cidr_block` (string, required), `availability_zones` (list(string), required), `tags` (map(string), default `{}`).
- **Key outputs:** `vpc_id`, `vpc_cidr_block`, `public_subnet_ids` (list), `private_subnet_ids` (list), `default_security_group_id`.
- **Matches CDK constructs:** `Amazon.CDK.AWS.EC2.Vpc` with public + private `SubnetConfiguration` across multiple AZs and NAT-per-AZ. Does NOT include intra/isolated subnets, VPC endpoints, or flow logs — add those at the call site or extend the module.
- **Notes:** Subnet CIDRs are computed via `cidrsubnet(var.cidr_block, 8, <index>)`; public subnets get the first N slots, private subnets take the next N (where N = `length(availability_zones)`). This means the caller doesn't pick subnet CIDRs directly — pick a large enough VPC CIDR. `map_public_ip_on_launch = true` on public subnets.

## `modules/alb`

- **Purpose:** Application Load Balancer with HTTPS listener (default 404 fixed-response), HTTP→HTTPS redirect listener, and a front-door security group. Target groups and listener rules are intentionally NOT created here — callers wire their own against the listener ARN.
- **Key inputs:** `name` (string, required), `vpc_id` (string, required), `public_subnet_ids` (list(string), required), `certificate_arn` (string, required), `allowed_cidr_blocks` (list(string), default `["0.0.0.0/0"]`), `internal` (bool, default `false`), `idle_timeout` (number, default `60`), `enable_deletion_protection` (bool, default `false`), `tags` (map(string), default `{}`).
- **Key outputs:** `alb_arn`, `alb_dns_name`, `alb_zone_id`, `https_listener_arn`, `security_group_id`.
- **Matches CDK constructs:** `Amazon.CDK.AWS.ElasticLoadBalancingV2.ApplicationLoadBalancer` with a standard 443 listener (cert from ACM) + 80→443 redirect. When the CDK stack also declares `ApplicationTargetGroup` + `AddAction`/`AddTargets`, those become `aws_lb_target_group` + `aws_lb_listener_rule` at the caller (see `live/dev/reference-service/main.tf` for the pattern).
- **Notes:** SSL policy is pinned to `ELBSecurityPolicy-TLS13-1-2-2021-06`. The module uses `aws_vpc_security_group_ingress_rule` / `_egress_rule` resources (NOT inline `ingress`/`egress` blocks) per repo convention. Services behind the ALB should allow ingress from `security_group_id` to reach their container port.

## `modules/ecs-service`

- **Purpose:** Fargate service + task definition attached to an existing ALB target group, with execution + task IAM roles, a task security group that allows ingress from an ALB SG, and a CloudWatch log group at `/ecs/<service_name>`. Does NOT create the ECS cluster, ALB, target group, or listener rule.
- **Key inputs:** `service_name` (string, required), `cluster_arn` (string, required), `image` (string, required), `vpc_id` (string, required), `subnet_ids` (list(string), required), `alb_security_group_id` (string, required), `target_group_arn` (string, required), `container_port` (number, default `8080`), `cpu` (number, default `512`), `memory` (number, default `1024`), `desired_count` (number, default `2`), `environment_variables` (map(string), default `{}`), `secret_arns` (map(string), default `{}`), `additional_task_role_policy_arns` (list(string), default `[]`), `log_retention_days` (number, default `30`), `tags` (map(string), default `{}`).
- **Key outputs:** `service_arn`, `service_name`, `task_definition_arn`, `task_role_arn`, `task_role_name`, `execution_role_arn`, `log_group_name`, `security_group_id`.
- **Matches CDK constructs:** `Amazon.CDK.AWS.ECS.FargateService` + `FargateTaskDefinition` + `AddContainer` + `RegisterLoadBalancerTargets` (or equivalent). Single-container tasks only. If the CDK stack uses `ApplicationLoadBalancedFargateService` (an L3 construct), split it: ALB via `modules/alb`, cluster as a raw `aws_ecs_cluster` in the root, target group + listener rule as raw resources in the root, Fargate service via this module.
- **Notes:** (1) `desired_count` changes are ignored via `lifecycle { ignore_changes = [desired_count] }` so autoscaling can adjust without Terraform fighting it. (2) Extra task permissions: prefer `additional_task_role_policy_arns`; otherwise attach `aws_iam_role_policy` at the caller using `task_role_name`. (3) `container_definitions` are built via `jsonencode(...)` in a `locals` block — that's why tags are plumbed explicitly (default_tags don't flow into the JSON payload). (4) `secret_arns` values must be Secrets Manager ARNs or SSM parameter ARNs — the execution role has the managed `AmazonECSTaskExecutionRolePolicy` attached, which grants read on both. (5) `assign_public_ip = false` — subnets must be private with NAT (use `module.network.private_subnet_ids`).

## `modules/iam-role`

- **Purpose:** Stand-alone IAM role with a caller-supplied trust policy JSON, managed-policy attachments, and keyed inline policies. Used for task roles, Lambda execution roles, service-linked roles, cross-account assume roles, etc.
- **Key inputs:** `name` (string, required), `trust_policy_json` (string, required), `managed_policy_arns` (list(string), default `[]`), `inline_policies` (map(string), default `{}` — key is policy name, value is policy JSON), `max_session_duration` (number, default `3600`), `tags` (map(string), default `{}`).
- **Key outputs:** `role_arn`, `role_name`, `role_id`.
- **Matches CDK constructs:** `Amazon.CDK.AWS.IAM.Role` — with `AddManagedPolicy` → `managed_policy_arns`, `AddToPolicy` / `AddInlinePolicy` → `inline_policies`, `AssumedBy` → `trust_policy_json`. Also a good fit for standalone service roles that the `ecs-service` module's built-in roles don't cover (e.g., a Bedrock-invoking task role whose permissions are complex enough to warrant a dedicated role — see the Bedrock pattern in the module's README).
- **Notes:** (1) Caller builds `trust_policy_json` either via `data.aws_iam_policy_document.<x>.json` (preferred) or `jsonencode(...)`. (2) This module does NOT create `aws_iam_instance_profile` — add that at the caller for EC2 instance-profile use cases. (3) `inline_policies` keys become the inline policy names — pick descriptive keys like `bedrock` or `s3_readonly`, not `inline-1`.

---

## Modules NOT present (but likely needed for future conversions)

The following types of modules do not exist yet. If a CDK stack needs them, author a new module in the same style (kebab-case dir, `main.tf`/`variables.tf`/`outputs.tf`/`versions.tf`/`README.md`, inline `locals.common_tags`, `"this"` resource labels, `_id`/`_arn` output suffixes) and add an entry above.

- `lambda` — Lambda function with execution role + log group + optional VPC attachment. Not yet authored.
- `rds` / `dynamodb` / `s3-bucket` — no stateful modules observed.
- `cloudfront` / `api-gateway` — no edge / API modules observed.
- `sqs` / `sns` / `eventbridge` — no messaging modules observed.
- `kms-key` — no standalone KMS module observed.
- `vpc-endpoint` — endpoints would be added inline today (the network module does not accept an endpoint list).

---

*This file was generated by `cdk-dotnet-to-terraform` init mode on 2026-04-20. Add entries here after authoring new modules during convert mode. Commit this file.*
