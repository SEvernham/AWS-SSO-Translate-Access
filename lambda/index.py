import json
import logging
import os
import base64
from urllib.parse import parse_qs, unquote_plus

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda function that handles IAM Identity Center SAML requests and redirects users.
    
    This function can handle both direct requests and SAML authentication requests
    from IAM Identity Center, then redirects users to the configured target URL.
    
    Args:
        event (dict): API Gateway event object containing request details
        context (object): Lambda context object containing runtime information
        
    Returns:
        dict: HTTP response with redirect or SAML handling
    """
    try:
        # Basic validation of event
        if event is None:
            raise ValueError("Event cannot be None")
        
        # Log the incoming request for debugging (sanitized)
        logger.info("Processing request")
        logger.debug(f"Event keys: {list(event.keys()) if isinstance(event, dict) else 'Invalid event type'}")
        
        # Get target URL from environment variable with fallback
        redirect_url = os.environ.get(
            'REDIRECT_TARGET_URL', 
            'https://us-east-1.console.aws.amazon.com/translate/home?region=us-east-1#translation'
        )
        
        # Validate redirect URL
        if not redirect_url or not redirect_url.startswith('https://'):
            raise ValueError("Invalid redirect URL configuration")
        
        # Check if this is a SAML request from IAM Identity Center
        http_method = event.get('httpMethod', event.get('requestContext', {}).get('http', {}).get('method', 'GET'))
        
        if http_method == 'POST':
            # Handle SAML POST request from IAM Identity Center
            logger.info("Handling SAML POST request")
            
            # Parse the body to check for SAML request
            body = event.get('body', '')
            if body:
                try:
                    # Handle both form-encoded and direct body
                    if event.get('isBase64Encoded', False):
                        body = base64.b64decode(body).decode('utf-8')
                    
                    # Check if this looks like a SAML request
                    if 'SAMLRequest' in body or 'saml' in body.lower():
                        logger.info("Detected SAML request, redirecting immediately")
                        # For a simple redirect app, we'll just redirect instead of processing SAML
                        return create_redirect_response(redirect_url)
                    
                except Exception as e:
                    logger.warning(f"Could not parse POST body: {e}")
        
        # For all other requests (GET or non-SAML POST), just redirect
        logger.info(f"Redirecting to: {redirect_url}")
        return create_redirect_response(redirect_url)
        
    except Exception as e:
        # Basic error handling for invalid requests
        logger.error(f"Error processing request: {str(e)}")
        
        # Return proper error response for API Gateway
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "error": "Invalid request",
                "message": "Unable to process the redirect request"
            })
        }

def create_redirect_response(redirect_url):
    """Create an HTML response that redirects via JavaScript and meta refresh"""
    html_content = f'''<!DOCTYPE html>
<html>
<head>
    <title>Redirecting...</title>
    <meta http-equiv="refresh" content="0;url={redirect_url}">
    <script type="text/javascript">
        window.location.href = "{redirect_url}";
    </script>
</head>
<body>
    <p>Redirecting to AWS Translate Console...</p>
    <p>If you are not redirected automatically, <a href="{redirect_url}">click here</a>.</p>
</body>
</html>'''
    
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/html; charset=utf-8",
            "Cache-Control": "no-cache, no-store, must-revalidate"
        },
        "body": html_content
    }