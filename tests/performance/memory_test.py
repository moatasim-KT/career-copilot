"""
Memory leak testing for Career Copilot API
"""
import psutil
import time
import json
import requests
import threading
from datetime import datetime
import os


class MemoryMonitor:
    """Monitor memory usage during testing"""
    
    def __init__(self, process_name="python", interval=1):
        self.process_name = process_name
        self.interval = interval
        self.monitoring = False
        self.memory_data = []
        self.process = None
        
    def find_process(self):
        """Find the target process"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if self.process_name in proc.info['name']:
                    # Check if it's our application
                    cmdline = ' '.join(proc.info['cmdline'])
                    if 'career-copilot' in cmdline or 'uvicorn' in cmdline:
                        self.process = psutil.Process(proc.info['pid'])
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    
    def start_monitoring(self):
        """Start memory monitoring"""
        if not self.find_process():
            print("Target process not found")
            return False
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        return True
    
    def stop_monitoring(self):
        """Stop memory monitoring"""
        self.monitoring = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join()
    
    def _monitor_loop(self):
        """Memory monitoring loop"""
        while self.monitoring:
            try:
                if self.process and self.process.is_running():
                    memory_info = self.process.memory_info()
                    memory_data = {
                        'timestamp': datetime.now().isoformat(),
                        'rss': memory_info.rss,  # Resident Set Size
                        'vms': memory_info.vms,  # Virtual Memory Size
                        'percent': self.process.memory_percent(),
                        'available_memory': psutil.virtual_memory().available
                    }
                    self.memory_data.append(memory_data)
                else:
                    # Try to find the process again
                    self.find_process()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break
            except Exception as e:
                print(f"Memory monitoring error: {e}")
            
            time.sleep(self.interval)
    
    def get_memory_stats(self):
        """Get memory statistics"""
        if not self.memory_data:
            return None
            
        rss_values = [data['rss'] for data in self.memory_data]
        vms_values = [data['vms'] for data in self.memory_data]
        percent_values = [data['percent'] for data in self.memory_data]
        
        return {
            'duration': len(self.memory_data),
            'rss': {
                'min': min(rss_values),
                'max': max(rss_values),
                'avg': sum(rss_values) / len(rss_values),
                'current': rss_values[-1]
            },
            'vms': {
                'min': min(vms_values),
                'max': max(vms_values),
                'avg': sum(vms_values) / len(vms_values),
                'current': vms_values[-1]
            },
            'percent': {
                'min': min(percent_values),
                'max': max(percent_values),
                'avg': sum(percent_values) / len(percent_values),
                'current': percent_values[-1]
            },
            'memory_growth': rss_values[-1] - rss_values[0] if len(rss_values) > 1 else 0,
            'leak_detected': self._detect_memory_leak(rss_values)
        }
    
    def _detect_memory_leak(self, rss_values):
        """Detect potential memory leak"""
        if len(rss_values) < 10:
            return False
            
        # Check for consistent growth over time
        growth_rate = (rss_values[-1] - rss_values[0]) / len(rss_values)
        return growth_rate > 1024 * 1024  # 1MB per measurement


class APITester:
    """API testing class for memory leak detection"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.verify = False
        
    def health_check(self):
        """Perform health check"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/health")
            return response.status_code == 200
        except:
            return False
    
    def upload_file(self, content="Test content"):
        """Upload a test file"""
        files = {'file': ('test.txt', content, 'text/plain')}
        try:
            response = self.session.post(f"{self.base_url}/api/v1/upload", files=files)
            return response.status_code in [200, 201]
        except:
            return False
    
    def get_analytics(self):
        """Get analytics data"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/analytics")
            return response.status_code in [200, 401]
        except:
            return False
    
    def continuous_operations(self, duration=300):
        """Perform continuous operations for specified duration"""
        start_time = time.time()
        operations = 0
        
        while time.time() - start_time < duration:
            # Perform various operations
            self.health_check()
            if operations % 10 == 0:
                self.upload_file(f"Test content {operations}")
            if operations % 5 == 0:
                self.get_analytics()
            
            operations += 1
            time.sleep(0.1)  # Small delay between operations
        
        return operations


def run_memory_test():
    """Run memory leak test"""
    print("Starting memory leak test...")
    
    # Initialize monitor
    monitor = MemoryMonitor()
    if not monitor.start_monitoring():
        print("Failed to start memory monitoring")
        return
    
    # Initialize API tester
    api_tester = APITester()
    
    # Wait for API to be ready
    print("Waiting for API to be ready...")
    for _ in range(30):
        if api_tester.health_check():
            break
        time.sleep(1)
    else:
        print("API not ready, aborting test")
        monitor.stop_monitoring()
        return
    
    print("API is ready, starting memory test...")
    
    # Run continuous operations for 5 minutes
    operations = api_tester.continuous_operations(duration=300)
    
    # Stop monitoring
    monitor.stop_monitoring()
    
    # Get results
    stats = monitor.get_memory_stats()
    
    if stats:
        print(f"Memory test completed:")
        print(f"  Operations performed: {operations}")
        print(f"  Test duration: {stats['duration']} seconds")
        print(f"  RSS memory: {stats['rss']['min']} - {stats['rss']['max']} bytes")
        print(f"  Memory growth: {stats['memory_growth']} bytes")
        print(f"  Leak detected: {stats['leak_detected']}")
        
        # Save results
        results = {
            'test_info': {
                'timestamp': datetime.now().isoformat(),
                'operations': operations,
                'duration': stats['duration']
            },
            'memory_stats': stats,
            'raw_data': monitor.memory_data
        }
        
        with open('memory-test-results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print("Results saved to memory-test-results.json")
    else:
        print("No memory data collected")


if __name__ == "__main__":
    run_memory_test()
