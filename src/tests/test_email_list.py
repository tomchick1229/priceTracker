"""Test email functionality with multiple recipients (email list)."""

import sys
from pathlib import Path
from datetime import datetime

# Add the project root to the path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.email_agent import EmailAgent


def test_email_list():
    """Test sending emails to multiple recipients."""
    print("=" * 60)
    print("EMAIL LIST TEST - MULTIPLE RECIPIENTS")
    print("=" * 60)
    
    # Define email list (multiple recipients)
    email_list = [
        "tomchickchick@gmail.com",  # Primary recipient
        "tomchickwk@gmail.com",     # Secondary recipient
        # Add more emails as needed
    ]
    
    print(f"📧 Testing with {len(email_list)} recipients:")
    for i, email in enumerate(email_list, 1):
        print(f"  {i}. {email}")
    
    try:
        agent = EmailAgent()
        
        # Test 1: Authentication
        print("\n🔍 Testing email connection...")
        if not agent.test_connection():
            print("❌ Email connection failed!")
            return False
        
        print("✅ Email connection successful!")
        
        # Test 2: Template email to multiple recipients
        print(f"\n📤 Sending template email to {len(email_list)} recipients...")
        
        template_content = f"""
🧪 EMAIL LIST TEST - MULTIPLE RECIPIENTS

Hello! This is a test email sent to multiple recipients from your Price Tracker system.

Test Details:
📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🎯 Test Type: Multiple Recipients Email List
👥 Recipients: {len(email_list)} people
🤖 System: Price Tracker Email Agent

Email List Features Tested:
✅ Multiple recipient support
✅ Bulk email sending
✅ Email formatting consistency
✅ Delivery to all recipients

If you receive this email, your email agent can successfully send to multiple recipients!

Recipients in this test:
{chr(10).join([f"• {email}" for email in email_list])}

---
Price Tracker System - Email List Test
        """.strip()
        
        template_success = agent.send_email(
            recipients=email_list,
            content=template_content,
            title="📧 Price Tracker - Email List Test (Multiple Recipients)"
        )
        
        # Test 3: CLI Summary to email list
        print(f"\n📊 Sending CLI summary to {len(email_list)} recipients...")
        
        # Use recent CLI output
        cli_summary = """[OK] fetched url=https://www.canadacomputers.com/en/racing-simulator-cockpits-seat-add-ons/234573/next-level-racing-hf8-haptic-feedback-gaming-pad-nlr-g001-nlr-g001.html price=249.99 src=jsonld
[WARN] amazon link skipped (use PA-API/Keepa)
[WARN] amazon link skipped (use PA-API/Keepa)
[ERROR] Failed to process https://www.bestbuy.ca/en-ca/product/edifier-r1280dbs-active-bluetooth-bookshelf-speakers/15555528: Could not extract price from https://www.bestbuy.ca/en-ca/product/edifier-r1280dbs-active-bluetooth-bookshelf-speakers/15555528

============================================================
PRICE SUMMARY
============================================================
Product              Lowest Seen     Current Price  
------------------------------------------------------------
GPU1                 $1445.68        $1445.68       
HF8                  $109.95         $249.99        
TEST_DROP            $80.00          $80.00         
============================================================"""
        
        summary_content = f"""
📊 PRICE TRACKER CLI SUMMARY - EMAIL LIST DISTRIBUTION

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Sent to: {len(email_list)} recipients

{cli_summary}

📈 Summary Insights:
• Canada Computers HF8: Currently $249.99 (up from lowest $109.95)
• GPU1: Stable at $1445.68
• TEST_DROP: Stable at $80.00

🔔 Threshold Settings:
• HF8: Needs $25+ AND 10%+ drop to trigger alert
• Edifier R1280DBs: Needs $15+ AND 10%+ drop to trigger alert

This automated CLI summary is being distributed to your configured email list!

Recipients:
{chr(10).join([f"• {email}" for email in email_list])}

---
Price Tracker System - CLI Summary Distribution
        """.strip()
        
        summary_success = agent.send_email(
            recipients=email_list,
            content=summary_content,
            title="📊 Price Tracker - CLI Summary (Email List Distribution)"
        )
        
        # Test 4: Price Alert to email list
        print(f"\n🚨 Sending price alert to {len(email_list)} recipients...")
        
        alert_success = agent.send_price_alert(
            recipients=email_list,
            product_id="HF8_EMAIL_LIST_TEST",
            old_price=249.99,
            new_price=179.99,
            retailer="Canada Computers",
            url="https://www.canadacomputers.com/test-email-list"
        )
        
        return template_success, summary_success, alert_success
        
    except Exception as e:
        print(f"❌ Error during email list test: {e}")
        return (False, False, False)


def test_single_vs_multiple():
    """Compare sending to single recipient vs multiple recipients."""
    print("\n" + "=" * 60)
    print("SINGLE VS MULTIPLE RECIPIENT COMPARISON")
    print("=" * 60)
    
    try:
        agent = EmailAgent()
        
        # Test single recipient
        print("📤 Testing single recipient...")
        single_success = agent.send_email(
            recipients=["tomchickchick@gmail.com"],
            content="This email was sent to a SINGLE recipient for comparison testing.",
            title="🎯 Price Tracker - Single Recipient Test"
        )
        
        # Test multiple recipients
        print("📤 Testing multiple recipients...")
        multiple_success = agent.send_email(
            recipients=["tomchickchick@gmail.com", "tomchickwk@gmail.com"],
            content="This email was sent to MULTIPLE recipients for comparison testing.",
            title="👥 Price Tracker - Multiple Recipients Test"
        )
        
        return single_success, multiple_success
        
    except Exception as e:
        print(f"❌ Error during comparison test: {e}")
        return (False, False)


def main():
    """Run email list tests."""
    print("🚀 STARTING EMAIL LIST TESTS")
    print("Testing email functionality with multiple recipients\n")
    
    # Test email list functionality
    template_ok, summary_ok, alert_ok = test_email_list()
    
    # Test single vs multiple
    single_ok, multiple_ok = test_single_vs_multiple()
    
    # Results summary
    print("\n" + "=" * 60)
    print("📋 EMAIL LIST TEST RESULTS")
    print("=" * 60)
    
    print("EMAIL LIST TESTS:")
    print(f"Template to Email List:    {'✅ SENT' if template_ok else '❌ FAILED'}")
    print(f"CLI Summary to Email List: {'✅ SENT' if summary_ok else '❌ FAILED'}")
    print(f"Price Alert to Email List: {'✅ SENT' if alert_ok else '❌ FAILED'}")
    
    print("\nCOMPARISON TESTS:")
    print(f"Single Recipient:          {'✅ SENT' if single_ok else '❌ FAILED'}")
    print(f"Multiple Recipients:       {'✅ SENT' if multiple_ok else '❌ FAILED'}")
    
    print("-" * 60)
    
    all_passed = all([template_ok, summary_ok, alert_ok, single_ok, multiple_ok])
    
    if all_passed:
        print("🎉 ALL EMAIL LIST TESTS PASSED!")
        print("✅ Email agent supports multiple recipients")
        print("✅ Template emails sent to email list")
        print("✅ CLI summaries distributed to email list") 
        print("✅ Price alerts sent to email list")
        print("✅ Single and multiple recipient modes working")
        print("\n📬 CHECK BOTH EMAIL ADDRESSES:")
        print("• tomchickchick@gmail.com")
        print("• tomchickwk@gmail.com")
        print("\nYou should have received 5 test emails at each address!")
    else:
        print("⚠️  Some email list tests failed")
        print("Check individual test outputs above for details")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
