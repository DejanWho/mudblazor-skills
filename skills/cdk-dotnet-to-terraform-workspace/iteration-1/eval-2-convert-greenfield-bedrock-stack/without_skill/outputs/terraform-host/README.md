# terraform-host — conventions at a glance

This is the mock host Terraform repo the skill writes into. Style conventions are documented here and visible in the `modules/` + `live/dev/reference-service/` example.

## Layout

```
terraform-host/
├── modules/
│   ├── network/         VPC + subnets (public/private) + NAT + route tables
│   ├── alb/             ALB + HTTPS listener + HTTP→HTTPS redirect + front SG
│   ├── ecs-service/     Fargate service + task/exec roles + log group + task SG
│   └── iam-role/        Stand-alone IAM role with inline + managed policies
└── live/
    └── <env>/
        └── <app>/       Root config — calls modules, wires target groups & listener rules
```

## Conventions

- **Module files:** every module has `main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`, `README.md`.
- **Resource labels:** `resource "aws_X" "this"` — always "this" for the primary; for multiples use `for_each`.
- **Variable names:** `snake_case`. Always has `description` and `type`. Required vars have no default; optional vars do.
- **Output names:** `snake_case` with `_arn`, `_id`, `_name`, `_dns_name`, etc. suffixes. Collection outputs end in `_ids`, etc.
- **Tagging:** modules maintain a `local.common_tags` merging a caller-supplied `tags` variable with module-specific keys (`Module`, `Name`). Root configs set environment/application-wide tags via `default_tags` on the provider AND via an explicit `local.common_tags` passed down to modules (both layers because `default_tags` doesn't propagate into container_definitions / similar JSON blobs).
- **Provider declaration:** only in root configs. Modules only declare `required_providers` in `versions.tf`.
- **Versions:** Terraform `>= 1.5, < 2.0`, AWS provider `~> 5.70`.
- **Backend:** S3 partial backend, key is `<env>/<app>/terraform.tfstate`; DynamoDB lock table supplied at init-time.
- **Cross-module refs:** module outputs within a root config. Cross-root refs, where they exist, use SSM parameters (not remote_state).
- **SG rules:** use `aws_vpc_security_group_ingress_rule` / `_egress_rule` resources (one rule per resource). Don't use inline `ingress`/`egress` blocks inside `aws_security_group`.
- **Container definitions:** built via `jsonencode(...)` in a `locals` block; logs to `/ecs/<service>` with `awslogs` driver.
- **Region:** `eu-central-1` (Frankfurt). Some services may override per-resource where needed.

## How CDK conversions land here

Convert mode of `cdk-dotnet-to-terraform` writes new live configs into `live/<env>/<app>/` and new modules into `modules/<name>/`. New modules must match the conventions above.
