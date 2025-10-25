"""Email agent for sending notifications."""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import ast

# Load environment variables
load_dotenv()


class EmailAgent:
    """Email agent for sending notifications with SMTP."""
    
    def __init__(self):
        """Initialize email agent with configuration from environment variables."""
        self.smtp_server = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('EMAIL_SMTP_PORT', '587'))
        username = os.getenv('EMAIL_USERNAME')
        password = os.getenv('EMAIL_PASSWORD')
        self.from_name = os.getenv('EMAIL_FROM_NAME', 'Price Tracker')
        self.use_tls = os.getenv('EMAIL_USE_TLS', 'true').lower() == 'true'
        self.admin_email_list = os.getenv('ADMIN_EMAIL_LIST', None)
        self.email_list = os.getenv('EMAIL_LIST', None)
        
        if not username or not password:
            raise ValueError("EMAIL_USERNAME and EMAIL_PASSWORD must be set in .env file")
        
        # Store as guaranteed strings
        self.username = username
        self.password = password

    def filter_positive(self, summary: dict) -> dict:
        """Filter summary to only include positive price drops."""
        positive_summary = []
        for item in summary:
            if item.get("savings") and item["savings"] > 0:
                positive_summary.append(item)
        return positive_summary
    
    def send_template_email(self, type: str, recipients: str, summary: dict) -> None:
        current_datetime = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
        
        env = Environment(loader=FileSystemLoader("templates"))
        if type == "summary":
            template = env.get_template("summary.j2")
        elif type == "positive":
            template = env.get_template("positive_email.j2")
            summary = self.filter_positive(summary)
        elif type == "negative":
            template = env.get_template("negative_email.j2")
        else:
            print(f"[EMAIL ERROR] Invalid email type: {type}")
            return
        print(f"{summary = }")
        owners = ""
        for item in summary:
            print(f"{item = }")
            if item.get("owner"):
                owners += ", " + item.get("owner")
        owners = owners.lstrip(", ")
        rendered = template.render(datetime=current_datetime, summary=summary, owners=owners)
        lines = rendered.strip().splitlines()
        title = lines[0].replace("# Subject:", "").strip()
        body = "\n".join(lines[1:]).strip()

        # Convert recipients string to actual email list
        email_list = []
        if recipients == "general" and self.email_list:
            email_list = ast.literal_eval(self.email_list)
        elif recipients == "admin" and self.admin_email_list:
            email_list = ast.literal_eval(self.admin_email_list)
        else:
            print(f"[EMAIL ERROR] Invalid recipients type or empty email list: {recipients}")
            return

        try: 
            self.send_email(
                recipients=email_list,
                content=body,
                title=title
            )
            return True
        except Exception as e:
            print(f"[EMAIL ERROR] Failed to send summary email: {e}")
            return False
            
            
    def send_email(self, 
                   recipients: List[str], 
                   content: str, 
                   title: str,
                   content_type: str = 'plain',
                   cc: Optional[List[str]] = None,
                   bcc: Optional[List[str]] = None) -> bool:
        """
        Send email to recipients.
        
        Args:
            recipients: List of email addresses to send to
            content: Email content/body
            title: Email subject line
            content_type: 'plain' or 'html'
            cc: Optional list of CC recipients
            bcc: Optional list of BCC recipients
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"{self.from_name} <{self.username}>"
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = title
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            
            # Attach body
            msg.attach(MIMEText(content, content_type))
            
            # Connect to server and send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                
                # Combine all recipients for actual sending
                all_recipients = recipients[:]
                if cc:
                    all_recipients.extend(cc)
                if bcc:
                    all_recipients.extend(bcc)
                
                server.sendmail(self.username, all_recipients, msg.as_string())
            
            print(f"[EMAIL] Successfully sent '{title}' to {len(recipients)} recipients")
            return True
            
        except Exception as e:
            print(f"[EMAIL ERROR] Failed to send email: {e}")
            return False
    
    def send_price_alert(self, 
                        recipients: List[str], 
                        product_id: str, 
                        old_price: float, 
                        new_price: float, 
                        retailer: str,
                        url: str) -> bool:
        """
        Send a price drop alert email.
        
        Args:
            recipients: List of email addresses
            product_id: Product identifier
            old_price: Previous price
            new_price: Current (lower) price
            retailer: Retailer name
            url: Product URL
            
        Returns:
            bool: True if sent successfully
        """
        savings = old_price - new_price
        savings_pct = (savings / old_price) * 100
        
        title = f"買野啦！！！ {product_id} 有減價！ - ${savings:.2f} !"
        
        content = f"""
而家唔買幾時買？！

Product: {product_id}
Retailer: {retailer}
Previous Price: ${old_price:.2f}
New Price: ${new_price:.2f}
Savings: ${savings:.2f} ({savings_pct:.1f}% off)

View Product: {url}

買啦頂你
- Kenborough Price Tracker
        """.strip()
        
        return self.send_email(recipients, content, title)
    
    def test_connection(self) -> bool:
        """Test email connection and configuration."""
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
            print("[EMAIL] Connection test successful")
            return True
        except Exception as e:
            print(f"[EMAIL ERROR] Connection test failed: {e}")
            return False
