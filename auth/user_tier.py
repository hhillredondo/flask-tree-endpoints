"""
User tier system for managing subscription levels and limit exemptions.

This module is designed to be easily extensible for future pro user subscriptions.
Currently, all users are 'free' tier. To add pro users later, simply update
get_user_tier() to check Cognito custom attributes, DynamoDB, or external services.
"""


def get_user_tier(user_id: str) -> str:
    """
    Get user's subscription tier.
    
    Args:
        user_id: The Cognito user ID (sub)
    
    Returns:
        'free' or 'pro' (defaults to 'free' for now)
    
    Future implementation options:
    - Check Cognito custom attribute 'custom:subscription_tier'
    - Or check DynamoDB UserProfiles table
    - Or check external subscription service (Stripe, etc.)
    """
    # For now, always return 'free'
    # Future: Check Cognito custom attribute or DynamoDB
    # Example:
    #   cognito_client = boto3.client('cognito-idp')
    #   response = cognito_client.admin_get_user(
    #       UserPoolId=os.getenv('AMPLIFY_USER_POOL_ID'),
    #       Username=user_id
    #   )
    #   for attr in response.get('UserAttributes', []):
    #       if attr['Name'] == 'custom:subscription_tier':
    #           return attr['Value']  # 'free' or 'pro'
    return 'free'


def is_limit_exempt(user_id: str) -> bool:
    """
    Check if user is exempt from limits (pro users).
    
    Args:
        user_id: The Cognito user ID (sub)
    
    Returns:
        True if user is exempt from limits (pro tier), False otherwise
    """
    return get_user_tier(user_id) == 'pro'


