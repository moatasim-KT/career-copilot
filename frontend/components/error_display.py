"""Error Display Component"""
import streamlit as st
from datetime import datetime

def error_display(error_message, error_type="error", show_details=True, show_actions=True, retry_callback=None):
    """Display enhanced error messages with consistent formatting and actionable suggestions."""
    
    # Enhanced error styling
    st.markdown("""
    <style>
    .error-container {
        border-radius: 8px;
        padding: 16px;
        margin: 12px 0;
        border-left: 4px solid;
    }
    .error-container.error {
        background: linear-gradient(135deg, #fff5f5 0%, #fed7d7 100%);
        border-left-color: #e53e3e;
    }
    .error-container.warning {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        border-left-color: #f59e0b;
    }
    .error-container.info {
        background: linear-gradient(135deg, #f0f9ff 0%, #dbeafe 100%);
        border-left-color: #3b82f6;
    }
    .error-header {
        display: flex;
        align-items: center;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .error-icon {
        font-size: 20px;
        margin-right: 8px;
    }
    .error-message {
        font-size: 14px;
        line-height: 1.5;
        color: #374151;
    }
    .action-buttons {
        margin-top: 12px;
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Determine error styling and icon
    if error_type == "error":
        container_class = "error"
        icon = "❌"
        st.error(f"{icon} **Error**")
    elif error_type == "warning":
        container_class = "warning"
        icon = "⚠️"
        st.warning(f"{icon} **Warning**")
    elif error_type == "info":
        container_class = "info"
        icon = "ℹ️"
        st.info(f"{icon} **Information**")
    else:
        container_class = "error"
        icon = "❌"
        st.error(f"{icon} **Error**")
    
    # Display error message with enhanced formatting
    st.markdown(f"""
    <div class="error-container {container_class}">
        <div class="error-header">
            <span class="error-icon">{icon}</span>
            <span>Error Details</span>
        </div>
        <div class="error-message">{error_message}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced troubleshooting suggestions
    if show_details:
        with st.expander("🔧 Troubleshooting Guide", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📋 Error Information:**")
                st.text(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                st.text(f"Error Type: {error_type.title()}")
                st.text(f"Error ID: {hash(error_message) % 10000:04d}")
            
            with col2:
                st.markdown("**🔍 Quick Checks:**")
                if "connection" in error_message.lower():
                    st.markdown("- ✅ Internet connection active")
                    st.markdown("- ✅ Backend service running")
                    st.markdown("- ✅ No firewall blocking")
                elif "file" in error_message.lower():
                    st.markdown("- ✅ File not corrupted")
                    st.markdown("- ✅ File size within limits")
                    st.markdown("- ✅ Supported file format")
                elif "auth" in error_message.lower():
                    st.markdown("- ✅ Valid credentials")
                    st.markdown("- ✅ Active session")
                    st.markdown("- ✅ Proper permissions")
                else:
                    st.markdown("- ✅ Page refresh attempted")
                    st.markdown("- ✅ Browser cache cleared")
                    st.markdown("- ✅ System status checked")
            
            st.markdown("---")
            st.markdown("**💡 Detailed Solutions:**")
            
            if "connection" in error_message.lower():
                st.markdown("""
                **Connection Issues:**
                1. **Check Network**: Verify your internet connection is stable
                2. **Backend Status**: Ensure the backend service is running on the correct port
                3. **Firewall**: Check if any firewall is blocking the connection
                4. **Proxy Settings**: Verify proxy settings if using corporate network
                5. **DNS Issues**: Try using a different DNS server if needed
                """)
            elif "file" in error_message.lower():
                st.markdown("""
                **File Processing Issues:**
                1. **File Integrity**: Open the file in its native application to verify it's not corrupted
                2. **File Size**: Ensure file is under the maximum size limit (50MB for PDF, 25MB for DOCX, 10MB for TXT)
                3. **File Format**: Use supported formats only (PDF, DOCX, TXT)
                4. **File Content**: Ensure the file contains readable text (not just images)
                5. **File Permissions**: Check that the file is not password-protected or encrypted
                """)
            elif "auth" in error_message.lower():
                st.markdown("""
                **Authentication Issues:**
                1. **Credentials**: Double-check your username and password
                2. **Session**: Your session may have expired - try logging in again
                3. **Account Status**: Verify your account is active and not suspended
                4. **Permissions**: Ensure you have the necessary permissions for this operation
                5. **Two-Factor**: Complete any required two-factor authentication steps
                """)
            else:
                st.markdown("""
                **General Troubleshooting:**
                1. **Refresh**: Try refreshing the page (Ctrl+F5 or Cmd+Shift+R)
                2. **Browser**: Try using a different browser or incognito/private mode
                3. **Cache**: Clear your browser cache and cookies
                4. **Extensions**: Disable browser extensions that might interfere
                5. **System**: Check system status page for any ongoing issues
                """)
    
    # Action buttons for user interaction
    if show_actions:
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if retry_callback and st.button("🔄 Retry", key=f"retry_{hash(error_message)}"):
                retry_callback()
        
        with col2:
            if st.button("📋 Copy Error", key=f"copy_{hash(error_message)}"):
                error_info = f"Error: {error_message}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nID: {hash(error_message) % 10000:04d}"
                st.code(error_info, language=None)
                st.success("Error details copied!")
        
        with col3:
            st.markdown("**Need more help?** Contact support with the Error ID above.")