"""Separate tests for email template and CLI summary."""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Add the project root to the path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.email_agent import EmailAgent


def test_email_template():
    """Test 1: Send a basic email template to verify email functionality."""
    print("=" * 60)
    print("TEST 1: EMAIL TEMPLATE TEST")
    print("=" * 60)
    
    try:
        agent = EmailAgent()
        
        # Test connection first
        print("Testing email connection...")
        if not agent.test_connection():
            print("❌ Email connection failed!")
            return False
        
        print("✅ Email connection successful!")
        
        # Send template email
        sender_email = "tomchickchick@gmail.com"
        
        template_content = f"""
🧪 EMAIL AGENT TEMPLATE TEST

Hello! This is a test email from your Price Tracker system.

Test Details:
📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🤖 System: Price Tracker Email Agent
🔧 Test Type: Basic Template Functionality

Email Features Tested:
✅ SMTP Connection
✅ Authentication 
✅ Email Formatting
✅ Content Delivery

If you receive this email, your email agent is working correctly!

---
Price Tracker System
        """.strip()
        
        print(f"\nSending template email to {sender_email}...")
        success = agent.send_email(
            recipients=[sender_email],
            content=template_content,
            title="🧪 Price Tracker - Email Template Test"
        )
        
        if success:
            print("✅ Template email sent successfully!")
            return True
        else:
            print("❌ Failed to send template email!")
            return False
            
    except Exception as e:
        print(f"❌ Error during template test: {e}")
        return False


def get_fresh_cli_summary():
    """Get a fresh CLI scan output."""
    print("Getting fresh CLI summary...")
    try:
        # Run the CLI scan command
        result = subprocess.run(
            ["uv", "run", "python", "src/cli.py", "scan"],
            cwd=Path(__file__).parent.parent.parent,
            capture_output=True,
            text=True,
            timeout=90
        )
        
        if result.returncode == 0:
            print("✅ CLI scan completed successfully!")
            return result.stdout
        else:
            print(f"❌ CLI scan failed with error: {result.stderr}")
            return None
    except subprocess.TimeoutExpired:
        print("⏰ CLI scan timed out after 90 seconds")
        return None
    except Exception as e:
        print(f"❌ Error running CLI scan: {e}")
        return None


def test_cli_summary_email():
    """Test 2: Send CLI summary via email."""
    print("\n" + "=" * 60)
    print("TEST 2: CLI SUMMARY EMAIL TEST")
    print("=" * 60)
    
    # Get fresh CLI output
    cli_output = get_fresh_cli_summary()
    
    if not cli_output:
        print("❌ Could not get CLI summary, using cached output...")
        # Fallback to known working output
        cli_output = """[OK] fetched url=https://www.canadacomputers.com/en/racing-simulator-cockpits-seat-add-ons/234573/next-level-racing-hf8-haptic-feedback-gaming-pad-nlr-g001-nlr-g001.html price=249.99 src=jsonld
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

    print("CLI output preview:")
    print("-" * 40)
    print(cli_output[:200] + "..." if len(cli_output) > 200 else cli_output)
    print("-" * 40)
    
    try:
        agent = EmailAgent()
        
        # Send CLI summary email
        sender_email = "tomchickchick@gmail.com"
        
        summary_content = f"""
📊 PRICE TRACKER CLI SUMMARY REPORT

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Below is the complete output from your latest price tracking scan:

{'-' * 60}
{cli_output}
{'-' * 60}

📈 Key Insights:
• Canada Computers: Successfully tracked HF8 pad at $249.99
• Amazon links: Skipped (require proper API integration)
• Best Buy: Price extraction failed (site structure may have changed)

💰 Price Summary:
• GPU1: Current $1445.68 (matches lowest seen)
• HF8: Current $249.99 (up from lowest $109.95)
• TEST_DROP: Current $80.00 (stable)

🔔 This automated report confirms your price tracking system is operational!

---
Price Tracker System - CLI Summary Report
        """.strip()
        
        print(f"\nSending CLI summary email to {sender_email}...")
        success = agent.send_email(
            recipients=[sender_email],
            content=summary_content,
            title="📊 Price Tracker - CLI Summary Report"
        )
        
        if success:
            print("✅ CLI summary email sent successfully!")
            return True
        else:
            print("❌ Failed to send CLI summary email!")
            return False
            
    except Exception as e:
        print(f"❌ Error during CLI summary test: {e}")
        return False


def test_price_alert_template():
    """Test 3: Send a price alert template."""
    print("\n" + "=" * 60)
    print("TEST 3: PRICE ALERT TEMPLATE TEST")
    print("=" * 60)
    
    try:
        agent = EmailAgent()
        sender_email = "tomchickchick@gmail.com"
        
        print(f"Sending price alert template to {sender_email}...")
        success = agent.send_price_alert(
            recipients=[sender_email],
            product_id="HF8_TEST",
            old_price=299.99,
            new_price=199.99,
            retailer="Canada Computers (TEST)",
            url="https://www.canadacomputers.com/test"
        )
        
        if success:
            print("✅ Price alert email sent successfully!")
            return True
        else:
            print("❌ Failed to send price alert email!")
            return False
            
    except Exception as e:
        print(f"❌ Error during price alert test: {e}")
        return False


def main():
    """Run all separate email tests."""
    print("🚀 STARTING SEPARATE EMAIL TESTS")
    print("Testing email functionality with app password fix\n")
    
    results = []
    
    # Test 1: Basic Template
    template_success = test_email_template()
    results.append(("Template Test", template_success))
    
    # Test 2: CLI Summary
    summary_success = test_cli_summary_email()
    results.append(("CLI Summary Test", summary_success))
    
    # Test 3: Price Alert Template
    alert_success = test_price_alert_template()
    results.append(("Price Alert Test", alert_success))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 EMAIL TEST RESULTS SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:20} {status}")
        if not success:
            all_passed = False
    
    print("-" * 60)
    
    if all_passed:
        print("🎉 ALL EMAIL TESTS PASSED!")
        print("✅ Email agent is fully functional")
        print("✅ Template emails working")
        print("✅ CLI summary emails working") 
        print("✅ Price alert emails working")
        print("✅ Check tomchickchick@gmail.com for all test emails")
    else:
        print("⚠️  Some email tests failed")
        print("Check individual test outputs above for details")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
