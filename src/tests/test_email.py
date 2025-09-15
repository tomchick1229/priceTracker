"""Test module for email agent functionality.

This script tests the email functionality using the EMAIL_LIST from the .env file.

Usage:
    python src/tests/test_email.py           # Interactive mode with prompts
    python src/tests/test_email.py --auto    # Automated mode (no prompts)

Requirements:
    - .env file with EMAIL_USERNAME, EMAIL_PASSWORD, and EMAIL_LIST configured
    - EMAIL_LIST should be in format: ['email1@example.com', 'email2@example.com']
"""

import sys
import os
import ast
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.email_agent import EmailAgent


def get_email_recipients():
    """Get email recipients from EMAIL_LIST environment variable."""
    email_list_str = os.getenv('EMAIL_LIST')
    if not email_list_str:
        print("⚠️  EMAIL_LIST not found in .env file")
        return []
    
    try:
        # Parse the string representation of the list
        email_list = ast.literal_eval(email_list_str)
        if isinstance(email_list, list):
            print(f"📧 Found {len(email_list)} email addresses in EMAIL_LIST:")
            for email in email_list:
                print(f"   - {email}")
            return email_list
        else:
            print("❌ EMAIL_LIST is not a valid list format")
            return []
    except (ValueError, SyntaxError) as e:
        print(f"❌ Error parsing EMAIL_LIST: {e}")
        print("   Make sure EMAIL_LIST is in format: ['email1@example.com', 'email2@example.com']")
        return []


def test_email_connection():
    """Test email connection without sending an email."""
    print("Testing email connection...")
    try:
        agent = EmailAgent()
        success = agent.test_connection()
        if success:
            print("✅ Email connection test passed!")
        else:
            print("❌ Email connection test failed!")
        return success
    except Exception as e:
        print(f"❌ Error creating email agent: {e}")
        return False


def test_send_email():
    """Test sending a basic email to EMAIL_LIST recipients."""
    print("\nTesting email sending to EMAIL_LIST...")
    try:
        agent = EmailAgent()
        
        # Get recipients from environment variable
        recipients = get_email_recipients()
        if not recipients:
            print("❌ No recipients found in EMAIL_LIST, skipping email send test")
            return False
        
        # Send test email
        success = agent.send_email(
            recipients=recipients,
            content="This is a test email from the Kenborough Price Tracker system. If you receive this, the email configuration is working correctly!",
            title="Kenborough Price Tracker - Email Test"
        )
        
        if success:
            print(f"✅ Test email sent successfully to {len(recipients)} recipients!")
        else:
            print("❌ Failed to send test email!")
        
        return success
    except Exception as e:
        print(f"❌ Error sending test email: {e}")
        return False


def test_price_alert_email():
    """Test sending a price alert email to EMAIL_LIST recipients."""
    print("\nTesting price alert email to EMAIL_LIST...")
    try:
        agent = EmailAgent()
        
        # Get recipients from environment variable
        recipients = get_email_recipients()
        if not recipients:
            print("❌ No recipients found in EMAIL_LIST, skipping price alert test")
            return False
        
        # Send test price alert
        success = agent.send_price_alert(
            recipients=recipients,
            product_id="TEST_PRODUCT - Sample Item",
            old_price=299.99,
            new_price=199.99,
            retailer="Test Store",
            url="https://example.com/product"
        )
        
        if success:
            print(f"✅ Price alert email sent successfully to {len(recipients)} recipients!")
        else:
            print("❌ Failed to send price alert email!")
        
        return success
    except Exception as e:
        print(f"❌ Error sending price alert email: {e}")
        return False


def test_all_emails_auto():
    """Run all email tests automatically without prompts."""
    print("=" * 50)
    print("AUTOMATED EMAIL TEST SUITE")
    print("=" * 50)
    
    # Show email configuration
    recipients = get_email_recipients()
    if not recipients:
        print("\n❌ No valid EMAIL_LIST found. Please check your .env file.")
        return False
    
    # Test 1: Connection test
    print("1. Testing email connection...")
    if not test_email_connection():
        print("❌ Connection test failed!")
        return False
    
    # Test 2: Basic email
    print("\n2. Testing basic email sending...")
    if not test_send_email():
        print("❌ Basic email test failed!")
        return False
    
    # Test 3: Price alert email
    print("\n3. Testing price alert email...")
    if not test_price_alert_email():
        print("❌ Price alert test failed!")
        return False
    
    print("\n" + "=" * 50)
    print("✅ All automated email tests passed!")
    print(f"📧 Successfully sent emails to {len(recipients)} recipients")
    print("=" * 50)
    return True


def main():
    """Run all email tests."""
    print("=" * 50)
    print("EMAIL AGENT TEST SUITE")
    print("=" * 50)
    print("Testing with EMAIL_LIST from .env file")
    print("=" * 50)
    
    # Show email configuration
    recipients = get_email_recipients()
    if not recipients:
        print("\n❌ No valid EMAIL_LIST found. Please check your .env file.")
        print("Example EMAIL_LIST format in .env:")
        print("EMAIL_LIST=['email1@example.com', 'email2@example.com']")
        return
    
    # Check if we should run automated tests
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--auto':
        test_all_emails_auto()
        return
    
    # Test 1: Connection test
    connection_ok = test_email_connection()
    
    if not connection_ok:
        print("\n❌ Connection test failed. Please check your .env configuration.")
        print("Required .env settings:")
        print("EMAIL_USERNAME=your_email@gmail.com")
        print("EMAIL_PASSWORD=your_app_password")
        print("EMAIL_LIST=['recipient1@example.com', 'recipient2@example.com']")
        return
    
    # Test 2: Basic email sending
    print("\n" + "=" * 30)
    send_basic = input("Do you want to test sending a basic email to EMAIL_LIST? (y/n): ").lower().strip()
    if send_basic == 'y':
        test_send_email()
    
    # Test 3: Price alert email
    print("\n" + "=" * 30)
    send_alert = input("Do you want to test sending a price alert email to EMAIL_LIST? (y/n): ").lower().strip()
    if send_alert == 'y':
        test_price_alert_email()
    
    print("\n" + "=" * 50)
    print("Email agent tests completed!")
    print(f"All tests used EMAIL_LIST with {len(recipients)} recipients")
    print("=" * 50)


if __name__ == "__main__":
    main()
