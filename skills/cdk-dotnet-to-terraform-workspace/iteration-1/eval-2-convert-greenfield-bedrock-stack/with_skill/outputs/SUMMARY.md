# Conversion Summary - CDK BedrockChatStack to Terraform

Converted `cdk/src/BedrockChatStack.cs` (single stack `BedrockChatStack-dev`) into a
Terraform live config at `terraform-host/live/dev/bedrock-chat/`.

Everything is greenfield - no `import` blocks were generated.

## Init phase

`skill-references/repo-conventions.md` and `skill-references/module-inventory.md` were
written during init based on a walkthrough of `terraform-host/modules/` and
`terraform-host/live/dev/reference-service/`. Four modules were catalogued:
`network`, `alb`, `ecs-service`, `iam-role`.

## Module decisions

| CDK layer | Destination |
|---|---|
| `Vpc` (3 AZs, public + private subnets, NAT per AZ) | Reused `modules/network` |
| `ApplicationLoadBalancer` + HTTPS listener + HTTP->HTTPS redirect + front SG | Reused `modules/alb` |
| `FargateService` + `FargateTaskDefinition` + container + log group + task/exec roles + task SG | Reused `modules/ecs-service` |
| `Cluster` (ECS) with `ContainerInsightsV2 = ENABLED` | Raw `aws_ecs_cluster` in root config (mirrors `reference-service`; there is no cluster module) |
| Target group + listener rule pointing the ALB HTTPS listener at the service | Raw `aws_lb_target_group` + `aws_lb_listener_rule` (the `alb` module intentionally leaves target groups + rules to callers) |
| `InterfaceVpcEndpoint(BEDROCK_RUNTIME)` + its dedicated security group + ingress rule from the Fargate task SG | Raw `aws_vpc_endpoint` + `aws_security_group` + `aws_vpc_security_group_ingress_rule` in the root config. The `network` module does not take a variadic endpoint list; per the inventory notes, endpoints live at the call site. |
| `taskRole.AddToPolicy({ bedrock:InvokeModel, bedrock:InvokeModelWithResponseStream, resources = [Claude 3.5 Sonnet ARN, Claude 3 Haiku ARN] })` | Raw `aws_iam_role_policy` attached to `module.api_service.task_role_name`, built from `data.aws_iam_policy_document.bedrock_invoke`. |
| `Certificate.FromCertificateArn(...)` | Passed in via `var.certificate_arn` (default mirrors the CDK-imported ARN). |

No new modules were authored. Every reusable piece had a clean existing-module match,
and the remaining pieces (Bedrock endpoint, target group, listener rule, cluster, task
role inline policy) are one-offs that the existing modules explicitly defer to callers.

## How the Bedrock task-role policy is wired

The `ecs-service` module creates its own task role and exposes `task_role_name`. Per
that module's README, attaching inline bedrock permissions at the caller is Option 2
(the recommended path today):

```hcl
data "aws_iam_policy_document" "bedrock_invoke" {
  statement {
    sid     = "InvokeClaudeModels"
    effect  = "Allow"
    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream",
    ]
    resources = local.bedrock_model_arns
  }
}

resource "aws_iam_role_policy" "task_bedrock_invoke" {
  name   = "bedrock-invoke"
  role   = module.api_service.task_role_name
  policy = data.aws_iam_policy_document.bedrock_invoke.json
}
```

`local.bedrock_model_arns` is built in `main.tf` from `var.region`,
`var.claude_sonnet_model_id`, and `var.claude_haiku_model_id`, matching the
CDK's `$"arn:aws:bedrock:{this.Region}::foundation-model/{modelId}"` construction.
The account segment in the ARN is intentionally empty (foundation models are AWS-owned).

## Files written

### New live config
- `terraform-host/live/dev/bedrock-chat/main.tf`
- `terraform-host/live/dev/bedrock-chat/variables.tf`
- `terraform-host/live/dev/bedrock-chat/outputs.tf`
- `terraform-host/live/dev/bedrock-chat/versions.tf`

### Skill references
- `skill-references/repo-conventions.md` (init phase)
- `skill-references/module-inventory.md` (init phase)

### No new modules

## Resources kept as raw (not modularised)

- `aws_ecs_cluster.this` - matches the repo's existing pattern in `reference-service`. A cluster module could be extracted if a second service lands in `bedrock-chat`, but clusters are usually per-app.
- `aws_lb_target_group.api` + `aws_lb_listener_rule.api` - intentional per `modules/alb` README: target groups and listener rules are owned by the service.
- `aws_vpc_endpoint.bedrock_runtime` + its SG and ingress rule - per `modules/network` inventory notes, VPC endpoints live at the call site.
- `aws_iam_role_policy.task_bedrock_invoke` + `data.aws_iam_policy_document.bedrock_invoke` - one-off inline policy, attached to the ecs-service task role.

## TODOs left in the output

- Container insights as a module input: the CDK sets `ContainerInsightsV2 = ENABLED` (enhanced). We set `setting { name = "containerInsights"; value = "enhanced" }` on the inline cluster resource, matching the synth output (`"Value": "enhanced"`). Flagged in `repo-conventions.md` section 14 as something to formalise if cluster creation ever moves into a module. Inline `TODO:` comment in `main.tf`.
- Manual prerequisite - Bedrock model access: Bedrock foundation models require per-account / per-region model access to be enabled (Bedrock console or `aws_bedrock_foundation_model_agreement_acceptance` in newer provider versions). The CDK stack does not manage this, and the host repo does not appear to manage model access either, so Terraform leaves it as a manual prerequisite.
- `certificate_arn` default is a placeholder that matches the CDK's imported ARN (all-zeros). The team should set this to a real ACM certificate ARN in their tfvars before first apply.

## Local verification

- `terraform fmt -recursive` was run on `terraform-host/`.
- `terraform init` / `validate` / `plan` are NOT run locally - they need network / registry / state backend access that this environment does not have. The pipeline run is the verification gate.

## Recommended next steps

1. On first `plan`, confirm the Bedrock VPC endpoint subnet attachment. The CDK synth output shows a single private subnet; our Terraform attaches to all three private subnets (the more common HA pattern). Confirm this matches intent.
2. Populate `var.certificate_arn` and `var.cost_center` before apply.
3. Ensure Bedrock model access for Claude 3.5 Sonnet and Claude 3 Haiku is enabled in `eu-central-1` before tasks attempt to call InvokeModel.
