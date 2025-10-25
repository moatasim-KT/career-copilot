
import os
import urllib.parse
import json
import time
import random
from typing import List, Dict, Any
import sys

# Placeholder for default API client
default_api = None

class LinkedInScraper:
    def __init__(self, default_api_client=None):
        self.browser_initialized = False
        self.linkedin_email = os.getenv('LINKEDIN_EMAIL')
        self.linkedin_password = os.getenv('LINKEDIN_PASSWORD')
        self.default_api_client = default_api_client if default_api_client else default_api

        if not self.linkedin_email or not self.linkedin_password:
            raise ValueError("LINKEDIN_EMAIL and LINKEDIN_PASSWORD environment variables must be set.")

    async def _initialize_browser(self):
        # The puppeteer tools handle browser instantiation implicitly on the first call.
        # This function primarily manages the logical state within the scraper class.
        if not self.browser_initialized:
            print("Logical browser initialization state set.")
            self.browser_initialized = True

    async def _login(self):
        await self._initialize_browser() # Ensure logical initialization
        print("Navigating to LinkedIn login page and attempting login...")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Navigate to login page
                self.default_api_client.puppeteer_navigate(url='https://www.linkedin.com/login')
                time.sleep(random.uniform(2, 4)) # Human-like delay

                # Fill username and password - common selectors
                self.default_api_client.puppeteer_fill(selector='#session_key', value=self.linkedin_email)
                time.sleep(random.uniform(1, 2))
                self.default_api_client.puppeteer_fill(selector='#session_password', value=self.linkedin_password)
                time.sleep(random.uniform(1, 2))

                # Click sign-in button
                self.default_api_client.puppeteer_click(selector='button[type="submit"]')
                time.sleep(random.uniform(3, 5)) # Wait for navigation

                # Verify successful login by waiting for a common element on the authenticated homepage
                success_check_script = "document.querySelector('input[aria-label=\"Search\"]') !== null"
                max_wait_attempts = 10
                for i in range(max_wait_attempts):
                    result = self.default_api_client.puppeteer_evaluate(script=success_check_script)
                    if result and result.get('output') == True:
                        print("Login successful!")
                        return True
                    print(f"Waiting for login success... attempt {i+1}/{max_wait_attempts}")
                    time.sleep(random.uniform(2, 5))
                
                raise Exception("Login failed: Could not verify successful login after multiple attempts.")

            except Exception as e:
                print(f"Error during LinkedIn login (attempt {attempt + 1}/{max_retries}): {e}")
                self.browser_initialized = False # Reset state if login fails
                if attempt < max_retries - 1:
                    sleep_time = 2 ** attempt * 5 # Exponential backoff
                    print(f"Retrying login in {sleep_time} seconds...")
                    time.sleep(sleep_time)
        raise Exception("Login failed after multiple retries.")


    async def scrape_jobs(self, keywords: str, location: str) -> List[Dict[str, Any]]:
        await self._login() # Ensure logged in
        print(f"Scraping jobs for keywords: {keywords}, location: {location}")

        try:
            # Construct search URL
            params = {'keywords': keywords, 'location': location}
            query = urllib.parse.urlencode(params)
            search_url = f"https://www.linkedin.com/jobs/search?{query}"

            self.default_api_client.puppeteer_navigate(url=search_url)
            time.sleep(random.uniform(3, 5)) # Wait for page to load

            # Scroll down to load more jobs (simulate infinite scroll)
            scroll_script = """
                window.scrollTo(0, document.body.scrollHeight);
            """
            for _ in range(3): # Scroll 3 times to load more jobs
                self.default_api_client.puppeteer_evaluate(script=scroll_script)
                time.sleep(random.uniform(2, 4))

            # Extract job details
            extract_script = """
                const jobs = [];
                const cards = document.querySelectorAll('ul.jobs-search__results-list li');
                for (const card of cards) {
                    const titleElement = card.querySelector('h3.base-search-card__title');
                    const companyElement = card.querySelector('h4.base-search-card__subtitle');
                    const locationElement = card.querySelector('span.job-search-card__location');
                    const linkElement = card.querySelector('a.base-card__full-link');
                    const snippetElement = card.querySelector('p.job-search-card__snippet');

                    jobs.push({
                        title: titleElement ? titleElement.innerText.trim() : '',
                        company: companyElement ? companyElement.innerText.trim() : '',
                        location: locationElement ? locationElement.innerText.trim() : '',
                        link: linkElement ? linkElement.href : '',
                        snippet: snippetElement ? snippetElement.innerText.trim() : ''
                    });
                }
                return jobs;
            """
            
            result = self.default_api_client.puppeteer_evaluate(script=extract_script)
            if result and result.get('output'):
                jobs_data = result.get('output')
                print(f"Found {len(jobs_data)} jobs.")
                return jobs_data
            else:
                print("No jobs found or extraction failed.")
                return []

        except Exception as e:
            print(f"Error during LinkedIn job scraping: {e}")
            raise

    async def scrape_job_description(self, job_url: str) -> str:
        await self._initialize_browser() # Ensure browser is initialized
        print(f"Scraping job description for URL: {job_url}")

        try:
            self.default_api_client.puppeteer_navigate(url=job_url)
            time.sleep(random.uniform(3, 5)) # Wait for page to load

            # Wait for the description element to be visible
            description_selector = 'div.show-more-less-html__markup'
            wait_for_description_script = f"document.querySelector('{description_selector}') !== null"
            
            max_attempts = 10
            for i in range(max_attempts):
                result = self.default_api_client.puppeteer_evaluate(script=wait_for_description_script)
                if result and result.get('output') == True:
                    print("Job description element found.")
                    break
                print(f"Waiting for job description element... attempt {i+1}/{max_attempts}")
                time.sleep(random.uniform(1, 3))
            else:
                raise Exception(f"Job description element '{description_selector}' not found after multiple attempts.")

            # Check for and click "Show more" button if it exists
            show_more_selector = 'button.show-more-less-button'
            check_show_more_script = f"document.querySelector('{show_more_selector}') !== null"
            
            result = self.default_api_client.puppeteer_evaluate(script=check_show_more_script)
            if result and result.get('output') == True:
                print("Clicking 'Show more' button.")
                self.default_api_client.puppeteer_click(selector=show_more_selector)
                time.sleep(random.uniform(1, 3)) # Wait for content to expand

            # Extract the complete job description
            extract_description_script = f"""
                const descElement = document.querySelector('{description_selector}');
                return descElement ? descElement.innerText.trim() : '';
            """
            result = self.default_api_client.puppeteer_evaluate(script=extract_description_script)
            if result and result.get('output'):
                description = result.get('output')
                print("Job description extracted.")
                return description
            else:
                print("Could not extract job description.")
                return ""

        except Exception as e:
            print(f"Error during LinkedIn job description scraping: {e}")
            raise


# Export instance for backward compatibility
try:
    linkedin_scraper = LinkedInScraper()
except Exception:
    # If initialization fails (e.g., missing credentials), create a placeholder
    linkedin_scraper = None
