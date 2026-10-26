# AWS — Detailed Instructions

Detailed guidance for working with AWS. Pairs with `instruction.md` (checklist) and
`examples.md` (code/CLI).

## 1. Credentials & the resolution chain

`boto3`/`botocore` resolve credentials in this order: explicit params → env vars →
shared credentials file (`~/.aws/credentials`) → shared config / SSO → container creds →
EC2/instance metadata (IAM role). Design for the **highest item that applies**:

- **In AWS** (Lambda/EC2/ECS): attach an IAM role; the SDK picks it up automatically.
- **Local dev**: `aws configure sso` (preferred) or named profiles; select with
  `AWS_PROFILE=myprofile` or `boto3.Session(profile_name="myprofile")`.
- **CI**: short-lived credentials via OIDC role assumption, not static keys.

Verify who you are: `aws sts get-caller-identity`. Switch region explicitly everywhere.

## 2. boto3 fundamentals

- **client vs resource**: `client("s3")` is low-level (1:1 with the API);
  `resource("s3")` is higher-level/object-oriented (note: resources are in maintenance
  mode — prefer clients for new code).
- **Sessions**: use `boto3.Session(region_name=..., profile_name=...)` to scope config;
  reuse a session/client (creating clients is relatively expensive).
- **Pagination**: many list APIs truncate. Use
  `paginator = client.get_paginator("list_objects_v2")` and iterate pages.
- **Waiters**: use `client.get_waiter(...)` to block until a resource reaches a state
  (e.g. instance running, object exists) instead of polling manually.
- **Retries**: configure via
  `from botocore.config import Config; Config(retries={"max_attempts": 10, "mode": "adaptive"})`.

## 3. S3 patterns

- Upload/download with `upload_file` / `download_file` (handles multipart automatically).
- Stream large objects: read `get_object(...)["Body"]` in chunks; don't `.read()` all.
- Use presigned URLs (`generate_presigned_url`) for temporary client-side access.
- Enable bucket versioning + server-side encryption (SSE-S3 or SSE-KMS) for important data.
- Lifecycle rules to transition cold data to Glacier and expire temp objects.

## 4. DynamoDB patterns

- Design the table around access patterns (single-table design when appropriate).
- Use `get_item`/`put_item`/`query` (avoid `scan` on large tables).
- Use `BatchWriteItem`/`BatchGetItem` for throughput; handle `UnprocessedItems`.
- Choose on-demand capacity for spiky/unknown load, provisioned for steady predictable load.

## 5. Lambda & serverless

- Keep handlers small; initialize clients **outside** the handler to reuse across
  invocations (warm starts).
- Pass config via environment variables; secrets via Secrets Manager/SSM at cold start.
- Set memory/timeout to the workload; watch cold-start cost for latency-sensitive paths.
- Grant the function role only the actions it needs.

## 6. IAM & security

- **Least privilege**: enumerate exact actions (`s3:GetObject`) and resource ARNs.
- Prefer **roles** and STS temporary credentials over IAM users with long-lived keys.
- Use **Secrets Manager** (rotation) or **SSM Parameter Store** (cheaper) for secrets.
- Turn on CloudTrail (audit), GuardDuty (threat detection); encrypt at rest and in transit.
- Never commit `.aws/credentials`, keys, or `.env` with secrets to the repo.

## 7. AWS CLI

- Profiles: `aws s3 ls --profile myprofile --region us-east-1`.
- `--query` (JMESPath) to filter output; `--output json|table|text`.
- `aws configure sso` for SSO; `aws sso login` to refresh.
- Dry-run mutating EC2 ops with `--dry-run` where supported.

## 8. Infrastructure as Code

- Prefer IaC over click-ops: **CloudFormation**, **AWS CDK** (Python), **Terraform**, or
  **SAM** for serverless. Keep infra reviewable and reproducible in version control.
- Tag everything (`Project`, `Environment`, `Owner`) for cost allocation and cleanup.

## 9. Observability & cost

- Centralize logs in CloudWatch Logs; emit custom metrics/alarms for SLOs.
- Use Cost Explorer + budgets/alerts; right-size and delete idle resources.
- Prefer serverless/on-demand for spiky workloads to avoid paying for idle capacity.

## 10. Pitfalls

- Forgetting the region → confusing "resource not found" errors.
- Unpaginated list calls → silently missing data beyond the first page.
- Loading huge S3 objects fully into memory → OOM; stream instead.
- Over-broad IAM (`Action: "*"`, `Resource: "*"`) → security risk.
- Leaving test EC2 instances / NAT gateways / buckets running → surprise bills.
