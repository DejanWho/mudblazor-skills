# terraform-host — Repository Conventions

This document describes the conventions observed in the `terraform-host/` repo, derived from walking every file under `modules/` and `live/dev/reference-service/`. Anything produced by CDK-to-Terraform conversion must conform to these conventions to merge cleanly.

## 1. Directory Layout

```
terraform-host/
├── README.md
├── modules/
│   ├── alb/
│   ├── ecs-service/
│   ├── iam-role/
│   └── network/
└── live/
    └── <env>/                 # e.g. dev, stg, prd
        └── <app>/             # e.g. reference-service
            ├── main.tf
            ├── outputs.tf
            ├── variables.tf
            └── versions.tf
```

- **`modules/`** — reusable, single-purpose modules. One directory per module.
- **`live/<env>/<app>/`** — root configs that compose modules into a deployable stack. `<env>` is the environment (dev / stg / prd) and `<app>` is the application name.
- **`README.md` at repo root** — documents conventions at a glance and how CDK conversions are intended to land in the tree.

## 2. Per-Module File Layout

Every module contains **exactly** these five files:

| File           | Purpose                                                                  |
|----------------|--------------------------------------------------------------------------|
| `main.tf`      | Resources, `locals`, data sources.                                       |
| `variables.tf` | All input variable declarations.                                         |
| `outputs.tf`   | All output declarations.                                                 |
| `versions.tf`  | `terraform` block with `required_version` + `required_providers`.        |
| `README.md`    | Human description: purpose, inputs, outputs, any usage patterns.         |

Root configs under `live/<env>/<app>/` use the same four `.tf` filenames (`main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`) but do not contain a `README.md`.

## 3. Resource Labeling Conventions

- **Primary resource:** always named `"this"` — e.g. `resource "aws_vpc" "this"`, `resource "aws_lb" "this"`, `resource "aws_ecs_service" "this"`.
- **Secondary / typed resources:** use a descriptive lowercase label tied to the role, e.g.:
  - `aws_subnet` split into `"public"` and `"private"`.
  - `aws_route_table` split into `"public"` and `"private"`.
  - `aws_iam_role` split into `"execution"` and `"task"` (in `ecs-service` module).
  - `aws_lb_listener` split into `"https"` and `"http_redirect"`.
- **Multiples** are expressed with `for_each` over a set/map — not `count`. The `for_each` key is typically a meaningful identifier (AZ name, CIDR) rather than an index.
- **Egress rules** named `"all"` when they are the catch-all egress-to-anywhere rule.

## 4. Variable Conventions

- **Case:** always `snake_case`.
- **Required fields on every variable:**
  - `description` — present on 100% of variables observed.
  - `type` — present on 100% of variables observed.
- **Required vs optional:**
  - **Required variables** have no `default`.
  - **Optional variables** always include a `default`.
- **Collection types:** `list(string)`, `map(string)`, or `map` of structured values. No HCL objects observed — simple types only.
- **Tagging variable** is always named `tags`, always typed `map(string)`, always defaulted to `{}`, and the description is consistent: `"Extra tags merged with the module-managed common_tags."` (or close variation).
- Booleans default to the safe/low-cost value (`internal = false`, `enable_deletion_protection = false`).
- Numbers use sensible defaults where applicable (`idle_timeout = 60`, `log_retention_days = 30`, `cpu = 512`, `memory = 1024`, `desired_count = 2`, `container_port = 8080`, `max_session_duration = 3600`).

### Variable naming patterns

| Semantic                          | Naming                                                            |
|-----------------------------------|-------------------------------------------------------------------|
| Single ID                         | `vpc_id`, `cluster_arn`, `target_group_arn`                       |
| Collection of IDs                 | `subnet_ids`, `public_subnet_ids`, `private_subnet_ids`           |
| ARN inputs                        | `_arn` suffix consistently                                        |
| Security group reference          | `alb_security_group_id` (qualified by role, not just `sg_id`)     |
| CIDR input (single)               | `cidr_block`                                                      |
| Collection of CIDRs               | `allowed_cidr_blocks`                                             |
| Number of units                   | `desired_count`, `log_retention_days`, `max_session_duration`     |
| Maps for env vars / policies      | `environment_variables`, `secret_arns`, `inline_policies`         |
| Lists of policy ARNs              | `managed_policy_arns`, `additional_task_role_policy_arns`         |
| JSON-as-string inputs             | `trust_policy_json` (suffix `_json`)                              |

## 5. Output Conventions

- **Case:** `snake_case`.
- **All outputs have a `description`.**
- **Suffixes** are semantic and consistent:
  - `_arn` — for ARNs (`alb_arn`, `service_arn`, `role_arn`, `task_role_arn`, `execution_role_arn`, `task_definition_arn`, `https_listener_arn`, `ecs_cluster_arn`, `api_service_arn`).
  - `_id` — for IDs (`vpc_id`, `role_id`, `security_group_id`, `default_security_group_id`).
  - `_name` — for names (`role_name`, `service_name`, `log_group_name`).
  - `_dns_name` — DNS-style hostnames (`alb_dns_name`).
  - `_zone_id` — Route53 zone IDs (`alb_zone_id`).
  - `_cidr_block` — CIDR blocks (`vpc_cidr_block`).
  - `_ids` (plural) — collection outputs (`public_subnet_ids`, `private_subnet_ids`).
- No output is named plainly (e.g. `arn` or `id` alone); the resource/role context is always in the name.
- When both the ARN and the name of the same resource are useful at callers, both are exposed (e.g. `task_role_arn` + `task_role_name`, `role_arn` + `role_name`, `service_arn` + `service_name`).

## 6. Tagging Pattern

### Inside modules

Every module has a `locals` block at the top of `main.tf`:

```hcl
locals {
  common_tags = merge(
    var.tags,
    {
      Module = "<module-name>"     # e.g. "network", "alb", "ecs-service", "iam-role"
      Name   = var.name            # or var.service_name in the ecs-service module
    }
  )
}
```

- The module adds at least `Module` and `Name`.
- The `ecs-service` module additionally adds `Service = var.service_name`.
- Per-resource overrides merge again inline, e.g.:
  ```hcl
  tags = merge(local.common_tags, { Name = "${var.name}-igw" })
  tags = merge(local.common_tags, { Name = "${var.name}-public-${each.key}", Tier = "public" })
  ```
- Private subnets carry `Tier = "private"`; public subnets carry `Tier = "public"`.

### Inside root configs

Root configs set environment/application-wide tags in **two layers** (both required because `default_tags` does not propagate into JSON blobs like `container_definitions`):

1. **Provider `default_tags`** in `versions.tf`:
   ```hcl
   provider "aws" {
     region = "eu-central-1"
     default_tags {
       tags = {
         Environment = "dev"
         Application = "reference"
         ManagedBy   = "terraform"
       }
     }
   }
   ```
2. **Explicit `local.common_tags`** in `main.tf`, passed into each module:
   ```hcl
   locals {
     common_tags = {
       Environment = var.environment
       Application = var.application
       CostCenter  = var.cost_center
       ManagedBy   = "terraform"
     }
   }
   ```

### Tag key style

PascalCase keys: `Environment`, `Application`, `CostCenter`, `ManagedBy`, `Module`, `Name`, `Service`, `Tier`.

Standard set of tag keys observed:
- `Environment` — dev / stg / prd
- `Application` — app name
- `CostCenter` — for showback
- `ManagedBy` — always `"terraform"`
- `Module` — set by each module
- `Name` — human-readable resource name
- `Service` — ECS service name (ecs-service module only)
- `Tier` — `public` / `private` for subnets

## 7. Provider Versions

Pinned identically in every `versions.tf`:

```hcl
terraform {
  required_version = ">= 1.5, < 2.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.70"
    }
  }
}
```

- **Terraform:** `>= 1.5, < 2.0` (open upper within the 1.x line).
- **AWS provider:** `~> 5.70` (pessimistic constraint at the minor level, allowing 5.70.x → 5.x but not 6.x).
- Only the `aws` provider is used in the observed surface.

## 8. Provider Declaration

- **Only in root configs.** Modules do **not** contain a `provider "aws" {}` block. They only declare `required_providers` in `versions.tf`.
- Provider configuration lives in the root's `versions.tf` alongside the `terraform` block (rather than a separate `providers.tf`).
- Region is hard-coded to `eu-central-1` in the provider block (not parameterized via variable in the observed root).

## 9. Backend Configuration

- Backend is **S3 with partial configuration**:
  ```hcl
  backend "s3" {
    # Backend config supplied at init time:
    # terraform init -backend-config="key=<env>/<app>/terraform.tfstate" ...
    key = "dev/reference-service/terraform.tfstate"
  }
  ```
- **State key convention:** `<env>/<app>/terraform.tfstate`.
- Bucket, region, DynamoDB lock table are supplied at `terraform init` time via `-backend-config` (not committed).
- DynamoDB is used for state locking.

## 10. Cross-Module / Cross-Root References

- **Within a root config:** reference module outputs directly (e.g. `module.network.vpc_id`, `module.alb.security_group_id`).
- **Across root configs:** use **SSM parameters**, not `terraform_remote_state`. (`data.aws_ssm_parameter.<name>` on the consumer side.)
- Module source paths are **relative**: `source = "../../../modules/<name>"` from a `live/<env>/<app>/` directory.

## 11. Security Group Rule Style

- **One rule per resource.** Always use `aws_vpc_security_group_ingress_rule` and `aws_vpc_security_group_egress_rule`.
- **Never** use inline `ingress`/`egress` blocks inside `aws_security_group`.
- Rule resources are named descriptively by role: `"https"`, `"http_redirect"`, `"from_alb"`, `"all"` (for the catch-all egress).
- `for_each = toset(var.allowed_cidr_blocks)` for rules that fan out over CIDR lists.
- Every rule has a `description`.
- `ip_protocol = "-1"` + `cidr_ipv4 = "0.0.0.0/0"` is the pattern for all-protocols egress.

## 12. ECS / Container Conventions

- **Task definitions** build `container_definitions` via `jsonencode([local.container_definition])` in a `locals` block — not inline string.
- **Logs** go to CloudWatch at `/ecs/<service_name>` with the `awslogs` driver.
- `awslogs-region` is read from `data "aws_region" "current" {}` — not hard-coded.
- `awslogs-stream-prefix` is the service name.
- Tasks run on **Fargate** (`launch_type = "FARGATE"`, `requires_compatibilities = ["FARGATE"]`, `network_mode = "awsvpc"`).
- `cpu` and `memory` are cast to string via `tostring(...)` for the task definition.
- `desired_count` is in `lifecycle.ignore_changes` to allow autoscalers to adjust it without drift.
- Tasks are deployed into **private subnets** (`assign_public_ip = false`).
- Environment variables are built from a `map(string)` via:
  ```hcl
  environment = [for k, v in var.environment_variables : { name = k, value = v }]
  ```
- Secrets are built from a `map(string)` of ARNs via:
  ```hcl
  secrets = [for k, arn in var.secret_arns : { name = k, valueFrom = arn }]
  ```

## 13. IAM Conventions

- **Trust policies** and **inline policies** accept JSON strings. The `iam-role` module prefers `data.aws_iam_policy_document.<x>.json` at the caller; `jsonencode(...)` is also acceptable.
- **Managed policy attachments** use `aws_iam_role_policy_attachment` with `for_each = toset(var.managed_policy_arns)`.
- **Inline policies** use `aws_iam_role_policy` keyed by policy name (`for_each = var.inline_policies`).
- The ECS task execution role automatically attaches `arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy`.
- Assume-role policies (inline in `ecs-service` module) use `jsonencode(...)` directly.
- Role names derive from the service name: `<service>-exec`, `<service>-task`.

## 14. Region

- **Default region:** `eu-central-1` (Frankfurt).
- Hard-coded in provider block of the observed root. Per-resource overrides allowed where needed.

## 15. Formatting / Style

- HCL is `terraform fmt`-clean (consistent two-space indent, aligned `=` in argument blocks).
- `locals` blocks go **first** in `main.tf`, before resources.
- `data` sources are declared close to the resource that uses them (e.g. `data "aws_region" "current" {}` in the ECS module sits just before the log group / task definition).
- Blank line between distinct resources; arguments grouped logically (essentials, then `tags` at the end).
- `tags = local.common_tags` sits as the last argument on a resource; or `tags = merge(local.common_tags, { Name = "..." })` when per-resource overrides are needed.

## 16. What is intentionally NOT in modules

- **Target groups** — services wire their own in the root config (see `aws_lb_target_group.api` in reference-service). This keeps the ALB module ALB-only.
- **Listener rules** — also in the root config.
- **ECS cluster** — root-level resource (`aws_ecs_cluster.this`), not a module.
- **ACM certificates** — passed in via `certificate_arn` variable.

## 17. Conversion Guidance (for CDK → Terraform output)

New modules added under `modules/<name>/` must:

- Have the five standard files (`main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`, `README.md`).
- Declare `required_providers` (not `provider`) in `versions.tf` with the pinned AWS version.
- Label primary resource `"this"`; use descriptive names for multiples and typed resources.
- Include a `local.common_tags` merge with at least `Module` and `Name` plus caller-provided `tags`.
- Follow the variable and output naming schemes above.
- Use per-resource security group rules (`aws_vpc_security_group_ingress_rule` / `_egress_rule`) — never inline blocks.
- Have a `README.md` documenting purpose, inputs, outputs, and usage patterns.

New live configs under `live/<env>/<app>/` must:

- Set both provider `default_tags` and `local.common_tags` and pass the latter into every module call.
- Use the `<env>/<app>/terraform.tfstate` backend key.
- Reference modules via relative `../../../modules/<name>` paths.
- Expose stack-level outputs (ALB DNS name, service ARN, cluster ARN, etc.).
