"""
Responsive UI Components for Mobile and Desktop Optimization
Provides adaptive layouts and mobile-optimized components.
"""

import streamlit as st
from typing import Dict, List, Tuple, Any, Optional


class ResponsiveLayout:
    """Handle responsive layouts for different screen sizes."""
    
    @staticmethod
    def get_screen_info() -> Dict[str, Any]:
        """Get screen information using JavaScript."""
        # Inject JavaScript to detect screen size
        screen_js = """
        <script>
        function updateScreenInfo() {
            const screenInfo = {
                width: window.innerWidth,
                height: window.innerHeight,
                devicePixelRatio: window.devicePixelRatio,
                isMobile: window.innerWidth < 768,
                isTablet: window.innerWidth >= 768 && window.innerWidth < 1024,
                isDesktop: window.innerWidth >= 1024
            };
            
            // Store in session storage for Streamlit to access
            sessionStorage.setItem('screenInfo', JSON.stringify(screenInfo));
            
            // Also try to communicate with parent window
            if (window.parent) {
                window.parent.postMessage({
                    type: 'screenInfo',
                    data: screenInfo
                }, '*');
            }
        }
        
        // Update on load and resize
        updateScreenInfo();
        window.addEventListener('resize', updateScreenInfo);
        </script>
        """
        
        st.components.v1.html(screen_js, height=0)
        
        # Return default values (will be updated by JavaScript)
        return {
            'width': 1200,
            'height': 800,
            'devicePixelRatio': 1,
            'isMobile': False,
            'isTablet': False,
            'isDesktop': True
        }
    
    @staticmethod
    def get_responsive_columns(mobile_cols: int = 1, tablet_cols: int = 2, desktop_cols: int = 3) -> List:
        """Get responsive column layout based on screen size."""
        screen_info = ResponsiveLayout.get_screen_info()
        
        if screen_info['isMobile']:
            return st.columns(mobile_cols)
        elif screen_info['isTablet']:
            return st.columns(tablet_cols)
        else:
            return st.columns(desktop_cols)
    
    @staticmethod
    def apply_responsive_css():
        """Apply responsive CSS styles."""
        responsive_css = """
        <style>
        /* Mobile styles */
        @media (max-width: 767px) {
            .stButton > button {
                width: 100% !important;
                margin-bottom: 8px !important;
                font-size: 14px !important;
                padding: 8px 16px !important;
            }
            
            .stSelectbox > div > div {
                font-size: 14px !important;
            }
            
            .stTextInput > div > div > input {
                font-size: 16px !important; /* Prevents zoom on iOS */
            }
            
            .stTextArea > div > div > textarea {
                font-size: 16px !important;
            }
            
            .stMetric {
                background-color: #f8f9fa !important;
                padding: 12px !important;
                border-radius: 8px !important;
                margin-bottom: 8px !important;
                border: 1px solid #e9ecef !important;
            }
            
            .stTabs [data-baseweb="tab-list"] {
                gap: 4px !important;
                flex-wrap: wrap !important;
            }
            
            .stTabs [data-baseweb="tab"] {
                padding: 8px 12px !important;
                font-size: 13px !important;
                min-width: auto !important;
                flex: 1 !important;
            }
            
            .stSidebar > div {
                width: 100% !important;
                min-width: 100% !important;
            }
            
            /* Hide sidebar by default on mobile */
            .stSidebar {
                transform: translateX(-100%) !important;
                transition: transform 0.3s ease !important;
            }
            
            .stSidebar.show {
                transform: translateX(0) !important;
            }
            
            /* File uploader mobile optimization */
            .stFileUploader > div {
                border: 2px dashed #ccc !important;
                border-radius: 8px !important;
                padding: 20px !important;
                text-align: center !important;
            }
            
            /* Progress bar mobile optimization */
            .stProgress > div > div {
                height: 8px !important;
                border-radius: 4px !important;
            }
            
            /* Alert boxes mobile optimization */
            .stAlert {
                padding: 12px !important;
                margin: 8px 0 !important;
                border-radius: 6px !important;
                font-size: 14px !important;
            }
        }
        
        /* Tablet styles */
        @media (min-width: 768px) and (max-width: 1023px) {
            .stButton > button {
                font-size: 15px !important;
                padding: 10px 20px !important;
            }
            
            .stMetric {
                padding: 14px !important;
                margin-bottom: 10px !important;
            }
            
            .stTabs [data-baseweb="tab"] {
                padding: 10px 16px !important;
                font-size: 14px !important;
            }
        }
        
        /* Desktop styles */
        @media (min-width: 1024px) {
            .stButton > button {
                font-size: 16px !important;
                padding: 12px 24px !important;
            }
            
            .stMetric {
                padding: 16px !important;
                margin-bottom: 12px !important;
            }
        }
        
        /* Common responsive utilities */
        .mobile-only {
            display: none !important;
        }
        
        .desktop-only {
            display: block !important;
        }
        
        @media (max-width: 767px) {
            .mobile-only {
                display: block !important;
            }
            
            .desktop-only {
                display: none !important;
            }
        }
        
        /* Touch-friendly elements */
        .touch-friendly {
            min-height: 44px !important;
            min-width: 44px !important;
        }
        
        /* Improved scrolling on mobile */
        .stVerticalBlock {
            -webkit-overflow-scrolling: touch !important;
        }
        
        /* Better spacing for mobile */
        @media (max-width: 767px) {
            .block-container {
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }
        }
        </style>
        """
        
        st.markdown(responsive_css, unsafe_allow_html=True)


class MobileOptimizedComponents:
    """Mobile-optimized versions of common components."""
    
    @staticmethod
    def mobile_file_uploader(label: str, accepted_types: List[str] = None, help_text: str = None):
        """Mobile-optimized file uploader."""
        accepted_types = accepted_types or ["pdf", "docx", "txt"]
        
        # Add mobile-specific styling
        st.markdown("""
        <style>
        .mobile-file-uploader {
            border: 2px dashed #007bff;
            border-radius: 12px;
            padding: 24px;
            text-align: center;
            background: linear-gradient(135deg, #f8f9ff 0%, #e3f2fd 100%);
            margin: 16px 0;
        }
        
        .mobile-file-uploader:hover {
            border-color: #0056b3;
            background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        }
        
        .file-upload-icon {
            font-size: 48px;
            margin-bottom: 12px;
            display: block;
        }
        
        .file-upload-text {
            font-size: 16px;
            font-weight: 500;
            color: #333;
            margin-bottom: 8px;
        }
        
        .file-upload-help {
            font-size: 14px;
            color: #666;
            margin-bottom: 16px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Create mobile-friendly upload area
        with st.container():
            st.markdown(f"""
            <div class="mobile-file-uploader">
                <div class="file-upload-icon">📁</div>
                <div class="file-upload-text">{label}</div>
                <div class="file-upload-help">
                    Tap to select or drag and drop<br>
                    Supported: {', '.join(accepted_types).upper()}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Actual file uploader (hidden styling will be applied by CSS)
            uploaded_file = st.file_uploader(
                label,
                type=accepted_types,
                help=help_text,
                label_visibility="collapsed"
            )
            
            return uploaded_file
    
    @staticmethod
    def mobile_button_group(buttons: List[Dict[str, Any]], columns: int = None):
        """Create mobile-optimized button group."""
        if not buttons:
            return {}
        
        # Auto-determine columns based on screen size
        if columns is None:
            screen_info = ResponsiveLayout.get_screen_info()
            if screen_info['isMobile']:
                columns = 1
            elif screen_info['isTablet']:
                columns = 2
            else:
                columns = min(len(buttons), 3)
        
        cols = st.columns(columns)
        results = {}
        
        for i, button in enumerate(buttons):
            col = cols[i % columns]
            
            with col:
                key = button.get('key', f"btn_{i}")
                label = button.get('label', f"Button {i+1}")
                button_type = button.get('type', 'secondary')
                disabled = button.get('disabled', False)
                help_text = button.get('help', None)
                
                results[key] = st.button(
                    label,
                    key=key,
                    type=button_type,
                    disabled=disabled,
                    help=help_text,
                    use_container_width=True
                )
        
        return results
    
    @staticmethod
    def mobile_metrics_grid(metrics: List[Dict[str, Any]], columns: int = None):
        """Create mobile-optimized metrics grid."""
        if not metrics:
            return
        
        # Auto-determine columns based on screen size
        if columns is None:
            screen_info = ResponsiveLayout.get_screen_info()
            if screen_info['isMobile']:
                columns = 1
            elif screen_info['isTablet']:
                columns = 2
            else:
                columns = min(len(metrics), 4)
        
        cols = st.columns(columns)
        
        for i, metric in enumerate(metrics):
            col = cols[i % columns]
            
            with col:
                label = metric.get('label', 'Metric')
                value = metric.get('value', '0')
                delta = metric.get('delta', None)
                delta_color = metric.get('delta_color', 'normal')
                help_text = metric.get('help', None)
                
                st.metric(
                    label=label,
                    value=value,
                    delta=delta,
                    delta_color=delta_color,
                    help=help_text
                )
    
    @staticmethod
    def mobile_progress_indicator(title: str, progress: float, message: str = "", show_percentage: bool = True):
        """Mobile-optimized progress indicator."""
        # Ensure progress is between 0 and 1
        progress = max(0, min(1, progress))
        
        st.markdown(f"""
        <div style="
            background: #f8f9fa;
            padding: 16px;
            border-radius: 8px;
            margin: 12px 0;
            border-left: 4px solid #007bff;
        ">
            <div style="
                font-weight: 600;
                margin-bottom: 8px;
                color: #333;
            ">{title}</div>
        """, unsafe_allow_html=True)
        
        # Progress bar
        st.progress(progress)
        
        # Progress details
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if message:
                st.caption(message)
        
        with col2:
            if show_percentage:
                st.caption(f"{progress * 100:.0f}%")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    @staticmethod
    def mobile_tabs(tabs: List[Dict[str, Any]], default_tab: int = 0):
        """Mobile-optimized tabs with better touch interaction."""
        if not tabs:
            return None, None
        
        # Create tab labels
        tab_labels = [tab.get('label', f'Tab {i+1}') for i, tab in enumerate(tabs)]
        
        # Create Streamlit tabs
        tab_objects = st.tabs(tab_labels)
        
        # Return active tab content
        for i, (tab_obj, tab_config) in enumerate(zip(tab_objects, tabs)):
            with tab_obj:
                content_func = tab_config.get('content')
                if content_func and callable(content_func):
                    content_func()
                elif 'content' in tab_config:
                    st.write(tab_config['content'])
        
        return tab_objects, tabs


class TouchOptimization:
    """Optimize interface for touch interactions."""
    
    @staticmethod
    def apply_touch_styles():
        """Apply touch-friendly styles."""
        touch_css = """
        <style>
        /* Touch-friendly button sizing */
        .stButton > button {
            min-height: 44px !important;
            min-width: 44px !important;
            touch-action: manipulation !important;
        }
        
        /* Touch-friendly input fields */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div {
            min-height: 44px !important;
            touch-action: manipulation !important;
        }
        
        /* Prevent zoom on input focus (iOS) */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            font-size: 16px !important;
        }
        
        /* Touch-friendly checkboxes and radio buttons */
        .stCheckbox > label,
        .stRadio > label {
            min-height: 44px !important;
            display: flex !important;
            align-items: center !important;
            touch-action: manipulation !important;
        }
        
        /* Improve touch scrolling */
        .stVerticalBlock,
        .stHorizontalBlock {
            -webkit-overflow-scrolling: touch !important;
            scroll-behavior: smooth !important;
        }
        
        /* Touch-friendly slider */
        .stSlider > div > div > div {
            min-height: 44px !important;
        }
        
        /* Touch-friendly file uploader */
        .stFileUploader > div {
            min-height: 60px !important;
            touch-action: manipulation !important;
        }
        
        /* Prevent text selection on buttons */
        .stButton > button {
            -webkit-user-select: none !important;
            -moz-user-select: none !important;
            -ms-user-select: none !important;
            user-select: none !important;
        }
        
        /* Touch feedback */
        .stButton > button:active {
            transform: scale(0.98) !important;
            transition: transform 0.1s ease !important;
        }
        
        /* Improve tap targets */
        .stTabs [data-baseweb="tab"] {
            min-height: 44px !important;
            min-width: 44px !important;
            touch-action: manipulation !important;
        }
        </style>
        """
        
        st.markdown(touch_css, unsafe_allow_html=True)
    
    @staticmethod
    def add_haptic_feedback():
        """Add haptic feedback for touch interactions (where supported)."""
        haptic_js = """
        <script>
        function addHapticFeedback() {
            // Add haptic feedback to buttons
            const buttons = document.querySelectorAll('.stButton > button');
            buttons.forEach(button => {
                button.addEventListener('click', () => {
                    // Haptic feedback (if supported)
                    if (navigator.vibrate) {
                        navigator.vibrate(10); // 10ms vibration
                    }
                });
            });
            
            // Add haptic feedback to tabs
            const tabs = document.querySelectorAll('.stTabs [data-baseweb="tab"]');
            tabs.forEach(tab => {
                tab.addEventListener('click', () => {
                    if (navigator.vibrate) {
                        navigator.vibrate(5); // 5ms vibration
                    }
                });
            });
        }
        
        // Apply haptic feedback when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', addHapticFeedback);
        } else {
            addHapticFeedback();
        }
        
        // Reapply when Streamlit updates the page
        const observer = new MutationObserver(addHapticFeedback);
        observer.observe(document.body, { childList: true, subtree: true });
        </script>
        """
        
        st.components.v1.html(haptic_js, height=0)


class AdaptiveContent:
    """Provide adaptive content based on device capabilities."""
    
    @staticmethod
    def show_device_appropriate_content(mobile_content, desktop_content):
        """Show different content based on device type."""
        screen_info = ResponsiveLayout.get_screen_info()
        
        if screen_info['isMobile']:
            mobile_content()
        else:
            desktop_content()
    
    @staticmethod
    def adaptive_image_size(base_width: int = 400) -> int:
        """Get adaptive image size based on screen width."""
        screen_info = ResponsiveLayout.get_screen_info()
        
        if screen_info['isMobile']:
            return min(base_width, int(screen_info['width'] * 0.9))
        elif screen_info['isTablet']:
            return min(base_width, int(screen_info['width'] * 0.7))
        else:
            return base_width
    
    @staticmethod
    def adaptive_chart_height(base_height: int = 400) -> int:
        """Get adaptive chart height based on screen size."""
        screen_info = ResponsiveLayout.get_screen_info()
        
        if screen_info['isMobile']:
            return min(base_height, 300)
        elif screen_info['isTablet']:
            return min(base_height, 350)
        else:
            return base_height


def initialize_responsive_ui():
    """Initialize responsive UI components."""
    # Apply responsive CSS
    ResponsiveLayout.apply_responsive_css()
    
    # Apply touch optimizations
    TouchOptimization.apply_touch_styles()
    TouchOptimization.add_haptic_feedback()
    
    # Store screen info in session state
    screen_info = ResponsiveLayout.get_screen_info()
    st.session_state.screen_info = screen_info
    
    return {
        'layout': ResponsiveLayout,
        'components': MobileOptimizedComponents,
        'touch': TouchOptimization,
        'adaptive': AdaptiveContent
    }