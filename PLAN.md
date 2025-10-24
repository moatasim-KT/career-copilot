### Plan for Robust LinkedIn Web Scraping

**Objective:** To enhance the existing LinkedIn web scraping logic to be more robust and reliable, addressing limitations such as JavaScript rendering, anti-scraping measures, and authentication, without relying on LinkedIn's official API.

**Current Limitations of the Provided Code:**
1.  **Static HTML Parsing:** `requests` and `BeautifulSoup` only process the initial HTML, missing content rendered by JavaScript.
2.  **Anti-Scraping Measures:** LinkedIn actively blocks simple, repeated requests, leading to unreliable data fetching.
3.  **Authentication:** The current script does not handle user authentication, which is often required for comprehensive job search results.
4.  **Brittle Selectors:** HTML element selectors are prone to breaking with website structure changes.
5.  **Rate Limiting:** Lack of sophisticated handling for rate limits can lead to IP bans.

**Proposed Solution:**
Transition from `requests` and `BeautifulSoup` to a browser automation approach using Puppeteer (via the provided `puppeteer` tools) to simulate a real user browsing experience. This will allow for JavaScript execution, dynamic content loading, and more resilient interaction with the LinkedIn website.

**Detailed Plan:**

**Step 1: Setup and Project Structure**
*   **1.1 Create `backend/app/services/linkedin_scraper.py`:** This new module will encapsulate all LinkedIn scraping logic using Puppeteer.
*   **1.2 Update `recommend_bp`:** Modify the existing `recommend_bp` blueprint to import and utilize functions from `linkedin_scraper.py`.
*   **1.3 Environment Variables:** Document and require `LINKEDIN_EMAIL` and `LINKEDIN_PASSWORD` environment variables for authentication. These should be loaded securely (e.g., from `.env.development`).

**Step 2: Implement Puppeteer-based Browser Automation**
*   **2.1 Initialize Browser:** Create a function in `linkedin_scraper.py` to launch a headless browser instance using `puppeteer_navigate`.
*   **2.2 LinkedIn Authentication:**
    *   Navigate to the LinkedIn login page.
    *   Use `puppeteer_fill` to input `LINKEDIN_EMAIL` and `LINKEDIN_PASSWORD` into the respective fields.
    *   Use `puppeteer_click` to submit the login form.
    *   Implement a wait mechanism (e.g., `puppeteer_evaluate` with a `waitForSelector`) to ensure successful login and page load.
*   **2.3 Job Search Page Scraping:**
    *   Construct the LinkedIn job search URL using keywords and location.
    *   Navigate the browser to this search URL.
    *   Implement a scrolling mechanism using `puppeteer_evaluate` to scroll down the page multiple times, allowing more job listings to load (infinite scroll handling).
    *   Use `puppeteer_evaluate` to execute JavaScript within the browser context to extract job details (title, company, location, link, snippet) from the dynamically loaded content. This JavaScript will use robust DOM selectors.
    *   Return the extracted job data.
*   **2.4 Individual Job Page Scraping (for detailed descriptions):**
    *   Create a function to navigate to a specific job URL.
    *   Wait for the job description element to be visible.
    *   Implement logic to click "Show more" buttons if they exist to reveal the full description.
    *   Use `puppeteer_evaluate` to extract the complete job description text.
    *   Return the detailed description.

**Step 3: Integrate with Existing Flask Application**
*   **3.1 Modify `recommendations` route:**
    *   Replace the `requests` and `BeautifulSoup` logic with calls to the new Puppeteer-based job search function in `linkedin_scraper.py`.
    *   Ensure proper error handling and fallback to cached data if Puppeteer scraping fails.
*   **3.2 Modify `add_recommended_job` route:**
    *   Update the logic to use the new Puppeteer-based individual job page scraping function when a detailed description is needed.

**Step 4: Error Handling and Robustness**
*   **4.1 Comprehensive Error Handling:** Implement `try-except` blocks around all Puppeteer operations to gracefully handle network issues, selector failures, and LinkedIn's anti-scraping measures.
*   **4.2 Retry Mechanism:** Implement a simple retry mechanism for failed Puppeteer operations with exponential backoff.
*   **4.3 User-Agent Rotation (Optional but Recommended):** Consider adding a list of User-Agents to rotate through to further mimic diverse user behavior. (This might be an enhancement for a later stage).
*   **4.4 Delays:** Introduce random delays between Puppeteer actions to avoid detection.

**Step 5: Testing**
*   **5.1 Unit Tests:** Write unit tests for the functions in `linkedin_scraper.py` to ensure they correctly interact with Puppeteer and extract data. (Mock Puppeteer interactions for faster tests).
*   **5.2 Integration Tests:** Create integration tests that simulate the full flow from the Flask route to the Puppeteer-based scraping, ensuring the data is correctly retrieved and processed.

**Step 6: Documentation and Cleanup**
*   **6.1 Update `README.md`:** Add instructions for setting up LinkedIn credentials as environment variables.
*   **6.2 Code Cleanup:** Remove the old `requests` and `BeautifulSoup` logic once the new system is fully functional.

**Success Criteria:**
*   The `recommendations` route successfully fetches job listings from LinkedIn using the new Puppeteer-based scraper.
*   The `add_recommended_job` route successfully fetches detailed job descriptions using the new Puppeteer-based scraper.
*   The scraping process is more resilient to LinkedIn's anti-scraping measures and JavaScript-rendered content.
*   Authentication is handled securely via environment variables.