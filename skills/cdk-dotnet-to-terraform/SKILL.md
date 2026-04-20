---
name: cdk-dotnet-to-terraform
description: Convert an AWS CDK project written in .NET / C# into Terraform, reusing the host repo's existing Terraform modules as both destination and style guide. First-run or on-demand, it walks the host repo to learn where modules live, how they're shaped, and what conventions the team follows, persisting that into its own reference files so later conversions stay consistent. Use this skill whenever the user mentions converting CDK to Terraform, porting CDK .NET / CDK C# / CDK csharp code, migrating AWS CDK to Terraform, replacing CDK with Terraform, generating Terraform for an existing CDK stack, `cdk synth` to Terraform, a `.csproj` that references `Amazon.CDK`, needing Terraform for a Bedrock / Anthropic-on-AWS / ALB / Fargate / Lambda deployment already defined in CDK, or asks the skill to "re-run init", "refresh the conventions", or "update the reference files". Trigger even when the user doesn't explicitly say "skill" — any request that combines CDK .NET source with a desire for Terraform output should land here.
---

# CDK (.NET 8) → Terraform

Your job is to turn an AWS CDK application written in C# / .NET 8 into Terraform that fits naturally into the host repo. "Fits naturally" is the hard part: every Terraform codebase has its own conventions — how modules are laid out, what goes in `variables.tf`, whether tags live in `locals`, how environments are split — and if the output of this skill ignores those conventions, the team will reject it on review. So before you convert anything, you learn the repo.

You have two modes:

- **Init mode** — analyse the host repo and write what you learned into your own reference files (`references/repo-conventions.md`, `references/module-inventory.md`). Run this on first use or when the user asks you to refresh.
- **Convert mode** — given a CDK .NET 8 project, translate it into Terraform that follows the conventions you wrote down, reusing existing modules where possible and authoring new ones in the same style when needed.

Keep the convert output faithful to the CDK intent. You're not rearchitecting the deployment; you're re-expressing it. Where CDK used an L2/L3 construct that corresponds to an existing repo module, use that module. Where it doesn't, write a new module shaped like its siblings. Fall back to raw resources only when a module would be absurd (a single SSM parameter, a one-off IAM policy attachment).

## Why this skill is unusual

Most migration skills have a fixed source and a fixed target. This one has a fixed *source format* (CDK .NET 8) but a target that **varies per host repo**. Two different Terraform repos might both consume a VPC, but one uses `terraform-aws-modules/vpc/aws` from the public registry while the other has `modules/network/` with a hand-rolled NAT-instance pattern and a specific tagging convention. Both are correct; they're just different. The init phase exists so you meet the repo on its own terms.

This also means your reference files `repo-conventions.md` and `module-inventory.md` are **per-repo artefacts**, not universal CDK knowledge. Treat them like code: commit them, let the user review them, re-run init when they go stale.

## Mode selection

When you're invoked, decide up front which mode you're in:

1. **Explicit re-init.** If the user's request contains phrases like "re-run init", "refresh the conventions", "update the reference files", "rescan the repo", or "forget what you know about this repo" — run init mode, overwriting `references/repo-conventions.md` and `references/module-inventory.md`. Then stop and show the user what you found; don't roll into conversion unless they also asked for a conversion in the same message.

2. **Missing or empty references.** If `references/repo-conventions.md` or `references/module-inventory.md` doesn't exist, or looks like it's still the template (contains placeholders like `<FILL IN>` or the file is <200 bytes), run init mode first, then continue to conversion if the user's original request was a conversion.

3. **Otherwise → conversion mode.**

If you're about to run init, say so out loud ("I don't have a conventions file for this repo yet — running init first, then I'll come back to the conversion"). Don't silently walk the repo; the user needs to see what you're doing because the output of init becomes persistent state.

## Init mode

The goal of init is a pair of files that make future conversions consistent: `references/repo-conventions.md` (how this repo writes Terraform) and `references/module-inventory.md` (what modules already exist and what they do). Follow `references/init-walkthrough.md` for the step-by-step procedure; the summary is:

1. **Find the Terraform.** Locate directories containing `.tf` files. Typical layouts are `terraform/`, `infra/`, `iac/`, `deploy/`, `modules/ + live/`, or `modules/ + envs/`. There may be more than one root — a large repo might have separate Terraform trees per application. Enumerate them all.

2. **Classify each directory.** Is it a module (has `variables.tf` + `outputs.tf`, no `backend` / `provider` block) or a root/live config (has `backend`, `provider`, `terraform { required_version = ... }`)? Something else (fixtures, examples)? Record the split.

3. **Read ~3–5 modules of different shapes.** Pick representatives — a networking one, a compute one, a stateful one, a utility one. For each, note: file layout, variable naming, output naming, tag conventions, how sub-resources are wired, README style, whether there's a `locals.tf`, whether providers are declared inside modules or inherited.

4. **Read ~2 root/live configs.** Note environment layout (folder-per-env? workspace?), state backend config, how modules are consumed (source path, version pinning), how cross-module refs work (remote state? module outputs? SSM?).

5. **Spot the invariants.** After skimming, write down what's consistent across examples: "modules always use `main.tf`/`variables.tf`/`outputs.tf`/`versions.tf`", "resources always include a `Name` and `Environment` tag from locals", "variable names are snake_case, outputs are snake_case with `_arn`/`_id` suffixes", "provider is declared in root only, never in modules", etc. These invariants become the rules you enforce during conversion.

6. **Write the two reference files.** Use the templates at `references/repo-conventions.md.template` and `references/module-inventory.md.template` as starting points. Fill every `<FILL IN>` placeholder; if something genuinely doesn't apply, write `N/A` with a short reason.

7. **Show the user a summary.** List the module inventory (one line each), the key conventions, and anything you were unsure about. Ask them to confirm or correct before you treat these files as authoritative. If they correct something, update the file and re-show.

If the repo has **no Terraform in it yet** (the team is starting fresh with this conversion as the seed), say so and ask the user for preferences: module location, file structure, tag conventions, backend config. Record their answers in the reference files. Don't invent preferences silently.

## Convert mode

This is the main job. You're given a path to a CDK .NET 8 project. You have `repo-conventions.md` and `module-inventory.md` from init. You need to produce Terraform in the right places that **parses and formats cleanly locally (`terraform fmt`)** and **validates + plans cleanly in the user's CI pipeline** after they push. Local validation is not available in this environment — `terraform init` / `validate` / `plan` all need network access (Terraform registry, state backend, AWS API) that the user's machine doesn't have. The final authority on whether the conversion is correct is the pipeline run; the skill is pipeline-agnostic and doesn't need to know how the pipeline is configured.

Work the phases in order. Don't skip; each one catches problems the next would amplify.

### Phase 1: Understand the CDK project

1. **Find and read `*.csproj`.** Confirm `Amazon.CDK.Lib` (or the older split packages) is referenced. Note the target framework (`net8.0`). Note any non-CDK NuGet dependencies — they hint at custom resources or non-standard patterns.

2. **Read the `cdk.json`.** It tells you the app entry point (`dotnet run --project src/MyApp`) and any context values / feature flags. Context values often carry environment-specific config; you'll need to represent them in Terraform as variables.

3. **Read `Program.cs` / `App` entrypoint.** This tells you which stacks exist and how they're instantiated (including the `Env` with `account` / `region`, and any props passed in). One `Stack` in CDK ≈ one root Terraform config or one module + call site — you'll decide in Phase 3.

4. **Read each `Stack` file.** These are the C# classes deriving from `Stack`. Note: construct instantiations, cross-stack references (`StackProps.Env`, exports/imports), tokens used (`Fn.Sub`, `Fn.Ref`), aspects, and any custom resources.

5. **Run `cdk synth`.** From the CDK project directory:
   ```bash
   cdk synth --all --json > /tmp/cdk-synth.json  # or similar
   ```
   If `cdk` isn't on PATH, try `npx aws-cdk synth` or, as a last resort, skip synth and rely on source reading (noting the risk). The synth output is the authoritative source for resource *properties* — CDK often inlines defaults the source doesn't show. You use the C# source for *structure* (what belongs where) and synth for *values*.

6. **Inventory the stacks and resources.** Produce (in your head or as working notes) a table: each stack, its resources with their logical IDs, and their physical IDs (from synth). This table drives Phase 3.

See `references/cdk-synth-harness.md` for synth troubleshooting, how to parse the CloudFormation output, and how to map CloudFormation logical IDs back to C# construct paths.

### Phase 2: Plan the conversion

Before you write any `.tf`, plan the mapping. Share the plan with the user before you start writing, so they can redirect you early.

1. **Decide target layout for each CDK Stack.** Options:
   - If the repo has an obvious "one folder per stack / app" convention in its live configs, create one there.
   - If the stack is small and cohesive, it might be a single root config that calls several modules.
   - If the stack has distinct subsystems, it might become several call-sites in one root config.
   
   The choice follows `repo-conventions.md`, not CDK's shape.

2. **For each resource or construct, decide: existing module, new module, or raw resource.**
   - **Existing module:** look up the inventory. A CDK `Vpc` with three AZs likely maps to the repo's `network` module; a Fargate service to the repo's `ecs-service` module; a Lambda to the repo's `lambda` module. Match by *inputs and outputs*, not name.
   - **New module:** if the construct is used more than once across the CDK app (or feels reusable — an ALB-in-front-of-Fargate pattern the repo will build again), author a new module in the same style as existing ones.
   - **Raw resource:** one-off IAM policies, a single S3 bucket that isn't going to be reused, SSM parameters, random CloudWatch log groups.

3. **Identify constructs with no clean Terraform analogue.** These are out-of-scope (see list at top) — `AwsCustomResource`, Lambda-backed CFN custom resources, `CfnInclude`, CDK Pipelines, CDK Aspects, cross-region replication patterns, L3 constructs that call multiple AWS APIs as part of creation (e.g. `BucketDeployment` which uploads files at deploy time). For each of these, plan to surface a `TODO: manual migration — <reason>` comment in the output and list it in your final report to the user. Do not fake them with shell-outs, `null_resource` + `local-exec`, or similar unless the user has asked for that explicitly.

4. **Decide import vs greenfield per resource.** If the user said some resources are already deployed and must be kept in place, generate an `imports.tf` file with `import` blocks (Terraform ≥1.5 syntax) keyed off the CloudFormation physical IDs from `cdk synth`'s template outputs. For greenfield resources, no import block. Stateful resources (RDS, DynamoDB, S3 with data, KMS keys with encrypted data) should default to import unless the user says otherwise — recreating them means data loss.

5. **Share the plan.** Tell the user: stacks, target locations, module choices (existing/new/raw), out-of-scope items, import/greenfield split. Wait for confirmation or redirection before writing files. If they've already said "just do it" at a high level, still tell them the plan — but you can proceed without waiting for a second confirmation.

### Phase 3: Write the Terraform

Now you write files. Follow the conventions ruthlessly — this is where drift creeps in.

1. **For each new module:** create `<modules-dir>/<name>/` with the same file layout the inventory shows (usually `main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`, `README.md`). Use the same variable naming, the same tag patterns, the same provider-declaration pattern (inside the module or not, as the inventory says). Study one existing module of similar shape before writing — *do not* go from memory of what Terraform modules usually look like, because your memory is not this repo's style.

2. **For the root / live config:** write the file(s) in the target directory. Module calls use the `source = "../../modules/<name>"` path the repo already uses (or whichever form the inventory documents — some repos pin versions, some don't). Wire up inputs from Terraform variables, locals, or data sources as the repo would.

3. **Write `imports.tf` (only if there are resources to import).** One `import` block per resource, with the `to = <address>` pointing at the resource/module instance you created and `id = "<physical-id-from-synth>"`. Put a comment above each block pointing to the CDK construct path it came from, so humans can trace it back.

4. **Never overwrite an existing file silently.** Before writing, check if a file already exists at the target path. If it does, *show the user the diff you'd apply and ask* — they may have hand-written something there already.

5. **Run `terraform fmt`** on the directories you touched. This is mandatory; formatting drift is the easiest thing to miss on review. `terraform fmt` is also the **only** Terraform command that works locally in this environment — it's pure HCL formatting and needs no network access.

6. **Do not run `terraform init`, `terraform validate`, or `terraform plan` locally** — the local environment is offline for Terraform's needs (no provider downloads, no registry, no state backend). Those commands will hang or fail. The actual validation happens in the user's CI pipeline after they push. Treat "pipeline-green" as the definition of success, and tell the user in the Phase 4 report that the pipeline run is the verification gate. The skill doesn't need to know the pipeline's internals — whatever `terraform` commands it runs, the user pastes any errors back and you iterate.

If you want to do extra local sanity-checking beyond `fmt`, read through the generated `.tf` carefully — in particular check: variable types declared, module call inputs match the module's `variables.tf`, referenced resources/modules actually exist, `for_each`/`count` keys are consistent, and no obvious typos in attribute references. This is a human-style read, not a tool run.

### Phase 4: Report

When you're done, tell the user:

1. **What you wrote.** File list, grouped by "new module" / "modified root config" / "new root config" / "imports file".
2. **Module decisions.** For each CDK construct, which existing module you reused vs which new module you authored vs which raw resources you wrote. This is where reviewers will spend most of their time.
3. **Import blocks generated** — count, and a note that `terraform plan` will be needed to verify each resolves correctly. `import` blocks that fail at plan time are the most common post-conversion issue.
4. **Out-of-scope items** — the `TODO` markers you left behind, with the CDK construct path for each.
5. **Local verification status.** `terraform fmt` result (clean or not) and your own read-through assessment per root config. Remind the user that `init` / `validate` / `plan` run in their CI pipeline, not locally.
6. **Recommended next steps.** Usually: (a) push the branch and let the pipeline run; (b) paste any errors / plan output back so the skill can iterate, particularly on `import` blocks (expect drift); (c) review module-inventory updates if you added a new module (it should be added to the inventory).

Don't declare success if `terraform fmt` isn't clean or if your read-through flagged anything obviously broken. Surface problems and ask what to do. Full validation is the pipeline's job, but don't hand the pipeline something that won't parse.

### Phase 5: Update the inventory

If Phase 3 authored any new modules, append them to `references/module-inventory.md` with a one-line description of what they do. Future conversions will then find and reuse them instead of authoring again.

## Principles

- **The repo's conventions win.** If your instinct conflicts with what's in `repo-conventions.md`, follow the file. That's why it exists.
- **Reuse before authoring.** Check the module inventory *before* deciding to write a new module. Same inputs and outputs = same module.
- **Copy the style of a sibling.** When authoring a new module, find the closest existing module and mirror its layout, naming, and wiring. Don't mix in a different style because it's "cleaner."
- **Use `cdk synth` for ground truth.** The C# source tells you the shape; the synthesized CloudFormation tells you the values. When they disagree, trust synth — CDK fills in defaults the source doesn't show.
- **Surface judgment calls.** Custom resources, cross-region patterns, CDK Pipelines, and anything that'd require `local-exec` hacks get a clear `TODO:` comment and go in the final report. The user decides, not you.
- **Don't fight the host repo.** If the repo has its own janky pattern (e.g., an unusual module structure, an internal provider), match it. You're not there to improve their Terraform.
- **No silent overwrites.** Every file you'd overwrite gets shown to the user first.

## When things go wrong

- **`cdk synth` fails.** The CDK app has to build before it synths. If it won't, ask the user to fix the build first, or fall back to source-only translation with an explicit warning that you couldn't cross-check values.
- **A construct has no clean module match and no clean resource mapping.** Write a `TODO:` comment with the CDK path and a description of what the construct did. Don't invent an approximation.
- **The repo has wildly inconsistent conventions across modules.** Pick the newer / more-used pattern as the reference, document in the summary that there's inconsistency, and ask the user which one to follow going forward.
- **The pipeline's `terraform validate` fails on a module you wrote.** Read the error the user pastes back from the pipeline, fix it, push again. If you can't figure out why a module reference is wrong, re-read the inventory — you probably passed an input name that the module doesn't have, or missed a `required` variable. Local-only clues: `terraform fmt` is clean but your read-through spotted a type mismatch between a module call's input and the module's `variables.tf`.
- **Resource import would clobber state.** If the user is going to apply this to a state file that already has resources, remind them that `import` blocks are additive and that `terraform plan` will show the real changes.
- **User says "just convert it, I'll fix the modules later".** Resist. A raw-resource dump that ignores the module layer isn't a productive diff — it's a wall of code the team will reject. Do the module work. If the user is adamant, surface the tradeoff once ("this'll be a lot more code and won't match the repo style") and then comply.

## Reference

- `references/init-walkthrough.md` — step-by-step init procedure, what to look for in each module, heuristics for inferring conventions.
- `references/construct-mapping.md` — CDK construct → Terraform resource/module cheat sheet. Covers networking, compute, storage, IAM, observability.
- `references/bedrock-patterns.md` — AWS Bedrock / Anthropic-on-Bedrock specific translation patterns (IAM for `bedrock:InvokeModel`, VPC endpoints, agent/knowledge-base resources, cross-region considerations).
- `references/cdk-synth-harness.md` — how to run `cdk synth` for .NET CDK projects, parse the CloudFormation output, and map CFN logical IDs back to C# construct paths.
- `references/import-blocks.md` — Terraform ≥1.5 `import` block syntax, how to pull physical IDs from synth output, and the pitfalls (drift on first plan, tagging differences, IAM policy document ordering).
- `references/repo-conventions.md.template` — starting point for the per-repo conventions file. **Init mode writes the real `repo-conventions.md` alongside this file.**
- `references/module-inventory.md.template` — starting point for the per-repo module inventory. **Init mode writes the real `module-inventory.md` alongside this file.**

The `.template` files ship with the skill; the real conventions files are generated per host repo during init and should be committed so the team (and future Claude sessions) share the same understanding.
