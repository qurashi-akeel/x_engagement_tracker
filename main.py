import time
import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException

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
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
        
    def login(self):
        """Login to Twitter"""
        try:
            self.driver.get("https://twitter.com/i/flow/login")
            time.sleep(3)
            
            # Enter username
            username_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]'))
            )
            username_input.send_keys(self.username)
            
            self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))
            ).click()
            time.sleep(2)
            
            # Check for verification
            try:
                verify_input = self.driver.find_element(By.CSS_SELECTOR, 'input[data-testid="ocfEnterTextTextInput"]')
                print("Verification required! Please enter the verification code in the browser window...")
                input("Press Enter after completing verification in the browser...")
            except NoSuchElementException:
                pass
                
            # Enter password
            password_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="password"]'))
            )
            password_input.send_keys(self.password)
            
            self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Log in']"))
            ).click()
            time.sleep(3)
            
            # Verify login
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="SideNav_NewTweet_Button"]')))
            print("Successfully logged in!")
                
        except Exception as e:
            print(f"Error logging in: {e}")
            raise Exception("Failed to login to Twitter")
            
    def get_all_comments(self, post_url):
        """Get all comments from a post"""
        self.driver.get(post_url)
        time.sleep(3)
        
        comments_data = {}
        last_height = 0
        processed_comments = set()
        scroll_count = 0
        
        print("Scrolling and collecting comments...")
        
        while True:
            scroll_count += 1
            print(f"Scroll #{scroll_count}")
            
            try:
                self.wait.until(EC.presence_of_element_located((
                    By.CSS_SELECTOR, 
                    'article[data-testid="tweet"]'
                )))
                
                comment_articles = self.driver.find_elements(
                    By.CSS_SELECTOR, 
                    'article[data-testid="tweet"]'
                )
                
            except Exception as e:
                print(f"Error finding comments on scroll #{scroll_count}: {str(e)}")
                comment_articles = []

            # Process new comments
            for article in comment_articles:
                try:
                    comment_id = article.get_attribute('aria-labelledby')
                    if comment_id in processed_comments:
                        continue
                    
                    processed_comments.add(comment_id)
                    
                    username_element = article.find_element(
                        By.CSS_SELECTOR, 
                        'div[data-testid="User-Name"] span'
                    )
                    username = username_element.text.replace('@', '').strip()
                    
                    time_element = article.find_element(By.CSS_SELECTOR, 'time')
                    timestamp = time_element.get_attribute('datetime')
                    
                    if timestamp:
                        try:
                            dt = pd.to_datetime(timestamp)
                            formatted_time = dt.strftime('%H:%M')
                        except:
                            formatted_time = timestamp
                    
                    if username and timestamp:
                        comments_data[username] = formatted_time
                        print(f"Found comment by: {username} at {formatted_time}")
                        
                except Exception as e:
                    continue
            
            # Scroll down
            try:
                current_height = self.driver.execute_script("return window.pageYOffset;")
                window_height = self.driver.execute_script("return window.innerHeight;")
                scroll_height = current_height + (window_height * 0.8)
                
                self.driver.execute_script(f"window.scrollTo(0, {scroll_height});")
                time.sleep(2)
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                
                if new_height == last_height:
                    time.sleep(3)
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)
                    final_height = self.driver.execute_script("return document.body.scrollHeight")
                    
                    if final_height == new_height:
                        break
                        
                last_height = new_height
                
            except Exception as e:
                print(f"Error during scrolling: {str(e)}")
                break
        
        print(f"\nFound {len(comments_data)} unique comments")
        
        # Create and save DataFrame with only the found comments
        comments_df = pd.DataFrame([
            {'Username': username, 'Comment_time': time}
            for username, time in comments_data.items()
        ])
        
        if not comments_df.empty:
            comments_df.sort_values('Comment_time', inplace=True)
            comments_df.to_csv('twitter_comments.csv', index=False)
            print("\nComment Analysis:")
            print(comments_df)
        else:
            print("\nNo comments found")
        
        return comments_data
            
    def close(self):
        self.driver.quit()

def load_data(data_file='data.json'):
    try:
        with open(data_file, 'r') as f:
            data = json.load(f)
        return data.get('post', ''), data.get('users', [])
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading data: {e}")
        return '', []

def load_credentials(env_file='.env'):
    try:
        with open(env_file, 'r') as f:
            lines = f.readlines()
            return (
                next((line.split('=')[1].strip() for line in lines if line.startswith('USERNAME=')), ''),
                next((line.split('=')[1].strip() for line in lines if line.startswith('PASSWORD=')), '')
            )
    except FileNotFoundError:
        print(f"Error: {env_file} not found!")
        return '', ''

def main():
    print("Twitter Comment Analyzer")
    print("----------------------")
    
    post_url, _ = load_data()
    username, password = load_credentials()
    
    if not all([post_url, username, password]):
        print("Error: Missing required configuration")
        return
        
    print(f"\nAnalyzing comments for post: {post_url}")
    
    try:
        scraper = TwitterScraper(username, password)
        scraper.get_all_comments(post_url)
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'scraper' in locals():
            scraper.close()

if __name__ == "__main__":
    main() 