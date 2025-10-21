/**
 * Test API Integration
 * Simple test to verify API client functionality
 */

async function testAPIIntegration() {
    console.log('Testing API Integration...');
    
    const apiClient = new APIClient();
    
    try {
        // Test 1: Get jobs
        console.log('Test 1: Getting jobs...');
        const jobs = await apiClient.getJobs({ limit: 5 });
        console.log('✓ Jobs retrieved:', jobs.length, 'jobs');
        
        // Test 2: Get statistics
        console.log('Test 2: Getting statistics...');
        const stats = await apiClient.getStatistics();
        console.log('✓ Statistics retrieved:', stats);
        
        // Test 3: Create a test job (if API is available)
        console.log('Test 3: Creating test job...');
        const testJob = {
            company: 'Test Company',
            position: 'Test Position',
            location: 'Test Location',
            status: 'wishlist'
        };
        
        const createdJob = await apiClient.createJob(testJob);
        console.log('✓ Job created:', createdJob);
        
        // Test 4: Update the test job
        if (createdJob && createdJob.id) {
            console.log('Test 4: Updating test job...');
            const updatedJob = await apiClient.updateJob(createdJob.id, { status: 'applied' });
            console.log('✓ Job updated:', updatedJob);
            
            // Test 5: Delete the test job
            console.log('Test 5: Deleting test job...');
            await apiClient.deleteJob(createdJob.id);
            console.log('✓ Job deleted');
        }
        
        console.log('🎉 All API tests passed!');
        return true;
        
    } catch (error) {
        console.error('❌ API test failed:', error);
        
        if (error instanceof APIError) {
            console.error('API Error Details:', {
                status: error.status,
                message: error.message,
                data: error.data
            });
        }
        
        return false;
    }
}

// Test toast notifications
function testToastNotifications() {
    console.log('Testing toast notifications...');
    
    ToastNotification.success('Success notification test');
    
    setTimeout(() => {
        ToastNotification.error('Error notification test');
    }, 1000);
    
    setTimeout(() => {
        ToastNotification.warning('Warning notification test');
    }, 2000);
    
    setTimeout(() => {
        ToastNotification.info('Info notification test');
    }, 3000);
}

// Run tests when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Add test button to page
    const testButton = document.createElement('button');
    testButton.textContent = 'Test API Integration';
    testButton.className = 'fixed bottom-4 left-4 bg-green-600 text-white px-4 py-2 rounded shadow-lg z-50';
    testButton.onclick = testAPIIntegration;
    document.body.appendChild(testButton);
    
    // Add toast test button
    const toastButton = document.createElement('button');
    toastButton.textContent = 'Test Notifications';
    toastButton.className = 'fixed bottom-4 left-40 bg-blue-600 text-white px-4 py-2 rounded shadow-lg z-50';
    toastButton.onclick = testToastNotifications;
    document.body.appendChild(toastButton);
});

// Export for manual testing
window.testAPIIntegration = testAPIIntegration;
window.testToastNotifications = testToastNotifications;