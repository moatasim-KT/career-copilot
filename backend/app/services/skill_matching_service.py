"""
Semantic skill matching system with NLP and embeddings
"""

import re
import hashlib
import json
import logging
from typing import Dict, List, Set, Tuple, Optional
from collections import Counter
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

from app.core.config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)


class SkillMatchingService:
    """Service for semantic skill matching using embeddings and NLP"""
    
    def __init__(self):
        self.embedding_cache = {}
        self.skill_vocabulary = self._build_skill_vocabulary()
        self.nlp_model = None
        self.sentence_transformer = None
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize NLP models with fallback options"""
        # Try to load sentence transformer for embeddings
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Loaded SentenceTransformer model for embeddings")
            except Exception as e:
                logger.warning(f"Failed to load SentenceTransformer: {e}")
                self.sentence_transformer = None
        
        # Try to load spaCy for NLP
        if SPACY_AVAILABLE:
            try:
                self.nlp_model = spacy.load("en_core_web_sm")
                logger.info("Loaded spaCy model for NLP")
            except Exception as e:
                logger.warning(f"Failed to load spaCy model: {e}")
                self.nlp_model = None
    
    def _build_skill_vocabulary(self) -> Set[str]:
        """Build comprehensive skill vocabulary with categories"""
        return {
            # Programming Languages
            'python', 'javascript', 'java', 'typescript', 'c++', 'c#', 'go', 'rust',
            'ruby', 'php', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'sql', 'html',
            'css', 'shell', 'bash', 'powershell', 'perl', 'lua', 'dart', 'elixir',
            
            # Web Frameworks & Libraries
            'react', 'angular', 'vue', 'svelte', 'node.js', 'express', 'next.js',
            'nuxt.js', 'gatsby', 'ember.js', 'backbone.js', 'jquery', 'bootstrap',
            'tailwind', 'material-ui', 'chakra-ui',
            
            # Backend Frameworks
            'django', 'flask', 'fastapi', 'spring', 'spring boot', 'asp.net',
            'rails', 'laravel', 'symfony', 'codeigniter', 'nestjs', 'koa',
            
            # Mobile Development
            'react native', 'flutter', 'ionic', 'xamarin', 'cordova', 'phonegap',
            'android', 'ios', 'swift ui', 'jetpack compose',
            
            # Machine Learning & AI
            'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy',
            'matplotlib', 'seaborn', 'jupyter', 'opencv', 'nltk', 'spacy',
            'transformers', 'hugging face', 'langchain', 'llama', 'bert',
            
            # Databases
            'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'cassandra',
            'dynamodb', 'oracle', 'sql server', 'sqlite', 'neo4j', 'influxdb',
            'clickhouse', 'snowflake', 'bigquery', 'redshift',
            
            # Cloud Platforms & Services
            'aws', 'azure', 'gcp', 'google cloud', 'heroku', 'vercel', 'netlify',
            'digitalocean', 'linode', 'cloudflare', 'firebase', 'supabase',
            
            # DevOps & Infrastructure
            'docker', 'kubernetes', 'jenkins', 'gitlab ci', 'github actions',
            'terraform', 'ansible', 'puppet', 'chef', 'vagrant', 'helm',
            'istio', 'prometheus', 'grafana', 'elk stack', 'datadog',
            
            # Operating Systems & Tools
            'linux', 'ubuntu', 'centos', 'debian', 'windows', 'macos',
            'git', 'svn', 'mercurial', 'vim', 'emacs', 'vscode', 'intellij',
            
            # Testing & Quality
            'jest', 'mocha', 'chai', 'cypress', 'selenium', 'pytest', 'junit',
            'testng', 'cucumber', 'postman', 'insomnia', 'swagger',
            
            # Methodologies & Practices
            'agile', 'scrum', 'kanban', 'lean', 'devops', 'ci/cd', 'tdd', 'bdd',
            'pair programming', 'code review', 'microservices', 'monolith',
            'serverless', 'event-driven', 'domain-driven design',
            
            # APIs & Protocols
            'rest', 'graphql', 'grpc', 'soap', 'websockets', 'oauth', 'jwt',
            'openapi', 'json', 'xml', 'yaml', 'protobuf', 'avro',
            
            # Data & Analytics
            'etl', 'data pipeline', 'apache spark', 'hadoop', 'kafka', 'airflow',
            'dbt', 'tableau', 'power bi', 'looker', 'metabase', 'superset',
            
            # Security
            'cybersecurity', 'penetration testing', 'vulnerability assessment',
            'owasp', 'ssl/tls', 'encryption', 'authentication', 'authorization',
            'zero trust', 'soc', 'siem', 'incident response',
            
            # Soft Skills
            'leadership', 'communication', 'problem solving', 'critical thinking',
            'teamwork', 'project management', 'mentoring', 'presentation',
            'documentation', 'requirements gathering', 'stakeholder management'
        }
    
    def extract_skills_from_text(self, text: str) -> List[str]:
        """Extract skills from job description or resume text using NLP"""
        if not text:
            return []
        
        found_skills = []
        text_lower = text.lower()
        
        # Method 1: Direct vocabulary matching with context awareness
        found_skills.extend(self._extract_skills_vocabulary_matching(text_lower))
        
        # Method 2: NLP-based entity extraction (if spaCy available)
        if self.nlp_model:
            found_skills.extend(self._extract_skills_nlp(text))
        
        # Method 3: Pattern-based extraction for technical terms
        found_skills.extend(self._extract_skills_patterns(text))
        
        # Method 4: Context-aware skill extraction
        found_skills.extend(self._extract_skills_contextual(text_lower))
        
        # Remove duplicates while preserving order and normalize
        seen = set()
        unique_skills = []
        for skill in found_skills:
            skill_normalized = skill.lower().strip()
            if skill_normalized and skill_normalized not in seen:
                seen.add(skill_normalized)
                unique_skills.append(skill_normalized)
        
        return unique_skills
    
    def _extract_skills_vocabulary_matching(self, text_lower: str) -> List[str]:
        """Extract skills using direct vocabulary matching"""
        found_skills = []
        
        # Sort skills by length (longest first) to avoid partial matches
        sorted_skills = sorted(self.skill_vocabulary, key=len, reverse=True)
        
        for skill in sorted_skills:
            # Use word boundaries for better matching
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.append(skill)
        
        return found_skills
    
    def _extract_skills_nlp(self, text: str) -> List[str]:
        """Extract skills using spaCy NLP model"""
        if not self.nlp_model:
            return []
        
        found_skills = []
        doc = self.nlp_model(text)
        
        # Extract named entities that might be skills
        for ent in doc.ents:
            if ent.label_ in ['ORG', 'PRODUCT', 'LANGUAGE']:
                skill_candidate = ent.text.lower()
                if skill_candidate in self.skill_vocabulary:
                    found_skills.append(skill_candidate)
        
        # Extract noun phrases that might be skills
        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.lower()
            if chunk_text in self.skill_vocabulary:
                found_skills.append(chunk_text)
        
        return found_skills
    
    def _extract_skills_patterns(self, text: str) -> List[str]:
        """Extract skills using regex patterns for technical terms"""
        found_skills = []
        
        # Pattern for programming languages and frameworks
        patterns = [
            r'\b([A-Z][a-z]+(?:\.[a-z]+)?)\b',  # React, Node.js
            r'\b([a-z]+\+\+)\b',  # C++, etc.
            r'\b([A-Z]{2,})\b',  # AWS, API, etc.
            r'\b([a-z]+-[a-z]+)\b',  # spring-boot, etc.
            r'\b([A-Z][a-zA-Z]*[A-Z][a-zA-Z]*)\b',  # CamelCase like JavaScript
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if match.lower() in self.skill_vocabulary:
                    found_skills.append(match.lower())
        
        return found_skills
    
    def _extract_skills_contextual(self, text_lower: str) -> List[str]:
        """Extract skills using contextual clues"""
        found_skills = []
        
        # Common contexts where skills appear
        skill_contexts = [
            r'experience with ([^,\n.]+)',
            r'proficient in ([^,\n.]+)',
            r'knowledge of ([^,\n.]+)',
            r'familiar with ([^,\n.]+)',
            r'expertise in ([^,\n.]+)',
            r'skilled in ([^,\n.]+)',
            r'working with ([^,\n.]+)',
            r'using ([^,\n.]+)',
            r'requirements?:?\s*([^.]+)',
            r'technologies?:?\s*([^.]+)',
            r'skills?:?\s*([^.]+)',
        ]
        
        for context_pattern in skill_contexts:
            matches = re.findall(context_pattern, text_lower, re.IGNORECASE)
            for match in matches:
                # Split by common delimiters
                potential_skills = re.split(r'[,;/&\n\t]+', match)
                for skill in potential_skills:
                    skill = skill.strip()
                    if skill in self.skill_vocabulary:
                        found_skills.append(skill)
        
        return found_skills
    
    def calculate_embedding(self, text: str) -> np.ndarray:
        """Calculate semantic embedding using available models with fallbacks"""
        if not text or not text.strip():
            return np.zeros(384)  # Default embedding size
        
        text = text.strip()
        
        # Method 1: Use SentenceTransformer if available (best quality)
        if self.sentence_transformer:
            try:
                embedding = self.sentence_transformer.encode(text)
                return embedding
            except Exception as e:
                logger.warning(f"SentenceTransformer encoding failed: {e}")
        
        # Method 2: Use OpenAI embeddings if available
        if OPENAI_AVAILABLE and settings.OPENAI_API_KEY:
            try:
                embedding = self._get_openai_embedding(text)
                if embedding is not None:
                    return embedding
            except Exception as e:
                logger.warning(f"OpenAI embedding failed: {e}")
        
        # Method 3: Fallback to enhanced local embedding
        return self._calculate_enhanced_local_embedding(text)
    
    def _get_openai_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get embedding from OpenAI API"""
        try:
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return np.array(response.data[0].embedding)
        except Exception as e:
            logger.warning(f"OpenAI API call failed: {e}")
            return None
    
    def _calculate_enhanced_local_embedding(self, text: str) -> np.ndarray:
        """Calculate enhanced local embedding as fallback"""
        text_lower = text.lower()
        
        # Feature 1: Character frequency vector (26 letters)
        char_freq = np.zeros(26)
        for char in text_lower:
            if 'a' <= char <= 'z':
                char_freq[ord(char) - ord('a')] += 1
        if char_freq.sum() > 0:
            char_freq = char_freq / char_freq.sum()
        
        # Feature 2: Word frequency features
        words = re.findall(r'\b\w+\b', text_lower)
        word_freq = Counter(words)
        
        # Top 50 most common tech words
        tech_words = [
            'python', 'javascript', 'java', 'react', 'node', 'sql', 'aws',
            'docker', 'kubernetes', 'api', 'database', 'web', 'mobile',
            'frontend', 'backend', 'fullstack', 'devops', 'cloud', 'data',
            'machine', 'learning', 'ai', 'analytics', 'testing', 'agile',
            'scrum', 'git', 'linux', 'windows', 'framework', 'library',
            'service', 'microservice', 'rest', 'graphql', 'mongodb',
            'postgresql', 'redis', 'elasticsearch', 'jenkins', 'ci',
            'cd', 'terraform', 'ansible', 'monitoring', 'security',
            'authentication', 'authorization', 'encryption', 'performance',
            'scalability', 'architecture'
        ]
        
        tech_features = np.zeros(len(tech_words))
        for i, word in enumerate(tech_words):
            tech_features[i] = word_freq.get(word, 0)
        
        if tech_features.sum() > 0:
            tech_features = tech_features / tech_features.sum()
        
        # Feature 3: N-gram features
        bigrams = [text_lower[i:i+2] for i in range(len(text_lower)-1)]
        trigrams = [text_lower[i:i+3] for i in range(len(text_lower)-2)]
        
        bigram_hash = sum(hash(bg) % 100 for bg in bigrams[:50]) / 100.0
        trigram_hash = sum(hash(tg) % 100 for tg in trigrams[:50]) / 100.0
        
        # Feature 4: Text statistics
        text_stats = np.array([
            len(text) / 1000.0,  # Text length
            len(words) / 100.0,  # Word count
            len(set(words)) / len(words) if words else 0,  # Vocabulary diversity
            sum(1 for c in text if c.isupper()) / len(text) if text else 0,  # Uppercase ratio
            sum(1 for c in text if c.isdigit()) / len(text) if text else 0,  # Digit ratio
        ])
        
        # Combine all features
        embedding = np.concatenate([
            char_freq,  # 26 features
            tech_features,  # 50 features
            [bigram_hash, trigram_hash],  # 2 features
            text_stats  # 5 features
        ])
        
        # Pad to standard size (384 dimensions like sentence-transformers)
        if len(embedding) < 384:
            padding = np.zeros(384 - len(embedding))
            embedding = np.concatenate([embedding, padding])
        else:
            embedding = embedding[:384]
        
        return embedding
    
    def get_cached_embedding(self, text: str) -> np.ndarray:
        """Get embedding with local caching for performance"""
        if not text or not text.strip():
            return np.zeros(384)
        
        # Create cache key from text hash
        cache_key = hashlib.sha256(text.encode('utf-8')).hexdigest()
        
        # Check cache first
        if cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]
        
        # Calculate embedding
        embedding = self.calculate_embedding(text)
        
        # Cache management - keep cache size reasonable
        if len(self.embedding_cache) >= 1000:
            # Remove oldest 20% of entries (FIFO)
            keys_to_remove = list(self.embedding_cache.keys())[:200]
            for key in keys_to_remove:
                del self.embedding_cache[key]
        
        # Store in cache
        self.embedding_cache[cache_key] = embedding
        
        return embedding
    
    def clear_embedding_cache(self):
        """Clear the embedding cache"""
        self.embedding_cache.clear()
        logger.info("Embedding cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            'cache_size': len(self.embedding_cache),
            'cache_limit': 1000,
            'cache_usage_percent': (len(self.embedding_cache) / 1000) * 100
        }
    
    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts using embeddings"""
        if not text1 or not text2:
            return 0.0
        
        # Get embeddings
        emb1 = self.get_cached_embedding(text1)
        emb2 = self.get_cached_embedding(text2)
        
        # Calculate cosine similarity
        similarity = self._cosine_similarity(emb1, emb2)
        
        # Apply similarity boost for exact matches
        if text1.lower().strip() == text2.lower().strip():
            similarity = max(similarity, 0.95)
        
        # Apply similarity boost for substring matches
        elif text1.lower() in text2.lower() or text2.lower() in text1.lower():
            similarity = max(similarity, 0.8)
        
        return float(max(0.0, min(1.0, similarity)))
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        # Handle zero vectors
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        similarity = dot_product / (norm1 * norm2)
        
        return float(similarity)
    
    def calculate_skill_match_score(
        self, 
        user_skills: List[str], 
        required_skills: List[str],
        use_semantic: bool = True
    ) -> Tuple[float, Dict]:
        """Calculate skill match score with semantic similarity and detailed breakdown"""
        if not required_skills:
            return 0.5, {'matching_skills': [], 'missing_skills': [], 'semantic_matches': []}
        
        if not user_skills:
            return 0.0, {
                'matching_skills': [],
                'missing_skills': required_skills,
                'semantic_matches': [],
                'match_ratio': 0.0
            }
        
        user_skills_lower = [s.lower().strip() for s in user_skills if s.strip()]
        required_skills_lower = [s.lower().strip() for s in required_skills if s.strip()]
        
        # Direct exact matches
        user_skills_set = set(user_skills_lower)
        required_skills_set = set(required_skills_lower)
        exact_matches = user_skills_set.intersection(required_skills_set)
        
        semantic_matches = []
        semantic_score = 0.0
        
        if use_semantic and (self.sentence_transformer or OPENAI_AVAILABLE):
            # Find semantic matches for unmatched required skills
            unmatched_required = required_skills_set - exact_matches
            
            for req_skill in unmatched_required:
                best_match = None
                best_similarity = 0.0
                
                for user_skill in user_skills_lower:
                    if user_skill not in exact_matches:
                        similarity = self.calculate_semantic_similarity(user_skill, req_skill)
                        if similarity > best_similarity and similarity > 0.6:  # Threshold for semantic match
                            best_similarity = similarity
                            best_match = user_skill
                
                if best_match:
                    semantic_matches.append({
                        'user_skill': best_match,
                        'required_skill': req_skill,
                        'similarity': round(best_similarity, 3)
                    })
                    semantic_score += best_similarity
        
        # Calculate scores
        exact_match_score = len(exact_matches) / len(required_skills_set)
        semantic_match_score = semantic_score / len(required_skills_set) if required_skills_set else 0
        
        # Combined score (exact matches weighted higher)
        total_score = (exact_match_score * 0.8) + (semantic_match_score * 0.2)
        
        # Bonus for having more skills than required
        extra_skills = user_skills_set - required_skills_set
        bonus = min(len(extra_skills) * 0.03, 0.15)  # Reduced bonus
        
        final_score = min(total_score + bonus, 1.0)
        
        # Identify missing skills (those without exact or strong semantic matches)
        matched_required = exact_matches.union({sm['required_skill'] for sm in semantic_matches})
        missing_skills = required_skills_set - matched_required
        
        details = {
            'matching_skills': list(exact_matches),
            'semantic_matches': semantic_matches,
            'missing_skills': list(missing_skills),
            'extra_skills': list(extra_skills)[:5],
            'exact_match_ratio': round(exact_match_score, 3),
            'semantic_match_ratio': round(semantic_match_score, 3),
            'total_match_ratio': round(total_score, 3),
            'bonus': round(bonus, 3),
            'final_score': round(final_score, 3)
        }
        
        return round(final_score, 3), details
    
    def calculate_skill_similarity_matrix(
        self, 
        user_skills: List[str], 
        job_skills: List[str],
        use_semantic: bool = True
    ) -> np.ndarray:
        """Calculate similarity matrix between user and job skills using semantic embeddings"""
        if not user_skills or not job_skills:
            return np.zeros((len(user_skills) or 1, len(job_skills) or 1))
        
        matrix = np.zeros((len(user_skills), len(job_skills)))
        
        for i, user_skill in enumerate(user_skills):
            for j, job_skill in enumerate(job_skills):
                user_skill_clean = user_skill.lower().strip()
                job_skill_clean = job_skill.lower().strip()
                
                # Exact match
                if user_skill_clean == job_skill_clean:
                    matrix[i][j] = 1.0
                # Substring match
                elif user_skill_clean in job_skill_clean or job_skill_clean in user_skill_clean:
                    matrix[i][j] = 0.85
                # Semantic similarity (if enabled and models available)
                elif use_semantic and (self.sentence_transformer or OPENAI_AVAILABLE):
                    similarity = self.calculate_semantic_similarity(user_skill, job_skill)
                    matrix[i][j] = similarity
                # Fallback to simple string similarity
                else:
                    matrix[i][j] = self._simple_string_similarity(user_skill_clean, job_skill_clean)
        
        return matrix
    
    def _simple_string_similarity(self, str1: str, str2: str) -> float:
        """Calculate simple string similarity as fallback"""
        if not str1 or not str2:
            return 0.0
        
        # Jaccard similarity on character level
        set1 = set(str1)
        set2 = set(str2)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def find_best_skill_matches(
        self, 
        user_skills: List[str], 
        job_skills: List[str],
        top_k: int = 5,
        min_similarity: float = 0.5
    ) -> List[Dict]:
        """Find best matching skills between user and job"""
        if not user_skills or not job_skills:
            return []
        
        similarity_matrix = self.calculate_skill_similarity_matrix(user_skills, job_skills)
        
        matches = []
        for i, user_skill in enumerate(user_skills):
            for j, job_skill in enumerate(job_skills):
                similarity = float(similarity_matrix[i][j])
                if similarity >= min_similarity:
                    matches.append({
                        'user_skill': user_skill,
                        'job_skill': job_skill,
                        'similarity': round(similarity, 3),
                        'match_type': self._get_match_type(similarity)
                    })
        
        # Sort by similarity (descending)
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        return matches[:top_k]
    
    def _get_match_type(self, similarity: float) -> str:
        """Classify match type based on similarity score"""
        if similarity >= 0.95:
            return 'exact'
        elif similarity >= 0.8:
            return 'strong'
        elif similarity >= 0.6:
            return 'moderate'
        else:
            return 'weak'
    
    def analyze_skill_gaps(
        self, 
        user_skills: List[str], 
        job_skills: List[str]
    ) -> Dict:
        """Analyze skill gaps and provide recommendations"""
        score, details = self.calculate_skill_match_score(user_skills, job_skills)
        
        # Categorize missing skills by importance (frequency in job market)
        missing_skills = details.get('missing_skills', [])
        
        # Simple importance scoring based on skill vocabulary presence
        skill_importance = {}
        for skill in missing_skills:
            # More common skills get higher importance
            if skill in ['python', 'javascript', 'sql', 'aws', 'docker']:
                skill_importance[skill] = 'high'
            elif skill in ['react', 'node.js', 'postgresql', 'kubernetes']:
                skill_importance[skill] = 'medium'
            else:
                skill_importance[skill] = 'low'
        
        return {
            'overall_match_score': score,
            'missing_skills': missing_skills,
            'skill_importance': skill_importance,
            'recommendations': self._generate_skill_recommendations(missing_skills),
            'strengths': details.get('matching_skills', []),
            'semantic_matches': details.get('semantic_matches', [])
        }
    
    def _generate_skill_recommendations(self, missing_skills: List[str]) -> List[Dict]:
        """Generate learning recommendations for missing skills"""
        recommendations = []
        
        skill_resources = {
            'python': {
                'priority': 'high',
                'learning_path': 'Start with Python basics, then move to web frameworks',
                'resources': ['Python.org tutorial', 'Automate the Boring Stuff', 'Real Python']
            },
            'javascript': {
                'priority': 'high',
                'learning_path': 'Learn ES6+ features, then frameworks like React',
                'resources': ['MDN Web Docs', 'JavaScript.info', 'FreeCodeCamp']
            },
            'react': {
                'priority': 'medium',
                'learning_path': 'Master JavaScript first, then React fundamentals',
                'resources': ['React Official Docs', 'React Tutorial', 'Scrimba React Course']
            },
            'aws': {
                'priority': 'high',
                'learning_path': 'Start with AWS fundamentals, get certified',
                'resources': ['AWS Training', 'A Cloud Guru', 'AWS Documentation']
            }
        }
        
        for skill in missing_skills[:5]:  # Top 5 missing skills
            if skill in skill_resources:
                recommendations.append({
                    'skill': skill,
                    **skill_resources[skill]
                })
            else:
                recommendations.append({
                    'skill': skill,
                    'priority': 'medium',
                    'learning_path': f'Research {skill} fundamentals and best practices',
                    'resources': [f'Official {skill} documentation', 'Online tutorials', 'Practice projects']
                })
        
        return recommendations
    
    def batch_extract_skills(self, texts: List[str]) -> List[List[str]]:
        """Extract skills from multiple texts efficiently"""
        return [self.extract_skills_from_text(text) for text in texts]
    
    def get_model_info(self) -> Dict:
        """Get information about loaded models"""
        return {
            'sentence_transformer_available': self.sentence_transformer is not None,
            'sentence_transformer_model': 'all-MiniLM-L6-v2' if self.sentence_transformer else None,
            'spacy_available': self.nlp_model is not None,
            'spacy_model': 'en_core_web_sm' if self.nlp_model else None,
            'openai_available': OPENAI_AVAILABLE and bool(settings.OPENAI_API_KEY),
            'vocabulary_size': len(self.skill_vocabulary),
            'cache_stats': self.get_cache_stats()
        }


# Global service instance
skill_matching_service = SkillMatchingService()