# Repo Conventions

Captured by `cdk-dotnet-to-terraform` init mode for the host Terraform repo at `terraform-host/`. Future convert-mode runs MUST follow this file — if your instinct conflicts with what's written here, follow the file.

---

## 1. Repo layout

- **Terraform root(s):** `terraform-host/` — a single Terraform tree with a `modules/` + `live/` split. `modules/` holds reusable building blocks; `live/<env>/<app>/` holds root configs that consume them.
- **Multiple trees?** No — one tree only.
- **Which tree does this skill target?** `terraform-host/` (the only tree). New modules land in `terraform-host/modules/<name>/`; new root configs land in `terraform-host/live/<env>/<app>/`.

## 2. Module layout

- **Module directory:** `terraform-host/modules/` (relative to repo root). Each module is a directory: `modules/<name>/`.
- **Module-naming convention:** kebab-case, no prefix, no AWS-service prefix. Names reflect role/shape (`network`, `alb`, `ecs-service`, `iam-role`), not the AWS resource type verbatim.
- **How modules are consumed:** via relative `source = "../../../modules/<name>"` from a root config at `live/<env>/<app>/`. No git refs, no registry.
- **Module versioning:** None — monorepo, always latest. Changes to a module affect every root config on next apply.

## 3. File layout inside a module

- **Standard files:** every module has exactly `main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`, and `README.md`. No `locals.tf` file is used.
- **What goes in `main.tf`:** a `locals { common_tags = merge(...) }` block at the top of the file, followed by all resources and any module-internal `data` sources. No variables or outputs live here.
- **Use of `locals.tf`:** N/A — locals are declared inline at the top of `main.tf`, not in a separate file.
- **`versions.tf` contents:** a `terraform { required_version = ">= 1.5, < 2.0"; required_providers { aws = { source = "hashicorp/aws"; version = "~> 5.70" } } }` block. No `provider "aws" { ... }` block inside modules.
- **README per module?** Yes — hand-written Markdown. Format: `# <module-name>` heading, one-line purpose sentence, `## Inputs` bulleted list with `(type, required/default)` annotations, `## Outputs` bulleted list with one-line descriptions. Some modules add an additional `## Pattern: ...` or `## Extending ...` section with example HCL.

## 4. Root / live config layout

- **Environments directory:** `terraform-host/live/<env>/<app>/` — one folder per (environment, application) pair. Example: `live/dev/reference-service/`.
- **Environment split pattern:** folder per env (no workspaces, no single-config + tfvars). Each env has its own backend state key.
- **File organization in root:** one flat `main.tf` that calls modules and wires cross-module glue resources (target groups, listener rules, ECS cluster) inline. Plus `variables.tf`, `outputs.tf`, `versions.tf`. No split by subsystem (no `network.tf` / `compute.tf`).

## 5. Naming conventions

- **Variables:** `snake_case`. Every variable has `description` and `type`. Required variables have no `default`; optional variables always have a `default`. Types are always declared (`string`, `number`, `bool`, `list(string)`, `map(string)`).
- **Outputs:** `snake_case` with descriptive suffixes: `_id`, `_arn`, `_name`, `_dns_name`, `_zone_id`. Collections use plural suffixes like `_ids` (`public_subnet_ids`, `private_subnet_ids`). Every output has a `description`.
- **Resource labels:** `resource "aws_<type>" "this"` for the single/primary instance of a resource. For multiples, use `for_each` on the primary resource (no numeric suffixes). When a module has genuinely separate categories of the same resource, distinct labels like `"public"` / `"private"` / `"https"` / `"http_redirect"` / `"execution"` / `"task"` are used (descriptive, not numbered).
- **Module instance names:** `module "<short-role>"` — matches the module directory name when there's one of them (`module "network"`, `module "alb"`), or a role-specific variant when there are several of the same module (`module "api_service"` using `ecs-service`).
- **Physical resource naming:** explicit naming everywhere it's supported, built from `${var.application}-${var.environment}` at the root config and from `${var.name}` or `${var.service_name}` inside modules. Modules accept a `name` or `service_name` variable and compose all child resource names from it (`${var.name}-public-${each.key}`, `${var.service_name}-tasks`, `${var.service_name}-exec`).

## 6. Tagging

- **Source of tags:** BOTH `default_tags` on the provider AND an explicit `tags` variable threaded into every module. Both layers are used because `default_tags` does not propagate into JSON-encoded payloads like ECS `container_definitions`.
- **Required keys:** `Environment`, `Application`, `ManagedBy` (always `"terraform"`), `CostCenter`. Modules add `Module = "<name>"` and `Name = var.name` (or `Service = var.service_name` for `ecs-service`) automatically via `local.common_tags`.
- **How modules accept extra tags:** every module has a `variable "tags" { type = map(string); default = {} }`. Inside the module, `locals { common_tags = merge(var.tags, { Module = "<name>", Name = var.name }) }` produces the tag set used on every resource. Per-resource overrides use `merge(local.common_tags, { Name = "<specific-name>", Tier = "public" })`.
- **Are tags set on every resource type that supports them?** Yes — observed on VPC, subnets, IGW, EIP, NAT gateway, route tables, ALB, listeners, security groups, target groups, ECS cluster/service/task definition, CloudWatch log group, IAM roles. Not set on `aws_route_table_association`, `aws_iam_role_policy_attachment`, `aws_vpc_security_group_ingress_rule`/`_egress_rule`, `aws_iam_role_policy` (these resource types don't support tags).

## 7. Provider configuration

- **Provider declaration location:** root configs ONLY. Modules declare `required_providers` in `versions.tf` but never a `provider "aws" { ... }` block.
- **`default_tags` used?** Yes, in root configs. The root `provider "aws"` sets `default_tags { tags = { Environment = "...", Application = "...", ManagedBy = "terraform" } }`. Note: the live config observed hardcodes these in the provider block rather than referencing `var.environment` — a mild redundancy with `local.common_tags`, but both layers exist intentionally (see section 6).
- **`aws` provider version floor:** `~> 5.70` (declared in every module's `versions.tf` and in root configs).
- **Multiple provider instances / aliases?** None observed. Single-region, single-account pattern. If a cross-region resource (e.g. us-east-1 ACM cert for CloudFront) is needed later, the author should add an aliased provider at the root config only.
- **Assume-role or profile config pattern:** Not declared in-code. The provider block only sets `region` and `default_tags`. Credentials/role are expected to come from the environment (CI OIDC, AWS SSO, or local env vars).

## 8. Backend configuration

- **Backend type:** `s3` (partial backend).
- **State key pattern:** `<env>/<app>/terraform.tfstate` — hardcoded per root config in the `backend "s3"` block.
- **Lock mechanism:** DynamoDB lock table — supplied at `terraform init` time via `-backend-config=...` flags (not declared in-code).
- **Backend config source:** partial backend. The `key` is in the root config; bucket, region, and DynamoDB table are supplied via `-backend-config=...` at init time.

## 9. Cross-module / cross-stack references

- **Pattern:** module outputs within a single root config (preferred). Cross-root references use SSM parameters, not `data.terraform_remote_state`.
- **SSM parameter naming (if used):** Not observed in the current repo (only one root config exists). If cross-root refs become needed, follow a pattern like `/<env>/<app>/<resource-type>/<name>` — confirm with the team before introducing.
- **Remote state key pattern (if used):** N/A — remote state is explicitly NOT used per the README ("Cross-root refs, where they exist, use SSM parameters (not remote_state)").

## 10. Terraform version floor

- **`required_version`:** `">= 1.5, < 2.0"` — declared in every module's `versions.tf` and in root configs.
- **Uses `import` blocks?** Not observed in this repo's current code, but the version floor (>= 1.5) supports them. Convert mode can emit `import` blocks when adopting existing CloudFormation-managed resources.
- **Uses `for_each` on modules?** Not observed — each module is called as a single instance per root config. `for_each` is used heavily on resources inside modules (subnets, NAT gateways, route tables, security group rules, policy attachments).
- **Uses `moved` blocks?** Not observed. Since the repo is young, refactors haven't required them yet.

## 11. Secrets handling

- **Where secrets live:** Secrets Manager and SSM Parameter Store (referenced by ARN, not read into Terraform state). The `ecs-service` module accepts a `secret_arns` map where values are Secrets Manager or SSM ARNs.
- **How Terraform reads them (if at all):** Terraform never reads secret values — only references ARNs. The ECS task's `secrets` in `container_definitions` resolve the values at task-launch time via the execution role.
- **Never-in-state policy:** Implicit — no `aws_secretsmanager_secret_version` or equivalent write-secret resources observed. Secret values are assumed to be set out-of-band (console, CLI, deploy pipeline) and Terraform only manages the shell (ARNs, policies).

## 12. Documentation conventions

- **Module README format:** Markdown. Structure: `# <module-name>` heading, one-line purpose statement, `## Inputs` bulleted list with `(type, required/default)`, `## Outputs` bulleted list. Some READMEs include a `## Pattern:` or `## Extending ...` section with example HCL (see `modules/iam-role/README.md` for the Bedrock pattern example, and `modules/ecs-service/README.md` for the "Extending task permissions" section).
- **Inline comment style:** sparse. No file-header banners. Short comments only where intent is non-obvious (e.g., the partial-backend comment in `live/dev/reference-service/versions.tf`).
- **CHANGELOG / release notes per module?** No — monorepo-style, no per-module versioning.

## 13. Inconsistencies noted during init

- `default_tags` in the root-config provider block hardcodes `Environment = "dev"` / `Application = "reference"` rather than referencing `var.environment` / `var.application`. Meanwhile, `local.common_tags` in the same `main.tf` does reference the variables. This is a minor redundancy; going forward, prefer referencing variables so the two layers stay in sync. If touching the block during conversion, keep the hardcoded form only if the root config is truly single-env single-app (which it is here).
- Otherwise: file layout, variable/output naming, tag plumbing, SG-rule style, and resource labeling (`"this"`) are fully consistent across the 4 modules reviewed.

## 14. Open questions / deferred decisions

- **Cross-root SSM parameter layout.** Only one root config exists today, so no cross-root reference pattern is established in code. If a future conversion needs to share data between root configs, confirm the SSM path pattern with the team (suggested: `/<env>/<app>/<resource-type>/<name>`) and record the decision here.
- **Cross-region / aliased providers.** No patterns observed. If a CDK stack requires cross-region resources (us-east-1 ACM for CloudFront, cross-region replication, etc.), the author should propose an aliased-provider pattern and confirm before writing.
- **Autoscaling policy placement.** `ecs-service` explicitly does not create autoscaling. The README implies it goes at the caller, but no example exists yet. If a conversion needs autoscaling, add it as raw resources in the root config and raise whether to upstream into a new module or extend `ecs-service`.
- **Container-image Lambdas.** No `lambda` module exists yet (despite the top-level README mentioning one might arrive). If a CDK stack uses Lambda, author a new module in the style of existing ones and add it to the inventory.

---

*This file was generated by `cdk-dotnet-to-terraform` init mode on 2026-04-20. Re-run init if the repo's Terraform style changes or new module patterns emerge. Commit this file so future sessions and reviewers share the same understanding.*
