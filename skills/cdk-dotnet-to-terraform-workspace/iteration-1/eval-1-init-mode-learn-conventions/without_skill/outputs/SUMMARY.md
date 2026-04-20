# Summary

## What I did

Analyzed the existing Terraform host repo at `terraform-host/` (input-only) to learn its conventions before any CDK-to-Terraform work. Walked every file under `modules/` (alb, ecs-service, iam-role, network) and the live config under `live/dev/reference-service/` and produced two reference documents capturing what the repo expects from new code.

### Files read

- `terraform-host/README.md`
- `terraform-host/modules/network/{main,variables,outputs,versions}.tf` + `README.md`
- `terraform-host/modules/alb/{main,variables,outputs,versions}.tf` + `README.md`
- `terraform-host/modules/ecs-service/{main,variables,outputs,versions}.tf` + `README.md`
- `terraform-host/modules/iam-role/{main,variables,outputs,versions}.tf` + `README.md`
- `terraform-host/live/dev/reference-service/{main,variables,outputs,versions}.tf`

### Files produced

1. `skill-references/repo-conventions.md` — directory layout, per-module file layout, resource labeling (`"this"` + `for_each`), variable and output naming schemes (`snake_case` with semantic suffixes `_arn` / `_id` / `_name` / `_ids` / `_dns_name`), two-layer tagging (provider `default_tags` + explicit `local.common_tags`), provider versions (`Terraform >= 1.5, < 2.0`, AWS `~> 5.70`), backend style (S3 partial, key `<env>/<app>/terraform.tfstate`, DynamoDB locking), cross-module references (module outputs within a root, SSM across roots), security-group rule style (per-rule resources, never inline blocks), ECS container-definition conventions (`jsonencode` in `locals`, `/ecs/<service>` log group, `aws_region.current` for log region, `lifecycle.ignore_changes = [desired_count]`), IAM conventions, region defaults, and a conversion-guidance section.

2. `skill-references/module-inventory.md` — one section per module (`network`, `alb`, `ecs-service`, `iam-role`) documenting purpose, resources created, every input (name / type / required / default / description), every output, and notable design choices. Includes a section for the reference live config and a summary table.

3. `SUMMARY.md` — this file.

## Key findings

- Consistent five-file module shape: `main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`, `README.md`. Root configs use the four `.tf` files without a README.
- Strong naming discipline: primary resource always `"this"`, `for_each` over keyed maps (AZ names, policy names, CIDRs), `_arn` / `_id` / `_name` / `_ids` output suffixes used consistently.
- Tagging is deliberately double-layered because provider `default_tags` does not propagate into JSON blobs like `container_definitions`.
- Security group rules use the per-resource style (`aws_vpc_security_group_ingress_rule` / `_egress_rule`), never inline `ingress`/`egress`.
- Modules never declare `provider`, only `required_providers`. Providers live in root `versions.tf`.
- State key convention: `<env>/<app>/terraform.tfstate`, backend is S3 partial (bucket/region/lock table passed at `terraform init`).
- Cross-root references use SSM parameters, not `terraform_remote_state`.
- Region default is `eu-central-1` (Frankfurt).

No files under `terraform-host/` were modified.
