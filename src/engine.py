"""Engine for price drop detection and alert deduplication."""

from typing import Optional, List
from src.models import OfferSnapshot, PriceEvent
from src.storage import Storage
from src.email_agent import EmailAgent

class PriceEngine:
    """Engine for detecting price drops and managing alerts."""
    
    def __init__(self, storage: Storage, email_recipients: Optional[List[str]] = None):
        self.storage = storage
        self.email_recipients = email_recipients or []
        self.email_agent = None
        self.email_agent = EmailAgent()
        
        # # Initialize email agent if recipients are provided and email is available
        # if self.email_recipients and EMAIL_AVAILABLE:
        #     try:
        #         self.email_agent = EmailAgent()
        #         print(f"[EMAIL] Initialized email notifications for {len(self.email_recipients)} recipients")
        #     except Exception as e:
        #         print(f"[EMAIL] Failed to initialize email agent: {e}")
        #         self.email_agent = None
    
    def detect_drop(self, snapshot: OfferSnapshot, min_abs: float, min_pct: float) -> Optional[PriceEvent]:
        """Detect if there's a price drop compared to last price.
        
        Args:
            snapshot: Current price snapshot
            min_abs: Minimum absolute drop threshold
            min_pct: Minimum percentage drop threshold (0.08 = 8%)
        
        Returns:
            PriceEvent if drop detected, None otherwise
        """
        last_price = self.storage.get_last_price(snapshot.product_id)
        if last_price is None:
            # No previous price to compare
            return None
        
        current_price = snapshot.price
        abs_drop = last_price - current_price
        pct_drop = abs_drop / last_price if last_price > 0 else 0
        
        # Check if both thresholds are met
        if abs_drop >= min_abs and pct_drop >= min_pct:
            # Check if we already alerted for this price recently
            if self.storage.check_recent_alert(snapshot.product_id, current_price):
                return None
            
            # Create price drop event
            reason = f"last {last_price:.2f} → {current_price:.2f} (-{pct_drop*100:.1f}%)"
            
            return PriceEvent(
                product_id=snapshot.product_id,
                retailer_id=snapshot.retailer_id,
                event_type="drop",
                old_price=last_price,
                new_price=current_price,
                pct_change=pct_drop,
                reason=reason
            )
        
        return None
    
    def process_snapshot(self, snapshot: OfferSnapshot, min_abs: float = 20, min_pct: float = 0.08) -> Optional[PriceEvent]:
        """Process a snapshot: save it and check for drops.
        
        Returns:
            PriceEvent if drop detected, None otherwise
        """
        # Save the snapshot first
        self.storage.save_snapshot(snapshot)
        
        # Check for price drop
        drop_event = self.detect_drop(snapshot, min_abs, min_pct)
        
        if drop_event:
            # Save the alert
            self.storage.save_alert(drop_event)
            
            # Send email notification if configured
            if self.email_agent and self.email_recipients:
                try:
                    self.email_agent.send_price_alert(
                        recipients=self.email_recipients,
                        product_id=snapshot.product_id,
                        old_price=drop_event.old_price,
                        new_price=drop_event.new_price,
                        retailer=snapshot.retailer_id,
                        url=snapshot.url
                    )
                except Exception as e:
                    print(f"[EMAIL ERROR] Failed to send price alert: {e}")
            
            return drop_event
        
        return None
