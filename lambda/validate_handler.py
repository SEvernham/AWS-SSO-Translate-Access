#!/usr/bin/env python3
"""
Validation script to verify Lambda handler follows AWS conventions.
"""

import sys
import os
import json

# Add current directory to path to import the handler
sys.path.insert(0, os.path.dirname(__file__))

try:
    from index import lambda_handler
except ImportError as e:
    print(f"❌ Failed to import lambda_handler: {e}")
    sys.exit(1)

def validate_handler_signature():
    """Validate that lambda_handler has correct signature."""
    import inspect
    
    sig = inspect.signature(lambda_handler)
    params = list(sig.parameters.keys())
    
    if len(params) != 2:
        print(f"❌ Handler should have 2 parameters, found {len(params)}: {params}")
        return False
    
    if params[0] != 'event' or params[1] != 'context':
        print(f"❌ Handler parameters should be 'event' and 'context', found: {params}")
        return False
    
    print("✅ Handler signature is correct: lambda_handler(event, context)")
    return True

def validate_response_format():
    """Validate that handler returns proper API Gateway response format."""
    
    # Mock context object
    class MockContext:
        def __init__(self):
            self.function_name = "test-function"
            self.aws_request_id = "test-request-id"
            self.log_group_name = "/aws/lambda/test-function"
            self.log_stream_name = "test-stream"
    
    # Test with valid event
    test_event = {
        "httpMethod": "GET",
        "path": "/",
        "headers": {},
        "queryStringParameters": None,
        "body": None
    }
    
    try:
        # Set environment variable for testing
        os.environ['REDIRECT_TARGET_URL'] = 'https://example.com/test'
        
        response = lambda_handler(test_event, MockContext())
        
        # Validate response structure
        required_keys = ['statusCode', 'headers', 'body']
        for key in required_keys:
            if key not in response:
                print(f"❌ Response missing required key: {key}")
                return False
        
        # Validate status code
        if not isinstance(response['statusCode'], int):
            print(f"❌ statusCode should be integer, got: {type(response['statusCode'])}")
            return False
        
        # Validate headers
        if not isinstance(response['headers'], dict):
            print(f"❌ headers should be dict, got: {type(response['headers'])}")
            return False
        
        # For redirect, check Location header
        if response['statusCode'] == 302:
            if 'Location' not in response['headers']:
                print("❌ 302 response missing Location header")
                return False
        
        print("✅ Response format is correct for API Gateway")
        print(f"   Status Code: {response['statusCode']}")
        print(f"   Headers: {list(response['headers'].keys())}")
        return True
        
    except Exception as e:
        print(f"❌ Handler raised exception: {e}")
        return False

def validate_error_handling():
    """Validate that handler properly handles invalid input."""
    
    class MockContext:
        def __init__(self):
            self.function_name = "test-function"
            self.aws_request_id = "test-request-id"
    
    try:
        # Test with None event
        response = lambda_handler(None, MockContext())
        
        if response['statusCode'] != 400:
            print(f"❌ Expected 400 status for None event, got: {response['statusCode']}")
            return False
        
        print("✅ Error handling works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error handling failed with exception: {e}")
        return False

def main():
    """Run all validation checks."""
    print("🔍 Validating Lambda handler conventions...")
    print()
    
    checks = [
        ("Handler Signature", validate_handler_signature),
        ("Response Format", validate_response_format),
        ("Error Handling", validate_error_handling)
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        print(f"Checking {name}...")
        if check_func():
            passed += 1
        print()
    
    print(f"📊 Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All Lambda handler convention checks passed!")
        return 0
    else:
        print("❌ Some checks failed. Please review the handler implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())