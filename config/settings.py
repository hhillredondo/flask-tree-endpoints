import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Amplify/Cognito settings
    AMPLIFY_USER_POOL_ID = os.getenv('AMPLIFY_USER_POOL_ID')
    AWS_REGION = os.getenv('AWS_REGION', 'eu-central-1')

    # ACL/DynamoDB settings
    ACL_TABLE_NAME = os.getenv('ACL_TABLE_NAME', 'TreeAcl')
    ROLE_CACHE_TTL_SECONDS = int(os.getenv('ROLE_CACHE_TTL_SECONDS', '30'))
    LOCK_TABLE_NAME = os.getenv('LOCK_TABLE_NAME', 'TreeEditorLocks')
    LOCK_TTL_SECONDS = int(os.getenv('LOCK_TTL_SECONDS', '300'))
    
    # Gremlin/Neptune settings
    GREMLIN_ENDPOINT = os.getenv('GREMLIN_ENDPOINT', 'localhost')
    GREMLIN_PORT = int(os.getenv('GREMLIN_PORT', '8182'))
    GREMLIN_SSL = os.getenv('GREMLIN_SSL', 'false').lower() == 'true'
    
    # CORS settings
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    # S3 media storage
    S3_MEDIA_BUCKET = os.getenv('S3_MEDIA_BUCKET')
    S3_MEDIA_PREFIX = os.getenv('S3_MEDIA_PREFIX', 'trees')
    S3_PUBLIC_BASE_URL = os.getenv('S3_PUBLIC_BASE_URL')
    S3_PIC_SIZE = int(os.getenv('S3_PIC_SIZE', '24'))
    S3_PRESIGNED_TTL_SECONDS = int(os.getenv('S3_PRESIGNED_TTL_SECONDS', '3600'))


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
