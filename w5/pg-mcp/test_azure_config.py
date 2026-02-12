"""
Azure OpenAI Configuration Test Script

This script helps you verify that your Azure OpenAI configuration is correct
before running the pg-mcp server.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import pg_mcp_server modules
sys.path.insert(0, str(Path(__file__).parent))

from pg_mcp_server.config.settings import Settings


def test_azure_openai_config():
    """Test Azure OpenAI configuration."""
    
    print("=" * 60)
    print("Azure OpenAI Configuration Test")
    print("=" * 60)
    print()
    
    # Check environment variables
    print("1. Checking environment variables...")
    print()
    
    config_path = os.getenv("CONFIG_PATH", "config.yaml")
    db_password = os.getenv("DB_PASSWORD")
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    
    issues = []
    
    if not db_password:
        issues.append("❌ DB_PASSWORD is not set")
    else:
        print(f"✅ DB_PASSWORD: {'*' * 8}")
    
    if not azure_api_key:
        issues.append("❌ AZURE_OPENAI_API_KEY is not set")
    else:
        print(f"✅ AZURE_OPENAI_API_KEY: {azure_api_key[:8]}...{azure_api_key[-4:]}")
    
    if not azure_endpoint:
        issues.append("❌ AZURE_OPENAI_ENDPOINT is not set")
    else:
        print(f"✅ AZURE_OPENAI_ENDPOINT: {azure_endpoint}")
    
    if not azure_deployment:
        issues.append("❌ AZURE_OPENAI_DEPLOYMENT is not set")
    else:
        print(f"✅ AZURE_OPENAI_DEPLOYMENT: {azure_deployment}")
    
    print(f"✅ CONFIG_PATH: {config_path}")
    print()
    
    # Check configuration file
    print("2. Loading configuration file...")
    print()
    
    config_file = Path(config_path)
    if not config_file.exists():
        issues.append(f"❌ Configuration file not found: {config_path}")
        print(f"❌ Configuration file not found: {config_path}")
    else:
        print(f"✅ Configuration file found: {config_path}")
        
        try:
            settings = Settings()
            print(f"✅ Configuration loaded successfully")
            print()
            
            # Check OpenAI configuration
            print("3. Checking OpenAI configuration...")
            print()
            
            openai_config = settings.openai
            
            if openai_config.use_azure:
                print("✅ Azure OpenAI mode is ENABLED")
                print()
                print(f"   - Azure Endpoint: {openai_config.azure_endpoint}")
                print(f"   - Azure Deployment: {openai_config.azure_deployment}")
                print(f"   - API Version: {openai_config.api_version}")
                print(f"   - Timeout: {openai_config.timeout}s")
                print(f"   - Max Retries: {openai_config.max_retries}")
                
                if not openai_config.azure_endpoint:
                    issues.append("❌ azure_endpoint is not set in config")
                if not openai_config.azure_deployment:
                    issues.append("❌ azure_deployment is not set in config")
            else:
                issues.append("❌ Azure OpenAI mode is DISABLED (use_azure=false)")
                print("❌ Azure OpenAI mode is DISABLED")
                print()
                print("   Please set 'use_azure: true' in your config file")
            
        except Exception as e:
            issues.append(f"❌ Failed to load configuration: {str(e)}")
            print(f"❌ Failed to load configuration: {str(e)}")
    
    print()
    
    # Check database configuration
    print("4. Checking database configuration...")
    print()
    
    try:
        db_config = settings.database
        print(f"✅ Database configuration loaded")
        print()
        print(f"   - Host: {db_config.host}")
        print(f"   - Port: {db_config.port}")
        print(f"   - Database: {db_config.database}")
        print(f"   - User: {db_config.user}")
        print(f"   - Password: {'*' * 8}")
    except Exception as e:
        issues.append(f"❌ Failed to load database configuration: {str(e)}")
        print(f"❌ Failed to load database configuration: {str(e)}")
    
    print()
    print("=" * 60)
    
    # Print summary
    if issues:
        print("❌ Configuration has issues:")
        print()
        for issue in issues:
            print(f"   {issue}")
        print()
        print("Please fix the issues above before running pg-mcp server.")
        return False
    else:
        print("✅ All checks passed!")
        print()
        print("Your Azure OpenAI configuration looks good.")
        print("You can now run the pg-mcp server:")
        print()
        print("   uvx --refresh --from . pg-mcp")
        print()
        return True


if __name__ == "__main__":
    success = test_azure_openai_config()
    sys.exit(0 if success else 1)
