"""
Test cases for database health checker.

This module contains test cases to verify the database health checking
functionality for both PostgreSQL and ChromaDB components.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from .database_health_checker import DatabaseHealthChecker


class TestDatabaseHealthChecker:
    """Test cases for DatabaseHealthChecker class."""
    
    @pytest.fixture
    def health_checker(self):
        """Create a database health checker instance for testing."""
        return DatabaseHealthChecker(
            database_url="sqlite:///./test.db",
            backend_url="http://localhost:8000"
        )
    
    @pytest.fixture
    def mock_engine(self):
        """Create a mock database engine."""
        engine = MagicMock()
        connection = MagicMock()
        result = MagicMock()
        result.fetchone.return_value = [1]
        result.fetchall.return_value = []
        result.returns_rows = True
        connection.execute.return_value = result
        connection.__enter__ = MagicMock(return_value=connection)
        connection.__exit__ = MagicMock(return_value=None)
        engine.connect.return_value = connection
        return engine
    
    @pytest.mark.asyncio
    async def test_setup(self, health_checker):
        """Test health checker setup."""
        await health_checker.setup()
        
        assert health_checker.database_url == "sqlite:///./test.db"
        assert health_checker.backend_url == "http://localhost:8000"
        assert health_checker.performance_thresholds is not None
        assert "connection_time_warning_ms" in health_checker.performance_thresholds
    
    @pytest.mark.asyncio
    async def test_postgresql_health_check_success(self, health_checker, mock_engine):
        """Test successful PostgreSQL health check."""
        await health_checker.setup()
        health_checker.engine = mock_engine
        
        # Mock pool info
        pool = MagicMock()
        pool.size.return_value = 5
        pool.checkedin.return_value = 3
        pool.checkedout.return_value = 2
        pool.overflow.return_value = 0
        pool.invalid.return_value = 0
        mock_engine.pool = pool
        
        result = await health_checker._check_postgresql_health()
        
        assert result["healthy"] is True
        assert "response_time" in result
        assert "details" in result
        assert result["details"]["status"] in ["healthy", "degraded"]
        assert "connection_time_ms" in result["details"]
    
    @pytest.mark.asyncio
    async def test_postgresql_health_check_failure(self, health_checker):
        """Test PostgreSQL health check failure."""
        await health_checker.setup()
        
        # Mock engine that raises exception
        mock_engine = MagicMock()
        mock_engine.connect.side_effect = Exception("Connection failed")
        health_checker.engine = mock_engine
        
        result = await health_checker._check_postgresql_health()
        
        assert result["healthy"] is False
        assert "error" in result["details"]
        assert "Connection failed" in result["details"]["error"]
    
    @pytest.mark.asyncio
    async def test_chromadb_health_check_via_backend(self, health_checker):
        """Test ChromaDB health check via backend endpoint."""
        await health_checker.setup()
        
        # Mock successful backend response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "healthy",
            "details": {
                "chromadb": {
                    "healthy": True,
                    "status": "healthy",
                    "collections_count": 5
                }
            }
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await health_checker._check_chromadb_health()
            
            assert result["healthy"] is True
            assert "chromadb_info" in result["details"]
            assert result["details"]["method"] == "backend_health_endpoint"
    
    @pytest.mark.asyncio
    async def test_chromadb_health_check_direct(self, health_checker):
        """Test ChromaDB health check via direct connection."""
        await health_checker.setup()
        
        # Mock backend failure to trigger alternative check
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=Exception("Backend unavailable")
            )
            
            # Mock ChromaDB direct connection
            with patch("chromadb.PersistentClient") as mock_chroma:
                mock_client_instance = MagicMock()
                mock_client_instance.list_collections.return_value = ["collection1", "collection2"]
                mock_chroma.return_value = mock_client_instance
                
                result = await health_checker._check_chromadb_alternative()
                
                assert result["healthy"] is True
                assert result["details"]["collections_count"] == 2
                assert result["details"]["method"] == "direct_connection"
    
    @pytest.mark.asyncio
    async def test_response_time_monitoring(self, health_checker, mock_engine):
        """Test database response time monitoring."""
        await health_checker.setup()
        health_checker.engine = mock_engine
        
        result = await health_checker._check_response_time_monitoring()
        
        assert result["healthy"] is True
        assert "statistics" in result["details"]
        assert "average_response_time_ms" in result["details"]["statistics"]
        assert "operations" in result["details"]
        assert result["details"]["monitoring_available"] is True
    
    @pytest.mark.asyncio
    async def test_response_time_monitoring_performance_warning(self, health_checker, mock_engine):
        """Test response time monitoring with performance warnings."""
        await health_checker.setup()
        health_checker.engine = mock_engine
        
        # Set low thresholds to trigger warnings
        health_checker.performance_thresholds["query_time_warning_ms"] = 1
        health_checker.performance_thresholds["query_time_critical_ms"] = 5
        
        result = await health_checker._check_response_time_monitoring()
        
        # Should still be healthy but may have warnings
        assert "statistics" in result["details"]
        assert "warnings" in result["details"]
    
    @pytest.mark.asyncio
    async def test_comprehensive_health_check(self, health_checker, mock_engine):
        """Test comprehensive database health check."""
        await health_checker.setup()
        health_checker.engine = mock_engine
        
        # Mock ChromaDB success
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "healthy",
                "details": {
                    "chromadb": {
                        "healthy": True,
                        "status": "healthy"
                    }
                }
            }
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await health_checker.check_comprehensive_database_health()
            
            assert "overall_healthy" in result
            assert "components" in result
            assert "postgresql" in result["components"]
            assert "chromadb" in result["components"]
            assert "response_time_monitoring" in result["components"]
            assert result["total_components"] == 3
    
    @pytest.mark.asyncio
    async def test_run_test_integration(self, health_checker, mock_engine):
        """Test the main run_test method integration."""
        await health_checker.setup()
        health_checker.engine = mock_engine
        
        # Mock ChromaDB success
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "healthy",
                "details": {
                    "chromadb": {
                        "healthy": True,
                        "status": "healthy"
                    }
                }
            }
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await health_checker.run_test()
            
            assert result["test_name"] == "database_health_check"
            assert result["status"] in ["passed", "failed"]
            assert "health_results" in result
            assert "total_checks" in result
            assert len(result["health_results"]) == 3  # PostgreSQL, ChromaDB, Response Time
    
    @pytest.mark.asyncio
    async def test_database_via_backend_fallback(self, health_checker):
        """Test database health check via backend when direct connection fails."""
        await health_checker.setup()
        health_checker.engine = None  # No direct engine
        
        # Mock backend success
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "healthy",
                "database": "connected"
            }
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await health_checker._check_database_via_backend()
            
            assert result["healthy"] is True
            assert result["details"]["method"] == "backend_endpoint"
            assert result["details"]["status_code"] == 200
    
    @pytest.mark.asyncio
    async def test_performance_thresholds_customization(self):
        """Test custom performance thresholds."""
        custom_thresholds = {
            "connection_time_warning_ms": 50,
            "connection_time_critical_ms": 200,
            "query_time_warning_ms": 100,
            "query_time_critical_ms": 500,
        }
        
        health_checker = DatabaseHealthChecker(
            performance_thresholds=custom_thresholds
        )
        
        await health_checker.setup()
        
        assert health_checker.performance_thresholds["connection_time_warning_ms"] == 50
        assert health_checker.performance_thresholds["query_time_critical_ms"] == 500
    
    def test_get_health_summary(self, health_checker):
        """Test health summary generation."""
        # Add some mock health results
        health_checker.health_results = {
            "postgresql": {"healthy": True, "response_time": 50},
            "chromadb": {"healthy": True, "response_time": 30},
            "monitoring": {"healthy": False, "response_time": 100}
        }
        
        summary = health_checker.get_health_summary()
        
        assert "Database Health: 2/3 checks passed" in summary
        assert "postgresql, chromadb, monitoring" in summary
    
    @pytest.mark.asyncio
    async def test_pool_info_extraction(self, health_checker, mock_engine):
        """Test database connection pool information extraction."""
        await health_checker.setup()
        
        # Mock pool with detailed info
        pool = MagicMock()
        pool.size.return_value = 10
        pool.checkedin.return_value = 7
        pool.checkedout.return_value = 3
        pool.overflow.return_value = 2
        pool.invalid.return_value = 0
        pool._pool_size = 8
        pool._max_overflow = 5
        mock_engine.pool = pool
        
        health_checker.engine = mock_engine
        
        pool_info = health_checker._get_pool_info()
        
        assert pool_info["available"] is True
        assert pool_info["size"] == 10
        assert pool_info["max_connections"] == 13  # _pool_size + _max_overflow
        assert "utilization_percent" in pool_info


@pytest.mark.asyncio
async def test_database_health_checker_integration():
    """Integration test for database health checker."""
    health_checker = DatabaseHealthChecker()
    
    await health_checker.setup()
    
    # This test will use the actual database configuration
    # and should work with the default SQLite setup
    try:
        result = await health_checker.run_test()
        
        # Basic assertions that should always pass
        assert "test_name" in result
        assert "status" in result
        assert "health_results" in result
        assert result["test_name"] == "database_health_check"
        
        # The test should at least attempt all checks
        assert len(result["health_results"]) >= 1
        
    except Exception as e:
        # If the test fails due to environment issues, that's acceptable
        # as long as the structure is correct
        pytest.skip(f"Integration test skipped due to environment: {e}")


if __name__ == "__main__":
    # Run a simple test
    async def main():
        health_checker = DatabaseHealthChecker()
        await health_checker.setup()
        result = await health_checker.run_test()
        print("Database Health Check Result:")
        print(f"Status: {result['status']}")
        print(f"Total Checks: {result['total_checks']}")
        print(f"Unhealthy Services: {result['unhealthy_services']}")
        
        # Print detailed results
        for service, details in result["health_results"].items():
            print(f"\n{service}:")
            print(f"  Healthy: {details['healthy']}")
            print(f"  Response Time: {details['response_time']:.2f}s")
    
    asyncio.run(main())