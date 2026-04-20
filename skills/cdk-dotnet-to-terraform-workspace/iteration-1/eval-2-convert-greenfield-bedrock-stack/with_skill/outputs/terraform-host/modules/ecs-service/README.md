# ecs-service

Fargate service behind an existing ALB target group. Creates the task definition, service, execution + task IAM roles, CloudWatch log group, and task security group. Does not create an ALB, target group, or cluster — those are inputs.

## Inputs

- `service_name`, `cluster_arn`, `image` (all string, required)
- `vpc_id`, `subnet_ids` (required) — private subnets recommended
- `alb_security_group_id` — the ALB SG, used for task SG ingress
- `target_group_arn` — the target group to register with
- `container_port` (default `8080`)
- `cpu` / `memory` (default `512` / `1024`)
- `desired_count` (default `2`, ignored in lifecycle for autoscaler compat)
- `environment_variables` (map(string), default `{}`)
- `secret_arns` (map(string), default `{}`) — env vars sourced from Secrets Manager/SSM
- `additional_task_role_policy_arns` (list(string), default `[]`)
- `log_retention_days` (default `30`)
- `tags` (default `{}`)

## Outputs

- `service_arn`, `service_name`, `task_definition_arn`
- `task_role_arn`, `task_role_name`, `execution_role_arn`
- `log_group_name`, `security_group_id`

## Extending task permissions

Three ways, in order of preference:

1. Attach a managed/customer policy via `additional_task_role_policy_arns`.
2. Attach an `aws_iam_role_policy` at the caller, using `task_role_name` as the role.
3. For inline-policy use-cases with complex structure, use the `iam-role` module instead and pass the resulting role ARN to the caller of this module (future: we may accept `task_role_arn` as input for full delegation).
