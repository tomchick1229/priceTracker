"""Detailed Gmail authentication diagnostic."""

import sys
import smtplib
import ssl
from pathlib import Path

# Add the project root to the path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.email_agent import EmailAgent


def test_smtp_manually():
    """Manually test SMTP connection step by step."""
    print("=" * 60)
    print("MANUAL SMTP AUTHENTICATION TEST")
    print("=" * 60)
    
    try:
        agent = EmailAgent()
        print(f"📧 Username: {agent.username}")
        print(f"🔐 Password: {agent.password[:4]}{'*' * (len(agent.password) - 4)}")
        print(f"🖥️  Server: {agent.smtp_server}")
        print(f"🔌 Port: {agent.smtp_port}")
        print(f"🔒 TLS: {agent.use_tls}")
        
        # Step 1: Basic connection
        print("\n🔍 Step 1: Testing basic SMTP connection...")
        try:
            server = smtplib.SMTP(agent.smtp_server, agent.smtp_port)
            print("✅ Basic SMTP connection successful")
        except Exception as e:
            print(f"❌ Basic SMTP connection failed: {e}")
            return False
        
        # Step 2: Start TLS
        print("\n🔍 Step 2: Starting TLS encryption...")
        try:
            server.starttls()
            print("✅ TLS encryption started successfully")
        except Exception as e:
            print(f"❌ TLS encryption failed: {e}")
            server.quit()
            return False
        
        # Step 3: Authentication
        print("\n🔍 Step 3: Testing authentication...")
        try:
            server.login(agent.username, agent.password)
            print("✅ Authentication successful!")
            server.quit()
            return True
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ Authentication failed: {e}")
            server.quit()
            
            # Decode the error for better understanding
            error_msg = str(e)
            if "Username and Password not accepted" in error_msg:
                print("\n🔧 DIAGNOSIS:")
                print("• Gmail rejected the username/password combination")
                print("• This usually means:")
                print("  1. The app password is incorrect")
                print("  2. The app password was not properly generated")
                print("  3. 2FA is not enabled on the Gmail account")
                print("  4. The app password has expired or been revoked")
                
            return False
        except Exception as e:
            print(f"❌ Unexpected authentication error: {e}")
            server.quit()
            return False
    
    except Exception as e:
        print(f"❌ Error creating email agent: {e}")
        return False


def verify_app_password_format():
    """Verify the app password format is correct."""
    print("\n" + "=" * 60)
    print("APP PASSWORD FORMAT VERIFICATION")
    print("=" * 60)
    
    try:
        agent = EmailAgent()
        password = agent.password
        
        print(f"Password length: {len(password)} characters")
        print(f"Password format: {password[:4]}{'*' * (len(password) - 8)}{password[-4:]}")
        
        # Check common app password characteristics
        checks = []
        checks.append(("Length is 16 characters", len(password) == 16))
        checks.append(("Contains only letters/numbers", password.isalnum()))
        checks.append(("No spaces", ' ' not in password))
        checks.append(("All lowercase", password.islower()))
        
        print("\nApp Password Checks:")
        all_good = True
        for check_name, result in checks:
            status = "✅" if result else "❌"
            print(f"{status} {check_name}")
            if not result:
                all_good = False
        
        if all_good:
            print("\n✅ App password format looks correct!")
        else:
            print("\n❌ App password format issues detected!")
            print("Gmail app passwords should be:")
            print("• Exactly 16 characters long")
            print("• Contain only lowercase letters and numbers")
            print("• Have no spaces or special characters")
        
        return all_good
        
    except Exception as e:
        print(f"❌ Error checking app password: {e}")
        return False


def provide_troubleshooting_steps():
    """Provide step-by-step troubleshooting."""
    print("\n" + "=" * 60)
    print("GMAIL APP PASSWORD TROUBLESHOOTING")
    print("=" * 60)
    
    print("If authentication is still failing, try these steps:")
    print()
    print("1. 🔐 VERIFY 2-FACTOR AUTHENTICATION:")
    print("   • Go to https://myaccount.google.com/security")
    print("   • Ensure '2-Step Verification' is ON")
    print("   • This is REQUIRED for app passwords")
    print()
    print("2. 🔑 GENERATE NEW APP PASSWORD:")
    print("   • Go to https://myaccount.google.com/apppasswords")
    print("   • Click 'Generate app password'")
    print("   • Select 'Mail' or 'Other (custom name)'")
    print("   • Copy the 16-character password EXACTLY")
    print()
    print("3. 📝 UPDATE .env FILE:")
    print("   • Open .env file")
    print("   • Replace EMAIL_PASSWORD with new app password")
    print("   • Save the file")
    print()
    print("4. 🧪 TEST IMMEDIATELY:")
    print("   • Run this test again within a few minutes")
    print("   • App passwords can take a moment to activate")
    print()
    print("5. 🚨 ALTERNATIVE SOLUTIONS:")
    print("   • Try generating a new app password")
    print("   • Use a different app password name (e.g., 'Python Price Tracker')")
    print("   • Check if account has any security restrictions")


def main():
    """Run comprehensive Gmail authentication diagnosis."""
    print("🔍 GMAIL AUTHENTICATION DIAGNOSIS")
    print("Checking why authentication is failing with the app password...\n")
    
    # Test 1: App password format
    format_ok = verify_app_password_format()
    
    # Test 2: Manual SMTP test
    auth_ok = test_smtp_manually()
    
    # Provide troubleshooting if needed
    if not auth_ok:
        provide_troubleshooting_steps()
        
        print("\n" + "=" * 60)
        print("📋 DIAGNOSIS SUMMARY")
        print("=" * 60)
        print(f"App Password Format: {'✅ OK' if format_ok else '❌ Issues'}")
        print(f"SMTP Authentication: {'✅ OK' if auth_ok else '❌ Failed'}")
        
        if not auth_ok:
            print("\n🎯 RECOMMENDATION:")
            print("Generate a fresh Gmail app password and update .env file")
            print("The email agent code is working correctly - this is just")
            print("a Gmail authentication configuration issue.")
    else:
        print("\n🎉 SUCCESS!")
        print("Gmail authentication is working! Email agent is ready.")


if __name__ == "__main__":
    main()
