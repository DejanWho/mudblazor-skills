# Init-mode summary — `terraform-host/`

## What I did

Ran the `cdk-dotnet-to-terraform` skill in init mode against the host Terraform repo at `terraform-host/`. Produced two reference files:

- `skill-references/repo-conventions.md` — how this repo writes Terraform (14 sections, all filled; no `<FILL IN>` left).
- `skill-references/module-inventory.md` — catalogue of the 4 existing modules with inputs/outputs/CDK-match hints.

Mode selection was clear-cut: the task prompt explicitly asked for init, and no prior convention files existed. No conversion work was attempted; this is scan-and-document only.

## What I read

Every `.tf` and `.md` file in `terraform-host/` — the repo is small enough to read exhaustively rather than sample. Specifically:

- `terraform-host/README.md` — the repo's own conventions doc. Confirmed against the actual code (the two matched).
- `terraform-host/modules/network/` — `main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`, `README.md`.
- `terraform-host/modules/alb/` — same five files.
- `terraform-host/modules/ecs-service/` — same five files.
- `terraform-host/modules/iam-role/` — same five files.
- `terraform-host/live/dev/reference-service/` — `main.tf`, `variables.tf`, `outputs.tf`, `versions.tf` (no `README.md` at the root-config level).

Only one root config exists (`live/dev/reference-service/`), so the "read two root configs" step in the init walkthrough was N/A — I noted this in the conventions file (section 9, "Cross-module references") and in the "Open questions" section.

## Key findings

- **Layout:** `modules/` + `live/<env>/<app>/` split, single Terraform tree, kebab-case module names.
- **Module files:** always `main.tf` / `variables.tf` / `outputs.tf` / `versions.tf` / `README.md`. Locals live inline at the top of `main.tf` — there's no `locals.tf` file.
- **Resource labels:** `"this"` for the primary resource; descriptive labels (`"public"` / `"private"` / `"https"` / `"execution"` / `"task"`) for distinct categories; `for_each` for collections (no numeric suffixes).
- **Variables:** snake_case, always with `description` and `type`. Required vars have no default, optional vars always have a default.
- **Outputs:** snake_case with `_id` / `_arn` / `_name` / `_dns_name` suffixes; collections use plural forms (`_ids`).
- **Tagging:** dual-layer — `default_tags` on the provider AND an explicit `tags` variable threaded into every module. Reason: `default_tags` doesn't propagate into ECS `container_definitions` JSON, so the repo keeps both paths active. Required keys: `Environment`, `Application`, `ManagedBy`, `CostCenter`, plus module-injected `Module` and `Name`.
- **Provider config:** declared only in root configs. Modules only set `required_providers` in `versions.tf`.
- **Versions:** Terraform `>= 1.5, < 2.0`, AWS provider `~> 5.70`.
- **Backend:** S3 partial backend, key `<env>/<app>/terraform.tfstate` hardcoded per root; bucket / lock table supplied via `-backend-config` at init.
- **Security group rules:** always use `aws_vpc_security_group_ingress_rule` / `_egress_rule` (per-rule resources). Never inline `ingress` / `egress` blocks inside `aws_security_group`.
- **Cross-root references:** use SSM parameters, not `data.terraform_remote_state`. Not yet exercised in code (only one root config exists today).
- **Module inventory:** 4 modules — `network`, `alb`, `ecs-service`, `iam-role`. Each has a clear "no overlap" scope: `alb` does not create target groups, `ecs-service` does not create ALBs/clusters, `network` does not create endpoints.

## Things I was unsure about / flagged for user confirmation

1. **Cross-root SSM parameter naming.** The README says cross-root refs use SSM, but only one root config exists, so there's no established path pattern. I recorded a suggested pattern (`/<env>/<app>/<resource-type>/<name>`) in the conventions file under "Open questions" but flagged it as unconfirmed.
2. **Hardcoded `default_tags` in the root provider.** `live/dev/reference-service/versions.tf` hardcodes `Environment = "dev"` and `Application = "reference"` in the provider's `default_tags` block, while the same root's `main.tf` uses `var.environment` / `var.application` in `local.common_tags`. It's a minor redundancy; I called it out in section 13 (Inconsistencies) and recommended preferring variable references going forward. Worth the user's steer.
3. **Modules not present.** The inventory's closing section lists categories with no current module (`lambda`, `rds`, `dynamodb`, `s3-bucket`, `kms-key`, `cloudfront`, `sqs`, `sns`, `vpc-endpoint`, etc.). A future CDK conversion that needs any of these will require authoring a new module; I captured the style rules convert mode should follow when doing so.
4. **Aliased / multi-region providers.** None observed. If a CDK stack has a us-east-1 ACM cert for CloudFront or similar cross-region patterns, the author should propose the aliased-provider placement and confirm before writing. Flagged in "Open questions."
5. **Autoscaling for `ecs-service`.** The module deliberately does not create autoscaling, and `desired_count` is ignored in `lifecycle`. The README hints that autoscaling belongs at the caller, but there's no example. Flagged in "Open questions."

Files produced are ready for user review. Per the skill's workflow, they should be considered draft until the user confirms or corrects anything above.
