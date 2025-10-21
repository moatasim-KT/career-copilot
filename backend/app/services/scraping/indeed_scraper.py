"""
Indeed job board scraper
"""

import logging
import re
from typing import Dict, List, Optional, Any
from urllib.parse import quote_plus, urljoin

from .base_scraper import BaseScraper
from app.schemas.job import JobCreate


logger = logging.getLogger(__name__)


class IndeedScraper(BaseScraper):
    """Scraper for Indeed job board"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_url = "https://www.indeed.com"
        self.name = "IndeedScraper"
    
    def _build_search_url(self, keywords: str, location: str, page: int = 0) -> str:
        """Build Indeed search URL"""
        params = []
        
        if keywords:
            params.append(f"q={quote_plus(keywords)}")
        
        if location:
            params.append(f"l={quote_plus(location)}")
        
        if page > 0:
            params.append(f"start={page * 10}")
        
        # Add additional parameters for better results
        params.extend([
            "sort=date",  # Sort by date
            "fromage=7",  # Jobs from last 7 days
        ])
        
        query_string = "&".join(params)
        return f"{self.base_url}/jobs?{query_string}"
    
    async def search_jobs(
        self, 
        keywords: str, 
        location: str = "", 
        max_results: int = 50
    ) -> List[JobCreate]:
        """Search for jobs on Indeed"""
        jobs = []
        page = 0
        max_pages = min(5, (max_results // 10) + 1)  # Indeed shows ~10 jobs per page
        
        logger.info(f"Starting Indeed search: '{keywords}' in '{location}'")
        
        while page < max_pages and len(jobs) < max_results:
            search_url = self._build_search_url(keywords, location, page)
            response = await self._make_request(search_url)
            
            if not response:
                logger.warning(f"Failed to fetch Indeed page {page}")
                break
            
            soup = self._parse_html(response.text)
            job_elements = self._find_job_elements(soup)
            
            if not job_elements:
                logger.info(f"No more jobs found on page {page}")
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
            
            logger.info(f"Found {len(page_jobs)} jobs on Indeed page {page}")
            page += 1
            
            # If we got fewer jobs than expected, we might be at the end
            if len(page_jobs) < 5:
                break
        
        logger.info(f"Indeed search completed: {len(jobs)} jobs found")
        return jobs
    
    def _find_job_elements(self, soup):
        """Find job listing elements in the page"""
        # Indeed uses various selectors, try multiple approaches
        selectors = [
            'div[data-jk]',  # Main job cards
            '.jobsearch-SerpJobCard',  # Alternative selector
            '.job_seen_beacon',  # Another common selector
            '[data-testid="job-title"]',  # Newer selector
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                logger.debug(f"Found {len(elements)} job elements using selector: {selector}")
                return elements
        
        logger.warning("No job elements found with any selector")
        return []
    
    def _parse_job_listing(self, job_element) -> Optional[Dict[str, Any]]:
        """Parse a single Indeed job listing"""
        try:
            job_data = {}
            
            # Extract job title
            title_selectors = [
                'h2.jobTitle a span',
                '[data-testid="job-title"] a span',
                '.jobTitle a',
                'h2 a span[title]'
            ]
            
            title = None
            for selector in title_selectors:
                title_elem = job_element.select_one(selector)
                if title_elem:
                    title = title_elem.get('title') or title_elem.get_text(strip=True)
                    break
            
            if not title:
                logger.debug("Could not extract job title")
                return None
            
            job_data['title'] = title
            
            # Extract company name
            company_selectors = [
                '[data-testid="company-name"]',
                '.companyName',
                'span.companyName a',
                'span.companyName'
            ]
            
            company = None
            for selector in company_selectors:
                company_elem = job_element.select_one(selector)
                if company_elem:
                    company = company_elem.get_text(strip=True)
                    break
            
            if not company:
                logger.debug("Could not extract company name")
                return None
            
            job_data['company'] = company
            
            # Extract location
            location_selectors = [
                '[data-testid="job-location"]',
                '.companyLocation',
                'div.companyLocation'
            ]
            
            for selector in location_selectors:
                location_elem = job_element.select_one(selector)
                if location_elem:
                    job_data['location'] = location_elem.get_text(strip=True)
                    break
            
            # Extract salary if available
            salary_selectors = [
                '.salary-snippet',
                '[data-testid="job-salary"]',
                '.salaryText'
            ]
            
            for selector in salary_selectors:
                salary_elem = job_element.select_one(selector)
                if salary_elem:
                    job_data['salary'] = salary_elem.get_text(strip=True)
                    break
            
            # Extract job URL
            url_selectors = [
                'h2.jobTitle a',
                '[data-testid="job-title"] a',
                'h2 a'
            ]
            
            for selector in url_selectors:
                url_elem = job_element.select_one(selector)
                if url_elem and url_elem.get('href'):
                    relative_url = url_elem['href']
                    job_data['url'] = urljoin(self.base_url, relative_url)
                    break
            
            # Extract job snippet/description
            snippet_selectors = [
                '.job-snippet',
                '[data-testid="job-snippet"]',
                '.summary'
            ]
            
            for selector in snippet_selectors:
                snippet_elem = job_element.select_one(selector)
                if snippet_elem:
                    job_data['description'] = snippet_elem.get_text(strip=True)
                    break
            
            # Extract additional metadata
            job_data['tags'] = self._extract_tags(job_element)
            job_data['requirements'] = self._extract_requirements(job_data.get('description', ''))
            
            return job_data
            
        except Exception as e:
            logger.error(f"Error parsing Indeed job listing: {e}")
            return None
    
    def _extract_tags(self, job_element) -> List[str]:
        """Extract tags/attributes from job listing"""
        tags = []
        
        # Look for remote work indicators
        text_content = job_element.get_text().lower()
        if any(keyword in text_content for keyword in ['remote', 'work from home', 'telecommute']):
            tags.append('remote')
        
        # Look for job type indicators
        if any(keyword in text_content for keyword in ['full-time', 'full time']):
            tags.append('full-time')
        elif any(keyword in text_content for keyword in ['part-time', 'part time']):
            tags.append('part-time')
        elif any(keyword in text_content for keyword in ['contract', 'contractor']):
            tags.append('contract')
        elif any(keyword in text_content for keyword in ['internship', 'intern']):
            tags.append('internship')
        
        return tags
    
    def _extract_requirements(self, description: str) -> Dict[str, Any]:
        """Extract requirements from job description"""
        if not description:
            return {}
        
        requirements = {}
        description_lower = description.lower()
        
        # Extract experience level
        if any(keyword in description_lower for keyword in ['entry level', 'junior', '0-2 years']):
            requirements['experience_level'] = 'entry'
        elif any(keyword in description_lower for keyword in ['senior', '5+ years', '7+ years']):
            requirements['experience_level'] = 'senior'
        elif any(keyword in description_lower for keyword in ['mid level', '3-5 years', '2-4 years']):
            requirements['experience_level'] = 'mid'
        
        # Extract common skills (basic keyword matching)
        common_skills = [
            'python', 'javascript', 'java', 'react', 'node.js', 'sql', 'aws', 
            'docker', 'kubernetes', 'git', 'agile', 'scrum', 'rest api',
            'machine learning', 'data science', 'tensorflow', 'pytorch'
        ]
        
        found_skills = []
        for skill in common_skills:
            if skill in description_lower:
                found_skills.append(skill)
        
        if found_skills:
            requirements['skills'] = found_skills
        
        return requirements