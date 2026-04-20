# CDK to Terraform conversion - BedrockChatStack

Converts the greenfield CDK .NET 8 stack `BedrockChatStack-dev` (ALB to Fargate
to Bedrock runtime) into the host Terraform repo, reusing existing modules.

## Files authored

### New live config: `terraform-host/live/dev/bedrock-chat/`
- `versions.tf` - Terraform 1.5+, AWS provider `~> 5.70`, S3 partial backend
  with key `dev/bedrock-chat/terraform.tfstate`, provider `default_tags` for
  `Environment`/`Application`/`ManagedBy`.
- `variables.tf` - env/app/region/CIDR/AZs/cert/image/cpu/memory/port/model ids.
  Defaults mirror the CDK context in `cdk.json` (`vpc-cidr = 10.30.0.0/16`,
  `region = eu-central-1`, sonnet `anthropic.claude-3-5-sonnet-20241022-v2:0`,
  haiku `anthropic.claude-3-haiku-20240307-v1:0`). `cost_center` and
  `certificate_arn` are required (no defaults), matching repo convention.
- `main.tf` - wires the modules and raw resources listed below.
- `outputs.tf` - exposes `alb_dns_name`, `alb_zone_id`, `ecs_cluster_arn`,
  `service_arn`, `task_role_arn`, `bedrock_runtime_endpoint_id`,
  `bedrock_runtime_endpoint_security_group_id`.

### New modules
None. Every CDK construct mapped cleanly onto an existing module or a small
number of raw resources living at the root config layer (matching how
`live/dev/reference-service/` handles its target group and listener rule).

## Mapping: CDK to Terraform

| CDK construct | Terraform |
| --- | --- |
| `Vpc` (3 AZ, NAT per AZ, public + private tiers) | `module.network` (existing `modules/network`) |
| `ApplicationLoadBalancer` + AlbSg + listeners | `module.alb` (existing `modules/alb`): HTTPS 443 w/ TLS13-1-2, HTTP 80 to 443 redirect |
| `Cluster` (containerInsightsV2) | `aws_ecs_cluster.this` inline with `containerInsights = "enhanced"` setting |
| `FargateTaskDefinition` + `FargateService` | `module.app_service` (existing `modules/ecs-service`): cpu=1024, memory=2048, desired=2 |
| `TaskLogGroup` (`/ecs/bedrock-chat-dev`, 30 days) | log group created by the `ecs-service` module as `/ecs/${service_name}`, retention 30d |
| `TaskExecutionRole` + `TaskRole` (assume ecs-tasks) | both created by the `ecs-service` module |
| Bedrock invoke policy scoped to Sonnet + Haiku | `aws_iam_role_policy.bedrock_invoke` at the caller, attached via `task_role_name` output |
| Target group (`/health`, 30s / 10s / 2 / 3, 200) | `aws_lb_target_group.app` + `aws_lb_listener_rule.app` at the root |
| `BedrockEndpointSg` | `aws_security_group.bedrock_endpoint` raw |
| Ingress Fargate to Bedrock endpoint on 443 | `aws_vpc_security_group_ingress_rule.bedrock_endpoint_from_tasks` |
| `InterfaceVpcEndpoint(BEDROCK_RUNTIME)` | `aws_vpc_endpoint.bedrock_runtime` (`com.amazonaws.<region>.bedrock-runtime`, private DNS) |
| ALB to tasks SG on 8080 | handled inside `ecs-service` module |
| Stack tags | provider `default_tags` + explicit `local.common_tags` passed into each module |

### Naming
- `service_name = "${application}-${environment}"` resolves to `bedrock-chat-dev`,
  which drives the log group name `/ecs/bedrock-chat-dev` matching the CDK
  stack's explicit `LogGroupName`.
- ALB name, ECS cluster name, target group name all follow the
  `${application}-${environment}[-tier]` pattern used by `reference-service`.

### Why no new module
- The existing `alb` module already emits both listeners (HTTPS + HTTP to HTTPS
  redirect) and the front SG; its HTTPS listener uses the TLS 1.3 policy that
  matches the CDK `SslPolicy.TLS13_12`.
- The existing `ecs-service` module already creates exec role, task role, task
  SG (with ALB ingress rule), log group `/ecs/<service>`, task def, and service
  with `assign_public_ip=false`, all matching the CDK behaviour.
- Bedrock-specific bits (VPC interface endpoint, endpoint SG, and the
  resource-scoped `bedrock:InvokeModel[WithResponseStream]` inline policy) are
  single-service glue. Per repo conventions these live at the root config as
  raw resources (the `iam-role` module README explicitly recommends adding
  task-role policies via `aws_iam_role_policy` at the caller using the
  `ecs-service` module's `task_role_name` output).

## Deltas from the CDK stack worth flagging

- **Certificate ARN**: CDK hard-coded a placeholder ACM ARN. The Terraform
  version takes it as a required `certificate_arn` variable (matching the
  reference-service pattern); the caller supplies the real ARN at apply time.
- **Bedrock endpoint subnets**: CDK put the endpoint in every AZ's private
  subnet; Terraform does the same via `module.network.private_subnet_ids`.
- **ECS cluster**: CDK uses `ContainerInsights.ENABLED` (v2) which synths to
  `containerInsights = "enhanced"`; Terraform matches with `"enhanced"`.
- **Container image**: `public.ecr.aws/nginx/nginx:stable` kept as the default,
  overridable via `var.container_image` when the real app image is ready.
- **HTTP to HTTPS redirect**: handled by the alb module's default 80 to 443 301.
- **`CDK_DEFAULT_ACCOUNT`**: CDK used the env var at synth time; Terraform
  does not need it, the provider picks up credentials from the caller's env.

## Formatting / validation

- `terraform fmt -recursive terraform-host/` could not be executed (Bash was
  denied permission for `terraform fmt` in this session). All authored files
  are written in `terraform fmt` canonical form: 2-space indent, aligned `=`
  within blocks, one blank line between resource stanzas, matching the existing
  modules.
- `terraform init / validate / plan` not run per the task's environment
  constraints (no internet, provider plugins cannot be downloaded).
- Files contain zero C# or CDK syntax, only HCL.
