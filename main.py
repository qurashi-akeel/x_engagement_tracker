import os
import time
import pandas as pd
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from tqdm import tqdm

class TwitterScraper:
    def __init__(self):
        self.setup_driver()
        
    def setup_driver(self):
        """Setup Chrome driver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
    def check_interaction(self, user1, user2):
        """Check if user1 has interacted with user2's tweets"""
        try:
            # Search for interactions
            search_url = f'https://twitter.com/search?q=(from%3A{user1}%20to%3A{user2})%20OR%20(from%3A{user1}%20%40{user2})&src=typed_query&f=live'
            self.driver.get(search_url)
            time.sleep(3)  # Allow page to load
            
            try:
                # Check if there are any results
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="tweet"]')))
                return True
            except TimeoutException:
                return False
                
        except Exception as e:
            print(f"Error checking interaction between {user1} and {user2}: {e}")
            return False
            
    def analyze_engagement(self, usernames):
        """Analyze engagement between users"""
        results = []
        total_comparisons = len(usernames) * (len(usernames) - 1)
        
        with tqdm(total=total_comparisons, desc="Analyzing interactions") as pbar:
            for user1 in usernames:
                metrics = {
                    'Userid': user1,
                    'Username': user1
                }
                
                for user2 in usernames:
                    if user1 != user2:
                        has_engaged = self.check_interaction(user1, user2)
                        metrics[user2] = 'TRUE' if has_engaged else 'FALSE'
                        pbar.update(1)
                        
                metrics['False_count'] = list(metrics.values()).count('FALSE')
                results.append(metrics)
                
        return pd.DataFrame(results)
        
    def close(self):
        """Close the browser"""
        self.driver.quit()

def main():
    print("Twitter Engagement Analyzer")
    print("--------------------------")
    
    # Get usernames from user input
    usernames = []
    while True:
        username = input("Enter a Twitter username (or press Enter to finish): ").strip()
        if not username:
            break
        usernames.append(username)
        
    if not usernames:
        print("No usernames provided. Exiting...")
        return
        
    print("\nAnalyzing engagement...")
    scraper = TwitterScraper()
    
    try:
        # Analyze engagement
        df = scraper.analyze_engagement(usernames)
        
        # Save to CSV
        output_file = "twitter_engagement.csv"
        df.to_csv(output_file, index=False)
        print(f"\nResults saved to {output_file}")
        print("\nEngagement Matrix:")
        print(df)
        
    finally:
        scraper.close()

if __name__ == "__main__":
    main() 