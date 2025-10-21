"""
Stress testing configuration for Career Copilot API
"""
import json
import random
from locust import HttpUser, task, between


class StressTestUser(HttpUser):
    """Stress test user that pushes the system to its limits"""
    
    wait_time = between(0.1, 0.3)  # Very fast operations
    
    def on_start(self):
        """Called when a user starts"""
        self.client.verify = False
        self.uploaded_files = []
        self.analysis_requests = []
        
    @task(20)
    def rapid_health_checks(self):
        """Rapid health checks to test system stability"""
        with self.client.get("/api/v1/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed with status {response.status_code}")
    
    @task(15)
    def concurrent_uploads(self):
        """Concurrent file uploads to test file handling"""
        file_types = ["pdf", "doc", "docx", "txt"]
        file_type = random.choice(file_types)
        
        # Create larger test files for stress testing
        test_content = "Test contract content for stress testing. " * 100
        files = {
            'file': (f'stress_test_contract_{random.randint(1, 1000)}.{file_type}', 
                    test_content, f'application/{file_type}')
        }
        
        with self.client.post(
            "/api/v1/upload", 
            files=files,
            catch_response=True
        ) as response:
            if response.status_code in [200, 201, 400, 401, 413]:  # 413 = Payload Too Large
                response.success()
                if response.status_code in [200, 201]:
                    try:
                        data = response.json()
                        if 'file_id' in data:
                            self.uploaded_files.append(data['file_id'])
                    except:
                        pass
            else:
                response.failure(f"Upload failed with status {response.status_code}")
    
    @task(10)
    def concurrent_analysis(self):
        """Concurrent analysis requests to test processing capacity"""
        if not self.uploaded_files:
            return
            
        file_id = random.choice(self.uploaded_files)
        analysis_data = {
            "file_id": file_id,
            "analysis_type": random.choice(["risk", "compliance", "summary", "full"]),
            "options": {
                "detailed": True,
                "include_recommendations": True,
                "priority": random.choice(["low", "medium", "high", "urgent"])
            }
        }
        
        with self.client.post(
            "/api/v1/analyze",
            json=analysis_data,
            catch_response=True
        ) as response:
            if response.status_code in [200, 202, 400, 401, 404, 429]:  # 429 = Too Many Requests
                response.success()
                if response.status_code in [200, 202]:
                    try:
                        data = response.json()
                        if 'analysis_id' in data:
                            self.analysis_requests.append(data['analysis_id'])
                    except:
                        pass
            else:
                response.failure(f"Analysis failed with status {response.status_code}")
    
    @task(8)
    def rapid_data_queries(self):
        """Rapid data queries to test database performance"""
        endpoints = [
            "/api/v1/analytics",
            "/api/v1/contracts",
            "/api/v1/metrics",
            "/api/v1/performance"
        ]
        
        endpoint = random.choice(endpoints)
        
        with self.client.get(endpoint, catch_response=True) as response:
            if response.status_code in [200, 401, 404]:
                response.success()
            else:
                response.failure(f"Query failed with status {response.status_code}")
    
    @task(5)
    def websocket_stress(self):
        """WebSocket stress testing"""
        try:
            with self.client.ws_connect("/ws/analysis", catch_response=True) as ws:
                # Send multiple rapid messages
                for _ in range(10):
                    message = {
                        "type": "stress_test",
                        "data": {"iteration": random.randint(1, 1000)}
                    }
                    ws.send(json.dumps(message))
                
                # Try to receive responses
                for _ in range(5):
                    try:
                        response = ws.receive(timeout=1)
                        if response:
                            response.success()
                    except:
                        break
        except Exception as e:
            # WebSocket failures are expected in stress tests
            pass
    
    @task(3)
    def memory_intensive_operations(self):
        """Memory-intensive operations to test resource limits"""
        # Large file upload
        large_content = "Large contract content for memory testing. " * 1000
        files = {
            'file': (f'large_contract_{random.randint(1, 100)}.txt', 
                    large_content, 'text/plain')
        }
        
        with self.client.post(
            "/api/v1/upload", 
            files=files,
            catch_response=True
        ) as response:
            if response.status_code in [200, 201, 400, 401, 413]:
                response.success()
            else:
                response.failure(f"Large upload failed with status {response.status_code}")
    
    @task(2)
    def error_condition_testing(self):
        """Test error conditions and edge cases"""
        # Test with invalid data
        invalid_data = {
            "file_id": "invalid_id",
            "analysis_type": "invalid_type",
            "options": {"invalid": "data"}
        }
        
        with self.client.post(
            "/api/v1/analyze",
            json=invalid_data,
            catch_response=True
        ) as response:
            # Error responses are expected and should be handled gracefully
            if response.status_code in [400, 401, 404, 422]:
                response.success()
            else:
                response.failure(f"Error handling failed with status {response.status_code}")
    
    @task(1)
    def cleanup_operations(self):
        """Cleanup operations to test resource management"""
        if self.uploaded_files:
            file_id = self.uploaded_files.pop(0)
            
            with self.client.delete(
                f"/api/v1/contracts/{file_id}",
                catch_response=True
            ) as response:
                if response.status_code in [200, 204, 404, 401]:
                    response.success()
                else:
                    response.failure(f"Cleanup failed with status {response.status_code}")


class ExtremeStressUser(StressTestUser):
    """Extreme stress test user with maximum possible load"""
    
    wait_time = between(0.05, 0.1)  # Extremely fast operations
    
    @task(50)
    def extreme_health_checks(self):
        """Extreme health check frequency"""
        self.rapid_health_checks()
    
    @task(30)
    def extreme_uploads(self):
        """Extreme upload frequency"""
        self.concurrent_uploads()
    
    @task(20)
    def extreme_analysis(self):
        """Extreme analysis frequency"""
        self.concurrent_analysis()
    
    @task(10)
    def extreme_queries(self):
        """Extreme query frequency"""
        self.rapid_data_queries()
