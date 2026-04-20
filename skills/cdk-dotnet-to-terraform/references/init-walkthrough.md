# Init Walkthrough

This is the step-by-step procedure for init mode. The goal is two files: `references/repo-conventions.md` (how the host repo writes Terraform) and `references/module-inventory.md` (what modules exist and what they do). Future conversions use these files as ground truth.

Treat init as research, not scaffolding. You're reading the repo to learn, not applying a template.

## Step 1 — Find the Terraform

Search the repo for `.tf` files and group by directory. Use `Glob` for this; the typical layouts are:

- `terraform/`, `infra/`, `iac/`, `deploy/` at the repo root
- `modules/` + `live/` or `modules/` + `envs/` or `modules/` + `stacks/` split
- Per-application trees: `apps/<name>/infra/` or `services/<name>/terraform/`

Some repos have **multiple independent Terraform trees**. Enumerate them all. If there's more than one, ask the user which one the CDK conversion is meant to feed into — they may want different conventions for different trees.

Watch for:
- `.tf.json` files (generated; skim but don't treat as source of truth for style)
- `*.tfvars` files (environment-specific inputs; useful for understanding live/ conventions)
- `.terraform/` dirs (ignore; provider downloads)
- `.terraform.lock.hcl` (note version pins; surface in conventions)

## Step 2 — Classify each Terraform directory

For each directory with `.tf` files, decide what kind of thing it is:

- **Module**: has `variables.tf` + `outputs.tf`, probably a `main.tf`, probably no `backend` block, probably no `provider` block (or providers-block only, not `provider "aws" { region = ... }`).
- **Root / live config**: has a `terraform { backend ... required_version ... }` block, has `provider "aws"` (or similar), consumes modules via `module "..." { source = ... }`.
- **Example / fixture / test**: often under `examples/`, `test/`, or `tests/` — skim but don't treat as representative of production style.

Write this classification down — you'll use it to pick what to read next.

## Step 3 — Sample 3–5 modules

Don't read every module; read representatives. Pick different categories:

- A **networking** module if one exists (`vpc`, `network`, `subnets`)
- A **compute** module (`ecs-service`, `lambda`, `ec2-asg`)
- A **stateful** module (`rds`, `dynamodb`, `s3-bucket`)
- A **utility** module (`iam-role`, `security-group`, `log-group`)

For each one, answer:

1. **File layout.** What's in `main.tf` vs `variables.tf` vs `outputs.tf` vs `versions.tf` vs `locals.tf`? Is there a `README.md`? An `examples/` dir inside?
2. **Variable style.** `snake_case` or `camelCase`? Are defaults common, or are most variables required? Are types always declared (`type = string`)? Are descriptions always present? Are validations used?
3. **Output style.** Naming convention (`vpc_id`, `vpc_arn`, `cluster_name`)? Are outputs always documented with `description`? Are sensitive outputs marked `sensitive = true`?
4. **Tag pattern.** Is there a `tags` variable? A `locals.tf` that merges a `tags_common` with a per-module tag? Does the repo use `default_tags` on the provider and skip module-level tagging?
5. **Provider declaration.** Inside modules (`provider "aws" { alias = "..." }`), or only in root configs? Are required providers declared in every module's `versions.tf`?
6. **Sub-resource wiring.** How are child resources named (resource name = module name? suffixes like `_primary`, `_replica`?)? Is `count`/`for_each` common?
7. **README style.** Is there a standard README per module? Headings? Auto-generated via `terraform-docs`?

## Step 4 — Sample 2 root / live configs

Read two root configs, ideally for different environments (dev, prod) if they exist.

Answer:

1. **Environment layout.** One folder per environment with duplicated `.tf`? Workspaces? A single config parameterised by `.tfvars`?
2. **Backend config.** Where's state stored? S3 + DynamoDB? Terraform Cloud? Is there a partial backend with `-backend-config` at init time?
3. **Provider config.** Region set in one place or everywhere? `default_tags` in the provider? Any assume-role config?
4. **Module consumption.** `source = "../../modules/vpc"` (relative path)? `source = "git::..."` (git)? `source = "app.terraform.io/..."` (private registry)? Are versions pinned?
5. **Cross-module refs.** How does the ECS module get the VPC ID? Module output pass-through? `data "terraform_remote_state"`? SSM parameters read via `data "aws_ssm_parameter"`?
6. **Secrets.** How do secrets flow into Terraform? `aws_secretsmanager_secret_version` with external-set values? SSM SecureString parameters? Environment variables + `TF_VAR_`?

## Step 5 — Spot the invariants

After your reads, write down the **invariants** — things that are consistent across examples. These become the rules for future conversion:

- File layout standard (always `main.tf` + `variables.tf` + `outputs.tf` + `versions.tf`, or variation)
- Variable naming convention
- Output naming convention with standard suffixes (`_id`, `_arn`, `_name`)
- Tag handling approach (pick one: `default_tags` on provider / explicit `tags` variable per module / both)
- Resource naming convention (`resource "aws_vpc" "this"` vs `resource "aws_vpc" "main"` vs `"primary"`)
- `count` / `for_each` usage patterns
- `locals.tf` usage — what kind of thing goes in locals vs variables

If you can't find a clear invariant on some dimension (e.g. half the modules use `"this"` and half use `"main"`), pick the one in the *newest* module (most recent git log on the file) and document in the conventions file that there's inconsistency.

## Step 6 — Write `references/repo-conventions.md`

Use `references/repo-conventions.md.template` as the shape. Fill every `<FILL IN>`. Structure:

1. **Repo layout** — where Terraform lives, any separate trees
2. **Module location** — absolute and relative paths, how modules are referenced from root configs
3. **File layout inside a module** — standard file set, what goes where
4. **Naming conventions** — resources, variables, outputs, modules themselves
5. **Tagging convention** — source of tags, required keys, how modules accept extra tags
6. **Provider config** — where declared, required_providers, version pins
7. **Backend config** — S3 key pattern, region, DynamoDB table, workspace usage
8. **Environment layout** — folder-per-env vs workspaces vs tfvars
9. **Cross-module references** — module outputs vs remote state vs SSM
10. **Version pinning** — Terraform version floor, AWS provider floor
11. **README style** — whether modules document their inputs/outputs, format used
12. **Inconsistencies noted** — where the repo isn't fully consistent, and which pattern to prefer going forward

If something genuinely doesn't apply to this repo, write `N/A — <reason>`. Don't leave a placeholder.

**Record observed values, not just patterns.** When you see a concrete value in the repo — the default AWS region (`eu-central-1`), the Terraform version floor (`>= 1.5, < 2.0`), the AWS provider pin (`~> 5.70`), the S3 state-key convention (`<env>/<app>/terraform.tfstate`), the required tag keys (`Environment`, `Application`, `CostCenter`, `ManagedBy`) — write the literal value in the conventions file, not an abstract description. "Single-region pattern" is not as useful to a future conversion as "eu-central-1 (Frankfurt) is the default region." Future Claude sessions and human reviewers both need the concrete facts. If a value varies across examples, name each value you saw and pick the canonical one.

## Step 7 — Write `references/module-inventory.md`

Use `references/module-inventory.md.template` as the shape. One line per module:

```
- `<module-path>` — <one-sentence description of what it creates> (inputs: <key inputs>; outputs: <key outputs>)
```

Examples (imagined):
```
- `modules/network` — VPC with 3 public + 3 private subnets, NAT gateway per AZ (inputs: cidr, azs, name; outputs: vpc_id, private_subnet_ids, public_subnet_ids)
- `modules/ecs-service` — Fargate service behind an existing ALB with CloudWatch logging (inputs: service_name, image, task_cpu, task_memory, vpc_id, subnet_ids, target_group_arn; outputs: service_arn, task_definition_arn)
- `modules/lambda` — Python/Node Lambda with zip-based deploy, optional VPC attachment (inputs: function_name, handler, runtime, source_path; outputs: function_arn, function_name)
- `modules/iam-role` — IAM role with managed-policy attachments and an optional inline policy (inputs: role_name, trust_policy, managed_policy_arns, inline_policy_json; outputs: role_arn, role_name)
```

The description should make it possible to decide, from the inventory alone, whether a CDK construct would match this module. Include the *shape* (inputs/outputs), not just the name.

## Step 8 — Present to the user

Summarise to the user in the chat:

- Where Terraform lives in their repo
- How many modules you found, with the inventory list
- The key conventions (3–5 bullet points they should confirm)
- Anything you were unsure about (ask them to clarify)

Ask them to review and correct. If they correct something — tags are actually applied differently, the `vpc` module they pointed you to is deprecated, etc. — update the conventions file and re-show.

Only treat the files as authoritative after the user confirms.

## Edge cases

**The repo has no Terraform yet.** Say so. Ask the user for their preferences: module location, file structure, tag convention, backend config, naming style. Record their answers in the conventions file. Don't invent defaults — the user is making policy here, not you.

**The repo has multiple Terraform trees with different conventions.** Write one conventions file per tree? Or ask which tree is the target and focus on that one? In practice, ask the user. Most teams have one "blessed" tree and some legacy; they'll tell you which one matters.

**The modules are in a separate repo (vendored via git source).** You can't always read them. Do your best with what you can reach — at minimum, scrape module calls in root configs to learn *which* modules are used and *what inputs* they accept. If a module's source is `git::https://...`, mention in the inventory that the source is external; the user may need to share access or copy the module in.

**The conventions are genuinely chaotic.** If there's no consistent style, say so. Then ask the user: do they want you to pick a style (and propose one based on the newest / most-used modules) or would they rather set a convention themselves? Either way, record the decision in the conventions file so future conversions don't drift.

**The user wants to skip init.** If they say "just convert it, I'll deal with style later" — push back once. Explain that without repo conventions, the output will be generic and likely need rework. If they insist, proceed with the most common Terraform conventions (snake_case variables, `main.tf`/`variables.tf`/`outputs.tf`, `default_tags` on the provider, modules under `modules/`, root configs under `live/<env>/`) and document in the conventions file that these are *defaults*, not observed. Mark the file clearly so future sessions know they're assumed.
