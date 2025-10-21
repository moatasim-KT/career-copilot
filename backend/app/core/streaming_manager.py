"""
Streaming manager for AI responses with performance optimization.
Handles streaming responses from LLM providers with real-time metrics.
"""

import asyncio
import time
import uuid
from typing import AsyncGenerator, Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from enum import Enum
import json

from langchain.schema import BaseMessage
from langchain.callbacks.base import AsyncCallbackHandler
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

from .logging import get_logger
from .performance_metrics import get_performance_metrics_collector, MetricType

logger = get_logger(__name__)


class StreamingMode(Enum):
    """Streaming modes for different use cases."""
    REAL_TIME = "real_time"  # Immediate streaming for interactive use
    BUFFERED = "buffered"    # Buffered streaming for better performance
    BATCH = "batch"          # Batch streaming for bulk processing


@dataclass
class StreamingChunk:
    """Individual streaming chunk data."""
    content: str
    chunk_id: str
    sequence_number: int
    timestamp: float
    token_count: int
    is_final: bool = False
    metadata: Dict[str, Any] = None


@dataclass
class StreamingSession:
    """Streaming session context."""
    session_id: str
    provider: str
    model: str
    operation: str
    mode: StreamingMode
    start_time: float
    first_token_time: Optional[float] = None
    total_chunks: int = 0
    total_tokens: int = 0
    buffer_size: int = 1024
    chunk_delay: float = 0.01  # Minimum delay between chunks


class StreamingCallbackHandler(AsyncCallbackHandler):
    """Callback handler for streaming LLM responses."""
    
    def __init__(self, session: StreamingSession, chunk_callback: Callable[[StreamingChunk], None]):
        """Initialize streaming callback handler."""
        super().__init__()
        self.session = session
        self.chunk_callback = chunk_callback
        self.sequence_number = 0
        self.buffer = ""
        self.last_chunk_time = time.time()
        
    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Handle new token from LLM."""
        current_time = time.time()
        
        # Record first token time
        if self.session.first_token_time is None:
            self.session.first_token_time = current_time
        
        # Add token to buffer
        self.buffer += token
        
        # Determine if we should emit a chunk
        should_emit = False
        
        if self.session.mode == StreamingMode.REAL_TIME:
            # Emit every token immediately
            should_emit = True
        elif self.session.mode == StreamingMode.BUFFERED:
            # Emit when buffer reaches size limit or after delay
            should_emit = (
                len(self.buffer) >= self.session.buffer_size or
                (current_time - self.last_chunk_time) >= self.session.chunk_delay
            )
        elif self.session.mode == StreamingMode.BATCH:
            # Emit larger chunks less frequently
            should_emit = len(self.buffer) >= (self.session.buffer_size * 2)
        
        if should_emit and self.buffer:
            await self._emit_chunk(current_time)
    
    async def on_llm_end(self, response, **kwargs) -> None:
        """Handle LLM completion."""
        # Emit any remaining buffer content
        if self.buffer:
            await self._emit_chunk(time.time(), is_final=True)
    
    async def _emit_chunk(self, timestamp: float, is_final: bool = False):
        """Emit a streaming chunk."""
        if not self.buffer:
            return
        
        # Estimate token count (rough approximation)
        token_count = len(self.buffer.split())
        
        chunk = StreamingChunk(
            content=self.buffer,
            chunk_id=f"{self.session.session_id}_{self.sequence_number}",
            sequence_number=self.sequence_number,
            timestamp=timestamp,
            token_count=token_count,
            is_final=is_final,
            metadata={
                "provider": self.session.provider,
                "model": self.session.model,
                "operation": self.session.operation,
                "mode": self.session.mode.value
            }
        )
        
        # Update session stats
        self.session.total_chunks += 1
        self.session.total_tokens += token_count
        self.sequence_number += 1
        
        # Call the chunk callback
        if self.chunk_callback:
            self.chunk_callback(chunk)
        
        # Clear buffer and update timing
        self.buffer = ""
        self.last_chunk_time = timestamp


class StreamingManager:
    """Manages streaming AI responses with performance optimization."""
    
    def __init__(self):
        """Initialize streaming manager."""
        self.active_sessions: Dict[str, StreamingSession] = {}
        self.performance_collector = get_performance_metrics_collector()
        self.chunk_processors: List[Callable[[StreamingChunk], None]] = []
        
        logger.info("Streaming manager initialized")
    
    def add_chunk_processor(self, processor: Callable[[StreamingChunk], None]):
        """Add a chunk processor for handling streaming chunks."""
        self.chunk_processors.append(processor)
    
    def create_streaming_session(self, provider: str, model: str, operation: str,
                               mode: StreamingMode = StreamingMode.BUFFERED,
                               buffer_size: int = 1024) -> StreamingSession:
        """Create a new streaming session."""
        session_id = str(uuid.uuid4())
        
        session = StreamingSession(
            session_id=session_id,
            provider=provider,
            model=model,
            operation=operation,
            mode=mode,
            start_time=time.time(),
            buffer_size=buffer_size
        )
        
        self.active_sessions[session_id] = session
        
        # Record session start in performance metrics
        self.performance_collector.record_request_start(
            request_id=session_id,
            provider=provider,
            model=model,
            operation=operation,
            is_streaming=True
        )
        
        logger.info(f"Created streaming session {session_id} for {provider}:{model}")
        return session
    
    def get_streaming_callback(self, session: StreamingSession) -> StreamingCallbackHandler:
        """Get streaming callback handler for a session."""
        def chunk_handler(chunk: StreamingChunk):
            # Record chunk in performance metrics
            self.performance_collector.record_streaming_chunk(
                request_id=session.session_id,
                chunk_size=len(chunk.content),
                chunk_content=chunk.content,
                is_first_chunk=(chunk.sequence_number == 0)
            )
            
            # Process chunk with registered processors
            for processor in self.chunk_processors:
                try:
                    processor(chunk)
                except Exception as e:
                    logger.error(f"Chunk processor error: {e}")
        
        return StreamingCallbackHandler(session, chunk_handler)
    
    async def stream_llm_response(self, llm, messages: List[BaseMessage], 
                                session: StreamingSession) -> AsyncGenerator[StreamingChunk, None]:
        """Stream LLM response with performance tracking."""
        chunks_yielded = []
        
        def collect_chunk(chunk: StreamingChunk):
            chunks_yielded.append(chunk)
        
        # Create callback handler
        callback = self.get_streaming_callback(session)
        
        # Add chunk collector
        original_processors = self.chunk_processors.copy()
        self.chunk_processors.append(collect_chunk)
        
        try:
            # Execute LLM with streaming callback
            response = await llm.ainvoke(messages, callbacks=[callback])
            
            # Yield collected chunks
            for chunk in chunks_yielded:
                yield chunk
                
                # Add small delay for real-time mode to prevent overwhelming
                if session.mode == StreamingMode.REAL_TIME:
                    await asyncio.sleep(0.001)
            
        except Exception as e:
            logger.error(f"Streaming error in session {session.session_id}: {e}")
            raise
        finally:
            # Restore original processors
            self.chunk_processors = original_processors
            
            # Finalize session
            await self._finalize_session(session, success=True)
    
    async def stream_with_optimization(self, llm, messages: List[BaseMessage],
                                     session: StreamingSession,
                                     optimization_config: Optional[Dict[str, Any]] = None) -> AsyncGenerator[StreamingChunk, None]:
        """Stream with advanced optimization techniques."""
        config = optimization_config or {}
        
        # Adaptive buffer sizing based on content type
        if config.get("adaptive_buffering", True):
            session.buffer_size = self._calculate_optimal_buffer_size(messages, session)
        
        # Token prediction for better chunking
        if config.get("token_prediction", True):
            predicted_tokens = self._predict_response_length(messages, session)
            session.chunk_delay = self._calculate_optimal_chunk_delay(predicted_tokens)
        
        # Use optimized streaming
        async for chunk in self.stream_llm_response(llm, messages, session):
            # Apply post-processing optimizations
            if config.get("chunk_compression", False):
                chunk = self._compress_chunk(chunk)
            
            yield chunk
    
    def _calculate_optimal_buffer_size(self, messages: List[BaseMessage], 
                                     session: StreamingSession) -> int:
        """Calculate optimal buffer size based on context."""
        base_size = 512
        
        # Adjust based on input length
        total_input_length = sum(len(msg.content) for msg in messages)
        if total_input_length > 5000:
            base_size = 1024
        elif total_input_length > 10000:
            base_size = 2048
        
        # Adjust based on operation type
        if session.operation in ["contract_analysis", "legal_precedent"]:
            base_size *= 2  # Larger chunks for analytical tasks
        elif session.operation == "communication":
            base_size //= 2  # Smaller chunks for interactive communication
        
        return max(256, min(base_size, 4096))
    
    def _predict_response_length(self, messages: List[BaseMessage], 
                               session: StreamingSession) -> int:
        """Predict approximate response length in tokens."""
        # Simple heuristic based on input length and operation type
        input_tokens = sum(len(msg.content.split()) for msg in messages)
        
        multipliers = {
            "contract_analysis": 2.0,
            "legal_precedent": 1.5,
            "negotiation": 1.2,
            "communication": 0.8,
            "general": 1.0
        }
        
        multiplier = multipliers.get(session.operation, 1.0)
        predicted_tokens = int(input_tokens * multiplier)
        
        return max(50, min(predicted_tokens, 4000))
    
    def _calculate_optimal_chunk_delay(self, predicted_tokens: int) -> float:
        """Calculate optimal delay between chunks."""
        # Shorter delays for longer responses to maintain engagement
        if predicted_tokens > 2000:
            return 0.005  # 5ms
        elif predicted_tokens > 1000:
            return 0.01   # 10ms
        else:
            return 0.02   # 20ms
    
    def _compress_chunk(self, chunk: StreamingChunk) -> StreamingChunk:
        """Apply compression optimizations to chunk."""
        # Remove excessive whitespace
        compressed_content = " ".join(chunk.content.split())
        
        # Update token count if content changed
        if compressed_content != chunk.content:
            chunk.content = compressed_content
            chunk.token_count = len(compressed_content.split())
        
        return chunk
    
    async def _finalize_session(self, session: StreamingSession, success: bool):
        """Finalize streaming session and record metrics."""
        end_time = time.time()
        
        # Calculate session metrics
        total_time = end_time - session.start_time
        first_token_latency = (session.first_token_time - session.start_time) if session.first_token_time else total_time
        
        # Record completion in performance metrics
        token_usage = {
            "total_tokens": session.total_tokens,
            "prompt_tokens": 0,  # Not available in streaming
            "completion_tokens": session.total_tokens
        }
        
        # Estimate cost (would need actual cost calculation)
        estimated_cost = session.total_tokens * 0.00002  # Rough estimate
        
        request_context = {
            "request_id": session.session_id,
            "provider": session.provider,
            "model": session.model,
            "operation": session.operation,
            "start_time": session.start_time,
            "is_streaming": True,
            "timestamp": session.start_time
        }
        
        self.performance_collector.record_request_completion(
            request_context=request_context,
            success=success,
            token_usage=token_usage,
            cost=estimated_cost
        )
        
        # Clean up session
        if session.session_id in self.active_sessions:
            del self.active_sessions[session.session_id]
        
        logger.info(f"Finalized streaming session {session.session_id}: "
                   f"{session.total_chunks} chunks, {session.total_tokens} tokens, "
                   f"{total_time:.2f}s total, {first_token_latency:.2f}s first token")
    
    def get_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get information about active streaming sessions."""
        return {
            session_id: {
                "provider": session.provider,
                "model": session.model,
                "operation": session.operation,
                "mode": session.mode.value,
                "start_time": session.start_time,
                "total_chunks": session.total_chunks,
                "total_tokens": session.total_tokens,
                "duration": time.time() - session.start_time
            }
            for session_id, session in self.active_sessions.items()
        }
    
    def get_streaming_performance_summary(self) -> Dict[str, Any]:
        """Get streaming performance summary."""
        active_count = len(self.active_sessions)
        
        # Get streaming metrics from performance collector
        summary = {
            "active_sessions": active_count,
            "session_details": self.get_active_sessions(),
            "performance_metrics": {}
        }
        
        # Add performance metrics for each provider/model combination
        for session in self.active_sessions.values():
            key = f"{session.provider}:{session.model}"
            if key not in summary["performance_metrics"]:
                streaming_metrics = self.performance_collector.get_streaming_metrics(
                    session.provider, session.model, session.operation
                )
                if streaming_metrics:
                    summary["performance_metrics"][key] = {
                        "first_token_latency": streaming_metrics.first_token_latency,
                        "tokens_per_second": streaming_metrics.tokens_per_second,
                        "streaming_efficiency": streaming_metrics.streaming_efficiency,
                        "average_chunk_size": streaming_metrics.average_chunk_size
                    }
        
        return summary
    
    async def cleanup_stale_sessions(self, max_age_seconds: int = 3600):
        """Clean up stale streaming sessions."""
        current_time = time.time()
        stale_sessions = [
            session_id for session_id, session in self.active_sessions.items()
            if (current_time - session.start_time) > max_age_seconds
        ]
        
        for session_id in stale_sessions:
            session = self.active_sessions[session_id]
            logger.warning(f"Cleaning up stale streaming session {session_id}")
            await self._finalize_session(session, success=False)


# Global streaming manager instance
_streaming_manager = None


def get_streaming_manager() -> StreamingManager:
    """Get the global streaming manager instance."""
    global _streaming_manager
    if _streaming_manager is None:
        _streaming_manager = StreamingManager()
    return _streaming_manager