# IAM Identity Center Redirect Application

A simple demonstration application that integrates with AWS IAM Identity Center to redirect authenticated users to the AWS Translate console.

## Project Structure

```
.
├── cloudformation/
│   ├── aws-translate-simple-access.yaml     # Permission set for AWS Translate access
│   └── workload-account-template.yaml      # Lambda function and API Gateway
├── lambda/
│   └── index.py                            # Lambda function code
└── README.md                               # This file
```

## Overview

This solution provides a proof-of-concept for custom applications in IAM Identity Center that redirect users to specific AWS console services. The solution uses a serverless architecture with AWS Lambda and API Gateway, deployed via CloudFormation templates that support multi-account environments.

### Architecture

- **Permission Set**: Grants users access to AWS Translate in the target account
- **Lambda Function**: Handles redirect requests and returns HTML redirect responses
- **API Gateway**: Provides HTTPS endpoint for IAM Identity Center SAML integration
- **IAM Identity Center SAML Application**: Manually created SAML 2.0 application in management account
- **Multi-Account Setup**: Permission set and application in management account, workload resources in separate account

## Deployment Instructions

### Prerequisites

Before deploying this solution, ensure you have:

1. **AWS CLI configured** with appropriate permissions for both accounts
2. **Two AWS accounts**:
   - **Management Account**: Contains IAM Identity Center instance
   - **Workload Account**: Will host the Lambda function and API Gateway
3. **IAM Identity Center enabled** in the management account
4. **Appropriate permissions** in both accounts:
   - Workload Account: CloudFormation, Lambda, API Gateway, IAM permissions
   - Management Account: CloudFormation, IAM Identity Center (SSO) permissions

### Step-by-Step Deployment

#### Phase 1: Deploy Permission Set (Management Account)

**Important**: Deploy the permission set first to establish the SAML audience identifier.

1. **Switch to the management account context**:
   ```bash
   aws configure set profile management-account
   # or
   export AWS_PROFILE=management-account
   ```

2. **Get your IAM Identity Center instance ARN**:
   ```bash
   aws sso-admin list-instances \
     --query 'Instances[0].InstanceArn' \
     --output text \
     --region us-east-1
   ```

3. **Deploy the permission set CloudFormation template**:
   ```bash
   aws cloudformation create-stack \
     --stack-name translate-permission-set \
     --template-body file://cloudformation/aws-translate-simple-access.yaml \
     --parameters \
       ParameterKey=IdentityCenterInstanceArn,ParameterValue=<YOUR_IDENTITY_CENTER_INSTANCE_ARN> \
       ParameterKey=WorkloadAccountId,ParameterValue=<WORKLOAD_ACCOUNT_ID> \
       ParameterKey=OrganizationName,ParameterValue="YourOrganization" \
     --region us-east-1
   ```

4. **Wait for stack creation to complete**:
   ```bash
   aws cloudformation wait stack-create-complete \
     --stack-name translate-permission-set \
     --region us-east-1
   ```

#### Phase 2: Deploy Workload Account Resources

1. **Switch to the workload account context**:
   ```bash
   aws configure set profile workload-account
   # or
   export AWS_PROFILE=workload-account
   ```

2. **Deploy the workload account CloudFormation template**:
   ```bash
   aws cloudformation create-stack \
     --stack-name iam-identity-center-redirect-workload \
     --template-body file://cloudformation/workload-account-template.yaml \
     --parameters \
       ParameterKey=RedirectTargetURL,ParameterValue=https://us-east-1.console.aws.amazon.com/translate/home?region=us-east-1#translation \
       ParameterKey=ApplicationName,ParameterValue=iam-identity-center-redirect-app \
     --capabilities CAPABILITY_NAMED_IAM \
     --region us-east-1
   ```

3. **Wait for stack creation to complete**:
   ```bash
   aws cloudformation wait stack-create-complete \
     --stack-name iam-identity-center-redirect-workload \
     --region us-east-1
   ```

4. **Retrieve the API Gateway endpoint URL** (needed for Phase 3):
   ```bash
   aws cloudformation describe-stacks \
     --stack-name iam-identity-center-redirect-workload \
     --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayEndpointURL`].OutputValue' \
     --output text \
     --region us-east-1
   ```

   **Save this URL** - you'll need it for the manual SAML application creation.

#### Phase 3: Create SAML Application Manually (Management Account)

**Important**: The SAML application must be created manually in the IAM Identity Center console.

1. **Access the IAM Identity Center console** in your management account
2. **Navigate to Applications** → **Add application**
3. **Choose "I have an application I want to setup"**
4. **Choose "SAML 2.0"** and click **Next**
5. **Configure the application**:
   - **Display name**: `AWS SSO Translate Access`
   - **Description**: `Direct access to AWS Translate console`
   - **Application ACS URL**: Enter your API Gateway URL from Phase 2
   - **Application SAML audience**: `TranslateUserAccess`
6. **Click Submit**
7. **Configure attribute mapping**:
   - Click **Actions** → **Edit attribute mappings**
   - **Maps to this string value or user attribute**: `${user:email}`
   - **Format**: Select `emailAddress`
   - Click **Save changes**

#### Phase 4: Assign Users and Test

1. **Assign users or groups** to the application:
   - In the application details, go to **Assigned users** or **Assigned groups**
   - Click **Assign users** or **Assign groups**
   - Select the appropriate users/groups and assign them

2. **Assign the permission set** to users for the workload account:
   - Go to **AWS accounts** in IAM Identity Center
   - Select your workload account
   - Assign users/groups with the **TranslateUserAccess** permission set

### Testing the Deployment

1. **Access the IAM Identity Center Access Portal** using your organization's URL
2. **Sign in** with your credentials
3. **Look for the "AWS SSO Translate Access" application** in your applications list
4. **Click on the application** - you should be redirected to the AWS Translate console
5. **Verify the redirect** works correctly and lands on the translation page

**Expected Behavior**: The application should redirect you to the AWS Translate console in the workload account where you have the TranslateUserAccess permission set assigned.

## Troubleshooting

### Common Issues and Solutions

#### 1. Application Not Working After Deployment

**Problem**: Application appears in Access Portal but gives 404 or authentication errors.

**Solution**: Ensure you completed the manual SAML configuration in Phase 3:
- Application must be configured as **SAML 2.0** type
- ACS URL must be set to your API Gateway endpoint
- SAML Audience must be set to "TranslateUserAccess" (matching permission set name)
- Attribute mapping must be configured: `${user:email}` → `emailAddress`

**Verification Steps**:
1. Test the API Gateway endpoint directly with curl to ensure it returns HTML redirect
2. Check CloudWatch logs for the Lambda function for any errors
3. Verify the SAML configuration matches the working setup described above

#### 2. Users Can't Access AWS Translate Console

**Problem**: Redirect works but users get permission denied in AWS Translate.

**Solution**: Ensure users are assigned the TranslateUserAccess permission set for the workload account:
1. Go to IAM Identity Center → AWS accounts
2. Select the workload account
3. Assign users/groups with the TranslateUserAccess permission set

#### 3. Stack Creation Failures

**Problem**: CloudFormation stack creation fails with permission errors.

**Solutions**:
- Ensure your AWS credentials have sufficient permissions for CloudFormation, Lambda, API Gateway, and IAM operations
- For the management account, ensure you have IAM Identity Center (SSO) administrative permissions
- Check that you're deploying in the correct AWS region (us-east-1 recommended)

#### 4. SAML Configuration Issues

**Problem**: Application created but SAML settings not working.

**Solution**: The working configuration requires these specific settings:
- **Application Type**: SAML 2.0 (not OAuth 2.0)
- **ACS URL**: Your API Gateway endpoint URL
- **SAML Audience**: "TranslateUserAccess" (must match permission set name)
- **Attribute Mapping**: `${user:email}` mapped to `emailAddress`

This configuration has been tested and confirmed working.

### Getting Help

If you encounter issues not covered in this troubleshooting guide:

1. **Check CloudWatch Logs** for the Lambda function for detailed error messages
2. **Review CloudFormation Events** in the AWS console for stack creation failures
3. **Verify IAM permissions** for both accounts meet the requirements
4. **Test the API Gateway endpoint directly** to isolate issues

## Parameter Reference

### Permission Set Template Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `IdentityCenterInstanceArn` | String | **Yes** | None | ARN of your IAM Identity Center instance |
| `WorkloadAccountId` | String | **Yes** | None | 12-digit AWS account ID where users will access AWS Translate |
| `OrganizationName` | String | No | `YourOrganization` | Your organization name for tagging |
| `PermissionSetName` | String | No | `TranslateUserAccess` | Name for the permission set (becomes SAML audience) |

### Workload Account Template Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `RedirectTargetURL` | String | No | AWS Translate Console URL | Target URL for redirect. Must be a valid HTTPS URL. |
| `ApplicationName` | String | No | `iam-identity-center-redirect-app` | Name for Lambda function and related resources. |

### Management Account Template Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `WorkloadAPIGatewayURL` | String | **Yes** | None | API Gateway endpoint URL from workload account deployment. |
| `ApplicationDisplayName` | String | No | `AWS-Translate-Console-Redirect` | Display name in IAM Identity Center Access Portal. |
| `ApplicationDescription` | String | No | Default description | Description shown to users in Access Portal. |
| `IdentityCenterInstanceArn` | String | **Yes** | None | ARN of your IAM Identity Center instance. |
| `SAMLAudience` | String | No | `TranslateUserAccess` | SAML Audience identifier (should match permission set name). |