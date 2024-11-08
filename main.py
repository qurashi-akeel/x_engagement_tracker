import time
import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from tqdm import tqdm

class TwitterScraper:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.setup_driver()
        self.login()
        
    def setup_driver(self):
        """Setup Chrome driver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
        
    def login(self):
        """Login to Twitter"""
        try:
            print("Logging into Twitter...")
            self.driver.get("https://twitter.com/i/flow/login")
            time.sleep(5)
            
            # Enter username
            print("Entering username...")
            username_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]'))
            )
            username_input.clear()
            username_input.send_keys(self.username)
            
            # Click the Next button
            next_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))
            )
            next_button.click()
            time.sleep(3)
            
            # Check if verification is needed
            try:
                verify_input = self.driver.find_element(By.CSS_SELECTOR, 'input[data-testid="ocfEnterTextTextInput"]')
                print("Verification required! Please enter the verification code in the browser window...")
                input("Press Enter after completing verification in the browser...")
            except NoSuchElementException:
                pass
                
            # Enter password
            print("Entering password...")
            password_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="password"]'))
            )
            password_input.clear()
            password_input.send_keys(self.password)
            
            # Click the Login button
            login_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Log in']"))
            )
            login_button.click()
            time.sleep(5)
            
            # Verify login success
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="SideNav_NewTweet_Button"]')))
                print("Successfully logged in!")
            except TimeoutException:
                raise Exception("Could not verify successful login")
                
        except Exception as e:
            print(f"Error logging in: {e}")
            print("Please check if credentials are correct and try again")
            raise Exception("Failed to login to Twitter")
        
    def check_interaction(self, user1, user2):
        """Check if user1 has interacted with user2's tweets"""
        search_url = f'https://twitter.com/search?q=(from%3A{user1}%20to%3A{user2})%20OR%20(from%3A{user1}%20%40{user2})&src=typed_query&f=live'
        
        try:
            self.driver.get(search_url)
            time.sleep(3)
            
            try:
                # First check if "No results" message exists
                no_results = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="empty_state_header_text"]')
                if no_results:
                    return False
                
                # Look for any tweet on the page
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="tweet"]')))
                return True
            except TimeoutException:
                return False
                
        except Exception as e:
            print(f"Error checking interaction between {user1} and {user2}: {e}")
            return False
            
    def analyze_engagement(self, usernames, target_accounts):
        """Analyze engagement between input users and target accounts"""
        results = []
        total_checks = len(usernames) * len(target_accounts)
        
        with tqdm(total=total_checks, desc="Analyzing interactions") as pbar:
            for username in usernames:
                metrics = {
                    'Username': username
                }
                
                for target in target_accounts:
                    has_engaged = self.check_interaction(username, target)
                    metrics[target] = 'TRUE' if has_engaged else 'FALSE'
                    pbar.update(1)
                    
                false_count = sum(1 for target in target_accounts if metrics[target] == 'FALSE')
                metrics['False_count'] = false_count
                results.append(metrics)
                
        return pd.DataFrame(results)
        
    def close(self):
        """Close the browser"""
        self.driver.quit()

def load_config(config_file='config.json'):
    """Load configuration from JSON file"""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        return (
            config.get('username', ''),
            config.get('password', ''),
            config.get('target_accounts', []),
            config.get('usernames_to_check', [])
        )
    except FileNotFoundError:
        print(f"Error: {config_file} not found!")
        return '', '', [], []
    except json.JSONDecodeError:
        print(f"Error: {config_file} is not valid JSON!")
        return '', '', [], []

def main():
    print("Twitter Engagement Analyzer")
    print("--------------------------")
    
    # Load configuration
    username, password, target_accounts, usernames = load_config()
    
    if not username or not password:
        print("Error: Twitter credentials not found in config.json")
        return
        
    if not target_accounts or not usernames:
        print("Error: Target accounts or usernames not found in config.json")
        return
        
    print("\nTarget accounts that will be analyzed:", ", ".join(target_accounts))
    print(f"Number of usernames to check: {len(usernames)}")
    
    print("\nInitializing...")
    try:
        scraper = TwitterScraper(username, password)
        
        # Analyze engagement
        df = scraper.analyze_engagement(usernames, target_accounts)
        
        # Reorder columns to match the image format
        columns = ['Username'] + target_accounts + ['False_count']
        df = df[columns]
        
        # Save to CSV
        output_file = "twitter_engagement.csv"
        df.to_csv(output_file, index=False)
        print(f"\nResults saved to {output_file}")
        print("\nEngagement Matrix:")
        print(df)
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'scraper' in locals():
            scraper.close()

if __name__ == "__main__":
    main() 