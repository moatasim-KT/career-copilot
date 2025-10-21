"""Enhanced File Upload Component with drag-and-drop, preview, and batch processing."""
import streamlit as st
import hashlib
import magic
import base64
import io
import json
from datetime import datetime
from typing import Optional, Dict, List, Union
from PIL import Image
try:
    import fitz  # PyMuPDF for PDF preview
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
import tempfile
import os

def file_upload_component():
    """Enhanced drag-and-drop file upload component with preview and batch processing."""
    
    # Initialize session state for file management
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []
    if 'upload_progress' not in st.session_state:
        st.session_state.upload_progress = {}
    if 'file_previews' not in st.session_state:
        st.session_state.file_previews = {}
    
    st.subheader("📤 Upload Contract Documents")
    
    # Enhanced upload requirements with better visual design
    with st.expander("ℹ️ Upload Requirements & Guidelines", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📄 Supported File Types:**")
            st.markdown("""
            - **PDF documents** (.pdf) - up to 50MB
            - **Microsoft Word** (.docx) - up to 25MB  
            - **Plain text files** (.txt) - up to 10MB
            """)
            
        with col2:
            st.markdown("**✅ Requirements:**")
            st.markdown("""
            - Files must contain readable text content
            - Password-protected files are not supported
            - Macro-enabled documents are not allowed
            - Files should be under the size limits
            """)
        
        st.markdown("---")
        st.markdown("**💡 Tips for Best Results:**")
        st.markdown("""
        - Use high-quality scanned documents for PDFs
        - Ensure text is selectable (not just images)
        - Remove any sensitive information before upload
        - Use standard fonts and formatting for better analysis
        """)
    
    # Enhanced drag-and-drop styling
    st.markdown("""
    <style>
    .drag-drop-area {
        border: 3px dashed #007bff;
        border-radius: 16px;
        padding: 40px 20px;
        text-align: center;
        background: linear-gradient(135deg, #f8f9ff 0%, #e3f2fd 100%);
        margin: 20px 0;
        transition: all 0.3s ease;
        cursor: pointer;
        position: relative;
        min-height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    .drag-drop-area:hover {
        border-color: #0056b3;
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,123,255,0.2);
    }
    .drag-drop-area.drag-over {
        border-color: #28a745;
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border-style: solid;
    }
    .upload-icon {
        font-size: 64px;
        margin-bottom: 16px;
        color: #007bff;
        animation: bounce 2s infinite;
    }
    .upload-text {
        font-size: 24px;
        font-weight: 700;
        color: #333;
        margin-bottom: 8px;
    }
    .upload-subtext {
        font-size: 16px;
        color: #666;
        margin-bottom: 20px;
    }
    .upload-features {
        font-size: 14px;
        color: #888;
        display: flex;
        gap: 20px;
        justify-content: center;
        flex-wrap: wrap;
    }
    .feature-item {
        display: flex;
        align-items: center;
        gap: 5px;
    }
    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% {
            transform: translateY(0);
        }
        40% {
            transform: translateY(-10px);
        }
        60% {
            transform: translateY(-5px);
        }
    }
    .file-preview-card {
        background: white;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border-left: 4px solid #28a745;
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .file-thumbnail {
        width: 80px;
        height: 80px;
        border-radius: 8px;
        object-fit: cover;
        border: 2px solid #e9ecef;
    }
    .file-info {
        flex: 1;
    }
    .file-name {
        font-weight: 600;
        font-size: 16px;
        color: #333;
        margin-bottom: 4px;
    }
    .file-details {
        font-size: 14px;
        color: #666;
        margin-bottom: 8px;
    }
    .progress-container {
        width: 100%;
        background: #f8f9fa;
        border-radius: 10px;
        overflow: hidden;
        height: 8px;
        margin-top: 8px;
    }
    .progress-bar {
        height: 100%;
        background: linear-gradient(90deg, #007bff, #0056b3);
        transition: width 0.3s ease;
        border-radius: 10px;
    }
    .batch-actions {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 16px;
        margin: 16px 0;
        border: 1px solid #dee2e6;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Enhanced drag-and-drop area
    st.markdown("""
    <div class="drag-drop-area" id="drag-drop-zone">
        <div class="upload-icon">📁</div>
        <div class="upload-text">Drag & Drop Files Here</div>
        <div class="upload-subtext">or click to browse and select multiple files</div>
        <div class="upload-features">
            <div class="feature-item">
                <span>📄</span>
                <span>Multi-file Support</span>
            </div>
            <div class="feature-item">
                <span>👁️</span>
                <span>Live Preview</span>
            </div>
            <div class="feature-item">
                <span>📊</span>
                <span>Progress Tracking</span>
            </div>
            <div class="feature-item">
                <span>🔒</span>
                <span>Secure Upload</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # File uploader with multi-file support
    uploaded_files = st.file_uploader(
        "Choose contract files",
        type=["pdf", "docx", "txt"],
        help="Drag and drop or click to select • Supported formats: PDF, DOCX, TXT • Multi-file upload supported",
        accept_multiple_files=True,
        key="contract_uploader_multi",
        label_visibility="collapsed"
    )
    
    # Process uploaded files
    if uploaded_files:
        return _process_multiple_files(uploaded_files)
    
    # Show existing files if any
    if st.session_state.uploaded_files:
        return _display_uploaded_files()
    
    return None

def _process_uploaded_file(uploaded_file) -> Optional[object]:
    """Process and validate uploaded file with comprehensive checks."""
    
    # Get file information
    file_content = uploaded_file.getvalue()
    file_size_mb = len(file_content) / (1024 * 1024)
    file_size_bytes = len(file_content)
    max_size_mb = 50
    
    # Extract file information
    file_info = _extract_file_info(uploaded_file, file_content)
    
    # Display file information
    _display_file_info(file_info, file_size_mb)
    
    # Perform security validation
    security_results = _perform_security_validation(file_info, file_content, file_size_mb, max_size_mb)
    
    # Display security validation results
    _display_security_validation(security_results, file_info)
    
    # Show file preview if applicable
    _display_file_preview(file_info, file_content, file_size_mb)
    
    # Display processing recommendations
    _display_processing_recommendations(file_info, security_results)
    
    # Upload timestamp
    st.caption(f"Uploaded at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Return file only if all security checks pass
    if security_results['all_checks_passed']:
        return uploaded_file
    else:
        st.error("⚠️ File failed security validation. Please fix the issues above before proceeding.")
        return None

def _extract_file_info(uploaded_file, file_content: bytes) -> Dict:
    """Extract comprehensive file information."""
    
    file_extension = uploaded_file.name.split('.')[-1].lower() if '.' in uploaded_file.name else "unknown"
    file_type = file_extension.upper()
    
    # Calculate file hash
    file_hash = hashlib.sha256(file_content).hexdigest()
    file_hash_short = file_hash[:16]
    
    # Detect MIME type
    try:
        mime_type = magic.from_buffer(file_content, mime=True)
        # Validate the detected MIME type against file extension
        if not _validate_mime_type_consistency(file_extension, mime_type):
            # If magic detection doesn't match extension, use fallback
            mime_type = _detect_mime_type_fallback(file_content, file_extension)
    except Exception as e:
        # Fallback MIME type detection
        mime_type = _detect_mime_type_fallback(file_content, file_extension)
    
    # Detect encoding for text files
    encoding = None
    if file_extension in ['txt', 'csv']:
        encoding = _detect_encoding(file_content)
    
    return {
        'filename': uploaded_file.name,
        'file_extension': file_extension,
        'file_type': file_type,
        'file_size_bytes': len(file_content),
        'file_hash': file_hash,
        'file_hash_short': file_hash_short,
        'mime_type': mime_type,
        'encoding': encoding,
        'content_type': getattr(uploaded_file, 'type', 'unknown')
    }

def _detect_mime_type_fallback(file_content: bytes, file_extension: str) -> str:
    """Enhanced fallback MIME type detection with multiple methods."""
    
    # Method 1: Magic number detection (most reliable)
    magic_mime = _detect_by_magic_numbers(file_content)
    if magic_mime:
        return magic_mime
    
    # Method 2: Content analysis for text files
    if file_extension in ['txt', 'csv']:
        content_mime = _detect_text_content(file_content)
        if content_mime:
            return content_mime
    
    # Method 3: Extension-based fallback
    extension_mime = _get_mime_by_extension(file_extension)
    if extension_mime:
        return extension_mime
    
    return 'application/octet-stream'

def _detect_by_magic_numbers(file_content: bytes) -> Optional[str]:
    """Detect MIME type by file magic numbers (signatures)."""
    if len(file_content) < 4:
        return None
    
    # PDF files - check for PDF signature
    if file_content.startswith(b'%PDF-'):
        return 'application/pdf'
    
    # Microsoft Office Open XML formats (ZIP-based)
    if (file_content.startswith(b'PK\x03\x04') or 
        file_content.startswith(b'PK\x05\x06') or 
        file_content.startswith(b'PK\x07\x08')):
        
        # Look deeper into ZIP structure for Office documents
        if len(file_content) > 2048:
            content_sample = file_content[:2048].lower()
            
            # DOCX detection
            if (b'word/' in content_sample or 
                b'[content_types].xml' in content_sample or
                b'wordprocessingml' in file_content[:4096].lower()):
                return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            
            # Excel detection
            elif b'xl/' in content_sample:
                return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            
            # PowerPoint detection
            elif b'ppt/' in content_sample:
                return 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        
        return 'application/zip'
    
    # Legacy Microsoft Office formats
    if file_content.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):
        return 'application/msword'
    
    # RTF files
    if file_content.startswith(b'{\\rtf'):
        return 'application/rtf'
    
    # HTML files
    content_start = file_content.lstrip().lower()
    if (content_start.startswith(b'<!doctype html') or 
        content_start.startswith(b'<html')):
        return 'text/html'
    
    # XML files
    if file_content.lstrip().startswith(b'<?xml'):
        return 'application/xml'
    
    return None

def _detect_text_content(file_content: bytes) -> Optional[str]:
    """Detect text-based MIME types by content analysis."""
    if not file_content:
        return None
    
    # Sample first 2KB for analysis
    sample_size = min(2048, len(file_content))
    sample = file_content[:sample_size]
    
    # Try to decode as text
    try:
        # Try UTF-8 first
        decoded = sample.decode('utf-8', errors='ignore')
        
        # Calculate ratio of printable characters
        printable_chars = sum(1 for c in decoded if c.isprintable() or c.isspace())
        printable_ratio = printable_chars / len(decoded) if decoded else 0
        
        # If mostly printable characters, it's likely text
        if printable_ratio > 0.85:
            decoded_lower = decoded.lower()
            
            # Check for HTML content
            if any(tag in decoded_lower for tag in ['<html', '<head', '<body', '<!doctype']):
                return 'text/html'
            
            # Check for XML content
            if decoded_lower.strip().startswith('<?xml'):
                return 'application/xml'
            
            # Check for CSV content
            lines = decoded.split('\n')[:5]
            if len(lines) > 1:
                comma_lines = [line for line in lines if line.strip() and ',' in line]
                if len(comma_lines) >= len(lines) // 2:  # At least half the lines have commas
                    avg_commas = sum(line.count(',') for line in comma_lines) / len(comma_lines)
                    if avg_commas >= 2:  # Average of 2+ commas per line
                        return 'text/csv'
            
            # Default to plain text
            return 'text/plain'
    
    except UnicodeDecodeError:
        # Try other common encodings
        for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
            try:
                decoded = sample.decode(encoding, errors='ignore')
                printable_chars = sum(1 for c in decoded if c.isprintable() or c.isspace())
                printable_ratio = printable_chars / len(decoded) if decoded else 0
                
                if printable_ratio > 0.85:
                    return 'text/plain'
            except UnicodeDecodeError:
                continue
    
    return None

def _get_mime_by_extension(file_extension: str) -> Optional[str]:
    """Get MIME type based on file extension."""
    mime_types = {
        'pdf': 'application/pdf',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'doc': 'application/msword',
        'txt': 'text/plain',
        'csv': 'text/csv',
        'html': 'text/html',
        'htm': 'text/html',
        'xml': 'application/xml',
        'rtf': 'application/rtf',
        'zip': 'application/zip'
    }
    
    return mime_types.get(file_extension.lower())

def _validate_mime_type_consistency(file_extension: str, mime_type: str) -> bool:
    """Validate that MIME type matches file extension."""
    # Define expected MIME types for each extension
    expected_mime_types = {
        'pdf': ['application/pdf'],
        'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
        'doc': ['application/msword'],
        'txt': ['text/plain'],
        'csv': ['text/csv', 'text/plain']
    }
    
    if file_extension in expected_mime_types:
        return mime_type in expected_mime_types[file_extension]
    
    return True  # Allow unknown extensions

def _detect_encoding(file_content: bytes) -> str:
    """Detect text encoding."""
    try:
        import chardet
        result = chardet.detect(file_content)
        return result.get('encoding', 'utf-8')
    except ImportError:
        # Fallback encoding detection
        encodings = ['utf-8', 'latin-1', 'cp1252']
        for encoding in encodings:
            try:
                file_content.decode(encoding)
                return encoding
            except UnicodeDecodeError:
                continue
        return 'unknown'

def _display_file_info(file_info: Dict, file_size_mb: float):
    """Display file information in a structured format."""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("File Name", file_info['filename'])
        st.metric("File Hash", file_info['file_hash_short'])
    
    with col2:
        st.metric("File Size", f"{file_size_mb:.2f} MB")
        st.metric("File Type", file_info['file_type'])
    
    with col3:
        st.metric("MIME Type", file_info['mime_type'])
        if file_info['encoding']:
            st.metric("Encoding", file_info['encoding'])

def _perform_security_validation(file_info: Dict, file_content: bytes, file_size_mb: float, max_size_mb: float) -> Dict:
    """Perform comprehensive security validation with enhanced checks."""
    
    checks = {}
    validation_messages = {}
    
    # File size validation
    checks['size_valid'] = file_size_mb <= max_size_mb
    if not checks['size_valid']:
        validation_messages['size_valid'] = f"File size ({file_size_mb:.2f} MB) exceeds maximum limit ({max_size_mb} MB)"
    
    # File extension validation
    valid_extensions = ['pdf', 'docx', 'txt']  # Removed 'doc' as it's not supported
    checks['extension_valid'] = file_info['file_extension'] in valid_extensions
    if not checks['extension_valid']:
        if file_info['file_extension'] == 'doc':
            validation_messages['extension_valid'] = "Legacy Word documents (.doc) are not supported. Please convert to .docx format."
        else:
            validation_messages['extension_valid'] = f"File extension '.{file_info['file_extension']}' is not supported. Supported types: {', '.join(valid_extensions)}"
    
    # File not empty
    checks['not_empty'] = len(file_content) > 0
    if not checks['not_empty']:
        validation_messages['not_empty'] = "File appears to be empty"
    
    # Enhanced MIME type validation
    mime_validation = _validate_mime_type_comprehensive(file_info, file_content)
    checks['mime_type_valid'] = mime_validation['valid']
    if not checks['mime_type_valid']:
        validation_messages['mime_type_valid'] = mime_validation['message']
    
    # Filename validation
    filename_validation = _validate_filename_comprehensive(file_info['filename'])
    checks['filename_safe'] = filename_validation['valid']
    if not checks['filename_safe']:
        validation_messages['filename_safe'] = filename_validation['message']
    
    # Content validation (enhanced)
    content_validation = _validate_content_comprehensive(file_content, file_info['file_extension'])
    checks['no_suspicious_patterns'] = content_validation['valid']
    if not checks['no_suspicious_patterns']:
        validation_messages['no_suspicious_patterns'] = content_validation['message']
    
    # File integrity check
    integrity_check = _check_file_integrity(file_content, file_info['file_extension'])
    checks['file_integrity'] = integrity_check['valid']
    if not checks['file_integrity']:
        validation_messages['file_integrity'] = integrity_check['message']
    
    # Overall validation
    checks['all_checks_passed'] = all(checks.values())
    checks['validation_messages'] = validation_messages
    
    return checks

def _validate_mime_type_comprehensive(file_info: Dict, file_content: bytes) -> Dict:
    """Comprehensive MIME type validation with detailed error messages."""
    
    detected_mime = file_info['mime_type']
    file_extension = file_info['file_extension']
    
    # Expected MIME types for each extension
    expected_mime_types = {
        'pdf': ['application/pdf'],
        'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
        'txt': ['text/plain', 'text/csv'],  # Allow CSV as text variant
        'csv': ['text/csv', 'text/plain']
    }
    
    expected_mimes = expected_mime_types.get(file_extension, [])
    
    if not expected_mimes:
        return {
            'valid': False,
            'message': f"Unknown file extension: .{file_extension}"
        }
    
    if detected_mime not in expected_mimes:
        # Special handling for common misdetections
        if file_extension == 'pdf' and detected_mime == 'text/plain':
            return {
                'valid': False,
                'message': "File appears to be text but has .pdf extension. This may indicate a corrupted PDF or misnamed text file."
            }
        elif file_extension == 'docx' and detected_mime == 'application/zip':
            # DOCX files are ZIP-based, so this might be OK if we can't detect the Office structure
            return {
                'valid': True,
                'message': "DOCX file detected as ZIP archive (this is normal for Office documents)"
            }
        elif file_extension == 'txt' and detected_mime in ['text/html', 'application/xml']:
            return {
                'valid': False,
                'message': f"File contains {detected_mime.split('/')[-1].upper()} content but has .txt extension. Please use the correct file extension."
            }
        else:
            return {
                'valid': False,
                'message': f"MIME type mismatch: expected {' or '.join(expected_mimes)} for .{file_extension} file, but detected {detected_mime}"
            }
    
    return {'valid': True, 'message': ''}

def _validate_filename_comprehensive(filename: str) -> Dict:
    """Comprehensive filename validation with detailed error messages."""
    
    if not filename:
        return {'valid': False, 'message': 'Filename cannot be empty'}
    
    # Check for dangerous characters
    dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\0', '\\', '/']
    found_dangerous = [char for char in dangerous_chars if char in filename]
    
    if found_dangerous:
        return {
            'valid': False,
            'message': f"Filename contains dangerous characters: {', '.join(found_dangerous)}"
        }
    
    # Check for reserved names (Windows)
    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5',
        'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4',
        'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    name_without_ext = filename.rsplit('.', 1)[0].upper()
    if name_without_ext in reserved_names:
        return {
            'valid': False,
            'message': f"Filename '{filename}' uses a reserved system name"
        }
    
    # Check filename length
    if len(filename) > 255:
        return {
            'valid': False,
            'message': f"Filename too long ({len(filename)} characters). Maximum allowed: 255 characters"
        }
    
    # Check for hidden files (starting with dot)
    if filename.startswith('.'):
        return {
            'valid': False,
            'message': "Hidden files (starting with '.') are not allowed"
        }
    
    return {'valid': True, 'message': ''}

def _validate_content_comprehensive(file_content: bytes, file_extension: str) -> Dict:
    """Enhanced content validation with detailed error messages."""
    
    # Check for suspicious patterns
    suspicious_patterns = [
        (b'<script', 'JavaScript code'),
        (b'javascript:', 'JavaScript URL'),
        (b'vbscript:', 'VBScript code'),
        (b'eval(', 'Code evaluation'),
        (b'exec(', 'Code execution'),
        (b'system(', 'System command'),
        (b'shell_exec(', 'Shell execution'),
        (b'<?php', 'PHP code'),
        (b'<%', 'Server-side code'),
        (b'#!/bin/sh', 'Shell script'),
        (b'#!/bin/bash', 'Bash script'),
        (b'powershell', 'PowerShell code')
    ]
    
    content_lower = file_content.lower()
    
    for pattern, description in suspicious_patterns:
        if pattern in content_lower:
            return {
                'valid': False,
                'message': f"Suspicious content detected: {description}. This may indicate a malicious file."
            }
    
    # PDF-specific checks
    if file_extension == 'pdf':
        pdf_checks = _validate_pdf_content(content_lower)
        if not pdf_checks['valid']:
            return pdf_checks
    
    # Check for excessive binary content in text files
    if file_extension in ['txt', 'csv']:
        null_bytes = content_lower.count(b'\x00')
        if null_bytes > 10:  # Allow some null bytes but not too many
            return {
                'valid': False,
                'message': f"Text file contains {null_bytes} null bytes, which suggests binary content or corruption"
            }
    
    return {'valid': True, 'message': ''}

def _validate_pdf_content(content_lower: bytes) -> Dict:
    """Validate PDF-specific content for security issues."""
    
    # Check for JavaScript in PDF
    if b'/javascript' in content_lower or b'/js' in content_lower:
        return {
            'valid': False,
            'message': "PDF contains JavaScript code, which is not allowed for security reasons"
        }
    
    # Check for auto-execute actions
    if b'/openaction' in content_lower:
        return {
            'valid': False,
            'message': "PDF contains auto-execute actions, which are not allowed for security reasons"
        }
    
    # Check for forms (warning, not blocking)
    if b'/acroform' in content_lower:
        # This is just a warning, not a blocking issue
        pass
    
    return {'valid': True, 'message': ''}

def _check_file_integrity(file_content: bytes, file_extension: str) -> Dict:
    """Check basic file integrity based on file type."""
    
    if not file_content:
        return {'valid': False, 'message': 'File is empty'}
    
    if file_extension == 'pdf':
        # PDF files should start with %PDF- and end with %%EOF
        if not file_content.startswith(b'%PDF-'):
            return {
                'valid': False,
                'message': 'PDF file does not have valid PDF signature. File may be corrupted or misnamed.'
            }
        
        # Check for PDF end marker (not always present in all PDFs, so just warn)
        if b'%%EOF' not in file_content[-1024:]:
            # This is common in some PDFs, so we'll allow it but could add a warning
            pass
    
    elif file_extension == 'docx':
        # DOCX files should be valid ZIP archives
        if not (file_content.startswith(b'PK\x03\x04') or 
                file_content.startswith(b'PK\x05\x06') or 
                file_content.startswith(b'PK\x07\x08')):
            return {
                'valid': False,
                'message': 'DOCX file does not have valid ZIP signature. File may be corrupted or misnamed.'
            }
    
    elif file_extension in ['txt', 'csv']:
        # For text files, check if content is decodable
        try:
            # Try to decode a sample to check if it's valid text
            sample = file_content[:1024]
            sample.decode('utf-8', errors='strict')
        except UnicodeDecodeError:
            # Try other common encodings
            encodings_tried = []
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    sample.decode(encoding, errors='strict')
                    break
                except UnicodeDecodeError:
                    encodings_tried.append(encoding)
            else:
                return {
                    'valid': False,
                    'message': f'Text file contains invalid characters that cannot be decoded with common encodings (tried: utf-8, {", ".join(encodings_tried)})'
                }
    
    return {'valid': True, 'message': ''}

def _check_suspicious_patterns(file_content: bytes, file_extension: str) -> bool:
    """Check for suspicious patterns in file content."""
    
    # Suspicious patterns to look for
    suspicious_patterns = [
        b'<script',
        b'javascript:',
        b'vbscript:',
        b'eval(',
        b'exec(',
        b'system(',
        b'shell_exec(',
        b'<?php',
        b'<%',
        b'#!/bin/sh',
        b'#!/bin/bash'
    ]
    
    content_lower = file_content.lower()
    
    for pattern in suspicious_patterns:
        if pattern in content_lower:
            return False
    
    # PDF-specific checks
    if file_extension == 'pdf':
        if b'/javascript' in content_lower or b'/js' in content_lower:
            return False
        if b'/openaction' in content_lower:
            return False
    
    return True

def _display_security_validation(security_results: Dict, file_info: Dict):
    """Display security validation results with detailed error messages."""
    
    with st.expander("🔒 Security Validation", expanded=not security_results['all_checks_passed']):
        
        # File hash for reference
        st.text(f"File Hash: {file_info['file_hash_short']} (SHA-256)")
        
        # Security checks with enhanced descriptions
        check_descriptions = {
            'size_valid': 'File size within limits',
            'extension_valid': 'Valid file extension',
            'not_empty': 'File is not empty',
            'mime_type_valid': 'MIME type matches extension',
            'filename_safe': 'Filename is safe',
            'no_suspicious_patterns': 'No suspicious content detected',
            'file_integrity': 'File integrity check'
        }
        
        validation_messages = security_results.get('validation_messages', {})
        
        for check_key, description in check_descriptions.items():
            if check_key in security_results and check_key != 'validation_messages':
                if security_results[check_key]:
                    st.success(f"✅ {description}")
                else:
                    error_message = validation_messages.get(check_key, "Check failed")
                    st.error(f"❌ {description}")
                    st.error(f"   → {error_message}")
        
        # Overall status
        if security_results['all_checks_passed']:
            st.success("🎉 All security checks passed!")
        else:
            st.error("⚠️ Some security checks failed. Please review the issues above.")
            
            # Provide helpful suggestions
            st.info("💡 **Suggestions to fix issues:**")
            
            failed_checks = [key for key, value in security_results.items() 
                           if key != 'validation_messages' and key != 'all_checks_passed' and not value]
            
            suggestions = []
            
            if 'size_valid' in failed_checks:
                suggestions.append("• Reduce file size or split large documents into smaller parts")
            
            if 'extension_valid' in failed_checks:
                if file_info['file_extension'] == 'doc':
                    suggestions.append("• Convert .doc files to .docx format using Microsoft Word or online converters")
                else:
                    suggestions.append("• Use supported file formats: PDF, DOCX, or TXT")
            
            if 'mime_type_valid' in failed_checks:
                suggestions.append("• Ensure file extension matches the actual file content")
                suggestions.append("• Re-save the file in the correct format if it was converted incorrectly")
            
            if 'filename_safe' in failed_checks:
                suggestions.append("• Rename the file to remove special characters")
                suggestions.append("• Use only letters, numbers, spaces, hyphens, and underscores in filenames")
            
            if 'no_suspicious_patterns' in failed_checks:
                suggestions.append("• Remove any embedded scripts or macros from the document")
                suggestions.append("• Save as a clean version without active content")
            
            if 'file_integrity' in failed_checks:
                suggestions.append("• Try re-saving or re-exporting the file from the original application")
                suggestions.append("• Check if the file was corrupted during transfer")
            
            for suggestion in suggestions:
                st.write(suggestion)

def _display_file_preview(file_info: Dict, file_content: bytes, file_size_mb: float):
    """Display file preview if applicable."""
    
    if file_info['file_extension'] == 'txt' and file_size_mb < 1:
        with st.expander("👁️ File Preview", expanded=False):
            try:
                encoding = file_info['encoding'] or 'utf-8'
                content = file_content.decode(encoding)
                
                # Show preview with truncation
                preview_length = 1000
                if len(content) > preview_length:
                    preview = content[:preview_length] + f"\n\n... (truncated, showing first {preview_length} characters of {len(content)} total)"
                else:
                    preview = content
                
                st.text_area("Content Preview", preview, height=200, disabled=True)
                
                # Content statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Characters", len(content))
                with col2:
                    st.metric("Lines", content.count('\n') + 1)
                with col3:
                    st.metric("Words", len(content.split()))
                    
            except UnicodeDecodeError:
                st.warning("Cannot preview file - contains non-text content or encoding issues")
    
    elif file_info['file_extension'] in ['pdf', 'docx', 'doc']:
        with st.expander("📄 Document Information", expanded=False):
            st.info(f"Document preview not available for {file_info['file_type']} files. The file will be processed after upload.")
            
            # Show basic document info
            if file_info['file_extension'] == 'pdf':
                st.text("PDF documents will be processed to extract text content for analysis.")
            elif file_info['file_extension'] in ['docx', 'doc']:
                st.text("Word documents will be processed to extract text content and preserve formatting information.")

def _display_processing_recommendations(file_info: Dict, security_results: Dict):
    """Display processing recommendations based on file analysis."""
    
    if security_results['all_checks_passed']:
        with st.expander("🚀 Processing Recommendations", expanded=False):
            
            recommendations = []
            warnings = []
            
            # File size recommendations
            file_size_mb = file_info['file_size_bytes'] / (1024 * 1024)
            if file_size_mb > 25:
                warnings.append("Very large file detected - processing may take several minutes")
            elif file_size_mb > 10:
                recommendations.append("Large file detected - processing may take longer than usual")
            elif file_size_mb < 0.05:  # Less than 50KB
                warnings.append("Very small file detected - ensure it contains sufficient contract content")
            elif file_size_mb < 0.1:
                recommendations.append("Small file detected - ensure it contains sufficient contract content")
            
            # MIME type detection feedback
            detected_mime = file_info['mime_type']
            file_extension = file_info['file_extension']
            
            # File type recommendations with MIME type context
            if file_extension == 'pdf':
                if detected_mime == 'application/pdf':
                    recommendations.append("✅ PDF properly detected - file signature is valid")
                    recommendations.append("PDF files work best when they contain selectable text (not scanned images)")
                    recommendations.append("If text extraction fails, the PDF may be image-based and require OCR")
                else:
                    warnings.append(f"PDF file detected as {detected_mime} - this may indicate file corruption")
                    
            elif file_extension == 'docx':
                if detected_mime == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                    recommendations.append("✅ DOCX properly detected - Office document structure is valid")
                elif detected_mime == 'application/zip':
                    recommendations.append("✅ DOCX detected as ZIP archive (normal for Office documents)")
                else:
                    warnings.append(f"DOCX file detected as {detected_mime} - this may indicate file issues")
                
                recommendations.append("DOCX files provide excellent text extraction and formatting preservation")
                recommendations.append("Tables and complex formatting will be preserved during processing")
                
            elif file_extension == 'txt':
                if detected_mime == 'text/plain':
                    recommendations.append("✅ Text file properly detected")
                elif detected_mime == 'text/csv':
                    recommendations.append("✅ CSV content detected - will be processed as structured text")
                else:
                    warnings.append(f"Text file detected as {detected_mime} - content may not be plain text")
                
                recommendations.append("Text files provide fast processing but may lack formatting information")
                recommendations.append("Ensure the file uses UTF-8 encoding for best compatibility")
            
            # Encoding recommendations
            if file_info['encoding']:
                if file_info['encoding'] == 'utf-8':
                    recommendations.append("✅ UTF-8 encoding detected - optimal for processing")
                else:
                    recommendations.append(f"File uses {file_info['encoding']} encoding - UTF-8 is recommended for best compatibility")
            
            # Security and integrity feedback
            if detected_mime == 'application/pdf':
                recommendations.append("✅ PDF security checks passed - no JavaScript or suspicious content detected")
            
            # MIME type consistency feedback
            expected_mimes = {
                'pdf': 'application/pdf',
                'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'txt': 'text/plain'
            }
            
            expected_mime = expected_mimes.get(file_extension)
            if expected_mime and detected_mime == expected_mime:
                recommendations.append("✅ File type and content are perfectly aligned")
            elif expected_mime and detected_mime != expected_mime:
                if not (file_extension == 'docx' and detected_mime == 'application/zip'):
                    warnings.append("⚠️ File extension and content type don't match perfectly")
            
            # Display warnings first
            for warning in warnings:
                st.warning(f"⚠️ {warning}")
            
            # Display recommendations
            if recommendations:
                for rec in recommendations:
                    st.info(f"💡 {rec}")
            else:
                st.success("✨ File is optimally configured for processing!")
            
            # Processing time estimate
            estimated_time = _estimate_processing_time(file_size_mb, file_info['file_extension'])
            st.info(f"⏱️ Estimated processing time: {estimated_time}")
            
            # Advanced file information
            with st.expander("🔍 Advanced File Analysis", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.text("Detection Methods Used:")
                    st.text("• Magic number analysis")
                    st.text("• Content pattern analysis") 
                    st.text("• Extension validation")
                    if 'magic' in globals():
                        st.text("• python-magic library")
                
                with col2:
                    st.text("File Characteristics:")
                    st.text(f"• MIME Type: {detected_mime}")
                    st.text(f"• File Size: {file_size_mb:.2f} MB")
                    if file_info['encoding']:
                        st.text(f"• Encoding: {file_info['encoding']}")
                    st.text(f"• Hash: {file_info['file_hash_short']}")
    
    else:
        # Show what needs to be fixed for failed validation
        st.error("🚫 File cannot be processed until validation issues are resolved.")
        
        failed_checks = [key for key, value in security_results.items() 
                        if key not in ['validation_messages', 'all_checks_passed'] and not value]
        
        st.write(f"**Issues found:** {len(failed_checks)} validation check(s) failed")
        st.write("Please address the issues shown in the Security Validation section above.")


def _estimate_processing_time(file_size_mb: float, file_extension: str) -> str:
    """Estimate processing time based on file size and type."""
    
    # Base processing rates (MB per second)
    processing_rates = {
        'pdf': 0.5,    # PDFs are slower due to text extraction
        'docx': 1.0,   # DOCX files are moderately fast
        'txt': 5.0     # Text files are very fast
    }
    
    rate = processing_rates.get(file_extension, 1.0)
    base_time = file_size_mb / rate
    
    # Add overhead for analysis
    analysis_overhead = 10  # seconds
    total_time = base_time + analysis_overhead
    
    if total_time < 30:
        return "Less than 30 seconds"
    elif total_time < 60:
        return f"About {int(total_time)} seconds"
    elif total_time < 300:
        return f"About {int(total_time / 60)} minutes"
    else:
        return "Several minutes (large file)"

# Utility functions for external use
def get_supported_file_types() -> List[str]:
    """Get list of supported file types."""
    return ["pdf", "docx", "txt", "doc"]

def validate_file_size(file_size_bytes: int, max_size_mb: float = 50) -> bool:
    """Validate file size against limits."""
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size_bytes <= max_size_bytes

def calculate_file_hash(file_content: bytes) -> str:
    """Calculate SHA-256 hash of file content."""
    return hashlib.sha256(file_content).hexdigest()

def _process_multiple_files(uploaded_files: List) -> Optional[Union[object, List[object]]]:
    """Process multiple uploaded files with batch operations and progress tracking."""
    
    if not uploaded_files:
        return None
    
    st.markdown("### 📊 Processing Multiple Files")
    
    # Initialize progress tracking
    total_files = len(uploaded_files)
    processed_files = []
    failed_files = []
    
    # Create progress containers
    overall_progress = st.progress(0)
    status_text = st.empty()
    
    # Process each file
    for i, uploaded_file in enumerate(uploaded_files):
        current_progress = (i / total_files)
        overall_progress.progress(current_progress)
        status_text.info(f"Processing file {i+1} of {total_files}: {uploaded_file.name}")
        
        # Process individual file
        with st.expander(f"📄 {uploaded_file.name}", expanded=False):
            processed_file = _process_uploaded_file(uploaded_file)
            
            if processed_file:
                processed_files.append(processed_file)
                
                # Generate and store preview
                preview_data = _generate_file_preview(uploaded_file)
                if preview_data:
                    st.session_state.file_previews[uploaded_file.name] = preview_data
                
                # Store in session state
                file_data = {
                    'file': uploaded_file,
                    'processed_at': datetime.now().isoformat(),
                    'file_id': f"file_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    'preview_available': preview_data is not None
                }
                st.session_state.uploaded_files.append(file_data)
                
            else:
                failed_files.append(uploaded_file.name)
    
    # Final progress update
    overall_progress.progress(1.0)
    status_text.success(f"✅ Completed processing {len(processed_files)} of {total_files} files")
    
    # Display batch summary
    _display_batch_summary(processed_files, failed_files, total_files)
    
    # Display batch actions if files were processed
    if processed_files:
        _display_batch_actions(processed_files)
    
    # Return processed files
    if len(processed_files) == 1:
        return processed_files[0]
    elif len(processed_files) > 1:
        return processed_files
    else:
        return None


def _generate_file_preview(uploaded_file) -> Optional[Dict]:
    """Generate preview thumbnail for uploaded file."""
    
    try:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        file_content = uploaded_file.getvalue()
        
        if file_extension == 'pdf':
            return _generate_pdf_preview(file_content, uploaded_file.name)
        elif file_extension == 'txt':
            return _generate_text_preview(file_content, uploaded_file.name)
        elif file_extension == 'docx':
            return _generate_docx_preview(file_content, uploaded_file.name)
        
    except Exception as e:
        st.warning(f"Could not generate preview for {uploaded_file.name}: {str(e)}")
        return None
    
    return None


def _generate_pdf_preview(file_content: bytes, filename: str) -> Optional[Dict]:
    """Generate thumbnail preview for PDF file."""
    
    if not PYMUPDF_AVAILABLE:
        # Return basic PDF info without preview
        return {
            'type': 'pdf_info',
            'data': f"PDF Document\nFilename: {filename}\nSize: {len(file_content):,} bytes\nPreview not available (PyMuPDF not installed)",
            'size_bytes': len(file_content),
            'filename': filename
        }
    
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        try:
            # Open PDF and get first page
            pdf_document = fitz.open(temp_file_path)
            
            if len(pdf_document) > 0:
                first_page = pdf_document[0]
                
                # Render page as image
                mat = fitz.Matrix(1.0, 1.0)  # Scale factor
                pix = first_page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                
                # Resize for thumbnail
                img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                
                # Convert to base64 for display
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                img_base64 = base64.b64encode(buffer.getvalue()).decode()
                
                pdf_document.close()
                
                return {
                    'type': 'image',
                    'data': img_base64,
                    'format': 'png',
                    'pages': len(pdf_document),
                    'filename': filename
                }
            
            pdf_document.close()
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except Exception as e:
        # Fallback to basic info
        return {
            'type': 'pdf_info',
            'data': f"PDF Document\nFilename: {filename}\nSize: {len(file_content):,} bytes\nPreview generation failed: {str(e)}",
            'size_bytes': len(file_content),
            'filename': filename
        }
    
    return None


def _generate_text_preview(file_content: bytes, filename: str) -> Optional[Dict]:
    """Generate preview for text file."""
    
    try:
        # Decode text content
        text_content = file_content.decode('utf-8', errors='ignore')
        
        # Get first 500 characters for preview
        preview_text = text_content[:500]
        if len(text_content) > 500:
            preview_text += "..."
        
        return {
            'type': 'text',
            'data': preview_text,
            'total_chars': len(text_content),
            'lines': len(text_content.split('\n')),
            'filename': filename
        }
        
    except Exception as e:
        st.warning(f"Could not generate text preview: {str(e)}")
        return None


def _generate_docx_preview(file_content: bytes, filename: str) -> Optional[Dict]:
    """Generate preview for DOCX file."""
    
    try:
        # For DOCX files, we'll show basic info since extracting text requires python-docx
        # which might not be available. We'll show file structure info instead.
        
        return {
            'type': 'docx',
            'data': f"Microsoft Word Document\nFilename: {filename}\nSize: {len(file_content):,} bytes",
            'size_bytes': len(file_content),
            'filename': filename
        }
        
    except Exception as e:
        st.warning(f"Could not generate DOCX preview: {str(e)}")
        return None


def _display_uploaded_files() -> Optional[Union[object, List[object]]]:
    """Display currently uploaded files with previews and management options."""
    
    if not st.session_state.uploaded_files:
        return None
    
    st.markdown("### 📁 Uploaded Files")
    
    files_to_return = []
    
    for i, file_data in enumerate(st.session_state.uploaded_files):
        uploaded_file = file_data['file']
        file_id = file_data.get('file_id', f'file_{i}')
        
        # Create file preview card
        with st.container():
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                # Display preview if available
                preview_data = st.session_state.file_previews.get(uploaded_file.name)
                if preview_data:
                    _display_file_preview_thumbnail(preview_data)
                else:
                    st.markdown("📄")
            
            with col2:
                # File information
                st.markdown(f"**{uploaded_file.name}**")
                file_size_mb = uploaded_file.size / (1024 * 1024)
                st.caption(f"Size: {file_size_mb:.2f} MB • Type: {uploaded_file.name.split('.')[-1].upper()}")
                st.caption(f"Uploaded: {file_data.get('processed_at', 'Unknown')}")
                
                # Progress bar (simulated)
                progress_value = st.session_state.upload_progress.get(file_id, 100)
                if progress_value < 100:
                    st.progress(progress_value / 100)
                    st.caption(f"Processing: {progress_value}%")
                else:
                    st.success("✅ Ready for analysis")
            
            with col3:
                # Action buttons
                if st.button("🗑️", key=f"remove_{file_id}", help="Remove file"):
                    _remove_file_from_session(i)
                    st.rerun()
                
                if st.button("👁️", key=f"preview_{file_id}", help="View preview"):
                    _show_detailed_preview(uploaded_file, preview_data)
        
        st.markdown("---")
        files_to_return.append(uploaded_file)
    
    # Batch actions
    if len(files_to_return) > 1:
        _display_batch_actions(files_to_return)
    
    # Return files for processing
    if len(files_to_return) == 1:
        return files_to_return[0]
    elif len(files_to_return) > 1:
        return files_to_return
    else:
        return None


def _display_file_preview_thumbnail(preview_data: Dict):
    """Display file preview thumbnail."""
    
    if preview_data['type'] == 'image':
        # Display image thumbnail
        img_html = f'<img src="data:image/png;base64,{preview_data["data"]}" class="file-thumbnail" alt="Preview">'
        st.markdown(img_html, unsafe_allow_html=True)
    elif preview_data['type'] == 'text':
        # Display text icon with preview
        st.markdown("📃")
        with st.expander("Preview", expanded=False):
            st.text(preview_data['data'][:100] + "..." if len(preview_data['data']) > 100 else preview_data['data'])
    elif preview_data['type'] == 'docx':
        # Display DOCX icon
        st.markdown("📝")
    elif preview_data['type'] == 'pdf_info':
        # Display PDF icon for basic info
        st.markdown("📄")
    else:
        # Default file icon
        st.markdown("📄")


def _display_batch_summary(processed_files: List, failed_files: List, total_files: int):
    """Display summary of batch processing results."""
    
    st.markdown("### 📊 Batch Processing Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Files", total_files)
    
    with col2:
        st.metric("Successfully Processed", len(processed_files), 
                 delta=f"{(len(processed_files)/total_files)*100:.1f}%")
    
    with col3:
        st.metric("Failed", len(failed_files),
                 delta=f"{(len(failed_files)/total_files)*100:.1f}%" if failed_files else "0%")
    
    # Show failed files if any
    if failed_files:
        with st.expander("❌ Failed Files", expanded=True):
            for filename in failed_files:
                st.error(f"• {filename}")


def _display_batch_actions(processed_files: List):
    """Display batch action buttons for multiple files."""
    
    st.markdown("### 🔧 Batch Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🚀 Analyze All Files", type="primary"):
            st.session_state.batch_analyze = True
            st.success("Batch analysis initiated!")
    
    with col2:
        if st.button("📊 Generate Report"):
            st.session_state.generate_batch_report = True
            st.info("Batch report generation started...")
    
    with col3:
        if st.button("🗑️ Clear All Files"):
            st.session_state.uploaded_files = []
            st.session_state.file_previews = {}
            st.session_state.upload_progress = {}
            st.rerun()
    
    with col4:
        if st.button("💾 Export File List"):
            _export_file_list(processed_files)


def _remove_file_from_session(index: int):
    """Remove file from session state."""
    
    if 0 <= index < len(st.session_state.uploaded_files):
        removed_file = st.session_state.uploaded_files.pop(index)
        filename = removed_file['file'].name
        
        # Remove from previews
        if filename in st.session_state.file_previews:
            del st.session_state.file_previews[filename]
        
        # Remove from progress tracking
        file_id = removed_file.get('file_id')
        if file_id and file_id in st.session_state.upload_progress:
            del st.session_state.upload_progress[file_id]


def _show_detailed_preview(uploaded_file, preview_data: Optional[Dict]):
    """Show detailed preview of file in modal-like expander."""
    
    with st.expander(f"👁️ Detailed Preview: {uploaded_file.name}", expanded=True):
        
        if preview_data:
            if preview_data['type'] == 'image':
                st.image(f"data:image/png;base64,{preview_data['data']}", 
                        caption=f"First page of {uploaded_file.name}")
                st.info(f"📄 PDF Document • {preview_data.get('pages', 'Unknown')} pages")
                
            elif preview_data['type'] == 'text':
                st.text_area("Content Preview", preview_data['data'], height=300, disabled=True)
                st.info(f"📃 Text Document • {preview_data.get('total_chars', 0):,} characters • {preview_data.get('lines', 0)} lines")
                
            elif preview_data['type'] == 'docx':
                st.info("📝 Microsoft Word Document")
                st.text(preview_data['data'])
                
            elif preview_data['type'] == 'pdf_info':
                st.info("📄 PDF Document")
                st.text(preview_data['data'])
                
        else:
            st.warning("Preview not available for this file type")
        
        # File metadata
        st.markdown("**File Information:**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.text(f"Filename: {uploaded_file.name}")
            st.text(f"Size: {uploaded_file.size:,} bytes")
            st.text(f"Type: {uploaded_file.type}")
        
        with col2:
            file_hash = hashlib.md5(uploaded_file.getvalue()).hexdigest()[:16]
            st.text(f"Hash: {file_hash}")
            st.text(f"Extension: {uploaded_file.name.split('.')[-1].upper()}")


def _export_file_list(processed_files: List):
    """Export list of processed files as JSON."""
    
    file_list = []
    for file_obj in processed_files:
        file_info = {
            'filename': file_obj.name,
            'size_bytes': file_obj.size,
            'type': file_obj.type,
            'hash': hashlib.md5(file_obj.getvalue()).hexdigest(),
            'uploaded_at': datetime.now().isoformat()
        }
        file_list.append(file_info)
    
    # Create downloadable JSON
    json_data = json.dumps(file_list, indent=2)
    
    st.download_button(
        label="📥 Download File List (JSON)",
        data=json_data,
        file_name=f"uploaded_files_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )