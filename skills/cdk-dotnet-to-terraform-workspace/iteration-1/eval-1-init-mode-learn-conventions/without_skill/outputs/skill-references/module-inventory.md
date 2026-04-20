# terraform-host — Module Inventory

Inventory of every module under `modules/` plus the reference live config under `live/dev/reference-service/`. For each, the purpose, required vs optional inputs, and all outputs.

---

## Module: `network`

**Path:** `modules/network/`

**Purpose:** VPC with public and private subnets spread across configurable availability zones. Provisions an Internet Gateway, one NAT Gateway per AZ (HA by default), public + private route tables, and the associated route-table associations and EIPs.

**Resources created:**
- `aws_vpc.this`
- `aws_subnet.public` (one per AZ, `for_each`)
- `aws_subnet.private` (one per AZ, `for_each`)
- `aws_internet_gateway.this`
- `aws_eip.nat` (one per public subnet)
- `aws_nat_gateway.this` (one per public subnet)
- `aws_route_table.public`
- `aws_route_table.private` (one per private subnet)
- `aws_route_table_association.public` (one per public subnet)
- `aws_route_table_association.private` (one per private subnet)

### Inputs

| Name                 | Type           | Required | Default | Description                                                      |
|----------------------|----------------|----------|---------|------------------------------------------------------------------|
| `name`               | `string`       | yes      | —       | Base name used for resource naming and tagging.                  |
| `cidr_block`         | `string`       | yes      | —       | IPv4 CIDR block for the VPC.                                     |
| `availability_zones` | `list(string)` | yes      | —       | List of AZ names to spread public + private subnets across.      |
| `tags`               | `map(string)`  | no       | `{}`    | Extra tags merged with module-managed `common_tags`.             |

### Outputs

| Name                        | Description                                 |
|-----------------------------|---------------------------------------------|
| `vpc_id`                    | ID of the created VPC.                      |
| `vpc_cidr_block`            | CIDR block of the created VPC.              |
| `public_subnet_ids`         | List of public subnet IDs, one per AZ.      |
| `private_subnet_ids`        | List of private subnet IDs, one per AZ.    |
| `default_security_group_id` | VPC default security group ID.              |

### Subnet sizing

Subnets are derived via `cidrsubnet(var.cidr_block, 8, <idx>)`. Public subnets use indices `0 .. n-1`; private subnets use indices `n .. 2n-1` where `n = length(var.availability_zones)`. That gives `/24` subnets inside a `/16` VPC.

---

## Module: `alb`

**Path:** `modules/alb/`

**Purpose:** Application Load Balancer with HTTPS listener (default 404 fixed response), HTTP-to-HTTPS redirect listener, and a front-facing security group. Target groups and listener rules are deliberately left to the caller so one ALB can host many services.

**Resources created:**
- `aws_security_group.this` (ALB front SG)
- `aws_vpc_security_group_ingress_rule.https` (one per allowed CIDR, `for_each`)
- `aws_vpc_security_group_ingress_rule.http_redirect` (one per allowed CIDR, `for_each`)
- `aws_vpc_security_group_egress_rule.all`
- `aws_lb.this`
- `aws_lb_listener.https` (default action: 404 text fixed-response)
- `aws_lb_listener.http_redirect` (default action: 301 to HTTPS)

### Inputs

| Name                         | Type           | Required | Default           | Description                                                   |
|------------------------------|----------------|----------|-------------------|---------------------------------------------------------------|
| `name`                       | `string`       | yes      | —                 | ALB name and base for tagging/naming dependent resources.     |
| `vpc_id`                     | `string`       | yes      | —                 | VPC the ALB lives in.                                         |
| `public_subnet_ids`          | `list(string)` | yes      | —                 | Public subnet IDs the ALB attaches to.                        |
| `certificate_arn`            | `string`       | yes      | —                 | ACM certificate ARN for the HTTPS listener.                   |
| `allowed_cidr_blocks`        | `list(string)` | no       | `["0.0.0.0/0"]`   | Client CIDR blocks allowed to reach the ALB.                  |
| `internal`                   | `bool`         | no       | `false`           | Whether the ALB is internal vs internet-facing.               |
| `idle_timeout`               | `number`       | no       | `60`              | ALB idle timeout in seconds.                                  |
| `enable_deletion_protection` | `bool`         | no       | `false`           | Enable deletion protection on the ALB.                        |
| `tags`                       | `map(string)`  | no       | `{}`              | Extra tags merged with module common_tags.                    |

### Outputs

| Name                 | Description                                                                    |
|----------------------|--------------------------------------------------------------------------------|
| `alb_arn`            | ARN of the ALB.                                                                |
| `alb_dns_name`       | ALB DNS name.                                                                  |
| `alb_zone_id`        | Route53 zone ID the ALB can alias from.                                        |
| `https_listener_arn` | ARN of the HTTPS listener — attach target groups / listener rules here.        |
| `security_group_id`  | Security group in front of the ALB. Services should allow ingress from this SG.|

### Design choices

- SSL policy pinned to `ELBSecurityPolicy-TLS13-1-2-2021-06`.
- HTTPS listener default is a 404 fixed response, forcing callers to explicitly attach listener rules.
- HTTP listener is redirect-only (`HTTP_301` to port 443).

---

## Module: `ecs-service`

**Path:** `modules/ecs-service/`

**Purpose:** A Fargate service behind an existing ALB target group. Provisions the task definition, ECS service, execution IAM role (with the managed `AmazonECSTaskExecutionRolePolicy`), task IAM role (for app-level permissions), CloudWatch log group, and task security group. Does **not** create the cluster, ALB, or target group — those are inputs.

**Resources created:**
- `data.aws_region.current`
- `aws_cloudwatch_log_group.this` at path `/ecs/<service_name>`
- `aws_security_group.this` (task SG)
- `aws_vpc_security_group_ingress_rule.from_alb` (container port from ALB SG)
- `aws_vpc_security_group_egress_rule.all`
- `aws_iam_role.execution`
- `aws_iam_role_policy_attachment.execution_managed` (attaches `AmazonECSTaskExecutionRolePolicy`)
- `aws_iam_role.task`
- `aws_iam_role_policy_attachment.task_additional` (one per entry in `additional_task_role_policy_arns`)
- `aws_ecs_task_definition.this`
- `aws_ecs_service.this` (lifecycle ignores `desired_count`)

### Inputs

| Name                               | Type           | Required | Default | Description                                                         |
|------------------------------------|----------------|----------|---------|---------------------------------------------------------------------|
| `service_name`                     | `string`       | yes      | —       | Service name — used for naming resources and tagging.               |
| `cluster_arn`                      | `string`       | yes      | —       | ARN of the ECS cluster to run the service in.                       |
| `image`                            | `string`       | yes      | —       | Container image URI.                                                |
| `vpc_id`                           | `string`       | yes      | —       | VPC ID the service lives in.                                        |
| `subnet_ids`                       | `list(string)` | yes      | —       | Subnet IDs for the Fargate tasks (typically private).               |
| `alb_security_group_id`            | `string`       | yes      | —       | ALB security group ID — task SG ingress allows traffic from this SG.|
| `target_group_arn`                 | `string`       | yes      | —       | Target group ARN the service registers against.                     |
| `cpu`                              | `number`       | no       | `512`   | Fargate task CPU units.                                             |
| `memory`                           | `number`       | no       | `1024`  | Fargate task memory (MiB).                                          |
| `desired_count`                    | `number`       | no       | `2`     | Desired task count. Ignored in lifecycle for autoscaler compat.     |
| `container_port`                   | `number`       | no       | `8080`  | Container port the service listens on.                              |
| `environment_variables`            | `map(string)`  | no       | `{}`    | Environment variables for the container (key → value).              |
| `secret_arns`                      | `map(string)`  | no       | `{}`    | Secret env vars (key → Secrets Manager or SSM parameter ARN).       |
| `additional_task_role_policy_arns` | `list(string)` | no       | `[]`    | Additional managed/customer policy ARNs attached to the task role.  |
| `log_retention_days`               | `number`       | no       | `30`    | CloudWatch log group retention (days).                              |
| `tags`                             | `map(string)`  | no       | `{}`    | Extra tags merged with module common_tags.                          |

### Outputs

| Name                  | Description                                                                              |
|-----------------------|------------------------------------------------------------------------------------------|
| `service_arn`         | ARN of the ECS service (actually the `.id`, which is the ARN for `aws_ecs_service`).     |
| `service_name`        | Name of the ECS service.                                                                 |
| `task_definition_arn` | ARN of the task definition (specific revision).                                          |
| `task_role_arn`       | Task role ARN.                                                                           |
| `task_role_name`      | Task role name — useful for `aws_iam_role_policy` attachment at the caller.              |
| `execution_role_arn`  | Execution role ARN.                                                                      |
| `log_group_name`      | CloudWatch log group name.                                                               |
| `security_group_id`   | Service task security group ID.                                                          |

### Extending task permissions (per module README)

Three paths, preferred order:
1. Attach a managed/customer policy via `additional_task_role_policy_arns`.
2. Attach an `aws_iam_role_policy` at the caller, using `task_role_name` as the role.
3. Use the stand-alone `iam-role` module for complex inline-policy cases.

---

## Module: `iam-role`

**Path:** `modules/iam-role/`

**Purpose:** Stand-alone IAM role with a trust policy, optional managed-policy attachments, and optional named inline policies. Intended for task roles, Lambda execution roles, service-linked roles, etc.

**Resources created:**
- `aws_iam_role.this`
- `aws_iam_role_policy_attachment.managed` (one per entry in `managed_policy_arns`)
- `aws_iam_role_policy.inline` (one per entry in `inline_policies`, keyed by policy name)

### Inputs

| Name                   | Type          | Required | Default | Description                                                              |
|------------------------|---------------|----------|---------|--------------------------------------------------------------------------|
| `name`                 | `string`      | yes      | —       | Role name.                                                               |
| `trust_policy_json`    | `string`      | yes      | —       | Trust policy as JSON. Prefer `data.aws_iam_policy_document.<x>.json`.   |
| `managed_policy_arns`  | `list(string)`| no       | `[]`    | Managed policies to attach.                                              |
| `inline_policies`      | `map(string)` | no       | `{}`    | Inline policies, keyed by policy name. Value is the policy JSON.        |
| `max_session_duration` | `number`      | no       | `3600`  | Max session duration in seconds.                                         |
| `tags`                 | `map(string)` | no       | `{}`    | Extra tags merged with module common_tags.                               |

### Outputs

| Name        | Description       |
|-------------|-------------------|
| `role_arn`  | ARN of the role.  |
| `role_name` | Name of the role. |
| `role_id`   | ID of the role.   |

### Usage pattern (from module README)

```hcl
data "aws_iam_policy_document" "bedrock_trust" { ... }
data "aws_iam_policy_document" "bedrock_invoke" { ... }

module "task_role" {
  source            = "../../modules/iam-role"
  name              = "${var.service_name}-task"
  trust_policy_json = data.aws_iam_policy_document.bedrock_trust.json
  inline_policies = {
    bedrock = data.aws_iam_policy_document.bedrock_invoke.json
  }
  tags = local.tags
}
```

---

## Live Config: `live/dev/reference-service`

**Path:** `live/dev/reference-service/`

**Purpose:** Reference stack that wires `network`, `alb`, and `ecs-service` modules together with a root-level ECS cluster, a target group, and a listener rule to expose an API service behind an HTTPS ALB.

**Composition:**
- `module.network` — VPC named `${application}-${environment}`.
- `module.alb` — ALB attached to the VPC's public subnets, terminated with `var.certificate_arn`.
- `aws_ecs_cluster.this` — root-level cluster (not a module).
- `aws_lb_target_group.api` — target group on port 8080 with `/health` health check (type `ip` for Fargate).
- `aws_lb_listener_rule.api` — priority 100, path pattern `/*`, forwards to the API target group.
- `module.api_service` — Fargate API service behind the target group, with `ASPNETCORE_ENVIRONMENT` + `LOG_LEVEL` env vars.

### Inputs (root variables)

| Name                 | Type           | Required | Default                                                    | Description                                   |
|----------------------|----------------|----------|------------------------------------------------------------|-----------------------------------------------|
| `environment`        | `string`       | no       | `"dev"`                                                    | Environment name (dev / stg / prd).           |
| `application`        | `string`       | no       | `"reference"`                                              | Application name — drives resource naming.    |
| `cost_center`        | `string`       | yes      | —                                                          | Cost center tag.                              |
| `vpc_cidr`           | `string`       | no       | `"10.20.0.0/16"`                                           | VPC CIDR block.                               |
| `availability_zones` | `list(string)` | no       | `["eu-central-1a", "eu-central-1b", "eu-central-1c"]`      | AZs to spread subnets across.                 |
| `certificate_arn`    | `string`       | yes      | —                                                          | ACM cert ARN for the ALB HTTPS listener.      |
| `api_image`          | `string`       | yes      | —                                                          | Container image URI for the API service.      |

### Outputs (root)

| Name              | Description           |
|-------------------|-----------------------|
| `alb_dns_name`    | Public ALB DNS name.  |
| `ecs_cluster_arn` | ECS cluster ARN.      |
| `api_service_arn` | API service ARN.      |

### Backend + provider

- Backend `s3`, key `dev/reference-service/terraform.tfstate`, rest supplied at init-time.
- Provider region `eu-central-1`.
- `default_tags` set to `{ Environment = "dev", Application = "reference", ManagedBy = "terraform" }`.
- `local.common_tags` adds `CostCenter` (from variable) and is passed into every module call.

---

## Summary Table

| Module         | Purpose                                        | Req. inputs                                                                                                                                       | Key outputs                                                                               |
|----------------|------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| `network`      | VPC + public/private subnets + NAT + routes    | `name`, `cidr_block`, `availability_zones`                                                                                                        | `vpc_id`, `vpc_cidr_block`, `public_subnet_ids`, `private_subnet_ids`, `default_security_group_id` |
| `alb`          | Public ALB + HTTPS listener + HTTP→HTTPS + SG  | `name`, `vpc_id`, `public_subnet_ids`, `certificate_arn`                                                                                          | `alb_arn`, `alb_dns_name`, `alb_zone_id`, `https_listener_arn`, `security_group_id`       |
| `ecs-service`  | Fargate service + roles + log group + task SG  | `service_name`, `cluster_arn`, `image`, `vpc_id`, `subnet_ids`, `alb_security_group_id`, `target_group_arn`                                       | `service_arn`, `service_name`, `task_definition_arn`, `task_role_arn`, `task_role_name`, `execution_role_arn`, `log_group_name`, `security_group_id` |
| `iam-role`     | Stand-alone IAM role + policies                | `name`, `trust_policy_json`                                                                                                                       | `role_arn`, `role_name`, `role_id`                                                        |
