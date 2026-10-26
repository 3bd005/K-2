# AWS — Quick Instruction Checklist

Scannable checklist. For depth, see `instructions.md`.

## Auth & setup
- [ ] Determine where code runs: in AWS → use an **IAM role** (no keys); local → profile/SSO.
- [ ] Set the region (`AWS_REGION` / `--region` / `region_name`); never assume a default.
- [ ] Confirm identity with `aws sts get-caller-identity` before destructive actions.
- [ ] Never hardcode access keys; read from the credential chain / env / Secrets Manager.

## Writing boto3 code
- [ ] Create one client/resource per service: `boto3.client("s3")`.
- [ ] Use **paginators** for any `list_*` / `describe_*` call.
- [ ] Wrap calls and handle `botocore.exceptions.ClientError` specifically.
- [ ] Use the default retry config or configure `Config(retries={"max_attempts": ...})`.
- [ ] Stream large S3 objects; don't load multi-GB bodies into memory.

## IAM / security
- [ ] Grant **least privilege**: specific actions + specific resource ARNs.
- [ ] Prefer temporary credentials (roles, STS) over long-lived keys.
- [ ] Store secrets in Secrets Manager / SSM Parameter Store, not in code or env files in repo.

## Before declaring done
- [ ] Resources are tagged (owner, project, env) for cost tracking.
- [ ] Test/throwaway resources are cleaned up (no orphaned EC2/buckets).
- [ ] Errors logged to CloudWatch; no secrets in logs.
- [ ] IAM policy reviewed — no `"*"` action/resource unless justified.
