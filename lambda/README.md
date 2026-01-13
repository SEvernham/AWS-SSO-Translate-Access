# Lambda Function Deployment Package

## Overview

This directory contains the Lambda function code for the IAM Identity Center redirect application. The function is designed to be deployed via CloudFormation template with inline code inclusion.

## Structure

```
lambda/
├── index.py          # Main Lambda function handler
├── requirements.txt  # Python dependencies (none required)
└── README.md        # This documentation file
```

## Lambda Handler Conventions

The Lambda function follows AWS Lambda handler conventions:

### Function Signature
- **Function Name**: `lambda_handler`
- **Parameters**: 
  - `event` (dict): API Gateway event object
  - `context` (object): Lambda context object
- **Returns**: dict with HTTP response format

### Response Format
The function returns responses compatible with API Gateway Lambda proxy integration:

```python
{
    "statusCode": 302,
    "headers": {
        "Location": "https://target-url.com",
        "Content-Type": "text/html",
        "Cache-Control": "no-cache, no-store, must-revalidate"
    },
    "body": ""
}
```

### Error Handling
- Input validation for event object
- URL validation for redirect target
- Proper HTTP error responses (400 for bad requests)
- Structured error messages in JSON format

### Environment Variables
- `REDIRECT_TARGET_URL`: Target URL for redirect (configured via CloudFormation)

## CloudFormation Integration

The Lambda function code is embedded inline in the CloudFormation template (`cloudformation/workload-account-template.yaml`) using the `ZipFile` property. This approach:

1. **Simplifies Deployment**: No need for separate S3 bucket or deployment artifacts
2. **Version Control**: Code is versioned with the template
3. **Self-Contained**: Template includes all necessary resources

### Template Integration Points

- **Handler**: Set to `index.lambda_handler`
- **Runtime**: `python3.11`
- **Environment Variables**: `REDIRECT_TARGET_URL` parameter passed from template
- **IAM Role**: Minimal execution role with basic Lambda permissions

## Validation Checklist

- ✅ Function follows `lambda_handler(event, context)` signature
- ✅ Returns proper HTTP response format for API Gateway
- ✅ Includes comprehensive error handling
- ✅ Uses environment variables for configuration
- ✅ Includes proper logging for debugging
- ✅ Code is formatted for CloudFormation inline inclusion
- ✅ No external dependencies required
- ✅ Follows AWS Lambda best practices

## Testing

The function can be tested locally by simulating API Gateway events:

```python
# Example test event
test_event = {
    "httpMethod": "GET",
    "path": "/",
    "headers": {},
    "queryStringParameters": None,
    "body": None
}

# Test context (minimal)
class TestContext:
    def __init__(self):
        self.function_name = "test-function"
        self.aws_request_id = "test-request-id"

# Run test
result = lambda_handler(test_event, TestContext())
print(result)
```