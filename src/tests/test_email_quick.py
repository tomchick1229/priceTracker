"""Quick email test once new app password is ready."""

import sys
from pathlib import Path
from datetime import datetime

# Add the project root to the path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.email_agent import EmailAgent


def quick_auth_test():
    """Quick authentication test."""
    print("🧪 QUICK EMAIL AUTHENTICATION TEST")
    print("=" * 50)
    
    try:
        agent = EmailAgent()
        print(f"Testing with: {agent.username}")
        
        if agent.test_connection():
            print("✅ Authentication SUCCESSFUL!")
            return True
        else:
            print("❌ Authentication still failing")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def send_test_emails():
    """Send both template and CLI summary test emails."""
    print("\n📧 SENDING TEST EMAILS")
    print("=" * 50)
    
    try:
        agent = EmailAgent()
        recipient = "tomchickchick@gmail.com"
        
        # Test 1: Simple template
        print("Sending template email...")
        template_success = agent.send_email(
            recipients=[recipient],
            content=f"""
🎉 EMAIL AGENT WORKING!

Great news! Your Gmail app password is now working correctly.

Test Details:
📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
✅ Authentication successful
✅ Email delivery working
✅ Price tracker email system ready

You can now receive price drop alerts and CLI summaries!
            """.strip(),
            title="✅ Price Tracker - Email Working!"
        )
        
        # Test 2: CLI Summary (using last known output)
        print("Sending CLI summary...")
        cli_summary = """[OK] fetched url=https://www.canadacomputers.com/... price=249.99 src=jsonld
[WARN] amazon link skipped (use PA-API/Keepa)
[WARN] amazon link skipped (use PA-API/Keepa)

============================================================
PRICE SUMMARY
============================================================
Product              Lowest Seen     Current Price  
------------------------------------------------------------
GPU1                 $1445.68        $1445.68       
HF8                  $109.95         $249.99        
TEST_DROP            $80.00          $80.00         
============================================================"""
        
        summary_success = agent.send_email(
            recipients=[recipient],
            content=f"""
📊 PRICE TRACKER CLI SUMMARY

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{cli_summary}

✅ Your price tracking system is fully operational and can now send automated reports!
            """.strip(),
            title="📊 Price Tracker - CLI Summary Report"
        )
        
        # Test 3: Price alert
        print("Sending price alert...")
        alert_success = agent.send_price_alert(
            recipients=[recipient],
            product_id="TEST_PRODUCT",
            old_price=299.99,
            new_price=199.99,
            retailer="Test Store",
            url="https://example.com/test"
        )
        
        return template_success, summary_success, alert_success
        
    except Exception as e:
        print(f"❌ Error sending emails: {e}")
        return False, False, False


def main():
    """Run quick test after app password update."""
    print("🚀 TESTING EMAIL AFTER APP PASSWORD UPDATE\n")
    
    # Quick auth test
    if not quick_auth_test():
        print("\n❌ Authentication still failing.")
        print("Please generate a NEW app password and update .env file.")
        print("Steps:")
        print("1. Go to https://myaccount.google.com/apppasswords")
        print("2. Generate new app password for 'Mail'")
        print("3. Update EMAIL_PASSWORD in .env file")
        print("4. Run this test again")
        return
    
    # Send test emails
    template_ok, summary_ok, alert_ok = send_test_emails()
    
    print("\n" + "=" * 50)
    print("📋 EMAIL TEST RESULTS")
    print("=" * 50)
    print(f"Authentication:     ✅ WORKING")
    print(f"Template Email:     {'✅ SENT' if template_ok else '❌ FAILED'}")
    print(f"CLI Summary Email:  {'✅ SENT' if summary_ok else '❌ FAILED'}")
    print(f"Price Alert Email:  {'✅ SENT' if alert_ok else '❌ FAILED'}")
    
    if all([template_ok, summary_ok, alert_ok]):
        print("\n🎉 ALL EMAIL TESTS PASSED!")
        print("✅ Your email agent is fully functional")
        print("✅ Check tomchickchick@gmail.com for 3 test emails")
        print("✅ Price tracking system ready for automated alerts")
    else:
        print("\n⚠️  Some emails failed to send")
        print("Authentication works but there may be other issues")
    
    print("=" * 50)


if __name__ == "__main__":
    main()
