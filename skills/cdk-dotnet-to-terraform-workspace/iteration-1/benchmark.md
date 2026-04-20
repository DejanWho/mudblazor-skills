# Benchmark: cdk-dotnet-to-terraform (iteration 1)

Generated: 2026-04-20T06:40:43.781950+00:00

## Per-eval pass rates

| Eval | with_skill | baseline | Δ |
|---|---|---|---|
| init-mode-learn-conventions | 15/16 (94%) | 15/16 (94%) | +0 pts |
| convert-greenfield-bedrock-stack | 16/16 (100%) | 16/16 (100%) | +0 pts |
| convert-with-vpc-import | 12/12 (100%) | 10/12 (83%) | +17 pts |

## Aggregate

| Metric | with_skill | baseline | Δ |
|---|---|---|---|
| Pass rate | 97.9% | 92.4% | +0.0556 |
| Time (s) | 488 | 359 | +129.0 |
| Tokens | 111163 | 79497 | +31665 |

## Notes
- Eval 1: with_skill wins on 1 assertion(s): module-inventory.md documents Inputs and Outputs (or equivalent) for modules
- Eval 1: baseline wins on 1 assertion(s) — worth investigating: repo-conventions.md mentions the default region (eu-central-1)
- Eval 3: with_skill wins on 2 assertion(s): main.tf calls the existing `network` module (not raw VPC resources), No raw `resource "aws_vpc" "..."` in the live config alongside the module (would
- Time: with_skill avg 487.9s vs baseline avg 358.9s (Δ +129.0s).
- Tokens: with_skill avg 111163 vs baseline avg 79497 (Δ +31665).