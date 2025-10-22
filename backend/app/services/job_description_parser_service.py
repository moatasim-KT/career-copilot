"""Job Description Parser Service for extracting structured data from job postings"""

import re
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import time

from ..services.llm_manager import LLMManager

logger = logging.getLogger(__name__)


class JobDescriptionParserService:
    """Service for parsing job descriptions and extracting structured data"""
    
    def __init__(self):
        self.llm_manager = LLMManager()
        
        # Common tech stack patterns for fallback extraction
        self.tech_patterns = [
            # Programming Languages
            r'\b(?:Python|Java|JavaScript|TypeScript|C\+\+|C#|Ruby|Go|Rust|Swift|Kotlin|PHP|Scala|R|MATLAB)\b',
            # Frontend Frameworks
            r'\b(?:React|Angular|Vue\.?js|Svelte|Next\.?js|Nuxt\.?js|Ember\.?js)\b',
            # Backend Frameworks
            r'\b(?:Node\.?js|Express|Django|Flask|FastAPI|Spring|Laravel|Rails|ASP\.NET|Gin|Fiber)\b',
            # Databases
            r'\b(?:MySQL|PostgreSQL|MongoDB|Redis|Elasticsearch|Cassandra|DynamoDB|SQLite|Oracle|SQL Server)\b',
            # Cloud & DevOps
            r'\b(?:AWS|Azure|GCP|Google Cloud|Docker|Kubernetes|Jenkins|GitLab CI|GitHub Actions|Terraform|Ansible)\b',
            # Tools & Technologies
            r'\b(?:Git|GitHub|GitLab|Jira|Confluence|Slack|Figma|Adobe|Photoshop|Sketch)\b',
            # Data & ML
            r'\b(?:TensorFlow|PyTorch|Pandas|NumPy|Scikit-learn|Jupyter|Apache Spark|Hadoop|Kafka)\b'
        ]
        
        # Experience level patterns
        self.experience_patterns = {
            'junior': [
                r'\b(?:junior|entry.?level|0-2\s+years?|1-3\s+years?|intern|graduate|new\s+grad)\b',
                r'\b(?:associate|assistant|trainee)\b'
            ],
            'mid': [
                r'\b(?:mid.?level|intermediate|2-5\s+years?|3-7\s+years?|4-6\s+years?)\b',
                r'\b(?:experienced|regular|standard)\b'
            ],
            'senior': [
                r'\b(?:senior|lead|principal|architect|5\+\s+years?|7\+\s+years?|expert|staff)\b',
                r'\b(?:manager|director|head\s+of|chief)\b'
            ]
        }
        
        # Salary patterns
        self.salary_patterns = [
            r'\$[\d,]+\s*-\s*\$[\d,]+',
            r'\$[\d,]+k?\s*-\s*\$?[\d,]+k?',
            r'[\d,]+k?\s*-\s*[\d,]+k?\s*(?:USD|dollars?)',
            r'salary:?\s*\$?[\d,]+\s*-\s*\$?[\d,]+'
        ]
        
        # Job type patterns
        self.job_type_patterns = {
            'full-time': [r'\b(?:full.?time|permanent|FTE)\b'],
            'part-time': [r'\b(?:part.?time|PTE)\b'],
            'contract': [r'\b(?:contract|contractor|freelance|consulting)\b'],
            'internship': [r'\b(?:intern|internship|co-op|coop)\b'],
            'temporary': [r'\b(?:temporary|temp|seasonal)\b']
        }
        
        # Remote work patterns
        self.remote_patterns = {
            'remote': [r'\b(?:remote|work\s+from\s+home|WFH|distributed)\b'],
            'hybrid': [r'\b(?:hybrid|flexible|mixed)\b'],
            'on-site': [r'\b(?:on.?site|office|in.?person|local)\b']
        }

    async def parse_job_description(self, job_url: Optional[str] = None, description_text: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse a job description from URL or text and extract structured data
        
        Args:
            job_url: URL of the job posting to scrape
            description_text: Direct text of job description
            
        Returns:
            Dictionary containing extracted data
        """
        try:
            # Get job description text
            if job_url:
                description_text = await self._scrape_job_description(job_url)
            
            if not description_text or not description_text.strip():
                raise ValueError("No job description text provided or scraped")
            
            # Use LLM for intelligent parsing
            llm_result = await self._parse_with_llm(description_text)
            
            # Fallback to rule-based parsing if LLM fails
            if not llm_result or not llm_result.get('tech_stack'):
                logger.warning("LLM parsing failed or incomplete, using fallback parsing")
                fallback_result = self._parse_with_rules(description_text)
                # Merge results, preferring LLM where available
                llm_result = {**fallback_result, **llm_result} if llm_result else fallback_result
            
            # Structure the final result
            parsed_data = {
                'tech_stack': llm_result.get('tech_stack', []),
                'requirements': llm_result.get('requirements', []),
                'responsibilities': llm_result.get('responsibilities', []),
                'experience_level': llm_result.get('experience_level'),
                'salary_range': llm_result.get('salary_range'),
                'job_type': llm_result.get('job_type'),
                'remote_option': llm_result.get('remote_option'),
                'company_info': llm_result.get('company_info', {}),
                'parsing_method': 'llm' if llm_result.get('tech_stack') else 'rules',
                'source_url': job_url
            }
            
            logger.info(f"Successfully parsed job description from {'URL' if job_url else 'text'}")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing job description: {str(e)}")
            raise

    async def _scrape_job_description(self, job_url: str) -> str:
        """Scrape job description from URL"""
        try:
            # Validate URL
            parsed_url = urlparse(job_url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError("Invalid URL provided")
            
            # Set up headers to mimic a real browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Make request with timeout
            response = requests.get(job_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Try different strategies to extract job description
            job_text = self._extract_job_text_from_html(soup, job_url)
            
            if not job_text.strip():
                raise ValueError("Could not extract job description text from the webpage")
            
            return job_text
            
        except requests.RequestException as e:
            logger.error(f"Error scraping job URL {job_url}: {str(e)}")
            raise ValueError(f"Failed to scrape job description: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing scraped content: {str(e)}")
            raise

    def _extract_job_text_from_html(self, soup: BeautifulSoup, job_url: str) -> str:
        """Extract job description text from HTML using various strategies"""
        
        # Strategy 1: Look for common job description selectors
        job_selectors = [
            # LinkedIn
            '.jobs-description-content__text',
            '.jobs-box__html-content',
            '.description__text',
            # Indeed
            '.jobsearch-jobDescriptionText',
            '.jobsearch-JobComponent-description',
            # Glassdoor
            '.jobDescriptionContent',
            '.desc',
            # Generic
            '.job-description',
            '.job-content',
            '.description',
            '[data-testid="job-description"]',
            '#job-description',
            '.posting-description'
        ]
        
        for selector in job_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(separator='\n', strip=True)
                if len(text) > 200:  # Ensure we got substantial content
                    return text
        
        # Strategy 2: Look for elements with job-related keywords
        job_keywords = ['responsibilities', 'requirements', 'qualifications', 'experience', 'skills']
        
        for element in soup.find_all(['div', 'section', 'article']):
            text = element.get_text(separator=' ', strip=True).lower()
            if any(keyword in text for keyword in job_keywords) and len(text) > 500:
                return element.get_text(separator='\n', strip=True)
        
        # Strategy 3: Find the largest text block (likely the job description)
        text_blocks = []
        for element in soup.find_all(['div', 'section', 'article', 'p']):
            text = element.get_text(separator=' ', strip=True)
            if len(text) > 200:
                text_blocks.append((len(text), text))
        
        if text_blocks:
            # Return the largest text block
            text_blocks.sort(reverse=True)
            return text_blocks[0][1]
        
        # Strategy 4: Fallback to body text
        body = soup.find('body')
        if body:
            return body.get_text(separator='\n', strip=True)
        
        # Last resort: all text
        return soup.get_text(separator='\n', strip=True)

    async def _parse_with_llm(self, description_text: str) -> Dict[str, Any]:
        """Use LLM to parse job description intelligently"""
        try:
            prompt = f"""
            Please analyze the following job description and extract structured information in JSON format.
            
            Extract the following information:
            1. tech_stack: Array of technologies, programming languages, frameworks, tools mentioned
            2. requirements: Array of key requirements and qualifications
            3. responsibilities: Array of main job responsibilities and duties
            4. experience_level: One of "junior", "mid", or "senior" based on requirements
            5. salary_range: Salary information if mentioned (e.g., "$80,000 - $120,000")
            6. job_type: One of "full-time", "part-time", "contract", "internship", "temporary"
            7. remote_option: One of "remote", "hybrid", "on-site" based on work arrangement
            8. company_info: Object with company name, industry, size if mentioned
            
            Job Description:
            {description_text}
            
            Please respond with valid JSON only, no additional text.
            """
            
            response = await self.llm_manager.generate_response(prompt)
            
            # Try to parse JSON response
            import json
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # Try to extract JSON from response if it's wrapped in text
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    logger.warning("LLM response was not valid JSON")
                    return {}
                    
        except Exception as e:
            logger.error(f"LLM parsing failed: {str(e)}")
            return {}

    def _parse_with_rules(self, description_text: str) -> Dict[str, Any]:
        """Fallback rule-based parsing"""
        try:
            text_lower = description_text.lower()
            
            # Extract tech stack
            tech_stack = set()
            for pattern in self.tech_patterns:
                matches = re.findall(pattern, description_text, re.IGNORECASE)
                tech_stack.update(matches)
            
            # Extract experience level
            experience_level = self._extract_experience_level_rules(text_lower)
            
            # Extract salary range
            salary_range = self._extract_salary_range(description_text)
            
            # Extract job type
            job_type = self._extract_job_type(text_lower)
            
            # Extract remote option
            remote_option = self._extract_remote_option(text_lower)
            
            # Extract basic requirements and responsibilities
            requirements = self._extract_requirements(description_text)
            responsibilities = self._extract_responsibilities(description_text)
            
            return {
                'tech_stack': list(tech_stack),
                'requirements': requirements,
                'responsibilities': responsibilities,
                'experience_level': experience_level,
                'salary_range': salary_range,
                'job_type': job_type,
                'remote_option': remote_option,
                'company_info': {}
            }
        except Exception as e:
            logger.error(f"Rule-based parsing failed: {str(e)}")
            return {
                'tech_stack': [],
                'requirements': [],
                'responsibilities': [],
                'experience_level': None,
                'salary_range': None,
                'job_type': None,
                'remote_option': None,
                'company_info': {}
            }

    def _extract_experience_level_rules(self, text: str) -> Optional[str]:
        """Extract experience level using regex patterns"""
        # Check for explicit years of experience
        years_match = re.search(r'(\d+)[\+\-\s]*years?\s+(?:of\s+)?experience', text)
        if years_match:
            years = int(years_match.group(1))
            if years <= 2:
                return 'junior'
            elif years <= 5:
                return 'mid'
            else:
                return 'senior'
        
        # Check for level keywords
        for level, patterns in self.experience_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return level
        
        return None

    def _extract_salary_range(self, text: str) -> Optional[str]:
        """Extract salary range using regex patterns"""
        for pattern in self.salary_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group().strip()
        return None

    def _extract_job_type(self, text: str) -> Optional[str]:
        """Extract job type using regex patterns"""
        for job_type, patterns in self.job_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return job_type
        return None

    def _extract_remote_option(self, text: str) -> Optional[str]:
        """Extract remote work option using regex patterns"""
        for remote_type, patterns in self.remote_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return remote_type
        return None

    def _extract_requirements(self, text: str) -> List[str]:
        """Extract requirements section"""
        requirements = []
        
        # Look for requirements section
        req_patterns = [
            r'(?:requirements?|qualifications?|must\s+have)[:\s]*\n(.*?)(?:\n\n|\nresponsibilities|\nduties|$)',
            r'(?:you\s+(?:will\s+)?need|we\s+(?:are\s+)?looking\s+for)[:\s]*\n(.*?)(?:\n\n|\nresponsibilities|\nduties|$)'
        ]
        
        for pattern in req_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                req_text = match.group(1)
                # Split by bullet points or new lines
                req_items = re.split(r'[•\-\*]\s*|^\s*\d+\.?\s*', req_text, flags=re.MULTILINE)
                requirements.extend([item.strip() for item in req_items if item.strip() and len(item.strip()) > 10])
                break
        
        return requirements[:10]  # Limit to top 10

    def _extract_responsibilities(self, text: str) -> List[str]:
        """Extract responsibilities section"""
        responsibilities = []
        
        # Look for responsibilities section
        resp_patterns = [
            r'(?:responsibilities|duties|you\s+will)[:\s]*\n(.*?)(?:\n\n|\nrequirements|\nqualifications|$)',
            r'(?:what\s+you.?ll\s+do|your\s+role)[:\s]*\n(.*?)(?:\n\n|\nrequirements|\nqualifications|$)'
        ]
        
        for pattern in resp_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                resp_text = match.group(1)
                # Split by bullet points or new lines
                resp_items = re.split(r'[•\-\*]\s*|^\s*\d+\.?\s*', resp_text, flags=re.MULTILINE)
                responsibilities.extend([item.strip() for item in resp_items if item.strip() and len(item.strip()) > 10])
                break
        
        return responsibilities[:10]  # Limit to top 10

    def generate_job_suggestions(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate suggestions for job fields based on parsed data"""
        suggestions = {
            'auto_populate': {},
            'confidence_scores': {}
        }
        
        try:
            # Suggest auto-population for high-confidence fields
            if parsed_data.get('tech_stack'):
                suggestions['auto_populate']['tech_stack'] = parsed_data['tech_stack']
                suggestions['confidence_scores']['tech_stack'] = 0.8 if parsed_data.get('parsing_method') == 'llm' else 0.6
            
            if parsed_data.get('requirements'):
                # Join requirements into a single text field
                requirements_text = '\n'.join(f"• {req}" for req in parsed_data['requirements'])
                suggestions['auto_populate']['requirements'] = requirements_text
                suggestions['confidence_scores']['requirements'] = 0.7
            
            if parsed_data.get('responsibilities'):
                # Join responsibilities into a single text field
                responsibilities_text = '\n'.join(f"• {resp}" for resp in parsed_data['responsibilities'])
                suggestions['auto_populate']['responsibilities'] = responsibilities_text
                suggestions['confidence_scores']['responsibilities'] = 0.7
            
            if parsed_data.get('salary_range'):
                suggestions['auto_populate']['salary_range'] = parsed_data['salary_range']
                suggestions['confidence_scores']['salary_range'] = 0.6
            
            if parsed_data.get('job_type'):
                suggestions['auto_populate']['job_type'] = parsed_data['job_type']
                suggestions['confidence_scores']['job_type'] = 0.7
            
            if parsed_data.get('remote_option'):
                suggestions['auto_populate']['remote_option'] = parsed_data['remote_option']
                suggestions['confidence_scores']['remote_option'] = 0.7
            
        except Exception as e:
            logger.error(f"Error generating job suggestions: {str(e)}")
        
        return suggestions