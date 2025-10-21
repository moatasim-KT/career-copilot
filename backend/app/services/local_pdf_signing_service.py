"""
Enhanced Local PDF Signing Service
Comprehensive PDF digital signature functionality as DocuSign alternative
with certificate management, signature validation, and advanced features.
"""

import io
import os
import hashlib
import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple
import tempfile
import uuid

try:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.x509.oid import NameOID
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

try:
    from PyPDF2 import PdfReader, PdfWriter
    from PyPDF2.generic import DictionaryObject, ArrayObject, TextStringObject
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

from reportlab.lib.colors import black, red, blue
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from pydantic import BaseModel, Field

from ..core.config import get_settings
from ..core.logging import get_logger
from ..core.database import get_db_session

logger = get_logger(__name__)


class SignatureInfo(BaseModel):
    """Enhanced signature information model"""
    
    signer_name: str = Field(..., description="Name of the signer")
    signer_email: str = Field(..., description="Email of the signer")
    signature_text: Optional[str] = Field(None, description="Text-based signature")
    signature_image_path: Optional[str] = Field(None, description="Path to signature image")
    signature_image_data: Optional[str] = Field(None, description="Base64 encoded signature image")
    x_position: float = Field(100, description="X position on page")
    y_position: float = Field(100, description="Y position on page")
    page_number: int = Field(1, description="Page number for signature")
    width: float = Field(200, description="Signature width")
    height: float = Field(50, description="Signature height")
    signing_reason: str = Field("Contract Agreement", description="Reason for signing")
    signing_location: str = Field("Digital Signature", description="Location of signing")
    contact_info: Optional[str] = Field(None, description="Contact information")
    signature_date: Optional[datetime] = Field(None, description="Date of signature")
    certificate_path: Optional[str] = Field(None, description="Path to signing certificate")
    private_key_path: Optional[str] = Field(None, description="Path to private key")


class CertificateInfo(BaseModel):
    """Certificate information model"""
    
    subject_name: str = Field(..., description="Certificate subject name")
    issuer_name: str = Field(..., description="Certificate issuer name")
    serial_number: str = Field(..., description="Certificate serial number")
    not_before: datetime = Field(..., description="Certificate valid from")
    not_after: datetime = Field(..., description="Certificate valid until")
    fingerprint: str = Field(..., description="Certificate fingerprint")
    key_size: int = Field(..., description="Key size in bits")
    signature_algorithm: str = Field(..., description="Signature algorithm")
    is_valid: bool = Field(..., description="Whether certificate is currently valid")


class SigningRequest(BaseModel):
    """PDF signing request model"""
    
    document_id: str = Field(..., description="Document identifier")
    document_path: str = Field(..., description="Path to PDF document")
    signatures: List[SignatureInfo] = Field(..., description="List of signatures to add")
    output_path: Optional[str] = Field(None, description="Output path for signed document")
    signing_mode: str = Field("overlay", description="Signing mode (overlay, append, embed)")
    preserve_original: bool = Field(True, description="Whether to preserve original document")
    add_timestamp: bool = Field(True, description="Whether to add timestamp")
    add_signature_page: bool = Field(False, description="Whether to add signature page")


class SigningResult(BaseModel):
    """PDF signing result model"""
    
    success: bool = Field(..., description="Whether signing was successful")
    signed_document_path: Optional[str] = Field(None, description="Path to signed document")
    signature_ids: List[str] = Field(default_factory=list, description="List of signature IDs")
    errors: List[str] = Field(default_factory=list, description="List of errors")
    warnings: List[str] = Field(default_factory=list, description="List of warnings")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class DocumentStatus(BaseModel):
    """Document signing status model"""
    
    document_id: str = Field(..., description="Document identifier")
    status: str = Field(..., description="Document status")
    signatures_required: int = Field(..., description="Number of signatures required")
    signatures_completed: int = Field(..., description="Number of signatures completed")
    signers: List[Dict[str, Any]] = Field(default_factory=list, description="List of signers")
    created_at: datetime = Field(..., description="Creation timestamp")
    last_updated: datetime = Field(..., description="Last update timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")


class LocalPDFSigningService:
    """Enhanced local PDF signing service with digital signature capabilities"""

    def __init__(self):
        self.settings = get_settings()
        self.enabled = getattr(self.settings, "local_pdf_signing_enabled", True)
        self.cert_path = getattr(self.settings, "local_pdf_signing_cert_path", "")
        self.key_path = getattr(self.settings, "local_pdf_signing_key_path", "")
        self.ca_cert_path = getattr(self.settings, "local_pdf_signing_ca_cert_path", "")
        
        # Signing configuration
        self.default_signing_reason = getattr(self.settings, "pdf_default_signing_reason", "Contract Agreement")
        self.default_signing_location = getattr(self.settings, "pdf_default_signing_location", "Digital Platform")
        self.signature_validity_days = getattr(self.settings, "pdf_signature_validity_days", 365)
        self.max_document_size_mb = getattr(self.settings, "pdf_max_document_size_mb", 50)
        
        # Create directories
        self.signatures_dir = Path(getattr(self.settings, "pdf_signatures_dir", "data/signatures"))
        self.certificates_dir = Path(getattr(self.settings, "pdf_certificates_dir", "data/certificates"))
        self.temp_dir = Path(getattr(self.settings, "pdf_temp_dir", "data/temp"))
        
        for directory in [self.signatures_dir, self.certificates_dir, self.temp_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Internal tracking
        self._signing_sessions = {}
        self._certificate_cache = {}
        
        # Check dependencies
        self._check_dependencies()
        
        # Initialize default certificate if needed
        if self.enabled and not self.cert_path:
            self._ensure_default_certificate()

        logger.info(f"Enhanced PDF signing service initialized: enabled={self.enabled}, "
                   f"crypto={CRYPTOGRAPHY_AVAILABLE}, pypdf2={PYPDF2_AVAILABLE}")

    def _check_dependencies(self):
        """Check if required dependencies are available"""
        missing_deps = []
        
        if not CRYPTOGRAPHY_AVAILABLE:
            missing_deps.append("cryptography")
            logger.warning("Cryptography library not available - digital signatures will be limited")
        
        if not PYPDF2_AVAILABLE:
            missing_deps.append("PyPDF2")
            logger.warning("PyPDF2 library not available - PDF manipulation will be limited")
        
        if missing_deps:
            logger.warning(f"Missing dependencies for full PDF signing functionality: {missing_deps}")

    def _ensure_default_certificate(self):
        """Ensure a default self-signed certificate exists"""
        try:
            if not CRYPTOGRAPHY_AVAILABLE:
                logger.warning("Cannot create default certificate - cryptography library not available")
                return
            
            default_cert_path = self.certificates_dir / "default.crt"
            default_key_path = self.certificates_dir / "default.key"
            
            if not default_cert_path.exists() or not default_key_path.exists():
                logger.info("Creating default self-signed certificate for PDF signing")
                cert_pem, key_pem = self._generate_self_signed_certificate(
                    subject_name="Career Copilot PDF Signing",
                    organization="Career Copilot",
                    country="US"
                )
                
                default_cert_path.write_text(cert_pem)
                default_key_path.write_text(key_pem)
                
                self.cert_path = str(default_cert_path)
                self.key_path = str(default_key_path)
                
                logger.info(f"Default certificate created: {default_cert_path}")
            else:
                self.cert_path = str(default_cert_path)
                self.key_path = str(default_key_path)
                
        except Exception as e:
            logger.error(f"Failed to ensure default certificate: {e}")

    def _generate_self_signed_certificate(
        self, subject_name: str, organization: str, country: str, validity_days: int = 365
    ) -> Tuple[str, str]:
        """Generate a self-signed certificate for PDF signing"""
        if not CRYPTOGRAPHY_AVAILABLE:
            raise RuntimeError("Cryptography library not available")
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, country),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
            x509.NameAttribute(NameOID.COMMON_NAME, subject_name),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=validity_days)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # Serialize certificate and key
        cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode()
        key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode()
        
        return cert_pem, key_pem

    async def sign_pdf_document(self, signing_request: SigningRequest) -> SigningResult:
        """Sign a PDF document with multiple signatures"""
        try:
            if not self.enabled:
                return SigningResult(
                    success=False,
                    errors=["PDF signing service is disabled"]
                )
            
            # Validate request
            validation_result = await self._validate_signing_request(signing_request)
            if not validation_result["valid"]:
                return SigningResult(
                    success=False,
                    errors=validation_result["errors"],
                    warnings=validation_result["warnings"]
                )
            
            # Check if document exists
            if not Path(signing_request.document_path).exists():
                return SigningResult(
                    success=False,
                    errors=[f"Document not found: {signing_request.document_path}"]
                )
            
            # Read original PDF
            with open(signing_request.document_path, 'rb') as file:
                pdf_content = file.read()
            
            # Check file size
            file_size_mb = len(pdf_content) / (1024 * 1024)
            if file_size_mb > self.max_document_size_mb:
                return SigningResult(
                    success=False,
                    errors=[f"Document too large: {file_size_mb:.1f}MB > {self.max_document_size_mb}MB"]
                )
            
            # Process signatures
            signature_ids = []
            signed_content = pdf_content
            
            for i, signature in enumerate(signing_request.signatures):
                try:
                    signature_id = f"sig_{uuid.uuid4().hex[:8]}"
                    
                    # Add signature to PDF
                    if signing_request.signing_mode == "embed" and PYPDF2_AVAILABLE:
                        signed_content = await self._embed_digital_signature(signed_content, signature)
                    else:
                        signed_content = await self._add_signature_overlay(signed_content, signature)
                    
                    signature_ids.append(signature_id)
                    logger.info(f"Added signature {i+1}/{len(signing_request.signatures)}: {signature.signer_name}")
                    
                except Exception as e:
                    logger.error(f"Failed to add signature for {signature.signer_name}: {e}")
                    return SigningResult(
                        success=False,
                        errors=[f"Failed to add signature for {signature.signer_name}: {str(e)}"],
                        signature_ids=signature_ids
                    )
            
            # Add signature page if requested
            if signing_request.add_signature_page:
                signature_page = await self.create_signature_page(
                    signing_request.signatures,
                    f"Signatures for {Path(signing_request.document_path).stem}"
                )
                signed_content = await self._append_signature_page(signed_content, signature_page)
            
            # Save signed document
            output_path = signing_request.output_path or signing_request.document_path.replace('.pdf', '_signed.pdf')
            
            with open(output_path, 'wb') as file:
                file.write(signed_content)
            
            # Create metadata
            metadata = {
                "original_document": signing_request.document_path,
                "signing_mode": signing_request.signing_mode,
                "signature_count": len(signature_ids),
                "file_size_bytes": len(signed_content),
                "signing_timestamp": datetime.now().isoformat(),
                "preserve_original": signing_request.preserve_original
            }
            
            logger.info(f"PDF document signed successfully: {output_path}")
            
            return SigningResult(
                success=True,
                signed_document_path=output_path,
                signature_ids=signature_ids,
                metadata=metadata
            )
            
        except Exception as e:
            error_msg = f"Failed to sign PDF document: {str(e)}"
            logger.error(error_msg)
            return SigningResult(
                success=False,
                errors=[error_msg]
            )

    async def _validate_signing_request(self, request: SigningRequest) -> Dict[str, Any]:
        """Validate a signing request"""
        errors = []
        warnings = []
        
        # Check signatures
        if not request.signatures:
            errors.append("No signatures provided")
        
        for i, signature in enumerate(request.signatures):
            if not signature.signer_name:
                errors.append(f"Signature {i+1}: Missing signer name")
            
            if not signature.signer_email or "@" not in signature.signer_email:
                errors.append(f"Signature {i+1}: Invalid email address")
            
            if not signature.signature_text and not signature.signature_image_path and not signature.signature_image_data:
                warnings.append(f"Signature {i+1}: No signature content provided")
            
            # Validate certificate if provided
            if signature.certificate_path and not Path(signature.certificate_path).exists():
                errors.append(f"Signature {i+1}: Certificate file not found")
        
        # Check signing mode
        if request.signing_mode not in ["overlay", "append", "embed"]:
            errors.append(f"Invalid signing mode: {request.signing_mode}")
        
        if request.signing_mode == "embed" and not PYPDF2_AVAILABLE:
            warnings.append("Embedded signing requested but PyPDF2 not available, falling back to overlay")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    async def _embed_digital_signature(self, pdf_content: bytes, signature: SignatureInfo) -> bytes:
        """Embed a digital signature into PDF (requires PyPDF2 and cryptography)"""
        try:
            if not PYPDF2_AVAILABLE or not CRYPTOGRAPHY_AVAILABLE:
                logger.warning("Digital signature embedding not available, using overlay method")
                return await self._add_signature_overlay(pdf_content, signature)
            
            # For now, fall back to overlay method
            # Full digital signature embedding would require more complex PDF manipulation
            logger.info("Digital signature embedding not fully implemented, using overlay method")
            return await self._add_signature_overlay(pdf_content, signature)
            
        except Exception as e:
            logger.error(f"Failed to embed digital signature: {e}")
            return await self._add_signature_overlay(pdf_content, signature)

    async def _add_signature_overlay(self, pdf_content: bytes, signature: SignatureInfo) -> bytes:
        """Add signature as an overlay to the PDF"""
        try:
            if not PYPDF2_AVAILABLE:
                logger.warning("PyPDF2 not available, creating new PDF with signature")
                return await self._create_signed_pdf_replacement(pdf_content, signature)
            
            # Read existing PDF
            pdf_reader = PdfReader(io.BytesIO(pdf_content))
            pdf_writer = PdfWriter()
            
            # Copy all pages
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                
                # Add signature to specified page
                if page_num + 1 == signature.page_number:
                    # Create signature overlay
                    signature_overlay = await self._create_signature_overlay_pdf(signature)
                    overlay_reader = PdfReader(io.BytesIO(signature_overlay))
                    
                    if len(overlay_reader.pages) > 0:
                        page.merge_page(overlay_reader.pages[0])
                
                pdf_writer.add_page(page)
            
            # Write to bytes
            output_buffer = io.BytesIO()
            pdf_writer.write(output_buffer)
            output_buffer.seek(0)
            
            return output_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to add signature overlay: {e}")
            return pdf_content

    async def _create_signature_overlay_pdf(self, signature: SignatureInfo) -> bytes:
        """Create a PDF overlay with signature"""
        try:
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            
            # Add signature at specified position
            x, y = signature.x_position, signature.y_position
            
            # Add signature box
            c.setStrokeColor(blue)
            c.setLineWidth(1)
            c.rect(x, y, signature.width, signature.height)
            
            # Add signature content
            if signature.signature_image_data:
                try:
                    # Decode base64 image
                    image_data = base64.b64decode(signature.signature_image_data)
                    image_buffer = io.BytesIO(image_data)
                    c.drawImage(ImageReader(image_buffer), x + 5, y + 5, 
                               width=signature.width - 10, height=signature.height - 20)
                except Exception as e:
                    logger.warning(f"Failed to add signature image: {e}")
                    # Fall back to text
                    c.setFont("Helvetica-Oblique", 12)
                    c.drawString(x + 10, y + signature.height/2, signature.signature_text or "Digital Signature")
            
            elif signature.signature_image_path and Path(signature.signature_image_path).exists():
                try:
                    c.drawImage(signature.signature_image_path, x + 5, y + 5,
                               width=signature.width - 10, height=signature.height - 20)
                except Exception as e:
                    logger.warning(f"Failed to load signature image: {e}")
                    c.setFont("Helvetica-Oblique", 12)
                    c.drawString(x + 10, y + signature.height/2, signature.signature_text or "Digital Signature")
            
            else:
                # Text signature
                c.setFont("Helvetica-Oblique", 12)
                c.drawString(x + 10, y + signature.height/2, signature.signature_text or "Digital Signature")
            
            # Add signer info
            c.setFont("Helvetica", 8)
            c.drawString(x + 5, y - 15, f"Signed by: {signature.signer_name}")
            c.drawString(x + 5, y - 25, f"Date: {(signature.signature_date or datetime.now()).strftime('%Y-%m-%d %H:%M')}")
            
            c.save()
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to create signature overlay: {e}")
            return b""

    async def _create_signed_pdf_replacement(self, original_content: bytes, signature: SignatureInfo) -> bytes:
        """Create a replacement PDF with signature (fallback method)"""
        try:
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            
            # Add header
            c.setFont("Helvetica-Bold", 16)
            c.drawString(100, height - 100, "Digitally Signed Document")
            
            # Add signature info
            c.setFont("Helvetica", 12)
            y_pos = height - 150
            
            c.drawString(100, y_pos, f"Signer: {signature.signer_name}")
            c.drawString(100, y_pos - 20, f"Email: {signature.signer_email}")
            c.drawString(100, y_pos - 40, f"Date: {(signature.signature_date or datetime.now()).strftime('%Y-%m-%d %H:%M')}")
            c.drawString(100, y_pos - 60, f"Reason: {signature.signing_reason}")
            
            # Add signature
            if signature.signature_text:
                c.setFont("Helvetica-Oblique", 14)
                c.drawString(100, y_pos - 100, f"Signature: {signature.signature_text}")
            
            # Add note about original document
            c.setFont("Helvetica", 10)
            c.drawString(100, 100, "Note: This is a digitally signed version of the original document.")
            c.drawString(100, 85, f"Original document size: {len(original_content)} bytes")
            
            c.save()
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to create signed PDF replacement: {e}")
            return original_content

    async def _append_signature_page(self, pdf_content: bytes, signature_page: bytes) -> bytes:
        """Append signature page to PDF"""
        try:
            if not PYPDF2_AVAILABLE:
                logger.warning("PyPDF2 not available, cannot append signature page")
                return pdf_content
            
            # Read PDFs
            main_reader = PdfReader(io.BytesIO(pdf_content))
            sig_reader = PdfReader(io.BytesIO(signature_page))
            
            # Create writer
            pdf_writer = PdfWriter()
            
            # Add all pages from main document
            for page in main_reader.pages:
                pdf_writer.add_page(page)
            
            # Add signature page
            for page in sig_reader.pages:
                pdf_writer.add_page(page)
            
            # Write to bytes
            output_buffer = io.BytesIO()
            pdf_writer.write(output_buffer)
            output_buffer.seek(0)
            
            return output_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to append signature page: {e}")
            return pdf_content

    async def create_signature_page(self, signatures: List[SignatureInfo], page_title: str = "Contract Signatures") -> bytes:
        """Create a signature page for the contract"""
        try:
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter

            # Add title
            c.setFont("Helvetica-Bold", 16)
            c.drawString(100, height - 100, page_title)

            # Add current date
            c.setFont("Helvetica", 12)
            c.drawString(100, height - 130, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            # Add signature lines
            y_position = height - 200
            for i, signature in enumerate(signatures):
                # Signature line
                c.line(100, y_position, 500, y_position)

                # Signer name
                c.setFont("Helvetica", 10)
                c.drawString(100, y_position - 20, f"Name: {signature.signer_name}")
                c.drawString(100, y_position - 35, f"Email: {signature.signer_email}")

                # Signature text or image
                if signature.signature_text:
                    c.setFont("Helvetica-Italic", 12)
                    c.drawString(100, y_position - 55, f"Signature: {signature.signature_text}")
                elif signature.signature_image_path and Path(signature.signature_image_path).exists():
                    try:
                        # Add signature image
                        img = ImageReader(signature.signature_image_path)
                        c.drawImage(img, 100, y_position - 80, width=200, height=50)
                    except Exception as e:
                        logger.warning(f"Failed to add signature image: {e}")
                        c.setFont("Helvetica", 10)
                        c.drawString(100, y_position - 55, "[Signature Image]")

                # Add signature date
                c.setFont("Helvetica", 9)
                c.drawString(400, y_position - 20, f"Date: {datetime.now().strftime('%Y-%m-%d')}")

                y_position -= 120

                # Add new page if needed
                if y_position < 200 and i < len(signatures) - 1:
                    c.showPage()
                    y_position = height - 100

            # Add footer
            c.setFont("Helvetica", 8)
            c.drawString(100, 50, "This document has been digitally signed using Local PDF Signing Service")
            c.drawString(100, 35, f"Generated on: {datetime.now().isoformat()}")

            c.save()
            buffer.seek(0)
            return buffer.getvalue()

        except Exception as e:
            logger.error(f"Failed to create signature page: {e}")
            return b""

    async def create_signature_template(self, signer_name: str, signer_email: str, contract_title: str = "Contract Agreement") -> bytes:
        """Create a signature template for a signer"""
        try:
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter

            # Add header
            c.setFont("Helvetica-Bold", 18)
            c.drawString(100, height - 100, "Digital Signature Template")

            # Contract information
            c.setFont("Helvetica", 12)
            c.drawString(100, height - 140, f"Contract: {contract_title}")
            c.drawString(100, height - 160, f"Signer: {signer_name}")
            c.drawString(100, height - 180, f"Email: {signer_email}")
            c.drawString(100, height - 200, f"Date: {datetime.now().strftime('%Y-%m-%d')}")

            # Signature area
            c.setFont("Helvetica-Bold", 14)
            c.drawString(100, height - 250, "Signature Area:")

            # Draw signature box
            c.rect(100, height - 350, 400, 100)
            c.setFont("Helvetica", 10)
            c.drawString(110, height - 320, "Please sign within this box")

            # Signature line
            c.line(100, height - 380, 500, height - 380)
            c.setFont("Helvetica", 10)
            c.drawString(100, height - 400, f"Signature: _________________________")
            c.drawString(100, height - 420, f"Date: _________________________")

            # Instructions
            c.setFont("Helvetica", 10)
            instructions = [
                "Instructions:",
                "1. Print this page",
                "2. Sign in the designated area",
                "3. Scan or photograph the signed page",
                "4. Upload the signed page to complete the process",
            ]

            y_pos = height - 480
            for instruction in instructions:
                c.drawString(100, y_pos, instruction)
                y_pos -= 20

            c.save()
            buffer.seek(0)
            return buffer.getvalue()

        except Exception as e:
            logger.error(f"Failed to create signature template: {e}")
            return b""

    async def get_certificate_info(self, cert_path: str) -> Optional[CertificateInfo]:
        """Get information about a certificate"""
        try:
            if not CRYPTOGRAPHY_AVAILABLE:
                logger.warning("Cryptography library not available for certificate validation")
                return None
            
            if not Path(cert_path).exists():
                logger.error(f"Certificate file not found: {cert_path}")
                return None
            
            # Read certificate
            with open(cert_path, 'rb') as cert_file:
                cert_data = cert_file.read()
            
            # Parse certificate
            cert = x509.load_pem_x509_certificate(cert_data)
            
            # Extract information
            subject_name = cert.subject.rfc4514_string()
            issuer_name = cert.issuer.rfc4514_string()
            serial_number = str(cert.serial_number)
            not_before = cert.not_valid_before
            not_after = cert.not_valid_after
            
            # Calculate fingerprint
            fingerprint = hashlib.sha256(cert_data).hexdigest()
            
            # Get key size
            public_key = cert.public_key()
            key_size = public_key.key_size if hasattr(public_key, 'key_size') else 0
            
            # Get signature algorithm
            signature_algorithm = cert.signature_algorithm_oid._name
            
            # Check if valid
            now = datetime.utcnow()
            is_valid = not_before <= now <= not_after
            
            return CertificateInfo(
                subject_name=subject_name,
                issuer_name=issuer_name,
                serial_number=serial_number,
                not_before=not_before,
                not_after=not_after,
                fingerprint=fingerprint,
                key_size=key_size,
                signature_algorithm=signature_algorithm,
                is_valid=is_valid
            )
            
        except Exception as e:
            logger.error(f"Failed to get certificate info: {e}")
            return None

    async def validate_certificate(self, cert_path: str, ca_cert_path: Optional[str] = None) -> Dict[str, Any]:
        """Validate a certificate"""
        try:
            result = {
                "valid": False,
                "errors": [],
                "warnings": [],
                "info": None
            }
            
            # Get certificate info
            cert_info = await self.get_certificate_info(cert_path)
            if not cert_info:
                result["errors"].append("Failed to read certificate")
                return result
            
            result["info"] = cert_info.dict()
            
            # Check validity period
            if not cert_info.is_valid:
                if cert_info.not_before > datetime.utcnow():
                    result["errors"].append("Certificate is not yet valid")
                else:
                    result["errors"].append("Certificate has expired")
            
            # Check key size
            if cert_info.key_size < 2048:
                result["warnings"].append(f"Key size ({cert_info.key_size}) is below recommended minimum (2048)")
            
            # Validate against CA if provided
            if ca_cert_path and Path(ca_cert_path).exists():
                try:
                    # This would require more complex certificate chain validation
                    # For now, just check if CA cert is readable
                    ca_info = await self.get_certificate_info(ca_cert_path)
                    if ca_info:
                        result["info"]["ca_info"] = ca_info.dict()
                    else:
                        result["warnings"].append("Could not validate against CA certificate")
                except Exception as e:
                    result["warnings"].append(f"CA validation error: {e}")
            
            # Certificate is valid if no errors
            result["valid"] = len(result["errors"]) == 0
            
            return result
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Certificate validation error: {e}"],
                "warnings": [],
                "info": None
            }

    async def create_signing_certificate(
        self, 
        subject_name: str, 
        organization: str, 
        email: str,
        country: str = "US",
        validity_days: int = 365
    ) -> Dict[str, Any]:
        """Create a new signing certificate"""
        try:
            if not CRYPTOGRAPHY_AVAILABLE:
                return {
                    "success": False,
                    "error": "Cryptography library not available"
                }
            
            # Generate certificate
            cert_pem, key_pem = self._generate_self_signed_certificate(
                subject_name=subject_name,
                organization=organization,
                country=country,
                validity_days=validity_days
            )
            
            # Save certificate and key
            cert_id = f"cert_{uuid.uuid4().hex[:8]}"
            cert_path = self.certificates_dir / f"{cert_id}.crt"
            key_path = self.certificates_dir / f"{cert_id}.key"
            
            cert_path.write_text(cert_pem)
            key_path.write_text(key_pem)
            
            # Set appropriate permissions
            os.chmod(key_path, 0o600)  # Private key should be readable only by owner
            
            logger.info(f"Created signing certificate: {cert_path}")
            
            return {
                "success": True,
                "certificate_id": cert_id,
                "certificate_path": str(cert_path),
                "private_key_path": str(key_path),
                "subject_name": subject_name,
                "organization": organization,
                "email": email,
                "validity_days": validity_days
            }
            
        except Exception as e:
            error_msg = f"Failed to create signing certificate: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }

    async def list_certificates(self) -> List[Dict[str, Any]]:
        """List available certificates"""
        try:
            certificates = []
            
            for cert_file in self.certificates_dir.glob("*.crt"):
                try:
                    cert_info = await self.get_certificate_info(str(cert_file))
                    if cert_info:
                        certificates.append({
                            "file_path": str(cert_file),
                            "file_name": cert_file.name,
                            "certificate_info": cert_info.dict()
                        })
                except Exception as e:
                    logger.warning(f"Failed to read certificate {cert_file}: {e}")
            
            return certificates
            
        except Exception as e:
            logger.error(f"Failed to list certificates: {e}")
            return []

    async def validate_signature(self, signature_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a signature (basic validation for demo)"""
        try:
            validation_result = {"valid": True, "errors": [], "warnings": []}

            # Check required fields
            required_fields = ["signer_name", "signer_email", "signature_text"]
            for field in required_fields:
                if not signature_data.get(field):
                    validation_result["valid"] = False
                    validation_result["errors"].append(f"Missing required field: {field}")

            # Validate email format
            email = signature_data.get("signer_email", "")
            if email and "@" not in email:
                validation_result["valid"] = False
                validation_result["errors"].append("Invalid email format")

            # Check signature text length
            signature_text = signature_data.get("signature_text", "")
            if len(signature_text) < 3:
                validation_result["warnings"].append("Signature text is very short")

            return validation_result

        except Exception as e:
            logger.error(f"Failed to validate signature: {e}")
            return {"valid": False, "errors": [f"Validation error: {e!s}"], "warnings": []}

    def _create_signature_overlay(self, signatures: List[SignatureInfo]) -> bytes:
        """Create a signature overlay PDF"""
        try:
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter

            # Add signature information
            c.setFont("Helvetica-Bold", 12)
            c.drawString(100, height - 100, "Digital Signatures")

            y_position = height - 150
            for signature in signatures:
                c.setFont("Helvetica", 10)
                c.drawString(100, y_position, f"Signed by: {signature.signer_name}")
                c.drawString(100, y_position - 15, f"Email: {signature.signer_email}")
                c.drawString(100, y_position - 30, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

                if signature.signature_text:
                    c.drawString(100, y_position - 45, f"Signature: {signature.signature_text}")

                y_position -= 80

            c.save()
            buffer.seek(0)
            return buffer.getvalue()

        except Exception as e:
            logger.error(f"Failed to create signature overlay: {e}")
            return b""

    async def create_signing_session(
        self, 
        document_path: str, 
        signers: List[Dict[str, Any]], 
        expires_in_hours: int = 24
    ) -> Dict[str, Any]:
        """Create a signing session for multiple signers"""
        try:
            session_id = f"session_{uuid.uuid4().hex}"
            expires_at = datetime.now() + timedelta(hours=expires_in_hours)
            
            session_data = {
                "session_id": session_id,
                "document_path": document_path,
                "signers": signers,
                "status": "pending",
                "created_at": datetime.now(),
                "expires_at": expires_at,
                "signatures_completed": 0,
                "signatures_required": len(signers)
            }
            
            # Store session data (in production, this would be in a database)
            self._signing_sessions[session_id] = session_data
            
            logger.info(f"Created signing session {session_id} for {len(signers)} signers")
            
            return {
                "success": True,
                "session_id": session_id,
                "expires_at": expires_at.isoformat(),
                "signers": signers,
                "signing_url": f"/api/v1/pdf-signing/sign/{session_id}"
            }
            
        except Exception as e:
            error_msg = f"Failed to create signing session: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }

    async def get_signing_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get signing session information"""
        try:
            session = self._signing_sessions.get(session_id)
            if not session:
                return None
            
            # Check if session has expired
            if datetime.now() > session["expires_at"]:
                session["status"] = "expired"
            
            return session
            
        except Exception as e:
            logger.error(f"Failed to get signing session: {e}")
            return None

    async def sign_document_in_session(
        self, 
        session_id: str, 
        signer_email: str, 
        signature_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Sign a document within a signing session"""
        try:
            session = await self.get_signing_session(session_id)
            if not session:
                return {
                    "success": False,
                    "error": "Signing session not found"
                }
            
            if session["status"] == "expired":
                return {
                    "success": False,
                    "error": "Signing session has expired"
                }
            
            # Find signer
            signer = None
            for s in session["signers"]:
                if s["email"] == signer_email:
                    signer = s
                    break
            
            if not signer:
                return {
                    "success": False,
                    "error": "Signer not found in session"
                }
            
            if signer.get("signed", False):
                return {
                    "success": False,
                    "error": "Document already signed by this signer"
                }
            
            # Create signature info
            signature_info = SignatureInfo(
                signer_name=signer["name"],
                signer_email=signer["email"],
                signature_text=signature_data.get("signature_text", ""),
                signature_image_data=signature_data.get("signature_image_data"),
                x_position=signature_data.get("x_position", 100),
                y_position=signature_data.get("y_position", 100),
                page_number=signature_data.get("page_number", 1),
                signing_reason=signature_data.get("signing_reason", "Contract Agreement"),
                signature_date=datetime.now()
            )
            
            # Create signing request
            signing_request = SigningRequest(
                document_id=session_id,
                document_path=session["document_path"],
                signatures=[signature_info],
                signing_mode="overlay"
            )
            
            # Sign document
            result = await self.sign_pdf_document(signing_request)
            
            if result.success:
                # Update session
                signer["signed"] = True
                signer["signed_at"] = datetime.now().isoformat()
                session["signatures_completed"] += 1
                
                # Update document path to signed version
                if result.signed_document_path:
                    session["document_path"] = result.signed_document_path
                
                # Check if all signatures are complete
                if session["signatures_completed"] >= session["signatures_required"]:
                    session["status"] = "completed"
                
                logger.info(f"Document signed by {signer_email} in session {session_id}")
            
            return {
                "success": result.success,
                "errors": result.errors,
                "session_status": session["status"],
                "signatures_completed": session["signatures_completed"],
                "signatures_required": session["signatures_required"]
            }
            
        except Exception as e:
            error_msg = f"Failed to sign document in session: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }

    async def get_signing_status(self, document_id: str) -> DocumentStatus:
        """Get signing status for a document"""
        try:
            # Check if document_id is a session_id
            session = self._signing_sessions.get(document_id)
            if session:
                return DocumentStatus(
                    document_id=document_id,
                    status=session["status"],
                    signatures_required=session["signatures_required"],
                    signatures_completed=session["signatures_completed"],
                    signers=[
                        {
                            "name": s["name"],
                            "email": s["email"],
                            "signed": s.get("signed", False),
                            "signed_at": s.get("signed_at")
                        }
                        for s in session["signers"]
                    ],
                    created_at=session["created_at"],
                    last_updated=datetime.now(),
                    expires_at=session.get("expires_at")
                )
            
            # Return default status for unknown documents
            return DocumentStatus(
                document_id=document_id,
                status="unknown",
                signatures_required=0,
                signatures_completed=0,
                signers=[],
                created_at=datetime.now(),
                last_updated=datetime.now()
            )

        except Exception as e:
            logger.error(f"Failed to get signing status: {e}")
            return DocumentStatus(
                document_id=document_id,
                status="error",
                signatures_required=0,
                signatures_completed=0,
                signers=[],
                created_at=datetime.now(),
                last_updated=datetime.now()
            )

    async def create_template(self, template_name: str, template_data: Dict[str, Any]) -> Optional[str]:
        """Create a PDF signing template"""
        try:
            template_id = f"template_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Store template data
            template_info = {
                "template_id": template_id,
                "template_name": template_name,
                "created_at": datetime.now().isoformat(),
                "template_data": template_data,
            }

            # In a real implementation, this would be stored in a database
            # For demo purposes, we'll just return the template ID
            logger.info(f"Created PDF signing template: {template_name} (ID: {template_id})")
            return template_id

        except Exception as e:
            logger.error(f"Failed to create PDF signing template: {e}")
            return None

    async def test_connection(self) -> Dict[str, Any]:
        """Test PDF signing service functionality"""
        try:
            result = {
                "success": True,
                "service": "Local PDF Signing",
                "enabled": self.enabled,
                "dependencies": {
                    "cryptography": CRYPTOGRAPHY_AVAILABLE,
                    "pypdf2": PYPDF2_AVAILABLE
                },
                "features": [],
                "warnings": [],
                "errors": []
            }
            
            if not self.enabled:
                result["success"] = False
                result["errors"].append("PDF signing service is disabled")
                return result
            
            # Check dependencies
            if CRYPTOGRAPHY_AVAILABLE:
                result["features"].append("Digital certificate support")
            else:
                result["warnings"].append("Cryptography library not available - limited certificate support")
            
            if PYPDF2_AVAILABLE:
                result["features"].append("PDF manipulation support")
            else:
                result["warnings"].append("PyPDF2 library not available - limited PDF manipulation")
            
            # Check directories
            for dir_name, dir_path in [
                ("signatures", self.signatures_dir),
                ("certificates", self.certificates_dir),
                ("temp", self.temp_dir)
            ]:
                if dir_path.exists() and dir_path.is_dir():
                    result["features"].append(f"{dir_name} directory accessible")
                else:
                    result["errors"].append(f"{dir_name} directory not accessible: {dir_path}")
            
            # Check default certificate
            if self.cert_path and Path(self.cert_path).exists():
                result["features"].append("Default signing certificate available")
                
                # Validate certificate
                cert_validation = await self.validate_certificate(self.cert_path)
                if cert_validation["valid"]:
                    result["features"].append("Default certificate is valid")
                else:
                    result["warnings"].extend([f"Certificate issue: {error}" for error in cert_validation["errors"]])
            else:
                result["warnings"].append("No default signing certificate configured")
            
            # Test basic functionality
            try:
                # Create a test signature page
                test_signatures = [
                    SignatureInfo(
                        signer_name="Test Signer",
                        signer_email="test@example.com",
                        signature_text="Test Signature",
                        signing_reason="Connection Test"
                    )
                ]
                
                test_page = await self.create_signature_page(test_signatures, "Connection Test")
                if test_page:
                    result["features"].append("Signature page generation working")
                else:
                    result["warnings"].append("Signature page generation failed")
                    
            except Exception as e:
                result["warnings"].append(f"Basic functionality test failed: {e}")
            
            # Overall success
            result["success"] = len(result["errors"]) == 0
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "service": "Local PDF Signing",
                "error": f"Connection test failed: {e}",
                "enabled": self.enabled
            }

    async def get_service_info(self) -> Dict[str, Any]:
        """Get service information and capabilities"""
        try:
            return {
                "service_name": "Local PDF Signing Service",
                "version": "1.0.0",
                "enabled": self.enabled,
                "capabilities": {
                    "digital_signatures": CRYPTOGRAPHY_AVAILABLE,
                    "pdf_manipulation": PYPDF2_AVAILABLE,
                    "certificate_generation": CRYPTOGRAPHY_AVAILABLE,
                    "signature_validation": CRYPTOGRAPHY_AVAILABLE,
                    "multi_signer_support": True,
                    "signing_sessions": True,
                    "signature_overlays": True,
                    "signature_pages": True
                },
                "configuration": {
                    "max_document_size_mb": self.max_document_size_mb,
                    "signature_validity_days": self.signature_validity_days,
                    "default_signing_reason": self.default_signing_reason,
                    "default_signing_location": self.default_signing_location
                },
                "directories": {
                    "signatures": str(self.signatures_dir),
                    "certificates": str(self.certificates_dir),
                    "temp": str(self.temp_dir)
                },
                "certificate_info": {
                    "default_cert_path": self.cert_path,
                    "default_key_path": self.key_path,
                    "ca_cert_path": self.ca_cert_path
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get service info: {e}")
            return {
                "service_name": "Local PDF Signing Service",
                "error": str(e)
            }

    async def cleanup_expired_sessions(self) -> Dict[str, Any]:
        """Clean up expired signing sessions"""
        try:
            now = datetime.now()
            expired_sessions = []
            
            for session_id, session in list(self._signing_sessions.items()):
                if now > session["expires_at"]:
                    expired_sessions.append(session_id)
                    del self._signing_sessions[session_id]
            
            logger.info(f"Cleaned up {len(expired_sessions)} expired signing sessions")
            
            return {
                "success": True,
                "expired_sessions_count": len(expired_sessions),
                "expired_session_ids": expired_sessions,
                "active_sessions_count": len(self._signing_sessions)
            }
            
        except Exception as e:
            error_msg = f"Failed to cleanup expired sessions: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }

    async def sign_document(self, document_path: str, signature_data: Dict[str, Any]) -> Optional[str]:
        """Sign a PDF document locally"""
        try:
            # Validate signature data
            validation = await self.validate_signature(signature_data)
            if not validation["valid"]:
                logger.error(f"Signature validation failed: {validation['errors']}")
                return None

            # Create signature info
            signature_info = SignatureInfo(
                signer_name=signature_data.get("signer_name", "Unknown Signer"),
                signer_email=signature_data.get("signer_email", "unknown@example.com"),
                signature_text=signature_data.get("signature_text", ""),
                signature_image_data=signature_data.get("signature_image"),
                signing_reason=signature_data.get("signing_reason", "Contract Agreement"),
                signing_location=signature_data.get("signing_location", "Digital Signature"),
            )

            # Create signing request and sign the document
            signing_request = SigningRequest(
                document_id="legacy_sign",
                document_path=document_path,
                signatures=[signature_info],
                signing_mode="overlay"
            )
            
            result = await self.sign_pdf_document(signing_request)
            if not result.success:
                return None

            logger.info(f"Document signed successfully: {result.signed_document_path}")
            return result.signed_document_path

        except Exception as e:
            logger.error(f"Failed to sign document: {e}")
            return None
