### To-Do List for Robust LinkedIn Web Scraping

This list is derived from the `PLAN.md` for implementing a robust LinkedIn web scraping solution.

*   **Step 1: Setup and Project Structure**
    *   [backend] Create `backend/app/services/linkedin_scraper.py` to house Puppeteer-based scraping logic.
    *   [backend] Modify `backend/app/api/recommend.py` (or equivalent) to import and use functions from `linkedin_scraper.py`.
    *   [documentation] Update `README.md` to include instructions for setting `LINKEDIN_EMAIL` and `LINKEDIN_PASSWORD` environment variables.

*   **Step 2: Implement Puppeteer-based Browser Automation**
    *   [backend] Implement a function in `linkedin_scraper.py` to initialize a headless browser instance using `puppeteer_navigate`.
    *   [backend] Implement LinkedIn authentication logic in `linkedin_scraper.py`:
        *   Navigate to LinkedIn login page.
        *   Use `puppeteer_fill` for email and password.
        *   Use `puppeteer_click` for login button.
        *   Use `puppeteer_evaluate` with `waitForSelector` for post-login page load.
    *   [backend] Implement job search page scraping in `linkedin_scraper.py`:
        *   Construct LinkedIn job search URL.
        *   Navigate browser to search URL.
        *   Implement scrolling mechanism using `puppeteer_evaluate` to load more jobs.
        *   Use `puppeteer_evaluate` to extract job details (title, company, location, link, snippet) using robust DOM selectors.
    *   [backend] Implement individual job page scraping in `linkedin_scraper.py`:
        *   Create a function to navigate to a specific job URL.
        *   Wait for job description element visibility.
        *   Implement logic to click "Show more" buttons if present.
        *   Use `puppeteer_evaluate` to extract the complete job description text.

*   **Step 3: Integrate with Existing Flask Application**
    *   [backend] Modify the `recommendations` route in `backend/app/api/recommend.py` to use the new Puppeteer-based job search function.
    *   [backend] Modify the `add_recommended_job` route in `backend/app/api/recommend.py` to use the new Puppeteer-based individual job page scraping function.

*   **Step 4: Error Handling and Robustness**
    *   [backend] Implement comprehensive `try-except` blocks around all Puppeteer operations in `linkedin_scraper.py`.
    *   [backend] Implement a simple retry mechanism with exponential backoff for failed Puppeteer operations.
    *   [backend] Introduce random delays between Puppeteer actions.

*   **Step 5: Testing**
    *   [test] Write unit tests for functions in `linkedin_scraper.py` (mocking Puppeteer interactions).
    *   [test] Create integration tests for the full Flask route to Puppeteer scraping flow.

*   **Step 6: Documentation and Cleanup**
    *   [documentation] Update `README.md` with instructions for setting up LinkedIn credentials.
    *   [backend] Remove old `requests` and `BeautifulSoup` logic from `backend/app/api/recommend.py`.

**Parallelizable Tasks:**
*   Step 1.1, 1.3 (can be started early)
*   Step 2.1, 2.2 (can be developed independently of scraping logic)
*   Step 2.3, 2.4 (can be developed somewhat independently, but rely on 2.1 and 2.2)
*   Step 4.1, 4.2, 4.3, 4.4 (can be integrated throughout Step 2 and 3 development)
*   Step 5.1, 5.2 (can be started once core scraping logic is in place)