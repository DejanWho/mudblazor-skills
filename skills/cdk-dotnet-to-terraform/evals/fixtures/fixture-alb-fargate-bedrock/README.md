# Fixture: ALB → Fargate → Bedrock

A mock environment for evaluating the `cdk-dotnet-to-terraform` skill. Two halves:

- `terraform-host/` — a simulated host Terraform repo the skill must learn conventions from (init mode) and write output into (convert mode). Has 4 modules (`network`, `ecs-service`, `alb`, `iam-role`) and one reference `live/` config so the style is visible.
- `cdk/` — a CDK .NET 8 project the skill must convert. Deploys an HTTPS ALB → Fargate service that calls Anthropic Claude on Amazon Bedrock, with a VPC endpoint for `bedrock-runtime` so Bedrock traffic doesn't leave the VPC. Pre-computed `cdk synth` output is in `cdk/cdk.out/` so the skill doesn't need `dotnet` / `cdk` on PATH.

## What a good conversion looks like

For this fixture, the skill should:

1. **Init mode** — walk `terraform-host/` and write `repo-conventions.md` + `module-inventory.md` capturing:
   - Modules live at `terraform-host/modules/<name>/`
   - Live configs at `terraform-host/live/<env>/<app>/`
   - Module file layout: `main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`, `README.md`
   - Variables are snake_case; outputs have `_arn` / `_id` / `_name` suffixes
   - Tags come from a `tags` variable + a locals-merged `common_tags` pattern
   - Resource labels use `this` consistently
   - AWS provider `~> 5.70`
   - Each module includes `terraform-host/modules/<n>/README.md` with a short inputs/outputs list

2. **Convert mode** — produce:
   - A new live config at `terraform-host/live/dev/bedrock-chat/` (or similar name from the CDK stack)
   - Module calls: `module.network` (reusing), `module.alb` (reusing), `module.ecs-service` (reusing), `module.iam-role` (reusing for the task role)
   - Raw resources: `aws_vpc_endpoint.bedrock_runtime` (no matching repo module), `aws_security_group.bedrock_endpoint`, `aws_iam_role_policy` granting `bedrock:InvokeModel*`
   - Follow the variable / tagging conventions observed in the reference service
   - Optionally an `imports.tf` if the prompt says some resources are deployed already

## Things that might reveal skill bugs

- Does init pick up the `iam-role` module's inline-policy map pattern, or does it miss the nuance and rewrite it?
- Does convert author a new module for the Bedrock VPC endpoint, or (correctly) leave it as raw resources because it's used once?
- Does the Bedrock IAM policy include `InvokeModelWithResponseStream`? The CDK source includes it.
- Does the skill wire the task role's `bedrock:InvokeModel` policy via the existing `iam-role` module's `inline_policies` input, or does it reach for a fresh `aws_iam_role_policy`?
- Does the skill pick `terraform-host/live/dev/<name>/` as the output path, matching the reference service?

## Running the eval

The skill is invoked with a prompt like:

```
Convert the CDK .NET 8 project at <fixture>/cdk/ to Terraform that fits into the repo at <fixture>/terraform-host/. The ECS service and ALB are not yet deployed to AWS (greenfield), but the VPC already exists with id vpc-0a1b2c3d4e5f6a7b8 — that VPC must be imported, not recreated. Use our existing modules where possible.
```
