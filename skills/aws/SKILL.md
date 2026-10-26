---
name: aws
description: Reference skill for working with AWS — auth/credentials, core services (S3, Lambda, EC2, DynamoDB, IAM, CloudWatch), the boto3 SDK, the AWS CLI, IaC, and security best practices. Load this for any AWS or cloud-deployment query.
metadata:
  type: reference
  provider: aws
  sdk: boto3
---

# AWS Skill

Context for interacting with Amazon Web Services from code and the CLI, with a focus on
the patterns most relevant to Python/agent workloads. Use it whenever a task touches AWS
auth, storage, compute, databases, IAM, or deployment.

## When to use this skill

- Reading/writing data in AWS (S3, DynamoDB), running compute (Lambda, EC2, ECS).
- Configuring credentials, regions, or IAM permissions.
- Writing `boto3` code or AWS CLI commands.
- Deploying or operating infrastructure, or reasoning about cost/security.

## Authentication & credentials (order of preference)

1. **IAM roles** — for code running in AWS (Lambda, EC2, ECS), use the attached role.
   No static keys. This is the default and the most secure option.
2. **Named profiles / SSO** — for local dev, use `aws configure sso` or `~/.aws/config`
   profiles; select with `AWS_PROFILE`.
3. **Environment variables** — `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`,
   `AWS_SESSION_TOKEN`, `AWS_REGION` for CI/short-lived use.
4. **Never** hardcode credentials in source, notebooks, or agent prompts.

`boto3` resolves credentials automatically via this chain — don't pass keys explicitly
unless you have a specific, justified reason.

## Core services cheat sheet

| Service     | Use for                                   | boto3 client name |
|-------------|-------------------------------------------|-------------------|
| S3          | Object/blob storage, static files, data   | `s3`              |
| DynamoDB    | Serverless key-value / document NoSQL     | `dynamodb`        |
| Lambda      | Event-driven serverless functions         | `lambda`          |
| EC2         | Virtual machines                          | `ec2`             |
| ECS / Fargate | Containers                              | `ecs`             |
| IAM         | Identities, roles, policies               | `iam`             |
| CloudWatch  | Logs, metrics, alarms                     | `logs`, `cloudwatch` |
| Secrets Mgr | Secrets storage/rotation                  | `secretsmanager`  |
| SQS / SNS   | Queues / pub-sub messaging                | `sqs`, `sns`      |
| Bedrock     | Managed foundation models                 | `bedrock-runtime` |

## Operating principles

- **Least privilege**: scope IAM policies to specific actions and resource ARNs.
- **Region-aware**: always set/region-qualify; pick the region closest to users/data.
- **Idempotent + paginated**: use paginators for list APIs; retries with backoff.
- **Observe**: log to CloudWatch; tag resources for cost allocation.
- **Cost-conscious**: prefer serverless/on-demand for spiky loads; clean up test resources.

## Cross-references

- `instruction.md` — quick checklist.
- `instructions.md` — detailed how-to and decision guidance.
- `examples.md` — runnable boto3 / CLI snippets.
