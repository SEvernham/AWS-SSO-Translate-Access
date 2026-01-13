import json
import logging
import os

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda function that returns HTTP 302 redirect to configured target URL.
    
    This function handles requests from API Gateway and returns an HTTP 302 redirect
    response to redirect users to the configured target URL (typically AWS Translate console).
    
    Args:
        event (dict): API Gateway event object containing request details
        context (object): Lambda context object containing runtime information
        
    Returns:
        dict: HTTP response with 302 redirect status and Location header
    """
    try:
        # Basic validation of event
        if event is None:
            raise ValueError("Event cannot be None")
        
        # Log the incoming request for debugging (sanitized)
        logger.info("Processing redirect request")
        logger.debug(f"Event keys: {list(event.keys()) if isinstance(event, dict) else 'Invalid event type'}")
        
        # Get target URL from environment variable with fallback
        redirect_url = os.environ.get(
            'REDIRECT_TARGET_URL', 
            'https://us-east-1.console.aws.amazon.com/translate/home?region=us-east-1#translation'
        )
        
        # Validate redirect URL
        if not redirect_url or not redirect_url.startswith('https://'):
            raise ValueError("Invalid redirect URL configuration")
        
        # Return HTTP 302 redirect response following Lambda proxy integration format
        response = {
            "statusCode": 302,
            "headers": {
                "Location": redirect_url,
                "Content-Type": "text/html",
                "Cache-Control": "no-cache, no-store, must-revalidate"
            },
            "body": ""
        }
        
        logger.info(f"Returning redirect to: {redirect_url}")
        return response
        
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