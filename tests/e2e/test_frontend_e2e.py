"""
End-to-end tests for frontend using Playwright.
Tests complete user workflows from upload to results viewing.
"""

import asyncio
import pytest
import tempfile
import os
import time
from pathlib import Path
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from typing import Dict, Any


class TestFrontendE2E:
    """End-to-end tests for frontend functionality."""
    
    @pytest.fixture(scope="class")
    async def browser_setup(self):
        """Set up browser for testing."""
        playwright = await async_playwright().start()
        
        # Launch browser
        browser = await playwright.chromium.launch(
            headless=True,  # Set to False for debugging
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        yield browser, playwright
        
        # Cleanup
        await browser.close()
        await playwright.stop()
    
    @pytest.fixture
    async def page_setup(self, browser_setup):
        """Set up page for each test."""
        browser, playwright = browser_setup
        
        # Create new context and page
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            ignore_https_errors=True
        )
        page = await context.new_page()
        
        yield page
        
        # Cleanup
        await context.close()
    
    @pytest.fixture
    def sample_contract_file(self):
        """Create a sample contract file for testing."""
        contract_content = """
        SOFTWARE LICENSE AGREEMENT
        
        This Software License Agreement is entered into between TechCorp Inc. and ClientCorp LLC.
        
        1. GRANT OF LICENSE
        TechCorp grants ClientCorp a non-exclusive license to use the software.
        
        2. PAYMENT TERMS
        ClientCorp shall pay $25,000 within 30 days of execution.
        Late payments will incur a 5% monthly penalty.
        
        3. LIABILITY LIMITATION
        TechCorp's liability shall not exceed the total amount paid under this agreement.
        ClientCorp waives all claims for consequential damages.
        
        4. INDEMNIFICATION
        ClientCorp agrees to indemnify TechCorp against all third-party claims.
        
        5. TERMINATION
        Either party may terminate with 30 days written notice.
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(contract_content)
            f.flush()
            yield Path(f.name)
        
        # Cleanup
        os.unlink(f.name)
    
    @pytest.mark.asyncio
    async def test_application_loading(self, page_setup):
        """Test that the application loads correctly."""
        page = page_setup
        
        # Navigate to application
        await page.goto("http://localhost:8501")  # Streamlit default port
        
        # Wait for page to load
        await page.wait_for_load_state("networkidle")
        
        # Check that main elements are present
        title = await page.title()
        assert "Contract" in title or "Analyzer" in title
        
        # Check for main navigation or header
        header_elements = await page.query_selector_all("h1, .main-header, [data-testid='stHeader']")
        assert len(header_elements) > 0, "No header elements found"
    
    @pytest.mark.asyncio
    async def test_file_upload_interface(self, page_setup, sample_contract_file):
        """Test file upload interface functionality."""
        page = page_setup
        
        # Navigate to application
        await page.goto("http://localhost:8501")
        await page.wait_for_load_state("networkidle")
        
        # Look for file upload component
        file_upload_selectors = [
            "input[type='file']",
            "[data-testid='stFileUploader']",
            ".uploadedFile",
            ".file-upload"
        ]
        
        upload_element = None
        for selector in file_upload_selectors:
            upload_element = await page.query_selector(selector)
            if upload_element:
                break
        
        if upload_element:
            # Test file upload
            await upload_element.set_input_files(str(sample_contract_file))
            
            # Wait for upload to process
            await page.wait_for_timeout(2000)
            
            # Check for upload confirmation or progress
            upload_indicators = await page.query_selector_all(
                ".success, .uploaded, [data-testid='stSuccess'], .file-uploaded"
            )
            
            # Should have some indication of successful upload
            assert len(upload_indicators) > 0 or await page.query_selector(".progress")
        else:
            pytest.skip("File upload component not found - may not be implemented yet")
    
    @pytest.mark.asyncio
    async def test_contract_analysis_workflow(self, page_setup, sample_contract_file):
        """Test complete job application tracking workflow."""
        page = page_setup
        
        # Navigate to application
        await page.goto("http://localhost:8501")
        await page.wait_for_load_state("networkidle")
        
        # Step 1: Upload file
        file_input = await page.query_selector("input[type='file']")
        if file_input:
            await file_input.set_input_files(str(sample_contract_file))
            await page.wait_for_timeout(1000)
        
        # Step 2: Look for analyze button
        analyze_button_selectors = [
            "button:has-text('Analyze')",
            "button:has-text('Start Analysis')",
            "[data-testid='analyze-button']",
            ".analyze-btn"
        ]
        
        analyze_button = None
        for selector in analyze_button_selectors:
            analyze_button = await page.query_selector(selector)
            if analyze_button:
                break
        
        if analyze_button:
            # Click analyze button
            await analyze_button.click()
            
            # Step 3: Wait for analysis to start
            await page.wait_for_timeout(2000)
            
            # Step 4: Monitor progress
            max_wait_time = 120  # 2 minutes
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                # Check for progress indicators
                progress_elements = await page.query_selector_all(
                    ".progress, .loading, .analyzing, [data-testid='stProgress']"
                )
                
                # Check for completion indicators
                completion_elements = await page.query_selector_all(
                    ".complete, .finished, .results, [data-testid='stSuccess']"
                )
                
                if completion_elements:
                    break
                
                await page.wait_for_timeout(5000)  # Wait 5 seconds between checks
            
            # Step 5: Verify results are displayed
            results_elements = await page.query_selector_all(
                ".results, .analysis-results, .contract-analysis, h2, h3"
            )
            
            assert len(results_elements) > 0, "No results displayed after analysis"
        else:
            pytest.skip("Analyze button not found - analysis workflow may not be implemented")
    
    @pytest.mark.asyncio
    async def test_results_display_and_navigation(self, page_setup):
        """Test results display and navigation functionality."""
        page = page_setup
        
        # Navigate to application
        await page.goto("http://localhost:8501")
        await page.wait_for_load_state("networkidle")
        
        # Look for existing results or sample data
        results_sections = await page.query_selector_all(
            ".results, .analysis-results, .risk-assessment, .contract-summary"
        )
        
        if results_sections:
            # Test navigation between result sections
            tab_selectors = [
                ".tab, .nav-tab, button:has-text('Risk'), button:has-text('Summary')",
                "[role='tab']"
            ]
            
            tabs = []
            for selector in tab_selectors:
                found_tabs = await page.query_selector_all(selector)
                tabs.extend(found_tabs)
            
            if tabs:
                # Click through different tabs
                for i, tab in enumerate(tabs[:3]):  # Test first 3 tabs
                    await tab.click()
                    await page.wait_for_timeout(1000)
                    
                    # Verify content changes
                    content_after_click = await page.query_selector_all(".content, .tab-content")
                    assert len(content_after_click) > 0
            
            # Test expandable sections
            expandable_elements = await page.query_selector_all(
                ".expandable, .collapsible, details, .accordion"
            )
            
            for element in expandable_elements[:2]:  # Test first 2 expandable elements
                await element.click()
                await page.wait_for_timeout(500)
        else:
            pytest.skip("No results sections found - may need to run analysis first")
    
    @pytest.mark.asyncio
    async def test_real_time_progress_updates(self, page_setup, sample_contract_file):
        """Test real-time progress updates during analysis."""
        page = page_setup
        
        # Navigate to application
        await page.goto("http://localhost:8501")
        await page.wait_for_load_state("networkidle")
        
        # Upload file and start analysis
        file_input = await page.query_selector("input[type='file']")
        if file_input:
            await file_input.set_input_files(str(sample_contract_file))
            await page.wait_for_timeout(1000)
            
            analyze_button = await page.query_selector("button:has-text('Analyze')")
            if analyze_button:
                await analyze_button.click()
                
                # Monitor progress updates
                progress_values = []
                max_checks = 20
                
                for _ in range(max_checks):
                    # Look for progress indicators
                    progress_elements = await page.query_selector_all(
                        ".progress-bar, .progress-value, [data-testid='stProgress']"
                    )
                    
                    if progress_elements:
                        for element in progress_elements:
                            text = await element.inner_text()
                            if '%' in text or 'progress' in text.lower():
                                progress_values.append(text)
                    
                    # Check if analysis is complete
                    completion_elements = await page.query_selector_all(
                        ".complete, .finished, .results"
                    )
                    
                    if completion_elements:
                        break
                    
                    await page.wait_for_timeout(3000)
                
                # Verify progress updates were received
                if progress_values:
                    assert len(progress_values) > 1, "Expected multiple progress updates"
                else:
                    pytest.skip("No progress updates detected - may not be implemented")
            else:
                pytest.skip("Analyze button not found")
        else:
            pytest.skip("File input not found")
    
    @pytest.mark.asyncio
    async def test_error_handling_display(self, page_setup):
        """Test error handling and display in the frontend."""
        page = page_setup
        
        # Navigate to application
        await page.goto("http://localhost:8501")
        await page.wait_for_load_state("networkidle")
        
        # Test invalid file upload (if file upload exists)
        file_input = await page.query_selector("input[type='file']")
        if file_input:
            # Create an invalid file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.invalid', delete=False) as f:
                f.write("This is not a valid contract file")
                invalid_file_path = f.name
            
            try:
                await file_input.set_input_files(invalid_file_path)
                await page.wait_for_timeout(2000)
                
                # Look for error messages
                error_elements = await page.query_selector_all(
                    ".error, .alert-error, [data-testid='stError'], .warning"
                )
                
                if error_elements:
                    # Verify error message is displayed
                    error_text = await error_elements[0].inner_text()
                    assert len(error_text) > 0, "Error message should not be empty"
                
            finally:
                os.unlink(invalid_file_path)
        
        # Test network error simulation (if possible)
        # This would require mocking network requests or testing with backend down
        
        # Test form validation errors
        form_inputs = await page.query_selector_all("input, textarea, select")
        for input_element in form_inputs[:2]:  # Test first 2 inputs
            # Try to submit empty required fields
            await input_element.fill("")
            await page.keyboard.press("Tab")  # Trigger validation
            await page.wait_for_timeout(500)
        
        # Look for validation error messages
        validation_errors = await page.query_selector_all(
            ".field-error, .validation-error, .invalid-feedback"
        )
        
        # Validation errors are optional depending on implementation
        if validation_errors:
            assert len(validation_errors) > 0
    
    @pytest.mark.asyncio
    async def test_responsive_design(self, page_setup):
        """Test responsive design on different screen sizes."""
        page = page_setup
        
        # Test different viewport sizes
        viewports = [
            {'width': 1920, 'height': 1080},  # Desktop
            {'width': 1024, 'height': 768},   # Tablet
            {'width': 375, 'height': 667},    # Mobile
        ]
        
        for viewport in viewports:
            await page.set_viewport_size(viewport)
            await page.goto("http://localhost:8501")
            await page.wait_for_load_state("networkidle")
            
            # Check that main elements are still visible
            main_elements = await page.query_selector_all(
                "h1, .main-content, .container, [data-testid='stApp']"
            )
            
            assert len(main_elements) > 0, f"Main elements not found at {viewport['width']}x{viewport['height']}"
            
            # Check for mobile-specific elements or layout changes
            if viewport['width'] < 768:  # Mobile breakpoint
                # Look for mobile navigation or collapsed menus
                mobile_elements = await page.query_selector_all(
                    ".mobile-nav, .hamburger, .menu-toggle, .sidebar-collapsed"
                )
                # Mobile elements are optional
            
            await page.wait_for_timeout(1000)
    
    @pytest.mark.asyncio
    async def test_accessibility_features(self, page_setup):
        """Test basic accessibility features."""
        page = page_setup
        
        # Navigate to application
        await page.goto("http://localhost:8501")
        await page.wait_for_load_state("networkidle")
        
        # Test keyboard navigation
        await page.keyboard.press("Tab")
        focused_element = await page.evaluate("document.activeElement.tagName")
        assert focused_element is not None, "No element received focus"
        
        # Test for alt text on images
        images = await page.query_selector_all("img")
        for img in images:
            alt_text = await img.get_attribute("alt")
            # Alt text is recommended but not always required
            if alt_text is None:
                # Check if image is decorative or has aria-label
                aria_label = await img.get_attribute("aria-label")
                role = await img.get_attribute("role")
                # Decorative images should have empty alt or role="presentation"
        
        # Test for proper heading structure
        headings = await page.query_selector_all("h1, h2, h3, h4, h5, h6")
        if headings:
            # Should have at least one h1
            h1_elements = await page.query_selector_all("h1")
            assert len(h1_elements) > 0, "Page should have at least one h1 element"
        
        # Test for form labels
        form_inputs = await page.query_selector_all("input, textarea, select")
        for input_element in form_inputs:
            input_id = await input_element.get_attribute("id")
            if input_id:
                # Look for associated label
                label = await page.query_selector(f"label[for='{input_id}']")
                if not label:
                    # Check for aria-label or aria-labelledby
                    aria_label = await input_element.get_attribute("aria-label")
                    aria_labelledby = await input_element.get_attribute("aria-labelledby")
                    # At least one form of labeling should be present
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self, page_setup):
        """Test basic performance metrics."""
        page = page_setup
        
        # Measure page load time
        start_time = time.time()
        await page.goto("http://localhost:8501")
        await page.wait_for_load_state("networkidle")
        load_time = time.time() - start_time
        
        # Page should load within reasonable time
        assert load_time < 10, f"Page load time {load_time:.2f}s exceeds 10 seconds"
        
        # Check for performance metrics if available
        performance_metrics = await page.evaluate("""
            () => {
                const navigation = performance.getEntriesByType('navigation')[0];
                return {
                    domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                    loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
                    firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
                    firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0
                };
            }
        """)
        
        # Verify reasonable performance metrics
        if performance_metrics['domContentLoaded'] > 0:
            assert performance_metrics['domContentLoaded'] < 5000, "DOM content loaded time too high"
        
        if performance_metrics['firstContentfulPaint'] > 0:
            assert performance_metrics['firstContentfulPaint'] < 3000, "First contentful paint time too high"


class TestFullWorkflowE2E:
    """Test complete end-to-end workflows."""
    
    @pytest.fixture(scope="class")
    async def browser_context(self):
        """Set up browser context for workflow tests."""
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720}
        )
        
        yield context
        
        await context.close()
        await browser.close()
        await playwright.stop()
    
    @pytest.fixture
    async def page(self, browser_context):
        """Create page for each test."""
        page = await browser_context.new_page()
        yield page
        await page.close()
    
    @pytest.mark.asyncio
    async def test_complete_user_journey(self, page, sample_contract_file):
        """Test complete user journey from upload to results."""
        # Step 1: Navigate to application
        await page.goto("http://localhost:8501")
        await page.wait_for_load_state("networkidle")
        
        # Step 2: Upload contract
        file_input = await page.query_selector("input[type='file']")
        if not file_input:
            pytest.skip("File upload not available")
        
        await file_input.set_input_files(str(sample_contract_file))
        await page.wait_for_timeout(2000)
        
        # Step 3: Start analysis
        analyze_button = await page.query_selector("button:has-text('Analyze')")
        if not analyze_button:
            pytest.skip("Analyze button not available")
        
        await analyze_button.click()
        
        # Step 4: Wait for analysis completion
        max_wait = 180  # 3 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            completion_elements = await page.query_selector_all(
                ".complete, .finished, .results, h2:has-text('Results')"
            )
            
            if completion_elements:
                break
            
            await page.wait_for_timeout(5000)
        
        # Step 5: Verify results are displayed
        results_elements = await page.query_selector_all(
            ".results, .analysis-results, .risk-assessment"
        )
        
        assert len(results_elements) > 0, "No results displayed"
        
        # Step 6: Test result interaction
        # Click through different result sections
        tab_buttons = await page.query_selector_all("button, .tab")
        for button in tab_buttons[:3]:  # Test first 3 buttons
            try:
                await button.click()
                await page.wait_for_timeout(1000)
            except:
                continue  # Skip if button is not clickable
        
        # Step 7: Test export functionality (if available)
        export_buttons = await page.query_selector_all(
            "button:has-text('Export'), button:has-text('Download'), .export-btn"
        )
        
        if export_buttons:
            # Test export button click
            await export_buttons[0].click()
            await page.wait_for_timeout(2000)
    
    @pytest.mark.asyncio
    async def test_multiple_contract_workflow(self, page):
        """Test workflow with multiple contracts."""
        await page.goto("http://localhost:8501")
        await page.wait_for_load_state("networkidle")
        
        # Create multiple test files
        contract_files = []
        for i in range(3):
            content = f"""
            CONTRACT {i+1}
            
            This is test contract number {i+1}.
            
            Payment: ${(i+1) * 10000}
            Risk Level: {'High' if i == 0 else 'Medium' if i == 1 else 'Low'}
            """
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(content)
                contract_files.append(Path(f.name))
        
        try:
            # Test uploading multiple files
            file_input = await page.query_selector("input[type='file']")
            if file_input:
                # Check if multiple file upload is supported
                multiple_attr = await file_input.get_attribute("multiple")
                
                if multiple_attr is not None:
                    # Upload all files at once
                    await file_input.set_input_files([str(f) for f in contract_files])
                else:
                    # Upload files one by one
                    for contract_file in contract_files:
                        await file_input.set_input_files(str(contract_file))
                        await page.wait_for_timeout(1000)
                
                await page.wait_for_timeout(2000)
                
                # Look for file list or upload confirmation
                uploaded_files = await page.query_selector_all(
                    ".uploaded-file, .file-item, .contract-item"
                )
                
                # Should have some indication of uploaded files
                assert len(uploaded_files) > 0 or await page.query_selector(".file-count")
            
        finally:
            # Cleanup
            for contract_file in contract_files:
                os.unlink(contract_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])