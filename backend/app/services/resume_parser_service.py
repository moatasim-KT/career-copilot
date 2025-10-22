"""Resume Parser Service for extracting structured data from resume documents"""

import os
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import magic
import PyPDF2
import pdfplumber
from docx import Document
from io import BytesIO

from ..services.llm_manager import LLMManager
from ..models.resume_upload import ResumeUpload
from ..core.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ResumeParserService:
    """Service for parsing resume documents and extracting structured data"""
    
    def __init__(self):
        self.llm_manager = LLMManager()
        self.supported_formats = {'.pdf', '.docx', '.doc'}
        
        # Common skill patterns for fallback extraction
        self.skill_patterns = [
            r'\b(?:Python|Java|JavaScript|TypeScript|C\+\+|C#|Ruby|Go|Rust|Swift|Kotlin)\b',
            r'\b(?:React|Angular|Vue|Node\.js|Express|Django|Flask|Spring|Laravel)\b',
            r'\b(?:AWS|Azure|GCP|Docker|Kubernetes|Jenkins|Git|GitHub|GitLab)\b',
            r'\b(?:SQL|MySQL|PostgreSQL|MongoDB|Redis|Elasticsearch)\b',
            r'\b(?:HTML|CSS|SASS|SCSS|Bootstrap|Tailwind)\b',
            r'\b(?:Machine Learning|AI|Data Science|TensorFlow|PyTorch|Pandas|NumPy)\b'
        ]
        
        # Experience level patterns
        self.experience_patterns = {
            'junior': [r'\b(?:junior|entry.?level|0-2\s+years?|intern|graduate|new\s+grad)\b'],
            'mid': [r'\b(?:mid.?level|intermediate|2-5\s+years?|3-7\s+years?)\b'],
            'senior': [r'\b(?:senior|lead|principal|architect|5\+\s+years?|7\+\s+years?|expert)\b']
        }

    async def parse_resume(self, file_path: str, filename: str, user_id: int) -> Dict[str, Any]:
        """
        Parse a resume file and extract structured data
        
        Args:
            file_path: Path to the uploaded resume file
            filename: Original filename
            user_id: ID of the user who uploaded the resume
            
        Returns:
            Dictionary containing extracted data
        """
        try:
            # Validate file format
            file_type = self._detect_file_type(file_path)
            if not file_type:
                raise ValueError(f"Unsupported file format for {filename}")
            
            # Extract text from file
            text_content = self._extract_text(file_path, file_type)
            if not text_content.strip():
                raise ValueError("No text content could be extracted from the resume")
            
            # Use LLM for intelligent parsing
            llm_result = await self._parse_with_llm(text_content)
            
            # Fallback to rule-based parsing if LLM fails
            if not llm_result or not llm_result.get('skills'):
                logger.warning("LLM parsing failed or incomplete, using fallback parsing")
                fallback_result = self._parse_with_rules(text_content)
                # Merge results, preferring LLM where available
                llm_result = {**fallback_result, **llm_result} if llm_result else fallback_result
            
            # Structure the final result
            parsed_data = {
                'raw_text': text_content,
                'skills': llm_result.get('skills', []),
                'experience_level': llm_result.get('experience_level'),
                'contact_info': llm_result.get('contact_info', {}),
                'education': llm_result.get('education', []),
                'work_experience': llm_result.get('work_experience', []),
                'summary': llm_result.get('summary', ''),
                'parsing_method': 'llm' if llm_result.get('skills') else 'rules'
            }
            
            logger.info(f"Successfully parsed resume {filename} for user {user_id}")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing resume {filename}: {str(e)}")
            raise

    def _detect_file_type(self, file_path: str) -> Optional[str]:
        """Detect file type using python-magic"""
        try:
            mime_type = magic.from_file(file_path, mime=True)
            
            if mime_type == 'application/pdf':
                return 'pdf'
            elif mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                return 'docx'
            elif mime_type in ['application/msword']:
                return 'doc'
            
            # Fallback to file extension
            ext = Path(file_path).suffix.lower()
            if ext in ['.pdf', '.docx', '.doc']:
                return ext[1:]  # Remove the dot
                
            return None
        except Exception as e:
            logger.error(f"Error detecting file type: {str(e)}")
            return None

    def _extract_text(self, file_path: str, file_type: str) -> str:
        """Extract text content from different file formats"""
        try:
            if file_type == 'pdf':
                return self._extract_pdf_text(file_path)
            elif file_type == 'docx':
                return self._extract_docx_text(file_path)
            elif file_type == 'doc':
                # For .doc files, try to read as docx (some are actually docx)
                try:
                    return self._extract_docx_text(file_path)
                except:
                    raise ValueError("Legacy .doc format not fully supported. Please convert to .docx or .pdf")
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            logger.error(f"Error extracting text from {file_type} file: {str(e)}")
            raise

    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF using multiple methods"""
        text = ""
        
        # Try pdfplumber first (better for complex layouts)
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            logger.warning(f"pdfplumber failed: {str(e)}, trying PyPDF2")
        
        # Fallback to PyPDF2 if pdfplumber fails
        if not text.strip():
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
            except Exception as e:
                logger.error(f"PyPDF2 also failed: {str(e)}")
                raise ValueError("Could not extract text from PDF file")
        
        return text.strip()

    def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {str(e)}")
            raise ValueError("Could not extract text from DOCX file")

    async def _parse_with_llm(self, text_content: str) -> Dict[str, Any]:
        """Use LLM to parse resume content intelligently"""
        try:
            prompt = f"""
            Please analyze the following resume text and extract structured information in JSON format.
            
            Extract the following information:
            1. skills: Array of technical skills, programming languages, frameworks, tools
            2. experience_level: One of "junior", "mid", or "senior" based on years of experience and role titles
            3. contact_info: Object with name, email, phone, location if available
            4. education: Array of education entries with degree, institution, year
            5. work_experience: Array of work entries with title, company, duration, description
            6. summary: Brief professional summary or objective
            
            Resume text:
            {text_content}
            
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

    def _parse_with_rules(self, text_content: str) -> Dict[str, Any]:
        """Fallback rule-based parsing"""
        try:
            # Extract skills using regex patterns
            skills = set()
            for pattern in self.skill_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                skills.update(matches)
            
            # Extract experience level
            experience_level = self._extract_experience_level(text_content)
            
            # Extract contact info
            contact_info = self._extract_contact_info(text_content)
            
            return {
                'skills': list(skills),
                'experience_level': experience_level,
                'contact_info': contact_info,
                'education': [],
                'work_experience': [],
                'summary': ''
            }
        except Exception as e:
            logger.error(f"Rule-based parsing failed: {str(e)}")
            return {
                'skills': [],
                'experience_level': None,
                'contact_info': {},
                'education': [],
                'work_experience': [],
                'summary': ''
            }

    def _extract_experience_level(self, text: str) -> Optional[str]:
        """Extract experience level using regex patterns"""
        text_lower = text.lower()
        
        # Check for explicit years of experience
        years_match = re.search(r'(\d+)[\+\-\s]*years?\s+(?:of\s+)?experience', text_lower)
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
                if re.search(pattern, text_lower):
                    return level
        
        return None

    def _extract_contact_info(self, text: str) -> Dict[str, str]:
        """Extract contact information using regex patterns"""
        contact_info = {}
        
        # Extract email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if email_match:
            contact_info['email'] = email_match.group()
        
        # Extract phone number
        phone_match = re.search(r'(\+?1?[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})', text)
        if phone_match:
            contact_info['phone'] = phone_match.group()
        
        # Extract name (first line that looks like a name)
        lines = text.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if line and len(line.split()) <= 4 and not '@' in line and not any(char.isdigit() for char in line):
                if len(line) > 3:  # Avoid single letters or very short strings
                    contact_info['name'] = line
                    break
        
        return contact_info

    async def suggest_profile_updates(self, parsed_data: Dict[str, Any], current_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate profile update suggestions based on parsed resume data"""
        suggestions = {
            'skills_to_add': [],
            'experience_level_suggestion': None,
            'contact_info_updates': {},
            'confidence_scores': {}
        }
        
        try:
            # Suggest new skills
            current_skills = set(skill.lower() for skill in current_profile.get('skills', []))
            parsed_skills = set(skill.lower() for skill in parsed_data.get('skills', []))
            new_skills = parsed_skills - current_skills
            suggestions['skills_to_add'] = list(new_skills)
            
            # Suggest experience level if different
            parsed_level = parsed_data.get('experience_level')
            current_level = current_profile.get('experience_level')
            if parsed_level and parsed_level != current_level:
                suggestions['experience_level_suggestion'] = parsed_level
            
            # Suggest contact info updates
            parsed_contact = parsed_data.get('contact_info', {})
            for key, value in parsed_contact.items():
                if value and not current_profile.get(key):
                    suggestions['contact_info_updates'][key] = value
            
            # Calculate confidence scores
            suggestions['confidence_scores'] = {
                'skills': 0.8 if parsed_data.get('parsing_method') == 'llm' else 0.6,
                'experience_level': 0.7 if parsed_level else 0.0,
                'contact_info': 0.9 if parsed_contact else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error generating profile suggestions: {str(e)}")
        
        return suggestions

    def validate_file(self, file_path: str, max_size_mb: int = 10) -> Tuple[bool, str]:
        """
        Validate uploaded resume file
        
        Args:
            file_path: Path to the file
            max_size_mb: Maximum file size in MB
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return False, "File does not exist"
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > max_size_mb * 1024 * 1024:
                return False, f"File size exceeds {max_size_mb}MB limit"
            
            # Check file type
            file_type = self._detect_file_type(file_path)
            if not file_type:
                return False, "Unsupported file format. Please upload PDF, DOCX, or DOC files."
            
            # Try to extract some text to ensure file is readable
            try:
                text = self._extract_text(file_path, file_type)
                if len(text.strip()) < 50:
                    return False, "File appears to be empty or contains insufficient text"
            except Exception as e:
                return False, f"File appears to be corrupted or unreadable: {str(e)}"
            
            return True, ""
            
        except Exception as e:
            return False, f"File validation error: {str(e)}"