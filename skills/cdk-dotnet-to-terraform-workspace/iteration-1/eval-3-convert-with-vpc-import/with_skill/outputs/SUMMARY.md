# Conversion summary — BedrockChatStack (CDK .NET 8) → Terraform

Target repo: `terraform-host/`
Target live config: `terraform-host/live/dev/bedrock-chat/`
Date: 2026-04-20

## Mode decisions

Init mode ran first (no pre-existing `repo-conventions.md` / `module-inventory.md`). Outputs written to `outputs/skill-references/`. Convert mode then produced the Terraform below.

## Files written

### New live config — `terraform-host/live/dev/bedrock-chat/`

- `main.tf` — module calls + raw resources for the greenfield pieces.
- `variables.tf` — env, application, CIDR, AZs, ACM cert ARN, image, Claude model IDs.
- `outputs.tf` — ALB DNS, cluster ARN, service ARN, VPC ID, Bedrock endpoint ID.
- `versions.tf` — Terraform `>= 1.5` floor, AWS `~> 5.70`, S3 partial backend with `dev/bedrock-chat/terraform.tfstate` key, provider + `default_tags`.
- `imports.tf` — VPC `import` block (required) plus commented-out scaffolds for every other `modules/network` resource so the user can fill in physical IDs.

### New modules

None. All CDK constructs mapped onto existing modules (`network`, `alb`, `ecs-service`).

### Skill reference files

- `outputs/skill-references/repo-conventions.md`
- `outputs/skill-references/module-inventory.md`

Per-repo artefacts; the skill's own source tree was not modified.

## Construct → Terraform mapping

| CDK construct | Terraform destination | Notes |
|---|---|---|
| `Vpc` (3 AZs, public + private subnets, 3 NAT GWs) | `module "network"` at `modules/network` | VPC **imported** via `imports.tf` with id `vpc-0a1b2c3d4e5f6a7b8`. Subnets/NAT/route tables greenfield unless further imports added. |
| `InterfaceVpcEndpoint` for `bedrock-runtime` | raw `aws_vpc_endpoint.bedrock_runtime` in root | `modules/network` has no endpoints input; created at call site per inventory pattern. |
| `BedrockEndpointSg` | raw `aws_security_group.bedrock_endpoint` + `aws_vpc_security_group_ingress_rule.bedrock_endpoint_from_tasks` in root | Rule resources (not inline ingress) per repo convention. |
| `Cluster` (ECS) with Container Insights V2 | raw `aws_ecs_cluster.this` in root | Matches reference-service style. `setting { name = "containerInsights", value = "enhanced" }` reproduces `ContainerInsightsV2 = ENABLED`. |
| `TaskLogGroup` | inside `module "api_service"` | Module creates `/ecs/<service_name>` → `/ecs/bedrock-chat-dev`. |
| `TaskExecutionRole` + `TaskRole` | inside `module "api_service"` | Module creates both; attaches `AmazonECSTaskExecutionRolePolicy` to exec role. |
| `TaskRole.AddToPolicy(Bedrock invoke)` | `aws_iam_role_policy.bedrock_invoke` + `data.aws_iam_policy_document.bedrock_invoke` in root | Caller-side extension via `role = module.api_service.task_role_name`. ARNs use `data.aws_region.current.name`. |
| `FargateTaskDefinition` + `AddContainer` + `FargateService` + service SG | `module "api_service"` at `modules/ecs-service` | CPU 1024 / mem 2048 / nginx image / port 8080 / env vars reproduced. Desired count 2 (module default). |
| `AlbSg` + `ApplicationLoadBalancer` + HTTPS listener + HTTP redirect listener | `module "alb"` at `modules/alb` | Module covers all four; TLS policy matches CDK. |
| ALB target group + listener rule | raw `aws_lb_target_group.api` + `aws_lb_listener_rule.api` in root | Matches reference-service pattern; health check matches CDK. |
| `service.Connections.AllowFrom(albSg, 8080)` | inside `module "api_service"` | Module creates `aws_vpc_security_group_ingress_rule.from_alb` from `var.alb_security_group_id`. |
| Bedrock SG `AddIngressRule` from task SG | `aws_vpc_security_group_ingress_rule.bedrock_endpoint_from_tasks` in root | References `module.api_service.security_group_id`. |
| `CfnOutput`s (`AlbDnsName`, `ServiceArn`) | `outputs.tf` entries + extras (VPC ID, endpoint ID). | |

Everything fit existing modules. No new module inventory entries needed.

## Imports

- **Imported:** 1 resource — the VPC.
  - CDK path: `BedrockChatStack-dev/Vpc`
  - Import address: `module.network.aws_vpc.this`
  - Physical ID: `vpc-0a1b2c3d4e5f6a7b8`
- **Scaffolded but commented out:** the rest of `modules/network` (6 subnets, 1 IGW, 3 EIPs, 3 NAT gateways, 4 route tables, route-table associations).
- **Greenfield (no import):** ALB, listeners, target group, listener rule, ECS cluster, Fargate service + task definition + roles + SG + log group, Bedrock interface endpoint, Bedrock endpoint SG + ingress rule, task-role Bedrock inline policy.

## Follow-ups / things the user should check

1. **Remaining `modules/network` resources — pick one strategy before `terraform apply`:**
   - **(a) Import them too.** Likely correct if the deployed VPC already has live subnets / NAT / route tables. Gather physical IDs (e.g. `aws ec2 describe-subnets --filters Name=vpc-id,Values=vpc-0a1b2c3d4e5f6a7b8`), uncomment + fill in the scaffolded import blocks in `imports.tf`. Addresses follow the module's `for_each` AZ-name keys.
   - **(b) Accept the greenfield creates.** Only viable if the VPC was provisioned empty. First plan would create 6 subnets + 1 IGW + 3 EIPs + 3 NAT GWs + 4 route tables + associations inside the existing VPC.

2. **Subnet CIDRs.** Module computes `cidrsubnet(var.cidr_block, 8, i)` (public) and `... i + len(azs))` (private). For `10.30.0.0/16` / 3 AZs: public `10.30.0.0/24`, `.1.0/24`, `.2.0/24`; private `.3.0/24`, `.4.0/24`, `.5.0/24` — consistent with the synth template. If deployed CIDRs differ, imports will show drift.

3. **Bedrock endpoint SG egress.** CDK synth has a "disallow all" egress placeholder for `AllowAllOutbound = false`. The Terraform SG has no explicit egress rules — equivalent strict stance.

4. **ACM cert is an out-of-stack input.** Required root variable `certificate_arn`.

5. **Container Insights V2 value.** Uses `"enhanced"` per AWS provider `5.70+`. Older providers may need `"enabled"`.

6. **Bedrock model access.** Enabling Claude access in Bedrock is an account-level console toggle — not managed in Terraform.

## Local verification

- `terraform fmt -recursive` could not be executed — `terraform` is not installed on the sandbox PATH, and Bash access to run it was also denied. Files were hand-aligned against the surrounding repo's existing `fmt` output. Run `terraform fmt -recursive terraform-host/` in your environment; any delta will be whitespace-only.
- `terraform init` / `validate` / `plan` intentionally not run — those run in the CI pipeline.

## Recommended next steps

1. Decide on follow-up #1 (additional imports vs greenfield) and update `imports.tf` accordingly before the first plan.
2. Run `terraform fmt -recursive terraform-host/` locally as a sanity check.
3. Push the branch. Let CI run `terraform init` / `validate` / `plan`.
4. Expect mild drift on the VPC import (tag ordering, `instance_tenancy` explicit vs implicit). Iterate once.
5. After clean plan, apply. The `import` block then becomes a no-op and can be removed later.
