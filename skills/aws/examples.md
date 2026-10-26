# AWS — Examples

Runnable `boto3` and AWS CLI snippets the agent can adapt. Assumes credentials are
resolved via the standard chain (role / profile / env) and a region is set.

## Session, client, and identity check

```python
import boto3

session = boto3.Session(region_name="us-east-1")  # or profile_name="dev"
sts = session.client("sts")
print(sts.get_caller_identity()["Arn"])
```

## S3 — upload, download, list (paginated), stream

```python
import boto3

s3 = boto3.client("s3")

# Upload / download (handles multipart automatically)
s3.upload_file("local.txt", "my-bucket", "path/local.txt")
s3.download_file("my-bucket", "path/local.txt", "copy.txt")

# List everything with a paginator
paginator = s3.get_paginator("list_objects_v2")
for page in paginator.paginate(Bucket="my-bucket", Prefix="path/"):
    for obj in page.get("Contents", []):
        print(obj["Key"], obj["Size"])

# Stream a large object in chunks (no full read into memory)
body = s3.get_object(Bucket="my-bucket", Key="big.bin")["Body"]
for chunk in body.iter_chunks(chunk_size=1024 * 1024):
    process(chunk)  # noqa: F821

# Presigned URL for temporary access
url = s3.generate_presigned_url(
    "get_object", Params={"Bucket": "my-bucket", "Key": "path/local.txt"}, ExpiresIn=3600
)
```

## Robust error handling & retries

```python
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

client = boto3.client("s3", config=Config(retries={"max_attempts": 10, "mode": "adaptive"}))

try:
    client.head_object(Bucket="my-bucket", Key="maybe.txt")
except ClientError as err:
    code = err.response["Error"]["Code"]
    if code in ("404", "NoSuchKey", "NotFound"):
        print("object does not exist")
    else:
        raise
```

## DynamoDB — put / get / query

```python
import boto3

ddb = boto3.client("dynamodb")

ddb.put_item(
    TableName="users",
    Item={"pk": {"S": "user#1"}, "name": {"S": "Sam"}, "age": {"N": "30"}},
)

resp = ddb.get_item(TableName="users", Key={"pk": {"S": "user#1"}})
print(resp.get("Item"))

q = ddb.query(
    TableName="users",
    KeyConditionExpression="pk = :pk",
    ExpressionAttributeValues={":pk": {"S": "user#1"}},
)
```

## Secrets Manager — fetch a secret

```python
import boto3, json

sm = boto3.client("secretsmanager")
secret = json.loads(sm.get_secret_value(SecretId="prod/db")["SecretString"])
db_password = secret["password"]
```

## Lambda handler (clients initialized outside for warm reuse)

```python
import boto3

s3 = boto3.client("s3")  # reused across warm invocations

def handler(event, context):
    bucket = event["bucket"]
    key = event["key"]
    obj = s3.get_object(Bucket=bucket, Key=key)
    return {"length": obj["ContentLength"]}
```

## Bedrock — invoke a foundation model

```python
import boto3, json

brt = boto3.client("bedrock-runtime", region_name="us-east-1")
resp = brt.invoke_model(
    modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
    body=json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 256,
        "messages": [{"role": "user", "content": "Hello"}],
    }),
)
print(json.loads(resp["body"].read()))
```

## AWS CLI quick reference

```bash
# Identity & SSO
aws sts get-caller-identity
aws configure sso
aws sso login --profile dev

# S3
aws s3 ls s3://my-bucket/path/ --profile dev --region us-east-1
aws s3 cp local.txt s3://my-bucket/path/

# Filter output with JMESPath
aws ec2 describe-instances \
  --query "Reservations[].Instances[].{id:InstanceId,state:State.Name}" \
  --output table
```

## Minimal least-privilege IAM policy (read one bucket)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::my-bucket",
        "arn:aws:s3:::my-bucket/*"
      ]
    }
  ]
}
```
