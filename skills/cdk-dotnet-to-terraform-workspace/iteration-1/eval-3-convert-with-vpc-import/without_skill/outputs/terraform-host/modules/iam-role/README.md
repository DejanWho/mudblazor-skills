# iam-role

Stand-alone IAM role with trust policy, managed policy attachments, and keyed inline policies. Used for task roles, Lambda execution roles, service-linked roles, etc.

## Inputs

- `name` (string, required) — role name.
- `trust_policy_json` (string, required) — trust policy as JSON. Prefer `data.aws_iam_policy_document.<x>.json` at the caller; `jsonencode(...)` is fine too.
- `managed_policy_arns` (list(string), default `[]`)
- `inline_policies` (map(string), default `{}`) — keyed by policy name, value is policy JSON.
- `max_session_duration` (number, default `3600`)
- `tags` (default `{}`)

## Outputs

- `role_arn`, `role_name`, `role_id`

## Pattern: task role with Bedrock access

```hcl
data "aws_iam_policy_document" "bedrock_trust" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "bedrock_invoke" {
  statement {
    actions   = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
    resources = [local.claude_sonnet_arn, local.claude_haiku_arn]
  }
}

module "task_role" {
  source            = "../../modules/iam-role"
  name              = "${var.service_name}-task"
  trust_policy_json = data.aws_iam_policy_document.bedrock_trust.json
  inline_policies = {
    bedrock = data.aws_iam_policy_document.bedrock_invoke.json
  }
  tags = local.tags
}
```
