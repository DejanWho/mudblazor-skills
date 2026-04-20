# Terraform `import` Blocks

Terraform 1.5 introduced `import` blocks — a declarative way to adopt existing AWS resources into Terraform state. Unlike the older `terraform import` CLI, `import` blocks are checked in as code, plan against the next apply, and are skipped once the resource is in state. That makes them perfect for converting a deployed CDK stack to Terraform without data loss.

This document covers: the syntax, how to generate blocks from `cdk synth` output, the per-resource ID formats, and the pitfalls.

## Syntax

```hcl
import {
  to = aws_s3_bucket.this
  id = "my-bucket-abc123"
}

resource "aws_s3_bucket" "this" {
  bucket = "my-bucket-abc123"
  # ...
}
```

Rules:

- `to` is a resource address — must match an actual resource in your configuration.
- `id` is the string Terraform passes to the provider to look the resource up. Format is resource-specific.
- For resources inside modules: `to = module.my_service.aws_lb.this`.
- For `for_each`/`count`: `to = module.my_service.aws_lb.this["primary"]` or `[0]`.
- Import blocks are **additive** — first `plan` shows what would be adopted, and `apply` actually adopts. If the resource already exists in state, the import block becomes a no-op (so it's safe to leave in until cleanup).

Terraform can generate `.tf` directly from imports using `terraform plan -generate-config-out=<file.tf>`. That command needs the provider downloaded and network access, so it's pipeline-only in this environment. Not available as a local shortcut — write the `.tf` by hand or from synth output. (If the user has an old pipeline artefact of `generate-config-out` output, they can share it as a starting scaffold, but it won't match repo conventions without reshaping.)

## Recommended layout

Put import blocks in a dedicated file per root config: `imports.tf`. One block per resource, commented with the CDK construct path so humans can trace it:

```hcl
# From CDK: MyStack/MyBucket
import {
  to = aws_s3_bucket.assets
  id = "myapp-assets-prod-abc123"
}

# From CDK: MyStack/MyService/TaskRole
import {
  to = module.service.aws_iam_role.task
  id = "MyStack-MyServiceTaskRole-1234567890ABC"
}
```

The comment block is mandatory. Reviewers need to verify that the CDK resource and the Terraform resource genuinely correspond.

## Per-resource ID formats

Terraform resource import IDs aren't standardised — each resource type documents its own format. Below are the common ones for Bedrock/ALB/Fargate/Lambda patterns. When in doubt, check the Terraform AWS provider docs for the resource and look for the "Import" section.

| Resource | Import ID format | Example |
|---|---|---|
| `aws_vpc` | VPC ID | `vpc-0a1b2c3d4e5f6a7b8` |
| `aws_subnet` | Subnet ID | `subnet-0a1b2c3d4e5f6a7b8` |
| `aws_security_group` | Security Group ID | `sg-0a1b2c3d4e5f6a7b8` |
| `aws_vpc_security_group_ingress_rule` | Rule ID | `sgr-0a1b2c3d4e5f6a7b8` |
| `aws_internet_gateway` | IGW ID | `igw-0a1b2c3d4e5f6a7b8` |
| `aws_nat_gateway` | NAT GW ID | `nat-0a1b2c3d4e5f6a7b8` |
| `aws_route_table` | Route Table ID | `rtb-0a1b2c3d4e5f6a7b8` |
| `aws_vpc_endpoint` | Endpoint ID | `vpce-0a1b2c3d4e5f6a7b8` |
| `aws_s3_bucket` | Bucket name | `my-bucket-name` |
| `aws_s3_bucket_server_side_encryption_configuration` | Bucket name | `my-bucket-name` |
| `aws_s3_bucket_versioning` | Bucket name | `my-bucket-name` |
| `aws_s3_bucket_public_access_block` | Bucket name | `my-bucket-name` |
| `aws_s3_bucket_lifecycle_configuration` | Bucket name | `my-bucket-name` |
| `aws_lambda_function` | Function name | `my-function` |
| `aws_iam_role` | Role name | `MyStack-TaskRole-1ABC2DEF3GHI4` |
| `aws_iam_role_policy` | `<role-name>:<policy-name>` | `MyStack-TaskRole-1ABC2DEF3GHI4:default` |
| `aws_iam_role_policy_attachment` | `<role-name>/<policy-arn>` | `MyRole/arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole` |
| `aws_iam_policy` | Policy ARN | `arn:aws:iam::123456789012:policy/MyPolicy` |
| `aws_ecs_cluster` | Cluster name | `my-cluster` |
| `aws_ecs_service` | `<cluster-name>/<service-name>` | `my-cluster/my-service` |
| `aws_ecs_task_definition` | Family or family:revision | `my-task` or `my-task:42` |
| `aws_lb` | ARN | `arn:aws:elasticloadbalancing:us-east-1:123:loadbalancer/app/my-alb/abc` |
| `aws_lb_listener` | ARN | `arn:aws:elasticloadbalancing:us-east-1:123:listener/app/my-alb/abc/def` |
| `aws_lb_target_group` | ARN | `arn:aws:elasticloadbalancing:us-east-1:123:targetgroup/my-tg/abc` |
| `aws_lb_listener_rule` | ARN | `arn:aws:elasticloadbalancing:us-east-1:123:listener-rule/app/my-alb/abc/def/ghi` |
| `aws_cloudwatch_log_group` | Log group name | `/ecs/my-service` |
| `aws_cloudwatch_metric_alarm` | Alarm name | `my-alarm` |
| `aws_dynamodb_table` | Table name | `my-table` |
| `aws_db_instance` | Identifier | `my-db` |
| `aws_rds_cluster` | Cluster identifier | `my-cluster` |
| `aws_rds_cluster_instance` | Instance identifier | `my-cluster-1` |
| `aws_secretsmanager_secret` | ARN | `arn:aws:secretsmanager:us-east-1:123:secret:my-secret-abc` |
| `aws_ssm_parameter` | Parameter name (with leading `/` if any) | `/myapp/config/db-url` |
| `aws_kms_key` | Key ID (not alias) | `abc1234d-1234-5678-9abc-def012345678` |
| `aws_kms_alias` | Alias name (with `alias/` prefix) | `alias/my-app` |
| `aws_sqs_queue` | Queue URL | `https://sqs.us-east-1.amazonaws.com/123/my-queue` |
| `aws_sns_topic` | Topic ARN | `arn:aws:sns:us-east-1:123:my-topic` |
| `aws_bedrockagent_agent` | Agent ID | `ABCDEFGHIJ` |
| `aws_bedrockagent_agent_action_group` | `<agent-id>,<agent-version>,<action-group-id>` | `ABCDEFGHIJ,DRAFT,KLMNOPQRST` |
| `aws_bedrockagent_knowledge_base` | Knowledge base ID | `ABCDEFGHIJ` |
| `aws_bedrock_guardrail` | Guardrail ID | `abcd1234efgh` |

Cross-check against the Terraform provider docs for the exact format — some resources have multiple valid formats (ARN vs ID) and the provider accepts both.

## Getting physical IDs from a deployed stack

The fastest way to harvest IDs from a live CloudFormation stack:

```bash
aws cloudformation list-stack-resources \
    --stack-name <StackName> \
    --query "StackResourceSummaries[].[LogicalResourceId,PhysicalResourceId,ResourceType]" \
    --output table
```

Pipe into your conversion: match each `LogicalResourceId` with the `Metadata.aws:cdk:path` in the template (both should share the same logical ID), and the `PhysicalResourceId` is what goes into the `id` of the import block.

If the user doesn't have AWS CLI access in this session, generate a *scaffold* imports.tf with `id = "FILL_ME_IN"` for each resource and include a comment with the logical ID + resource type + a hint on how to find it. The user can fill in the IDs later.

## The first `terraform plan` after import

Expect drift. Common sources:

1. **IAM policy JSON reformatting.** AWS stores policies with specific whitespace and statement ordering that differs from what the CDK emitted. Fix: format the policy document in Terraform to match what's deployed. Use `data.aws_iam_policy_document` — it produces consistent output.

2. **Implicit defaults set by AWS.** Some resources have optional properties that default server-side. If you don't set them in Terraform, plan shows them as "change from X to null." Either set them explicitly or accept the drift on one apply.

3. **Tag ordering.** Tags are stored unordered in AWS but Terraform renders them in map order. First plan will often show tag map rewrites — benign, but visible.

4. **S3 bucket configurations.** The post-2022 S3 resources (`aws_s3_bucket_versioning`, etc.) often show drift for buckets imported from CFN, because CFN's `AWS::S3::Bucket` bundles these settings in its `Properties` but Terraform splits them. Each of the split resources needs its own `import` block pointing at the bucket name. If you forget one (e.g. you imported `aws_s3_bucket` but not `aws_s3_bucket_public_access_block`), first plan will try to *create* the block — which will fail or duplicate state.

5. **ECS service `desired_count`.** If the service autoscaler adjusted the count after deploy, your Terraform `desired_count` will drift. Teams handle this with `ignore_changes = [desired_count]` — check the existing pattern in the repo.

6. **Lambda code.** `aws_lambda_function` tracks the `filename` or `s3_key` of the code. If CDK uploaded a zip to a CDK-managed bucket you're not recreating, the import will point at an artefact Terraform can't rebuild. Set `ignore_changes = [source_code_hash, filename, s3_key]` as a pragmatic fix, or make the Terraform Lambda module fetch the same zip from S3.

7. **CDK-generated logical IDs baked into resource names.** CDK names resources by hashing the construct path. If the CFN has `MyStack-MyBucket12345-abc` as the bucket name and your Terraform uses `bucket = "myapp-assets"`, first apply will try to create a new bucket. Either keep the CDK-generated name (ugly but safe) or rename with a `moved` block and a multi-step migration — depends on how much the team cares about the name.

## Moved blocks for within-state reorganization

If you're converting iteratively — first a partial import, then re-organizing resources into modules — use `moved` blocks to rename without recreating:

```hcl
moved {
  from = aws_s3_bucket.assets
  to   = module.storage.aws_s3_bucket.assets
}
```

`moved` blocks are different from `import`: they reorganize state, they don't adopt new resources. Useful when you realise after import that a resource should be inside a module.

## Removed blocks

For resources that CDK created but you want Terraform to no longer manage (without destroying them in AWS):

```hcl
removed {
  from = aws_cloudwatch_log_group.orphan
  lifecycle {
    destroy = false
  }
}
```

Useful for CDK-created log groups, custom resources, etc., that you don't want to bring into Terraform management.

## The pragmatic import workflow

Local environment note: `terraform init`, `terraform validate`, and `terraform plan` all need network access and are not available locally in this setup. All of those steps happen in the user's CI pipeline (whatever form that takes — the skill doesn't need to know). The skill's local job is to produce `.tf` that parses cleanly (`terraform fmt`) and that a human read-through doesn't flag as obviously wrong.

1. Generate the Terraform code (Phase 3 of convert workflow).
2. Generate `imports.tf` with every `import` block keyed to the deployed stack's physical IDs.
3. Run `terraform fmt` on the touched directories. Read through the output with fresh eyes — watch for undefined variables, type mismatches on module inputs, and obvious typos in attribute references. No local `terraform validate` is possible.
4. User pushes to the branch. The CI pipeline runs Terraform against real providers and state.
5. User shares the pipeline output (or the relevant errors / plan diff). Expect drift on first plan (see the list above). Iterate on the Terraform code, push again.
6. Once plan is acceptable, user runs the pipeline's apply step — imports happen here. Resources are now in state; the plan going forward is clean.
7. User deletes `imports.tf` (or leaves it; blocks are no-ops once imported).

Step 4 / 5 is where most real-world problems show up. Don't promise a clean plan on first try — promise a clear diff and a plan that's possible to resolve iteratively through the pipeline.
