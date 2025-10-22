"""OAuth service for social authentication"""

import httpx
from typing import Dict, Optional, Tuple
from authlib.integrations.starlette_client import OAuth
from authlib.integrations.base_client import OAuthError
from sqlalchemy.orm import Session
from ..core.config import get_settings
from ..models.user import User
from ..core.security import create_access_token
import secrets
import string

settings = get_settings()


class OAuthService:
    """Service for handling OAuth authentication with multiple providers"""
    
    def __init__(self):
        self.oauth = OAuth()
        self._setup_providers()
    
    def _setup_providers(self):
        """Setup OAuth providers based on configuration"""
        if not settings.oauth_enabled:
            return
            
        # Google OAuth setup
        if settings.google_client_id and settings.google_client_secret:
            self.oauth.register(
                name='google',
                client_id=settings.google_client_id,
                client_secret=settings.google_client_secret,
                server_metadata_url='https://accounts.google.com/.well-known/openid_configuration',
                client_kwargs={
                    'scope': 'openid email profile'
                }
            )
        
        # LinkedIn OAuth setup
        if settings.linkedin_client_id and settings.linkedin_client_secret:
            self.oauth.register(
                name='linkedin',
                client_id=settings.linkedin_client_id,
                client_secret=settings.linkedin_client_secret,
                access_token_url='https://www.linkedin.com/oauth/v2/accessToken',
                authorize_url='https://www.linkedin.com/oauth/v2/authorization',
                api_base_url='https://api.linkedin.com/v2/',
                client_kwargs={
                    'scope': 'r_liteprofile r_emailaddress'
                }
            )
        
        # GitHub OAuth setup
        if settings.github_client_id and settings.github_client_secret:
            self.oauth.register(
                name='github',
                client_id=settings.github_client_id,
                client_secret=settings.github_client_secret,
                access_token_url='https://github.com/login/oauth/access_token',
                authorize_url='https://github.com/login/oauth/authorize',
                api_base_url='https://api.github.com/',
                client_kwargs={
                    'scope': 'user:email'
                }
            )
    
    def get_authorization_url(self, provider: str, redirect_uri: str) -> str:
        """Get authorization URL for OAuth provider"""
        if not settings.oauth_enabled:
            raise ValueError("OAuth is not enabled")
            
        client = getattr(self.oauth, provider, None)
        if not client:
            raise ValueError(f"OAuth provider '{provider}' not configured")
        
        return client.authorize_redirect_uri(redirect_uri)
    
    async def handle_callback(self, provider: str, code: str, state: str = None) -> Dict:
        """Handle OAuth callback and exchange code for token"""
        if not settings.oauth_enabled:
            raise ValueError("OAuth is not enabled")
        
        try:
            if provider == 'google':
                return await self._handle_google_callback(code)
            elif provider == 'linkedin':
                return await self._handle_linkedin_callback(code)
            elif provider == 'github':
                return await self._handle_github_callback(code)
            else:
                raise ValueError(f"Unsupported OAuth provider: {provider}")
        except Exception as e:
            raise OAuthError(f"OAuth callback failed: {str(e)}")
    
    async def _handle_google_callback(self, code: str) -> Dict:
        """Handle Google OAuth callback"""
        async with httpx.AsyncClient() as client:
            # Exchange code for token
            token_response = await client.post(
                'https://oauth2.googleapis.com/token',
                data={
                    'client_id': settings.google_client_id,
                    'client_secret': settings.google_client_secret,
                    'code': code,
                    'grant_type': 'authorization_code',
                    'redirect_uri': settings.google_redirect_uri
                }
            )
            token_data = token_response.json()
            
            if 'access_token' not in token_data:
                raise OAuthError("Failed to get access token from Google")
            
            # Get user info
            user_response = await client.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f"Bearer {token_data['access_token']}"}
            )
            user_data = user_response.json()
            
            return {
                'provider': 'google',
                'oauth_id': user_data['id'],
                'email': user_data['email'],
                'name': user_data.get('name', ''),
                'picture': user_data.get('picture', ''),
                'access_token': token_data['access_token']
            }
    
    async def _handle_linkedin_callback(self, code: str) -> Dict:
        """Handle LinkedIn OAuth callback"""
        async with httpx.AsyncClient() as client:
            # Exchange code for token
            token_response = await client.post(
                'https://www.linkedin.com/oauth/v2/accessToken',
                data={
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': settings.linkedin_redirect_uri,
                    'client_id': settings.linkedin_client_id,
                    'client_secret': settings.linkedin_client_secret
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            token_data = token_response.json()
            
            if 'access_token' not in token_data:
                raise OAuthError("Failed to get access token from LinkedIn")
            
            # Get user profile
            profile_response = await client.get(
                'https://api.linkedin.com/v2/me',
                headers={'Authorization': f"Bearer {token_data['access_token']}"}
            )
            profile_data = profile_response.json()
            
            # Get user email
            email_response = await client.get(
                'https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))',
                headers={'Authorization': f"Bearer {token_data['access_token']}"}
            )
            email_data = email_response.json()
            
            email = None
            if 'elements' in email_data and email_data['elements']:
                email = email_data['elements'][0]['handle~']['emailAddress']
            
            return {
                'provider': 'linkedin',
                'oauth_id': profile_data['id'],
                'email': email,
                'name': f"{profile_data.get('firstName', {}).get('localized', {}).get('en_US', '')} {profile_data.get('lastName', {}).get('localized', {}).get('en_US', '')}".strip(),
                'picture': profile_data.get('profilePicture', {}).get('displayImage~', {}).get('elements', [{}])[0].get('identifiers', [{}])[0].get('identifier', ''),
                'access_token': token_data['access_token']
            }
    
    async def _handle_github_callback(self, code: str) -> Dict:
        """Handle GitHub OAuth callback"""
        async with httpx.AsyncClient() as client:
            # Exchange code for token
            token_response = await client.post(
                'https://github.com/login/oauth/access_token',
                data={
                    'client_id': settings.github_client_id,
                    'client_secret': settings.github_client_secret,
                    'code': code
                },
                headers={'Accept': 'application/json'}
            )
            token_data = token_response.json()
            
            if 'access_token' not in token_data:
                raise OAuthError("Failed to get access token from GitHub")
            
            # Get user info
            user_response = await client.get(
                'https://api.github.com/user',
                headers={'Authorization': f"token {token_data['access_token']}"}
            )
            user_data = user_response.json()
            
            # Get user email (GitHub may not provide email in user endpoint)
            email = user_data.get('email')
            if not email:
                email_response = await client.get(
                    'https://api.github.com/user/emails',
                    headers={'Authorization': f"token {token_data['access_token']}"}
                )
                emails = email_response.json()
                primary_email = next((e['email'] for e in emails if e['primary']), None)
                email = primary_email or (emails[0]['email'] if emails else None)
            
            return {
                'provider': 'github',
                'oauth_id': str(user_data['id']),
                'email': email,
                'name': user_data.get('name', user_data.get('login', '')),
                'picture': user_data.get('avatar_url', ''),
                'access_token': token_data['access_token']
            }
    
    def create_or_link_user(self, oauth_data: Dict, db: Session) -> Tuple[User, str]:
        """Create new user or link existing user with OAuth data"""
        provider = oauth_data['provider']
        oauth_id = oauth_data['oauth_id']
        email = oauth_data['email']
        
        if not email:
            raise ValueError("Email is required for user creation")
        
        # Check if user already exists with this OAuth provider
        existing_oauth_user = db.query(User).filter(
            User.oauth_provider == provider,
            User.oauth_id == oauth_id
        ).first()
        
        if existing_oauth_user:
            # Update existing OAuth user with latest info
            existing_oauth_user.profile_picture_url = oauth_data.get('picture', '')
            existing_oauth_user.updated_at = existing_oauth_user.updated_at
            # Re-populate profile in case of new data
            self._pre_populate_profile(existing_oauth_user, oauth_data, provider)
            db.commit()
            token = create_access_token({"sub": existing_oauth_user.username, "user_id": existing_oauth_user.id})
            return existing_oauth_user, token
        
        # Check if user exists with same email
        existing_email_user = db.query(User).filter(User.email == email).first()
        
        if existing_email_user:
            # Link OAuth to existing email user
            if existing_email_user.oauth_provider is None:
                existing_email_user.oauth_provider = provider
                existing_email_user.oauth_id = oauth_id
                existing_email_user.profile_picture_url = oauth_data.get('picture', '')
                existing_email_user.updated_at = existing_email_user.updated_at
                # Pre-populate profile for newly linked account
                self._pre_populate_profile(existing_email_user, oauth_data, provider)
                db.commit()
                token = create_access_token({"sub": existing_email_user.username, "user_id": existing_email_user.id})
                return existing_email_user, token
            else:
                raise ValueError("Email already associated with another OAuth account")
        
        # Create new user
        username = self._generate_username_from_oauth(oauth_data, db)
        # For SQLite compatibility, OAuth users get a placeholder password
        placeholder_password = f"oauth_{provider}_{oauth_id}"
        new_user = User(
            username=username,
            email=email,
            hashed_password=placeholder_password,  # Placeholder for OAuth users
            oauth_provider=provider,
            oauth_id=oauth_id,
            profile_picture_url=oauth_data.get('picture', '')
        )
        
        # Pre-populate profile if possible
        self._pre_populate_profile(new_user, oauth_data, provider)
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        token = create_access_token({"sub": new_user.username, "user_id": new_user.id})
        return new_user, token
    
    def _generate_username_from_oauth(self, oauth_data: Dict, db: Session) -> str:
        """Generate unique username from OAuth data"""
        name = oauth_data.get('name', '')
        email = oauth_data.get('email', '')
        provider = oauth_data['provider']
        
        # Try to create username from name
        if name:
            base_username = name.lower().replace(' ', '_').replace('-', '_')
            # Remove non-alphanumeric characters except underscore
            base_username = ''.join(c for c in base_username if c.isalnum() or c == '_')
        else:
            # Fallback to email prefix
            base_username = email.split('@')[0].lower()
        
        # Ensure username is unique
        username = base_username
        counter = 1
        while db.query(User).filter(User.username == username).first():
            username = f"{base_username}_{counter}"
            counter += 1
        
        return username
    
    def _pre_populate_profile(self, user: User, oauth_data: Dict, provider: str) -> None:
        """Pre-populate user profile based on OAuth provider data"""
        name = oauth_data.get('name', '')
        
        # Basic skill extraction based on provider
        if provider == 'github':
            # GitHub users might have technical skills
            # This is a basic implementation - could be enhanced with GitHub API calls
            # to fetch repositories and extract technologies
            basic_skills = ['Git', 'GitHub']
            if user.skills is None:
                user.skills = basic_skills
            else:
                # Add GitHub skills if not already present
                existing_skills = [skill.lower() for skill in user.skills]
                for skill in basic_skills:
                    if skill.lower() not in existing_skills:
                        user.skills.append(skill)
        
        elif provider == 'linkedin':
            # LinkedIn users might have professional skills
            # This is a basic implementation - could be enhanced with LinkedIn API calls
            # to fetch actual profile data including skills and experience
            if name:
                # Extract potential skills from name/title if it contains technical terms
                technical_terms = [
                    'developer', 'engineer', 'programmer', 'architect', 'analyst',
                    'manager', 'lead', 'senior', 'junior', 'full stack', 'frontend',
                    'backend', 'devops', 'data scientist', 'ml engineer'
                ]
                name_lower = name.lower()
                detected_skills = []
                
                if any(term in name_lower for term in ['developer', 'engineer', 'programmer']):
                    detected_skills.extend(['Software Development', 'Programming'])
                if 'full stack' in name_lower:
                    detected_skills.extend(['Full Stack Development', 'Frontend', 'Backend'])
                if 'frontend' in name_lower:
                    detected_skills.append('Frontend Development')
                if 'backend' in name_lower:
                    detected_skills.append('Backend Development')
                if 'devops' in name_lower:
                    detected_skills.extend(['DevOps', 'CI/CD'])
                if any(term in name_lower for term in ['data scientist', 'ml engineer']):
                    detected_skills.extend(['Data Science', 'Machine Learning'])
                
                if detected_skills:
                    if user.skills is None:
                        user.skills = detected_skills
                    else:
                        existing_skills = [skill.lower() for skill in user.skills]
                        for skill in detected_skills:
                            if skill.lower() not in existing_skills:
                                user.skills.append(skill)
        
        elif provider == 'google':
            # Google OAuth provides limited profile information
            # Basic setup for Google users
            if user.skills is None:
                user.skills = []
    
    def disconnect_oauth_account(self, user_id: int, provider: str, db: Session) -> bool:
        """Disconnect OAuth account from user"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        if user.oauth_provider == provider:
            # Check if user has a real password (not placeholder) - if not, they can't disconnect OAuth
            if user.hashed_password.startswith('oauth_'):
                raise ValueError("Cannot disconnect OAuth account without setting a password first")
            
            user.oauth_provider = None
            user.oauth_id = None
            user.profile_picture_url = None
            user.updated_at = user.updated_at
            db.commit()
            return True
        
        return False


# Global OAuth service instance
oauth_service = OAuthService()