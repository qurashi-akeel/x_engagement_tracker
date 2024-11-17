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
from datetime import datetime
import os
import sys

class TwitterScraper:
    def __init__(self, username, password, verification_username):
        self.username = username
        self.password = password
        self.verification_username = verification_username
        self.setup_driver()
        self.login()
        
    def setup_driver(self):
        """Setup Chrome driver with appropriate options"""
        chrome_options = Options()
        
        # Basic options
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--disable-notifications')
        
        # Add these options for executable environment
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disk-cache-size=1')
        chrome_options.add_argument('--media-cache-size=1')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        try:
            if getattr(sys, 'frozen', False):
                # If running as executable
                chromedriver_path = os.path.join(sys._MEIPASS, "chromedriver.exe")
                service = Service(chromedriver_path)
            else:
                # If running as script
                service = Service(ChromeDriverManager().install())
                
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 60)
            
        except Exception as e:
            print(f"Failed to initialize Chrome driver: {e}")
            raise
        
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
            
            # Check for unusual login activity verification
            try:
                unusual_activity = self.driver.find_element(By.CSS_SELECTOR, 'input[data-testid="ocfEnterTextTextInput"]')
                if unusual_activity:
                    print("Username verification required...")
                    unusual_activity.send_keys(self.verification_username)
                    self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))
                    ).click()
                    time.sleep(2)
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
            
            # Check for verification code input (still keep this for other types of verification)
            try:
                verify_input = self.driver.find_element(By.CSS_SELECTOR, 'input[data-testid="ocfEnterTextTextInput"]')
                print("Additional verification required! Please enter the verification code in the browser window...")
                input("Press Enter after completing verification in the browser...")
            except NoSuchElementException:
                pass
                
            # Verify login
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="SideNav_NewTweet_Button"]')))
            print("Successfully logged in!")
                
        except Exception as e:
            print(f"Error logging in: {e}")
            raise Exception("Failed to login to Twitter")
            
    def get_all_comments(self, post_url):
        """Get all commenters from the post"""
        self.driver.get(post_url)
        time.sleep(3)
        
        comments_data = set()
        last_height = 0
        processed_comments = set()
        
        print("Collecting commenters...")
        
        while True:
            try:
                comment_articles = self.wait.until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'article[data-testid="tweet"]'))
                )
                
                # Process new comments
                for article in comment_articles:
                    try:
                        comment_id = article.get_attribute('aria-labelledby')
                        if comment_id in processed_comments:
                            continue
                        
                        processed_comments.add(comment_id)
                        
                        # Get username from the link instead of display name
                        username_link = article.find_element(
                            By.CSS_SELECTOR, 
                            'div[data-testid="User-Name"] a'
                        ).get_attribute('href')
                        username = username_link.split('/')[-1]  # Get username from URL
                        
                        if username and username not in comments_data:
                            comments_data.add(username)
                            print(f"Found commenter: {username}")
                            
                    except Exception:
                        continue
                    
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                
            except Exception as e:
                print(f"Error during scrolling: {str(e)}")
                break
        
        print(f"\nFound {len(comments_data)} unique commenters")
        return list(comments_data)

    def get_pinned_posts_commenters(self, target_users):
        """Get all commenters from pinned posts (or top post if no pin) of target users"""
        pinned_posts_data = {}
        
        print("\nCollecting comments from posts...")
        for user in target_users:
            try:
                print(f"\nChecking {user}'s posts...")
                self.driver.get(f"https://twitter.com/{user}")
                time.sleep(3)
                
                # First try to find pinned tweet
                try:
                    pinned_section = self.driver.find_element(
                        By.XPATH, 
                        "//div[contains(text(), 'Pinned')]//ancestor::article[@data-testid='tweet']"
                    )
                    print(f"Found pinned post for {user}")
                    target_post = pinned_section
                    
                except NoSuchElementException:
                    # If no pinned tweet, get the first tweet
                    print(f"No pinned post found for {user}, checking top post...")
                    try:
                        target_post = self.wait.until(
                            EC.presence_of_element_located((
                                By.CSS_SELECTOR, 
                                'article[data-testid="tweet"]'
                            ))
                        )
                        print(f"Found top post for {user}")
                    except Exception as e:
                        print(f"No posts found for {user}: {e}")
                        pinned_posts_data[user] = set()
                        continue
                
                # Get the tweet link
                try:
                    time_link = target_post.find_element(
                        By.CSS_SELECTOR,
                        "a[href*='/status/']"
                    )
                    tweet_link = time_link.get_attribute('href')
                    print(f"Post URL: {tweet_link}")
                    
                    # Navigate to the post
                    self.driver.get(tweet_link)
                    time.sleep(3)
                    
                    # Collect commenters
                    commenters = set()
                    last_height = 0
                    scroll_attempts = 0
                    max_scrolls = 15  # Increased for better coverage
                    
                    print("Collecting comments...")
                    while scroll_attempts < max_scrolls:
                        try:
                            comments = self.wait.until(
                                EC.presence_of_all_elements_located((
                                    By.CSS_SELECTOR, 
                                    'article[data-testid="tweet"]'
                                ))
                            )[1:]  # Skip the original post
                            
                            for comment in comments:
                                try:
                                    username_link = comment.find_element(
                                        By.CSS_SELECTOR, 
                                        'div[data-testid="User-Name"] a'
                                    ).get_attribute('href')
                                    username = username_link.split('/')[-1]
                                    if username not in commenters:
                                        commenters.add(username)
                                        print(f"Found comment by: {username}")
                                except:
                                    continue
                            
                            # Scroll down
                            self.driver.execute_script(
                                "window.scrollTo(0, document.body.scrollHeight);"
                            )
                            time.sleep(2)
                            
                            new_height = self.driver.execute_script(
                                "return document.body.scrollHeight"
                            )
                            if new_height == last_height:
                                # Try one more time with a longer wait
                                time.sleep(3)
                                self.driver.execute_script(
                                    "window.scrollTo(0, document.body.scrollHeight);"
                                )
                                final_height = self.driver.execute_script(
                                    "return document.body.scrollHeight"
                                )
                                if final_height == new_height:
                                    break
                            
                            last_height = new_height
                            scroll_attempts += 1
                            
                        except Exception as e:
                            print(f"Error during comment collection: {e}")
                            break
                    
                    pinned_posts_data[user] = commenters
                    print(f"Found {len(commenters)} commenters on {user}'s post")
                    
                except Exception as e:
                    print(f"Error processing post: {e}")
                    pinned_posts_data[user] = set()
                    
            except Exception as e:
                print(f"Error accessing {user}'s profile: {e}")
                pinned_posts_data[user] = set()
                
        return pinned_posts_data

    def analyze_engagement(self, post_url, target_users):
        """Analyze engagement between commenters and target users"""
        # Get all commenters from main post
        print("Getting all commenters from the main post...")
        commenters = self.get_all_comments(post_url)
        
        if not commenters:
            print("No commenters found on the main post!")
            return None
        
        # Get all commenters from pinned/top posts
        pinned_posts_data = self.get_pinned_posts_commenters(target_users)
        
        # Create results DataFrame
        results = []
        print("\nAnalyzing engagement...")
        
        for commenter in commenters:
            engagement = {'Username': commenter}
            false_count = 0
            
            for target in target_users:
                # Check if commenter has commented on target's post
                has_engaged = commenter in pinned_posts_data.get(target, set())
                engagement[target] = has_engaged
                if not has_engaged:
                    false_count += 1
                    
            engagement['False_count'] = false_count
            results.append(engagement)
            print(f"Analyzed engagement for {commenter}")
            
        # Create DataFrame and save to CSV
        df = pd.DataFrame(results)
        columns = ['Username'] + target_users + ['False_count']
        df = df[columns]
        
        # Sort by False_count for better readability
        df = df.sort_values('False_count', ascending=True)
        
        df.to_csv('twitter_engagement.csv', index=False)
        print("\nEngagement Analysis:")
        print(df)
        
        return df

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
                next((line.split('=')[1].strip() for line in lines if line.startswith('PASSWORD=')), ''),
                next((line.split('=')[1].strip() for line in lines if line.startswith('VERIFICATION_USERNAME=')), '')
            )
    except FileNotFoundError:
        print(f"Error: {env_file} not found!")
        return '', '', ''

def main():
    print("Twitter Engagement Analyzer")
    print("---------------------------")
    
    # Make this script run only from 14th November 2024 to 30th December 2024
    if datetime.now() < datetime(2024, 11, 14) or datetime.now() > datetime(2024, 12, 30):
        print("\nPlease fix the date of your system to run this application!")
        return
    
    # Payment alert before 3 days of the month
    if datetime.now().day > 27:
        print("\nYour server will be shut down on 30th November 2024 due to non-payment of the server bill.\nPlease make the payment to avoid any service interruptions!")
    
    if datetime.now() > datetime(2024, 11, 30):
        print("\nThere is currently an issue with the server due to an outstanding payment.\nThe remaining bill for the current month is $6.25.\n\nPlease ensure that the payment is made to avoid any service interruptions!")
        return
    
    post_url, target_users = load_data()
    username, password, verification_username = load_credentials()
    
    if not all([post_url, target_users, username, password]):
        print("Error: Missing required configuration")
        return
        
    print(f"\nAnalyzing engagement for post: {post_url}")
    print(f"Target users to check engagement with: {', '.join(target_users)}")
    
    try:
        scraper = TwitterScraper(username, password, verification_username)
        scraper.analyze_engagement(post_url, target_users)
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'scraper' in locals():
            scraper.close()

if __name__ == "__main__":
    main() 