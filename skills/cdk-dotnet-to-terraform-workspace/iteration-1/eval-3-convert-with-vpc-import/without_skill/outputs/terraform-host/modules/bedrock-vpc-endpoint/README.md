# bedrock-vpc-endpoint

AWS PrivateLink interface endpoint for `bedrock-runtime` in the current region,
fronted by its own security group. Private DNS is enabled so in-VPC clients can
call the standard Bedrock Runtime endpoint hostnames without NAT.

## Inputs

- `name` (string, required) - base name used in resource naming and tags.
- `vpc_id` (string, required) - VPC to attach the endpoint to.
- `subnet_ids` (list(string), required) - private subnets for endpoint ENIs.
- `client_security_group_ids` (list(string), default `[]`) - SGs whose members
  may reach the endpoint on 443.
- `tags` (map(string), default `{}`) - extra tags.

## Outputs

- `endpoint_id`, `endpoint_arn`, `endpoint_dns_entries`
- `security_group_id` - endpoint SG. Clients should reference it for egress
  rules if they want tightly-scoped allow-lists.
