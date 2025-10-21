"""
DocuSign Sandbox Service
Free DocuSign sandbox integration for development and demos
"""

import base64
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel

from ..core.config import get_settings
from ..core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class DocuSignRecipient(BaseModel):
    """DocuSign recipient"""
    email: str
    name: str
    role: str = "signer"
    recipient_id: str = "1"


class DocuSignEnvelope(BaseModel):
    """DocuSign envelope"""
    envelope_id: str
    status: str
    created: datetime
    sent: Optional[datetime] = None
    completed: Optional[datetime] = None
    recipients: List[DocuSignRecipient] = []


class DocuSignSandboxService:
    """Free DocuSign sandbox service for development and demos"""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = getattr(self.settings, 'docusign_sandbox_base_url', 'https://demo.docusign.net/restapi/v2.1')
        self.client_id = getattr(self.settings, 'docusign_sandbox_client_id', '')
        self.client_secret = getattr(self.settings, 'docusign_sandbox_client_secret', '')
        self.redirect_uri = getattr(self.settings, 'docusign_sandbox_redirect_uri', '')
        self.scopes = getattr(self.settings, 'docusign_sandbox_scopes', 'signature,impersonation')
        self.enabled = getattr(self.settings, 'docusign_sandbox_enabled', False)
        
        self.access_token = None
        self.token_expires_at = None
        self.account_id = None
        
        logger.info(f"DocuSign Sandbox service initialized: {self.base_url}")
    
    async def authenticate(self) -> bool:
        """Authenticate with DocuSign sandbox"""
        try:
            if not self.enabled or not self.client_id or not self.client_secret:
                logger.warning("DocuSign sandbox not enabled or credentials missing")
                return False
            
            # For sandbox, we'll use a mock authentication
            # In production, implement OAuth2 flow
            self.access_token = f"sandbox_token_{datetime.now().timestamp()}"
            self.token_expires_at = datetime.now() + timedelta(hours=1)
            self.account_id = "sandbox_account_123"
            
            logger.info("DocuSign sandbox authenticated successfully")
            return True
            
        except Exception as e:
            logger.error(f"DocuSign sandbox authentication failed: {e}")
            return False
    
    async def create_envelope(
        self,
        document_content: bytes,
        document_name: str,
        recipients: List[DocuSignRecipient],
        subject: str,
        message: str = ""
    ) -> Optional[str]:
        """Create a DocuSign envelope"""
        try:
            if not await self._ensure_authenticated():
                return None
            
            # Encode document content
            document_base64 = base64.b64encode(document_content).decode('utf-8')
            
            # Create envelope payload
            envelope_payload = {
                "emailSubject": subject,
                "emailBlurb": message,
                "documents": [{
                    "documentId": "1",
                    "name": document_name,
                    "documentBase64": document_base64
                }],
                "recipients": {
                    "signers": []
                },
                "status": "sent"
            }
            
            # Add recipients
            for i, recipient in enumerate(recipients):
                signer = {
                    "email": recipient.email,
                    "name": recipient.name,
                    "recipientId": str(i + 1),
                    "routingOrder": str(i + 1),
                    "tabs": {
                        "signHereTabs": [{
                            "documentId": "1",
                            "pageNumber": "1",
                            "xPosition": "100",
                            "yPosition": "100"
                        }]
                    }
                }
                envelope_payload["recipients"]["signers"].append(signer)
            
            # In sandbox mode, return a mock envelope ID
            envelope_id = f"sandbox_envelope_{datetime.now().timestamp()}"
            
            # Store envelope data for demo purposes
            await self._store_envelope_data(envelope_id, envelope_payload)
            
            logger.info(f"DocuSign envelope created: {envelope_id}")
            return envelope_id
            
        except Exception as e:
            logger.error(f"Failed to create DocuSign envelope: {e}")
            return None
    
    async def get_envelope_status(self, envelope_id: str) -> Optional[DocuSignEnvelope]:
        """Get envelope status"""
        try:
            if not await self._ensure_authenticated():
                return None
            
            # Retrieve stored envelope data
            envelope_data = await self._get_envelope_data(envelope_id)
            if not envelope_data:
                logger.warning(f"Envelope not found: {envelope_id}")
                return None
            
            # Simulate different statuses for demo
            statuses = ["sent", "delivered", "signed", "completed", "declined"]
            current_status = statuses[hash(envelope_id) % len(statuses)]
            
            # Create recipients from stored data
            recipients = []
            for signer in envelope_data.get("recipients", {}).get("signers", []):
                recipients.append(DocuSignRecipient(
                    email=signer.get("email", ""),
                    name=signer.get("name", ""),
                    role="signer",
                    recipient_id=signer.get("recipientId", "1")
                ))
            
            envelope = DocuSignEnvelope(
                envelope_id=envelope_id,
                status=current_status,
                created=datetime.now() - timedelta(hours=1),
                sent=datetime.now() - timedelta(minutes=30) if current_status != "sent" else None,
                completed=datetime.now() if current_status == "completed" else None,
                recipients=recipients
            )
            
            return envelope
            
        except Exception as e:
            logger.error(f"Failed to get envelope status: {e}")
            return None
    
    async def void_envelope(self, envelope_id: str, reason: str) -> bool:
        """Void a DocuSign envelope"""
        try:
            if not await self._ensure_authenticated():
                return False
            
            # Update envelope status to voided
            envelope_data = await self._get_envelope_data(envelope_id)
            if envelope_data:
                envelope_data["status"] = "voided"
                envelope_data["voided_reason"] = reason
                await self._store_envelope_data(envelope_id, envelope_data)
            
            logger.info(f"DocuSign envelope voided: {envelope_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to void envelope {envelope_id}: {e}")
            return False
    
    async def get_envelope_documents(self, envelope_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get envelope documents"""
        try:
            if not await self._ensure_authenticated():
                return None
            
            envelope_data = await self._get_envelope_data(envelope_id)
            if not envelope_data:
                return None
            
            documents = []
            for doc in envelope_data.get("documents", []):
                documents.append({
                    "document_id": doc.get("documentId"),
                    "name": doc.get("name"),
                    "type": "content",
                    "uri": f"/envelopes/{envelope_id}/documents/{doc.get('documentId')}"
                })
            
            return documents
            
        except Exception as e:
            logger.error(f"Failed to get envelope documents: {e}")
            return None
    
    async def download_document(self, envelope_id: str, document_id: str) -> Optional[bytes]:
        """Download document from envelope"""
        try:
            if not await self._ensure_authenticated():
                return None
            
            envelope_data = await self._get_envelope_data(envelope_id)
            if not envelope_data:
                return None
            
            # Find the document
            for doc in envelope_data.get("documents", []):
                if doc.get("documentId") == document_id:
                    document_base64 = doc.get("documentBase64", "")
                    return base64.b64decode(document_base64)
            
            logger.warning(f"Document not found: {document_id} in envelope {envelope_id}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to download document: {e}")
            return None
    
    async def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get account information"""
        try:
            if not await self._ensure_authenticated():
                return None
            
            # Return mock account info for sandbox
            return {
                "account_id": self.account_id,
                "account_name": "Sandbox Account",
                "base_uri": self.base_url,
                "is_default": True,
                "account_settings": {
                    "allow_envelope_sending": True,
                    "allow_envelope_downloading": True,
                    "allow_signer_reassign": True
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            return None
    
    async def _ensure_authenticated(self) -> bool:
        """Ensure we have a valid authentication token"""
        if not self.access_token or (self.token_expires_at and datetime.now() >= self.token_expires_at):
            return await self.authenticate()
        return True
    
    async def _store_envelope_data(self, envelope_id: str, data: Dict[str, Any]) -> None:
        """Store envelope data for demo purposes"""
        # In a real implementation, this would be stored in a database
        # For demo purposes, we'll use a simple in-memory store
        if not hasattr(self, '_envelope_store'):
            self._envelope_store = {}
        
        self._envelope_store[envelope_id] = data
    
    async def _get_envelope_data(self, envelope_id: str) -> Optional[Dict[str, Any]]:
        """Get stored envelope data"""
        if not hasattr(self, '_envelope_store'):
            return None
        
        return self._envelope_store.get(envelope_id)
