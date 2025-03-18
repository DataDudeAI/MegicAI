"""
Google Ads Integration
Handles displaying Google AdSense ads and tracking ad impressions/clicks
"""
import os
import uuid
import logging
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("google_ads")

class GoogleAdsManager:
    """Manages Google AdSense integration and tracking"""
    
    def __init__(self, publisher_id: Optional[str] = None, config_file: str = None):
        """Initialize Google Ads Manager"""
        self.publisher_id = publisher_id or os.getenv("GOOGLE_ADSENSE_PUBLISHER_ID", "")
        self.config_file = config_file or os.path.join(os.path.dirname(__file__), "ads_config.json")
        
        # Load ad units configuration
        self.ad_units = self._load_ad_units()
        
        # Track impressions and clicks
        self.impressions_file = os.path.join(os.path.dirname(__file__), "impressions.json")
        self.clicks_file = os.path.join(os.path.dirname(__file__), "clicks.json")
        
        # Create tracking files if they don't exist
        self._initialize_tracking_files()
    
    def _load_ad_units(self) -> Dict[str, Any]:
        """Load ad units configuration"""
        default_ad_units = {
            "sidebar": {
                "ad_unit_id": "1234567890",
                "ad_format": "display",
                "width": 300,
                "height": 250,
                "slot": "sidebar-ad",
                "enabled": True
            },
            "footer": {
                "ad_unit_id": "0987654321",
                "ad_format": "display",
                "width": 728,
                "height": 90,
                "slot": "footer-ad",
                "enabled": True
            },
            "reward_video": {
                "ad_unit_id": "5678901234",
                "ad_format": "video",
                "slot": "reward-video-ad",
                "enabled": True,
                "reward_credits": 10
            }
        }
        
        # Create config file with default values if it doesn't exist
        if not os.path.exists(self.config_file):
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, "w") as f:
                json.dump({"publisher_id": self.publisher_id, "ad_units": default_ad_units}, f, indent=2)
            return default_ad_units
        
        # Load config from file
        try:
            with open(self.config_file, "r") as f:
                config = json.load(f)
                
                # Update publisher ID if it was set in the config file
                if config.get("publisher_id"):
                    self.publisher_id = config["publisher_id"]
                
                return config.get("ad_units", default_ad_units)
        except Exception as e:
            logger.error(f"Error loading ad units config: {e}")
            return default_ad_units
    
    def _initialize_tracking_files(self):
        """Initialize tracking files if they don't exist"""
        os.makedirs(os.path.dirname(self.impressions_file), exist_ok=True)
        
        if not os.path.exists(self.impressions_file):
            with open(self.impressions_file, "w") as f:
                json.dump([], f)
        
        if not os.path.exists(self.clicks_file):
            with open(self.clicks_file, "w") as f:
                json.dump([], f)
    
    def get_ad_code(self, ad_position: str) -> Dict[str, Any]:
        """
        Get HTML/JS code for displaying an ad at the specified position
        Returns both the ad code and metadata about the ad
        """
        if not self.publisher_id:
            logger.warning("No Google AdSense publisher ID configured")
            return {"success": False, "error": "No publisher ID configured"}
        
        # Get ad unit configuration
        ad_unit = self.ad_units.get(ad_position)
        if not ad_unit:
            logger.error(f"Ad position '{ad_position}' not configured")
            return {"success": False, "error": f"Ad position '{ad_position}' not found"}
        
        if not ad_unit.get("enabled", True):
            logger.info(f"Ad unit '{ad_position}' is disabled")
            return {"success": False, "error": "Ad unit is disabled"}
        
        # Generate HTML/JS code for the ad
        ad_format = ad_unit.get("ad_format", "display")
        ad_unit_id = ad_unit.get("ad_unit_id", "")
        ad_slot = ad_unit.get("slot", f"{ad_position}-ad")
        
        if ad_format == "display":
            width = ad_unit.get("width", 300)
            height = ad_unit.get("height", 250)
            
            ad_code = f"""
            <ins class="adsbygoogle"
                 style="display:inline-block;width:{width}px;height:{height}px"
                 data-ad-client="ca-pub-{self.publisher_id}"
                 data-ad-slot="{ad_unit_id}"></ins>
            <script>
                 (adsbygoogle = window.adsbygoogle || []).push({{}});
            </script>
            """
        elif ad_format == "video":
            ad_code = f"""
            <div id="{ad_slot}" class="reward-ad-container">
                <div class="reward-ad-placeholder">
                    <p>Watch a video to earn {ad_unit.get('reward_credits', 5)} credits</p>
                    <button class="watch-ad-btn" onclick="loadRewardAd('{ad_slot}', '{ad_unit_id}', {ad_unit.get('reward_credits', 5)})">Watch Now</button>
                </div>
            </div>
            """
        else:
            logger.error(f"Unsupported ad format: {ad_format}")
            return {"success": False, "error": f"Unsupported ad format: {ad_format}"}
        
        # Generate a unique ID for tracking this ad impression
        impression_id = str(uuid.uuid4())
        
        # Record the impression for tracking
        self._record_impression(impression_id, ad_position, ad_unit_id)
        
        return {
            "success": True,
            "ad_code": ad_code,
            "impression_id": impression_id,
            "ad_position": ad_position,
            "ad_format": ad_format,
            "reward_credits": ad_unit.get("reward_credits", 0) if ad_format == "video" else 0
        }
    
    def _record_impression(self, impression_id: str, ad_position: str, ad_unit_id: str):
        """Record an ad impression for tracking"""
        try:
            # Load existing impressions
            with open(self.impressions_file, "r") as f:
                impressions = json.load(f)
            
            # Add new impression
            impressions.append({
                "id": impression_id,
                "timestamp": datetime.now().isoformat(),
                "ad_position": ad_position,
                "ad_unit_id": ad_unit_id
            })
            
            # Save updated impressions
            with open(self.impressions_file, "w") as f:
                json.dump(impressions, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error recording ad impression: {e}")
    
    def record_ad_click(self, impression_id: str, user_id: Optional[str] = None) -> bool:
        """Record an ad click for tracking"""
        try:
            # Load existing clicks
            with open(self.clicks_file, "r") as f:
                clicks = json.load(f)
            
            # Add new click
            clicks.append({
                "impression_id": impression_id,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            })
            
            # Save updated clicks
            with open(self.clicks_file, "w") as f:
                json.dump(clicks, f, indent=2)
                
            return True
                
        except Exception as e:
            logger.error(f"Error recording ad click: {e}")
            return False
    
    def record_reward_ad_completion(self, impression_id: str, user_id: str) -> Dict[str, Any]:
        """
        Record completion of a reward ad and return reward information
        
        Args:
            impression_id: The unique ID of the ad impression
            user_id: The user ID to reward
            
        Returns:
            Dictionary with reward information and success status
        """
        try:
            # Find the impression to determine the ad unit
            with open(self.impressions_file, "r") as f:
                impressions = json.load(f)
            
            # Find the impression with matching ID
            impression = next((imp for imp in impressions if imp.get("id") == impression_id), None)
            if not impression:
                logger.error(f"Impression ID {impression_id} not found")
                return {
                    "success": False, 
                    "error": "Invalid impression ID"
                }
            
            # Get the ad position from the impression
            ad_position = impression.get("ad_position")
            ad_unit = self.ad_units.get(ad_position)
            
            if not ad_unit:
                logger.error(f"Ad unit for position {ad_position} not found")
                return {
                    "success": False,
                    "error": "Ad unit not found"
                }
            
            # Get the reward amount
            reward_credits = ad_unit.get("reward_credits", 0)
            
            # Record the ad completion (we could store this in a separate file)
            self.record_ad_click(impression_id, user_id)
            
            return {
                "success": True,
                "reward_credits": reward_credits,
                "user_id": user_id,
                "impression_id": impression_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing reward ad completion: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_html_header_code(self) -> str:
        """Get the HTML code to include in the page header for AdSense"""
        if not self.publisher_id:
            return ""
            
        return f"""
        <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-{self.publisher_id}"
             crossorigin="anonymous"></script>
        """
    
    def get_reward_ad_js(self) -> str:
        """Get the JavaScript code for handling reward ads"""
        return """
        <script>
        let rewardAdLoaded = false;
        let adEventListenersAdded = false;
        let currentAdSlot = null;
        let rewardAmount = 0;
        
        function loadRewardAd(adSlot, adUnitId, credits) {
            currentAdSlot = adSlot;
            rewardAmount = credits;
            
            // Show loading indicator
            document.getElementById(adSlot).innerHTML = '<div class="loading-ad">Loading ad, please wait...</div>';
            
            // Create a new ad container
            const adContainer = document.createElement('div');
            adContainer.id = adSlot + '-container';
            document.getElementById(adSlot).appendChild(adContainer);
            
            // Load the Google ad
            const adManager = new google.ads.AdManager(adContainer);
            
            // Set up the ad
            adManager.setAdUnitPath(`/ca-pub-${publisherId}/${adUnitId}`);
            adManager.setAdSize([300, 250]);
            
            // Add event listeners
            if (!adEventListenersAdded) {
                adManager.addEventListener('loaded', onAdLoaded);
                adManager.addEventListener('error', onAdError);
                adManager.addEventListener('completed', onAdCompleted);
                adEventListenersAdded = true;
            }
            
            // Load the ad
            adManager.load();
        }
        
        function onAdLoaded() {
            rewardAdLoaded = true;
            document.getElementById(currentAdSlot).querySelector('.loading-ad').style.display = 'none';
        }
        
        function onAdError(error) {
            document.getElementById(currentAdSlot).innerHTML = 
                `<div class="ad-error">Error loading ad: ${error.message}. Please try again later.</div>`;
        }
        
        function onAdCompleted() {
            // Send a request to the server to record the completion and reward the user
            fetch('/api/ads/reward', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    impression_id: currentImpressionId,
                    completed: true
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Show success message
                    document.getElementById(currentAdSlot).innerHTML = 
                        `<div class="reward-success">Congratulations! You earned ${rewardAmount} credits.</div>`;
                    
                    // Update user credits display if available
                    const creditsDisplay = document.getElementById('user-credits');
                    if (creditsDisplay) {
                        const currentCredits = parseInt(creditsDisplay.innerText, 10);
                        creditsDisplay.innerText = currentCredits + rewardAmount;
                    }
                } else {
                    document.getElementById(currentAdSlot).innerHTML = 
                        `<div class="reward-error">Error: ${data.error}</div>`;
                }
            })
            .catch(error => {
                document.getElementById(currentAdSlot).innerHTML = 
                    `<div class="reward-error">Error: Unable to process reward. Please try again.</div>`;
            });
        }
        </script>
        """

# Example usage
if __name__ == "__main__":
    # Initialize the ads manager
    ads_manager = GoogleAdsManager()
    
    # Get ad code for the sidebar
    sidebar_ad = ads_manager.get_ad_code("sidebar")
    print(f"Sidebar ad success: {sidebar_ad['success']}")
    
    if sidebar_ad['success']:
        print(f"Impression ID: {sidebar_ad['impression_id']}")
        
    # Get the header code for AdSense
    header_code = ads_manager.get_html_header_code()
    print(f"Header code length: {len(header_code)}") 