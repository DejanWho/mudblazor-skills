# `cdk synth` Harness for .NET CDK

You use `cdk synth` because the CDK source code doesn't tell you the whole story. CDK fills in defaults (log retention, security group rules, IAM policies for implicit wiring) that never appear in the C# code. The synthesized CloudFormation template does show them, and that's what actually gets deployed. For anything nontrivial, synth is authoritative.

This document covers: how to run synth for a .NET CDK project, what the output looks like, how to map it back to the C# source, and how to pull out the values you need for Terraform.

## Running synth

.NET CDK projects have the same lifecycle as JS/TS ones at the synth layer — the difference is the build step. The CDK CLI runs the app entry point (from `cdk.json` `app` field) and expects it to write CloudFormation templates to `cdk.out/`.

A typical `cdk.json` for a .NET project:

```json
{
  "app": "dotnet run --project src/MyApp/MyApp.csproj"
}
```

To run synth:

```bash
cd <cdk-project-dir>
cdk synth --all --json
```

Flags worth knowing:

- `--all` — synth every stack defined by the app (default only synths the first one if there are multiple).
- `--json` — output JSON instead of YAML. Easier to parse.
- `--quiet` (or `-q`) — suppress the template echo to stdout so only the template JSON is printed.
- `--output <dir>` — specify output dir (default `cdk.out`). Useful if you don't want to touch the project's own `cdk.out`.
- `--context <k>=<v>` — set CDK context values (stage/env config). Sometimes required to make the app build.

To get just the template for one stack:

```bash
cdk synth <StackName> --json --quiet > /tmp/<stack>.template.json
```

To list stacks without synthesizing:

```bash
cdk list
```

### Troubleshooting

**`cdk: command not found`.** Use `npx aws-cdk` instead, or install with `npm install -g aws-cdk`. If neither works, ask the user to run synth themselves and paste the template.

**`dotnet: command not found`.** The .NET SDK isn't installed. Either install .NET 8 SDK or ask the user to run synth.

**`Unable to resolve AWS account to use`.** CDK needs environment context. Try:
```bash
cdk synth --all --json -c @aws-cdk/core:bootstrapQualifier=hnb659fds \
    --profile <aws-profile>
```
Or explicitly: `export AWS_REGION=us-east-1 AWS_DEFAULT_ACCOUNT=000000000000 && cdk synth --all --json`. Some CDK apps use the default account from environment; a bogus account ID often works for pure synth (no bootstrap check).

**`Feature flags not recognized`.** The CDK version in `Amazon.CDK.Lib` NuGet may be newer or older than the `cdk` CLI. Install a matching CLI: `npm install -g aws-cdk@2.<N>` where `<N>` matches the major version in the csproj.

**Build errors in the C# code itself.** CDK has to build before it can synth. Run `dotnet build` separately to see the real errors. If the project won't build, stop — ask the user to fix it first, or fall back to source-only translation with a clear warning.

**The app uses `Amazon.CDK.App` but doesn't call `app.Synth()`.** Unlike JS, .NET CDK does need explicit `app.Synth()` at the end of `Main`. If missing, synth silently produces no output. Grep the entry point; fix if necessary.

**Existing `cdk.out/` as fallback:** before concluding you can't get synth output, check whether `cdk.out/` already exists in the CDK project directory (or an adjacent path the user can point you at). It may contain `*.template.json` files from a previous synth — use them. Check the modification time; if they look fresh relative to the C# source (newer than `*.cs` files), trust them. If they're older, warn the user they may be stale but still use them for structure while treating property values with suspicion.

**No fallback at all:** if neither live synth nor an existing `cdk.out/` is available, tell the user, and proceed with source reading only. Explicitly flag in the final report that values came from source (not synth) and that the CI pipeline's `terraform plan` against deployed resources is the only way to catch discrepancies.

## What synth produces

Running synth creates `cdk.out/`:

```
cdk.out/
├── <StackName>.template.json       ← the CloudFormation template
├── <StackName>.assets.json         ← asset manifest (Lambda zips, Docker images)
├── manifest.json                   ← inventory of stacks and their dependencies
├── cdk.out                         ← marker file
└── tree.json                       ← construct tree (for debugging)
```

The **template.json** is what you parse. It's a standard CloudFormation template with:

- `Resources` — the AWS resources to create (each with `Type`, `Properties`, `Metadata`)
- `Outputs` — stack outputs (cross-stack refs, user-surfaced values)
- `Parameters` — input parameters (rare in CDK; usually used via context instead)
- `Conditions` — conditional creation (rare in CDK)
- `Mappings` — static lookups (rare in CDK)

The **manifest.json** is useful for enumerating stacks:
```json
{
  "version": "36.0.0",
  "artifacts": {
    "MyAppStack.assets": { "type": "cdk:asset-manifest", ... },
    "MyAppStack": {
      "type": "aws:cloudformation:stack",
      "properties": { "templateFile": "MyAppStack.template.json" },
      "dependencies": [...]
    }
  }
}
```

The **tree.json** lets you map logical IDs back to construct paths — crucial for understanding what the C# code intended:
```json
{
  "tree": {
    "children": {
      "MyStack": {
        "children": {
          "MyBucket": {
            "constructInfo": { "fqn": "aws-cdk-lib.aws_s3.Bucket" },
            "children": {
              "Resource": {
                "attributes": {
                  "aws:cdk:cloudformation:type": "AWS::S3::Bucket",
                  "aws:cdk:cloudformation:props": {...}
                }
              }
            }
          }
        }
      }
    }
  }
}
```

## Parsing the template

Load `template.json` with your tool of choice (Bash + `jq`, or Python, or reading via the Read tool). The structure you care about:

```json
{
  "Resources": {
    "MyBucketF68F3FF0": {
      "Type": "AWS::S3::Bucket",
      "Properties": {
        "BucketEncryption": {
          "ServerSideEncryptionConfiguration": [
            { "ServerSideEncryptionByDefault": { "SSEAlgorithm": "AES256" } }
          ]
        },
        "PublicAccessBlockConfiguration": {
          "BlockPublicAcls": true,
          "BlockPublicPolicy": true,
          "IgnorePublicAcls": true,
          "RestrictPublicBuckets": true
        }
      },
      "UpdateReplacePolicy": "Retain",
      "DeletionPolicy": "Retain",
      "Metadata": {
        "aws:cdk:path": "MyStack/MyBucket/Resource"
      }
    }
  }
}
```

Every resource has:

- **Logical ID** (`MyBucketF68F3FF0`) — used for intra-stack refs in CFN.
- **Type** (`AWS::S3::Bucket`) — the AWS resource type.
- **Properties** — the config. **This is the source of truth** for what to put into the Terraform resource.
- **Metadata.`aws:cdk:path`** — the construct path, i.e. where in the C# code this came from.

## Mapping logical IDs to construct paths

Use the `aws:cdk:path` in `Metadata` to trace a resource back to C#. Example path `MyStack/MyService/LB/SecurityGroup/Resource` means:

- `MyStack` — the CDK `Stack` subclass
- `MyService` — a nested construct (maybe a custom service construct)
- `LB` — a load balancer created by that construct
- `SecurityGroup` — the security group the LB created
- `Resource` — the L1 resource leaf

This matters because it tells you where in the C# to look if you need to understand intent. For a raw `aws_s3_bucket` conversion, logical-ID-to-properties is enough; but when CDK L2 wires up multiple resources behind a single method call (`alb.AddListener(...)` creates listener + target group + security group rule + DNS), you need the path to see which resources belong together.

## Extracting physical IDs for imports

CloudFormation templates describe what *will* be created, but `import` blocks need the physical ID of what *is* already there. Sources:

1. **The deployed CloudFormation stack.** `aws cloudformation list-stack-resources --stack-name <name>` returns logical IDs paired with physical IDs. This is the most reliable source.
2. **The synth output + known defaults.** Some resources have deterministic names (e.g. SQS queues without `QueueName` get a name CDK derives from the logical ID). But many (S3 buckets, Lambda functions without explicit names) get random suffixes only the deployed stack knows. Don't guess.
3. **The user.** If you can't query the deployed stack, ask the user for the physical IDs. Provide a template they can fill in.

Physical IDs to capture per service:

| Resource type | Physical ID format | How to get it |
|---|---|---|
| `AWS::S3::Bucket` | bucket name (e.g. `myapp-assets-abc123`) | `aws s3api list-buckets` or stack resource API |
| `AWS::Lambda::Function` | function name | stack resource API |
| `AWS::IAM::Role` | role name | stack resource API |
| `AWS::EC2::VPC` | VPC ID (`vpc-...`) | stack resource API |
| `AWS::DynamoDB::Table` | table name | stack resource API |
| `AWS::ECS::Cluster` | cluster name | stack resource API |
| `AWS::ECS::Service` | `<cluster>/<service>` (compound!) | stack resource API; Terraform format is `cluster/service` |
| `AWS::ElasticLoadBalancingV2::LoadBalancer` | ARN | stack resource API |
| `AWS::ElasticLoadBalancingV2::TargetGroup` | ARN | stack resource API |
| `AWS::ElasticLoadBalancingV2::Listener` | ARN | stack resource API |
| `AWS::RDS::DBInstance` | identifier | stack resource API |
| `AWS::SecretsManager::Secret` | ARN or name | stack resource API (note: import by ARN is safer) |
| `AWS::IAM::ManagedPolicy` | ARN | stack resource API |

Terraform `import` block requirements vary per resource — consult the resource's Terraform docs for the exact ID format it expects. See `import-blocks.md` for examples.

## Cross-stack references

CDK cross-stack refs create CloudFormation Exports/Imports. In synth output you'll see, e.g. in Stack A:

```json
"Outputs": {
  "ExportsOutputFnGetAttVpcABC123Arn": {
    "Value": { "Fn::GetAtt": ["VpcABC123", "Arn"] },
    "Export": { "Name": "MyStackA:ExportsOutputFnGetAttVpcABC123Arn" }
  }
}
```

And in Stack B:
```json
"SomeResource": {
  "Properties": {
    "VpcId": { "Fn::ImportValue": "MyStackA:ExportsOutputFnGetAttVpcABC123Arn" }
  }
}
```

In Terraform, you handle this differently depending on the host repo's conventions:

- **Via module outputs** if both stacks become one root config (the cleanest case).
- **Via `data "terraform_remote_state"`** if they stay as separate root configs using the same S3/DynamoDB backend.
- **Via SSM parameters** (Stack A writes to `/myapp/vpc-id`, Stack B reads with `data "aws_ssm_parameter"`) if the repo uses that pattern.

Check the repo's existing cross-stack pattern (from init) and match it.

## The three-source pattern for each resource

For every CDK resource you're converting, have three views in mind:

1. **C# source** — what the developer wrote. Tells you intent.
2. **Template Properties** — what CloudFormation sees. Tells you actual values (including CDK defaults).
3. **Terraform resource docs** — what the Terraform AWS provider expects. Tells you field names and formats.

Translation is the intersection: take intent and values from (1) + (2), express them in the shape of (3). When (1) and (2) disagree (e.g. the developer wrote `MemorySize = 512` but CDK changed it because of a feature flag), (2) wins.
