"""
Configuration file for API Data Puller
"""

import os
from typing import Dict

# Default configuration
DEFAULT_CONFIG = {
    'api': {
        'base_url': 'https://api.example.com',
        'version': 'v1',
        'timeout': 30,
        'max_retries': 3,
        'requests_per_second': 10
    },
    'output': {
        'directory': 'data',
        'format': 'json'
    },
    'logging': {
        'level': 'INFO',
        'file': 'logs/api_data.log'
    }
}

def get_config() -> Dict:
    """
    Get configuration from environment variables or defaults
    
    Returns:
        Dict: Configuration dictionary
    """
    config = DEFAULT_CONFIG.copy()
    
    # Override with environment variables if available
    config['api']['base_url'] = os.getenv('API_BASE_URL', config['api']['base_url'])
    config['api']['version'] = os.getenv('API_VERSION', config['api']['version'])
    config['api']['timeout'] = int(os.getenv('TIMEOUT_SECONDS', str(config['api']['timeout'])))
    config['api']['max_retries'] = int(os.getenv('MAX_RETRIES', str(config['api']['max_retries'])))
    config['api']['requests_per_second'] = int(os.getenv('REQUESTS_PER_SECOND', str(config['api']['requests_per_second'])))
    
    config['output']['directory'] = os.getenv('OUTPUT_DIRECTORY', config['output']['directory'])
    config['output']['format'] = os.getenv('OUTPUT_FORMAT', config['output']['format'])
    
    config['logging']['level'] = os.getenv('LOG_LEVEL', config['logging']['level'])
    config['logging']['file'] = os.getenv('LOG_FILE', config['logging']['file'])
    
    return config
