"""
Database performance testing for Career Copilot API
"""
import psycopg2
import time
import json
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import os


class DatabasePerformanceTester:
    """Test database performance under various loads"""
    
    def __init__(self, db_url="postgresql://contract_user:contract_password@localhost:5432/contract_analyzer_test"):
        self.db_url = db_url
        self.connection_pool = []
        self.results = {
            'connection_tests': [],
            'query_tests': [],
            'concurrent_tests': [],
            'transaction_tests': []
        }
    
    def create_connection(self):
        """Create a new database connection"""
        try:
            conn = psycopg2.connect(self.db_url)
            return conn
        except Exception as e:
            print(f"Failed to create connection: {e}")
            return None
    
    def test_connection_performance(self, num_connections=10):
        """Test database connection performance"""
        print(f"Testing {num_connections} database connections...")
        
        start_time = time.time()
        connections = []
        
        for i in range(num_connections):
            conn_start = time.time()
            conn = self.create_connection()
            conn_end = time.time()
            
            if conn:
                connections.append(conn)
                self.results['connection_tests'].append({
                    'connection_id': i,
                    'connection_time': conn_end - conn_start,
                    'success': True
                })
            else:
                self.results['connection_tests'].append({
                    'connection_id': i,
                    'connection_time': conn_end - conn_start,
                    'success': False
                })
        
        total_time = time.time() - start_time
        
        # Close connections
        for conn in connections:
            conn.close()
        
        print(f"Connection test completed in {total_time:.2f} seconds")
        return {
            'total_connections': num_connections,
            'successful_connections': len(connections),
            'total_time': total_time,
            'avg_connection_time': total_time / num_connections
        }
    
    def test_query_performance(self, num_queries=100):
        """Test query performance"""
        print(f"Testing {num_queries} database queries...")
        
        conn = self.create_connection()
        if not conn:
            print("Failed to create database connection")
            return None
        
        cursor = conn.cursor()
        
        # Test queries
        queries = [
            "SELECT 1",  # Simple query
            "SELECT COUNT(*) FROM information_schema.tables",  # Metadata query
            "SELECT current_timestamp",  # Function query
            "SELECT version()",  # System query
        ]
        
        query_results = []
        
        for i in range(num_queries):
            query = queries[i % len(queries)]
            
            start_time = time.time()
            try:
                cursor.execute(query)
                result = cursor.fetchone()
                end_time = time.time()
                
                query_results.append({
                    'query_id': i,
                    'query': query,
                    'execution_time': end_time - start_time,
                    'success': True,
                    'result': str(result) if result else None
                })
            except Exception as e:
                end_time = time.time()
                query_results.append({
                    'query_id': i,
                    'query': query,
                    'execution_time': end_time - start_time,
                    'success': False,
                    'error': str(e)
                })
        
        cursor.close()
        conn.close()
        
        successful_queries = [q for q in query_results if q['success']]
        avg_execution_time = sum(q['execution_time'] for q in successful_queries) / len(successful_queries) if successful_queries else 0
        
        print(f"Query test completed: {len(successful_queries)}/{num_queries} successful")
        print(f"Average execution time: {avg_execution_time:.4f} seconds")
        
        self.results['query_tests'] = query_results
        
        return {
            'total_queries': num_queries,
            'successful_queries': len(successful_queries),
            'avg_execution_time': avg_execution_time,
            'max_execution_time': max(q['execution_time'] for q in successful_queries) if successful_queries else 0,
            'min_execution_time': min(q['execution_time'] for q in successful_queries) if successful_queries else 0
        }
    
    def test_concurrent_queries(self, num_threads=10, queries_per_thread=10):
        """Test concurrent query performance"""
        print(f"Testing {num_threads} concurrent threads with {queries_per_thread} queries each...")
        
        def worker_thread(thread_id):
            """Worker thread for concurrent testing"""
            conn = self.create_connection()
            if not conn:
                return {
                    'thread_id': thread_id,
                    'success': False,
                    'error': 'Failed to create connection'
                }
            
            cursor = conn.cursor()
            thread_results = []
            
            for i in range(queries_per_thread):
                start_time = time.time()
                try:
                    cursor.execute("SELECT pg_sleep(0.1), current_timestamp")  # Simulate work
                    result = cursor.fetchone()
                    end_time = time.time()
                    
                    thread_results.append({
                        'query_id': i,
                        'execution_time': end_time - start_time,
                        'success': True
                    })
                except Exception as e:
                    end_time = time.time()
                    thread_results.append({
                        'query_id': i,
                        'execution_time': end_time - start_time,
                        'success': False,
                        'error': str(e)
                    })
            
            cursor.close()
            conn.close()
            
            return {
                'thread_id': thread_id,
                'success': True,
                'results': thread_results
            }
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker_thread, i) for i in range(num_threads)]
            thread_results = [future.result() for future in as_completed(futures)]
        
        total_time = time.time() - start_time
        
        successful_threads = [t for t in thread_results if t['success']]
        total_queries = sum(len(t['results']) for t in successful_threads)
        successful_queries = sum(len([q for q in t['results'] if q['success']]) for t in successful_threads)
        
        print(f"Concurrent test completed in {total_time:.2f} seconds")
        print(f"Successful threads: {len(successful_threads)}/{num_threads}")
        print(f"Successful queries: {successful_queries}/{total_queries}")
        
        self.results['concurrent_tests'] = thread_results
        
        return {
            'num_threads': num_threads,
            'queries_per_thread': queries_per_thread,
            'total_time': total_time,
            'successful_threads': len(successful_threads),
            'total_queries': total_queries,
            'successful_queries': successful_queries,
            'queries_per_second': total_queries / total_time if total_time > 0 else 0
        }
    
    def test_transaction_performance(self, num_transactions=50):
        """Test transaction performance"""
        print(f"Testing {num_transactions} database transactions...")
        
        conn = self.create_connection()
        if not conn:
            print("Failed to create database connection")
            return None
        
        transaction_results = []
        
        for i in range(num_transactions):
            start_time = time.time()
            try:
                cursor = conn.cursor()
                
                # Begin transaction
                cursor.execute("BEGIN")
                
                # Perform some operations
                cursor.execute("SELECT current_timestamp")
                cursor.execute("SELECT pg_sleep(0.01)")  # Simulate work
                cursor.execute("SELECT version()")
                
                # Commit transaction
                cursor.execute("COMMIT")
                
                end_time = time.time()
                
                transaction_results.append({
                    'transaction_id': i,
                    'execution_time': end_time - start_time,
                    'success': True
                })
                
                cursor.close()
                
            except Exception as e:
                try:
                    cursor.execute("ROLLBACK")
                except:
                    pass
                
                end_time = time.time()
                transaction_results.append({
                    'transaction_id': i,
                    'execution_time': end_time - start_time,
                    'success': False,
                    'error': str(e)
                })
        
        conn.close()
        
        successful_transactions = [t for t in transaction_results if t['success']]
        avg_execution_time = sum(t['execution_time'] for t in successful_transactions) / len(successful_transactions) if successful_transactions else 0
        
        print(f"Transaction test completed: {len(successful_transactions)}/{num_transactions} successful")
        print(f"Average execution time: {avg_execution_time:.4f} seconds")
        
        self.results['transaction_tests'] = transaction_results
        
        return {
            'total_transactions': num_transactions,
            'successful_transactions': len(successful_transactions),
            'avg_execution_time': avg_execution_time,
            'max_execution_time': max(t['execution_time'] for t in successful_transactions) if successful_transactions else 0,
            'min_execution_time': min(t['execution_time'] for t in successful_transactions) if successful_transactions else 0
        }
    
    def run_all_tests(self):
        """Run all database performance tests"""
        print("Starting database performance tests...")
        
        # Test connection performance
        connection_results = self.test_connection_performance(20)
        
        # Test query performance
        query_results = self.test_query_performance(100)
        
        # Test concurrent queries
        concurrent_results = self.test_concurrent_queries(10, 20)
        
        # Test transaction performance
        transaction_results = self.test_transaction_performance(50)
        
        # Compile results
        all_results = {
            'test_info': {
                'timestamp': datetime.now().isoformat(),
                'database_url': self.db_url
            },
            'connection_performance': connection_results,
            'query_performance': query_results,
            'concurrent_performance': concurrent_results,
            'transaction_performance': transaction_results,
            'raw_data': self.results
        }
        
        # Save results
        with open('database-test-results.json', 'w') as f:
            json.dump(all_results, f, indent=2)
        
        print("Database performance tests completed")
        print("Results saved to database-test-results.json")
        
        return all_results


def main():
    """Main function to run database performance tests"""
    # Get database URL from environment or use default
    db_url = os.getenv('POSTGRES_URL', 'postgresql://contract_user:contract_password@localhost:5432/contract_analyzer_test')
    
    tester = DatabasePerformanceTester(db_url)
    results = tester.run_all_tests()
    
    # Print summary
    print("\n=== DATABASE PERFORMANCE SUMMARY ===")
    if results['connection_performance']:
        cp = results['connection_performance']
        print(f"Connections: {cp['successful_connections']}/{cp['total_connections']} successful")
        print(f"Average connection time: {cp['avg_connection_time']:.4f} seconds")
    
    if results['query_performance']:
        qp = results['query_performance']
        print(f"Queries: {qp['successful_queries']}/{qp['total_queries']} successful")
        print(f"Average query time: {qp['avg_execution_time']:.4f} seconds")
    
    if results['concurrent_performance']:
        ccp = results['concurrent_performance']
        print(f"Concurrent: {ccp['successful_queries']}/{ccp['total_queries']} queries successful")
        print(f"Queries per second: {ccp['queries_per_second']:.2f}")
    
    if results['transaction_performance']:
        tp = results['transaction_performance']
        print(f"Transactions: {tp['successful_transactions']}/{tp['total_transactions']} successful")
        print(f"Average transaction time: {tp['avg_execution_time']:.4f} seconds")


if __name__ == "__main__":
    main()
