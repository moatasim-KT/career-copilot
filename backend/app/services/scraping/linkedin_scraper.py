"""
LinkedIn job board scraper

Note: LinkedIn has strong anti-scraping measures. This implementation provides
a basic framework but may require additional measures like:
- Proxy rotation
- CAPTCHA solving
- Session management
- More sophisticated user agent rotation

For production use, consider using LinkedIn's official API or specialized
scraping services that handle LinkedIn's anti-bot measures.
"""

import logging
import re
from typing import Dict, List, Optional, Any
from urllib.parse import quote_plus, urljoin

from .base_scraper import BaseScraper, RateLimiter
from app.schemas.job import JobCreate


logger = logging.getLogger(__name__)


class LinkedInScraper(BaseScraper):
    """Scraper for LinkedIn job board"""
    
    def __init__(self, **kwargs):
        # Use more conservative rate limiting for LinkedIn
        rate_limiter = RateLimiter(min_delay=3.0, max_delay=8.0)
        super().__init__(rate_limiter=rate_limiter, **kwargs)
        self.base_url = "https://www.linkedin.com"
        self.name = "LinkedInScraper"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers specifically for LinkedIn"""
        headers = super()._get_headers()
        headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        })
        return headers
    
    def _build_search_url(self, keywords: str, location: str, page: int = 0) -> str:
        """Build LinkedIn search URL"""
        params = []
        
        if keywords:
            params.append(f"keywords={quote_plus(keywords)}")
        
        if location:
            params.append(f"location={quote_plus(location)}")
        
        if page > 0:
            params.append(f"start={page * 25}")  # LinkedIn shows ~25 jobs per page
        
        # Add additional parameters
        params.extend([
            "sortBy=DD",  # Sort by date
            "f_TPR=r604800",  # Jobs from last 7 days
            "f_JT=F",  # Full-time jobs
        ])
        
        query_string = "&".join(params)
        return f"{self.base_url}/jobs/search?{query_string}"
    
    async def search_jobs(
        self, 
        keywords: str, 
        location: str = "", 
        max_results: int = 50
    ) -> List[JobCreate]:
        """Search for jobs on LinkedIn"""
        jobs = []
        page = 0
        max_pages = min(3, (max_results // 25) + 1)  # Be conservative with LinkedIn
        
        logger.info(f"Starting LinkedIn search: '{keywords}' in '{location}'")
        logger.warning("LinkedIn has strong anti-scraping measures. Results may be limited.")
        
        while page < max_pages and len(jobs) < max_results:
            search_url = self._build_search_url(keywords, location, page)
            response = await self._make_request(search_url)
            
            if not response:
                logger.warning(f"Failed to fetch LinkedIn page {page}")
                break
            
            # Check if we're being blocked
            if self._is_blocked(response.text):
                logger.warning("LinkedIn is blocking requests. Stopping scrape.")
                break
            
            soup = self._parse_html(response.text)
            job_elements = self._find_job_elements(soup)
            
            if not job_elements:
                logger.info(f"No more jobs found on LinkedIn page {page}")
                break
            
            page_jobs = []
            for job_element in job_elements:
                if len(jobs) >= max_results:
                    break
                
                job_data = self._parse_job_listing(job_element)
                if job_data:
                    job_obj = self._create_job_object(job_data)
                    if job_obj:
                        jobs.append(job_obj)
                        page_jobs.append(job_obj)
            
            logger.info(f"Found {len(page_jobs)} jobs on LinkedIn page {page}")
            page += 1
            
            # Be extra conservative with LinkedIn
            if len(page_jobs) < 10:
                break
        
        logger.info(f"LinkedIn search completed: {len(jobs)} jobs found")
        return jobs
    
    def _is_blocked(self, html_content: str) -> bool:
        """Check if LinkedIn is blocking our requests"""
        blocked_indicators = [
            "challenge",
            "captcha",
            "blocked",
            "security check",
            "unusual activity",
            "authwall"
        ]
        
        content_lower = html_content.lower()
        return any(indicator in content_lower for indicator in blocked_indicators)
    
    def _find_job_elements(self, soup):
        """Find job listing elements in LinkedIn page"""
        # LinkedIn job selectors (these may change frequently)
        selectors = [
            '.jobs-search__results-list li',
            '.job-result-card',
            '[data-entity-urn*="jobPosting"]',
            '.jobs-search-results__list-item',
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                logger.debug(f"Found {len(elements)} LinkedIn job elements using selector: {selector}")
                return elements
        
        logger.warning("No LinkedIn job elements found with any selector")
        return []
    
    def _parse_job_listing(self, job_element) -> Optional[Dict[str, Any]]:
        """Parse a single LinkedIn job listing"""
        try:
            job_data = {}
            
            # Extract job title
            title_selectors = [
                '.job-result-card__title',
                'h3.job-result-card__title a',
                '.jobs-unified-top-card__job-title a',
                '[data-control-name="job_search_job_result_title"]'
            ]
            
            title = None
            for selector in title_selectors:
                title_elem = job_element.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break
            
            if not title:
                logger.debug("Could not extract LinkedIn job title")
                return None
            
            job_data['title'] = title
            
            # Extract company name
            company_selectors = [
                '.job-result-card__subtitle',
                'h4.job-result-card__subtitle a',
                '.jobs-unified-top-card__company-name a',
                '[data-control-name="job_search_company_name"]'
            ]
            
            company = None
            for selector in company_selectors:
                company_elem = job_element.select_one(selector)
                if company_elem:
                    company = company_elem.get_text(strip=True)
                    break
            
            if not company:
                logger.debug("Could not extract LinkedIn company name")
                return None
            
            job_data['company'] = company
            
            # Extract location
            location_selectors = [
                '.job-result-card__location',
                '.jobs-unified-top-card__bullet',
                '.job-result-card__meta .job-result-card__location'
            ]
            
            for selector in location_selectors:
                location_elem = job_element.select_one(selector)
                if location_elem:
                    job_data['location'] = location_elem.get_text(strip=True)
                    break
            
            # Extract job URL
            url_selectors = [
                '.job-result-card__title a',
                'h3 a',
                '[data-control-name="job_search_job_result_title"]'
            ]
            
            for selector in url_selectors:
                url_elem = job_element.select_one(selector)
                if url_elem and url_elem.get('href'):
                    relative_url = url_elem['href']
                    job_data['url'] = urljoin(self.base_url, relative_url)
                    break
            
            # Extract job snippet/description
            snippet_selectors = [
                '.job-result-card__snippet',
                '.jobs-unified-top-card__job-insight',
                '.job-result-card__summary'
            ]
            
            for selector in snippet_selectors:
                snippet_elem = job_element.select_one(selector)
                if snippet_elem:
                    job_data['description'] = snippet_elem.get_text(strip=True)
                    break
            
            # Extract additional metadata
            job_data['tags'] = self._extract_tags(job_element)
            job_data['requirements'] = self._extract_requirements(job_data.get('description', ''))
            
            # LinkedIn-specific metadata
            self._extract_linkedin_metadata(job_element, job_data)
            
            return job_data
            
        except Exception as e:
            logger.error(f"Error parsing LinkedIn job listing: {e}")
            return None
    
    def _extract_linkedin_metadata(self, job_element, job_data: Dict[str, Any]):
        """Extract LinkedIn-specific metadata"""
        # Extract posting time
        time_selectors = [
            '.job-result-card__listdate',
            '.jobs-unified-top-card__posted-date',
            'time'
        ]
        
        for selector in time_selectors:
            time_elem = job_element.select_one(selector)
            if time_elem:
                job_data['posted_time'] = time_elem.get_text(strip=True)
                break
        
        # Extract applicant count if available
        applicant_selectors = [
            '.job-result-card__meta-item',
            '.jobs-unified-top-card__applicant-count'
        ]
        
        for selector in applicant_selectors:
            applicant_elem = job_element.select_one(selector)
            if applicant_elem:
                text = applicant_elem.get_text(strip=True).lower()
                if 'applicant' in text:
                    job_data['applicant_count'] = text
                    break
    
    def _extract_tags(self, job_element) -> List[str]:
        """Extract tags/attributes from LinkedIn job listing"""
        tags = []
        
        # Look for remote work indicators
        text_content = job_element.get_text().lower()
        if any(keyword in text_content for keyword in ['remote', 'work from home', 'hybrid']):
            tags.append('remote')
        
        # Look for seniority level
        if any(keyword in text_content for keyword in ['senior', 'sr.', 'lead']):
            tags.append('senior')
        elif any(keyword in text_content for keyword in ['junior', 'jr.', 'entry']):
            tags.append('junior')
        elif any(keyword in text_content for keyword in ['principal', 'staff', 'architect']):
            tags.append('principal')
        
        # Look for job type
        if any(keyword in text_content for keyword in ['full-time', 'full time']):
            tags.append('full-time')
        elif any(keyword in text_content for keyword in ['contract', 'contractor']):
            tags.append('contract')
        
        return tags
    
    def _extract_requirements(self, description: str) -> Dict[str, Any]:
        """Extract requirements from LinkedIn job description"""
        if not description:
            return {}
        
        requirements = {}
        description_lower = description.lower()
        
        # Extract experience level
        if any(keyword in description_lower for keyword in ['entry level', 'junior', '0-2 years', 'new grad']):
            requirements['experience_level'] = 'entry'
        elif any(keyword in description_lower for keyword in ['senior', '5+ years', '7+ years', 'experienced']):
            requirements['experience_level'] = 'senior'
        elif any(keyword in description_lower for keyword in ['mid level', '3-5 years', '2-4 years']):
            requirements['experience_level'] = 'mid'
        elif any(keyword in description_lower for keyword in ['principal', 'staff', '10+ years']):
            requirements['experience_level'] = 'principal'
        
        # Extract education requirements
        if any(keyword in description_lower for keyword in ['bachelor', "bachelor's", 'bs', 'ba']):
            requirements['education'] = 'bachelor'
        elif any(keyword in description_lower for keyword in ['master', "master's", 'ms', 'ma', 'mba']):
            requirements['education'] = 'master'
        elif any(keyword in description_lower for keyword in ['phd', 'ph.d', 'doctorate']):
            requirements['education'] = 'phd'
        
        # Extract common skills
        tech_skills = [
            'python', 'javascript', 'java', 'react', 'angular', 'vue', 'node.js', 
            'sql', 'postgresql', 'mysql', 'mongodb', 'aws', 'azure', 'gcp',
            'docker', 'kubernetes', 'git', 'jenkins', 'terraform',
            'machine learning', 'data science', 'tensorflow', 'pytorch',
            'rest api', 'graphql', 'microservices', 'agile', 'scrum'
        ]
        
        found_skills = []
        for skill in tech_skills:
            if skill in description_lower:
                found_skills.append(skill)
        
        if found_skills:
            requirements['skills'] = found_skills
        
        return requirements