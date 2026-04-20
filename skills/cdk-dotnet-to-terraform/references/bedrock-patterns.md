# Bedrock / Anthropic-on-AWS Patterns

Amazon Bedrock is a managed service for foundation models (including Anthropic Claude). Unlike EC2 or Lambda, Bedrock has **no infrastructure resource you provision** for the model itself — you enable *model access* at the account/region level via the Bedrock console (or the `aws_bedrock_*_access` resources in newer providers), and then your application invokes the model via the Bedrock Runtime API.

That means the Terraform output for a "Bedrock deployment" is usually **not** a Bedrock resource at all — it's the *surrounding* infrastructure:

- IAM roles/policies with `bedrock:InvokeModel` (and related) permissions
- Optional VPC endpoint(s) for `bedrock-runtime` if traffic stays in the VPC
- Optional agents, knowledge bases, guardrails, custom models (these *do* have Terraform resources)
- The compute that calls Bedrock (Fargate, Lambda, EC2) and the load balancer in front of it

Below: the patterns you'll run into and their Terraform translations.

## 1. Model access

CDK has no construct for "enable Claude in Bedrock" because that's an account-level toggle. Terraform has `aws_bedrock_model_invocation_logging_configuration` and, in recent provider versions, `aws_bedrock_foundation_model_agreement_acceptance` — but many teams manage model access out-of-band (Bedrock console) and keep Terraform focused on the infra.

**What to do:** do not try to manage model access in Terraform unless the host repo already does. If you find `aws_bedrock_model_invocation_logging_configuration` in the existing Terraform, extend that pattern; otherwise, leave model access as a manual prerequisite and mention it in the final report.

## 2. IAM for invoking Bedrock

This is the piece you almost always need to generate. CDK typically looks like:

```csharp
role.AddToPolicy(new PolicyStatement(new PolicyStatementProps {
    Actions = new[] {
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
    },
    Resources = new[] {
        $"arn:aws:bedrock:{region}::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0",
        $"arn:aws:bedrock:{region}::foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
    }
}));
```

**Terraform:**

```hcl
data "aws_iam_policy_document" "bedrock_invoke" {
  statement {
    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream",
    ]
    resources = [
      "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0",
      "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/anthropic.claude-3-haiku-20240307-v1:0",
    ]
  }
}

resource "aws_iam_role_policy" "bedrock_invoke" {
  role   = aws_iam_role.app.id
  policy = data.aws_iam_policy_document.bedrock_invoke.json
}
```

**Gotchas:**

- **Model IDs are region-scoped.** The ARN format is `arn:aws:bedrock:<region>::foundation-model/<model-id>`. Double colon between region and `foundation-model` — the account segment is empty because foundation models are AWS-owned.
- **Cross-region inference profiles** have a different ARN: `arn:aws:bedrock:<region>:<account>:inference-profile/<profile-id>`. Action is `bedrock:InvokeModel*` same as above, but resources include *both* the profile ARN and the underlying model ARNs in all constituent regions. If the CDK code references cross-region profiles (newer Anthropic models use them for Claude 3.5 Sonnet v2 availability), translate both.
- **Streaming** — `InvokeModelWithResponseStream` is a separate action from `InvokeModel`. If the CDK policy only grants `InvokeModel` but the app uses streaming, the Lambda/Fargate call will 403 at runtime. Match CDK exactly; don't narrow the policy.
- Don't grant `bedrock:*` unless the CDK did. Least-privilege is the pattern.

## 3. VPC endpoint for bedrock-runtime (private networking)

If the CDK stack puts compute in private subnets and you want Bedrock traffic to stay inside the VPC (not go through the NAT gateway), you need an interface VPC endpoint.

CDK:
```csharp
vpc.AddInterfaceEndpoint("BedrockRuntimeEndpoint", new InterfaceVpcEndpointOptions {
    Service = InterfaceVpcEndpointAwsService.BEDROCK_RUNTIME,
    PrivateDnsEnabled = true
});
```

Terraform:
```hcl
resource "aws_vpc_endpoint" "bedrock_runtime" {
  vpc_id              = module.network.vpc_id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.bedrock-runtime"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = module.network.private_subnet_ids
  security_group_ids  = [aws_security_group.bedrock_endpoint.id]
  private_dns_enabled = true
}
```

**Gotchas:**

- The endpoint security group must allow **ingress on 443 from whatever calls it** (Fargate task SG, Lambda SG). This is easy to miss.
- Some agent/KB features need *both* `bedrock-runtime` AND `bedrock-agent-runtime` endpoints. CDK creates both if you use the Agents L2. Check synth output for multiple `AWS::EC2::VPCEndpoint` resources.
- The endpoint costs ~$0.01/hour per AZ. Teams sometimes skip it in dev and only create it in prod — respect whatever the CDK code does.

## 4. Bedrock Agents

Newer feature, newer CDK constructs (`Amazon.CDK.AWS.BedrockAgent`, sometimes `Amazon.CDK.AWS.Bedrock.Alpha`). Maps to Terraform `aws_bedrockagent_agent`, `aws_bedrockagent_agent_action_group`, `aws_bedrockagent_agent_alias`.

CDK:
```csharp
var agent = new Agent(this, "Agent", new AgentProps {
    FoundationModel = BedrockFoundationModel.ANTHROPIC_CLAUDE_3_5_SONNET_V2_0,
    Instruction = "You are a helpful assistant for ...",
    Name = "support-agent"
});
```

Terraform:
```hcl
resource "aws_bedrockagent_agent" "support" {
  agent_name                  = "support-agent"
  agent_resource_role_arn     = aws_iam_role.agent.arn
  foundation_model            = "anthropic.claude-3-5-sonnet-20241022-v2:0"
  instruction                 = "You are a helpful assistant for ..."
  idle_session_ttl_in_seconds = 1800
}
```

**Gotchas:**

- The agent needs its own IAM role (`agent_resource_role_arn`). CDK synthesises this role automatically; in Terraform you write it explicitly with trust policy for `bedrock.amazonaws.com` and an inline policy allowing `bedrock:InvokeModel` on the foundation model.
- `agent_resource_role_arn` must have a specific name pattern in some accounts (historical; check existing Bedrock resources in your repo).
- Action groups reference Lambda functions — wire those up separately.

## 5. Knowledge Bases

CDK: `Amazon.CDK.AWS.BedrockAgent.KnowledgeBase` (or the alpha module).

Terraform: `aws_bedrockagent_knowledge_base`. Requires:

- An OpenSearch Serverless collection (or Pinecone, RDS, etc.) for vector storage — `aws_opensearchserverless_collection` + `aws_opensearchserverless_security_policy` + `aws_opensearchserverless_access_policy` if you're using that backend
- An S3 bucket + `aws_bedrockagent_data_source` for ingestion
- An IAM role for the KB with permissions to read S3 and write to the vector store

This is a large amount of wiring. Strong candidate for a repo module if the team uses KBs more than once.

## 6. Guardrails

CDK: `Amazon.CDK.AWS.Bedrock.CfnGuardrail` (L1) or alpha L2.

Terraform: `aws_bedrock_guardrail` + `aws_bedrock_guardrail_version`. Mostly property-for-property.

## 7. Custom models / provisioned throughput

Much rarer. CDK may use L1 constructs (`CfnModelCustomizationJob`, `CfnProvisionedModelThroughput`). Terraform: `aws_bedrock_custom_model`, `aws_bedrock_provisioned_model_throughput`. Mention in the report; default is to convert only if present in the CDK code.

## 8. Typical end-to-end architecture

The common shape — and the one the user described — is: **ALB → Fargate (or Lambda) → Bedrock**. Here's what converts to what:

| CDK layer | Terraform destination |
|---|---|
| `Vpc` + subnets + NAT + VPC endpoints for bedrock-runtime, ECR, S3, CloudWatch Logs | repo's `network` module (or author one) |
| `Cluster` (ECS) + `FargateTaskDefinition` + `FargateService` | repo's `ecs-service` / `fargate-service` module (or author one) |
| `ApplicationLoadBalancer` + listener + target group | repo's `alb` / `load-balancer` module (often combined with the ECS service module) |
| `Role` for the Fargate task (task role) with `bedrock:InvokeModel` + `logs:CreateLogStream` etc | raw `aws_iam_role` + `aws_iam_role_policy` in the service module, or a `iam-role` module if the repo has one |
| `Role` for the Fargate task execution (pull image, write logs) | same as above |
| `LogGroup` at `/ecs/<service>` | `aws_cloudwatch_log_group` in the service module |
| Config via `Environment` variables + `Secrets` (Secrets Manager) | `environment` and `secrets` arrays in the task definition container_definitions JSON; `aws_secretsmanager_secret` + `aws_iam_role_policy` granting `secretsmanager:GetSecretValue` for each referenced secret |

If there's an **API Gateway** between the ALB-equivalent and Fargate (e.g. `HttpApi` + VPC link to an NLB), the pattern shifts — but most Bedrock-backed apps use a plain ALB because streaming works better over long-lived HTTP than through API Gateway.

## 9. Things to watch for in CDK-for-Bedrock code

- **Cross-region model calls.** If the app is deployed in `us-west-2` but calls a model only available in `us-east-1`, the IAM policy must allow the `us-east-1` model ARN, and the app must specify that region in the Bedrock client. Terraform should faithfully reproduce whatever the CDK code does.
- **Inference profiles.** Newer pattern; the app calls an inference profile ID, and AWS routes to the best region. Different IAM shape (see §2 above).
- **Request-response logging to CloudWatch / S3.** `aws_bedrock_model_invocation_logging_configuration` is the Terraform resource. One per region. If the CDK code creates this, convert it — but note that it's a singleton, so don't create multiple if there are multiple stacks.
- **Agents with multiple action groups.** Each action group is its own `aws_bedrockagent_agent_action_group`. Wire them to the parent agent via `agent_id`.
- **Guardrail versions vs drafts.** Agents reference a guardrail *version*; the resource `aws_bedrock_guardrail_version` creates immutable snapshots. Publishing a new version is an explicit step — preserve the versioning strategy from CDK if present.

## 10. One more gotcha: model IDs in variables

Model IDs change over time (new Claude versions). CDK code often hardcodes the string. In Terraform, *consider* making the model ID a variable on the relevant module rather than a hardcoded value, so bumping the model is a tfvars change instead of a module edit. But only do this if the host repo's existing modules parameterise similar values — don't invent a new convention. If uncertain, keep it hardcoded and surface the ID in the final report so the user knows where to change it later.
