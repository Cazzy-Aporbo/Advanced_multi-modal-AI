"""
Real-time Stream Processing Engine
License: Apache 2.0

A lightweight stream processing engine with exactly-once semantics,
event-time processing, watermarks, and stateful transformations.
Supports tumbling, sliding, and session windows with custom triggers.
"""

import asyncio
import pickle
import struct
import time
import heapq
import mmap
import os
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, Generic, Iterator, List, Optional, Set, Tuple, TypeVar, Union
import threading
import weakref
import rocksdb
import xxhash


T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')
R = TypeVar('R')


class EventTime:
    """Manages event time and processing time semantics"""
    
    def __init__(self, timestamp: int, watermark: int = 0):
        self.timestamp = timestamp
        self.watermark = watermark
        self.processing_time = int(time.time() * 1000)
    
    def __lt__(self, other):
        return self.timestamp < other.timestamp
    
    def __repr__(self):
        return f"EventTime(ts={self.timestamp}, wm={self.watermark})"


class WindowType(Enum):
    TUMBLING = auto()
    SLIDING = auto()
    SESSION = auto()
    GLOBAL = auto()


@dataclass
class Window:
    """Time window definition"""
    start: int
    end: int
    type: WindowType
    
    def contains(self, timestamp: int) -> bool:
        return self.start <= timestamp < self.end
    
    def overlaps(self, other: 'Window') -> bool:
        return self.start < other.end and other.start < self.end
    
    def merge(self, other: 'Window') -> 'Window':
        return Window(
            min(self.start, other.start),
            max(self.end, other.end),
            self.type
        )
    
    def __hash__(self):
        return hash((self.start, self.end, self.type))


class WatermarkGenerator:
    """Generates watermarks for event-time processing"""
    
    def __init__(self, max_out_of_orderness: int = 5000, interval: int = 200):
        self.max_out_of_orderness = max_out_of_orderness
        self.interval = interval
        self.current_max_timestamp = 0
        self.last_emit_time = 0
    
    def extract_timestamp(self, element: Any) -> int:
        """Override to extract timestamp from element"""
        if hasattr(element, 'timestamp'):
            return element.timestamp
        elif isinstance(element, dict) and 'timestamp' in element:
            return element['timestamp']
        return int(time.time() * 1000)
    
    def get_watermark(self, timestamp: int) -> Optional[int]:
        self.current_max_timestamp = max(self.current_max_timestamp, timestamp)
        current_time = int(time.time() * 1000)
        
        if current_time - self.last_emit_time >= self.interval:
            self.last_emit_time = current_time
            return self.current_max_timestamp - self.max_out_of_orderness
        
        return None


class StateBackend(ABC):
    """Abstract state backend for fault tolerance"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[bytes]:
        pass
    
    @abstractmethod
    def put(self, key: str, value: bytes):
        pass
    
    @abstractmethod
    def delete(self, key: str):
        pass
    
    @abstractmethod
    def checkpoint(self) -> bytes:
        pass
    
    @abstractmethod
    def restore(self, checkpoint: bytes):
        pass


class RocksDBStateBackend(StateBackend):
    """RocksDB-based state backend with checkpointing"""
    
    def __init__(self, db_path: str = "/tmp/stream_state"):
        self.db_path = db_path
        os.makedirs(db_path, exist_ok=True)
        
        opts = rocksdb.Options()
        opts.create_if_missing = True
        opts.max_open_files = 300000
        opts.write_buffer_size = 67108864
        opts.max_write_buffer_number = 3
        opts.target_file_size_base = 67108864
        
        self.db = rocksdb.DB(db_path, opts)
        self.write_batch = rocksdb.WriteBatch()
        self.pending_writes = 0
    
    def get(self, key: str) -> Optional[bytes]:
        return self.db.get(key.encode())
    
    def put(self, key: str, value: bytes):
        self.write_batch.put(key.encode(), value)
        self.pending_writes += 1
        
        if self.pending_writes >= 1000:
            self.flush()
    
    def delete(self, key: str):
        self.write_batch.delete(key.encode())
        self.pending_writes += 1
        
        if self.pending_writes >= 1000:
            self.flush()
    
    def flush(self):
        if self.pending_writes > 0:
            self.db.write(self.write_batch)
            self.write_batch = rocksdb.WriteBatch()
            self.pending_writes = 0
    
    def checkpoint(self) -> bytes:
        self.flush()
        checkpoint = rocksdb.Checkpoint(self.db)
        checkpoint_dir = f"{self.db_path}_checkpoint_{int(time.time())}"
        checkpoint.create_checkpoint(checkpoint_dir)
        return checkpoint_dir.encode()
    
    def restore(self, checkpoint: bytes):
        checkpoint_dir = checkpoint.decode()
        if os.path.exists(checkpoint_dir):
            self.db.close()
            os.rename(checkpoint_dir, self.db_path)
            opts = rocksdb.Options()
            self.db = rocksdb.DB(self.db_path, opts)


class InMemoryStateBackend(StateBackend):
    """In-memory state backend for testing"""
    
    def __init__(self):
        self.state = {}
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[bytes]:
        with self._lock:
            return self.state.get(key)
    
    def put(self, key: str, value: bytes):
        with self._lock:
            self.state[key] = value
    
    def delete(self, key: str):
        with self._lock:
            self.state.pop(key, None)
    
    def checkpoint(self) -> bytes:
        with self._lock:
            return pickle.dumps(dict(self.state))
    
    def restore(self, checkpoint: bytes):
        with self._lock:
            self.state = pickle.loads(checkpoint)


class StateStore:
    """Manages operator state with exactly-once guarantees"""
    
    def __init__(self, backend: StateBackend, operator_id: str):
        self.backend = backend
        self.operator_id = operator_id
        self._cache = {}
        self._dirty = set()
        self._lock = threading.Lock()
    
    def _make_key(self, key: str) -> str:
        return f"{self.operator_id}:{key}"
    
    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            if key in self._cache:
                return self._cache[key]
            
            db_key = self._make_key(key)
            value = self.backend.get(db_key)
            
            if value is not None:
                deserialized = pickle.loads(value)
                self._cache[key] = deserialized
                return deserialized
            
            return default
    
    def put(self, key: str, value: Any):
        with self._lock:
            self._cache[key] = value
            self._dirty.add(key)
    
    def flush(self):
        with self._lock:
            for key in self._dirty:
                db_key = self._make_key(key)
                value = pickle.dumps(self._cache[key])
                self.backend.put(db_key, value)
            
            self._dirty.clear()
            
            if hasattr(self.backend, 'flush'):
                self.backend.flush()


class StreamElement(Generic[T]):
    """Wrapper for stream elements with metadata"""
    
    __slots__ = ('value', 'timestamp', 'watermark', 'headers', 'key')
    
    def __init__(self, value: T, timestamp: int = None, key: Optional[str] = None):
        self.value = value
        self.timestamp = timestamp or int(time.time() * 1000)
        self.watermark = self.timestamp
        self.headers = {}
        self.key = key
    
    def with_timestamp(self, timestamp: int) -> 'StreamElement[T]':
        self.timestamp = timestamp
        return self
    
    def with_key(self, key: str) -> 'StreamElement[T]':
        self.key = key
        return self


class Operator(ABC, Generic[T, R]):
    """Base class for stream operators"""
    
    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__
        self.operator_id = f"{self.name}_{id(self)}"
        self.state_store = None
        self.context = None
        self.downstream = []
        self.metrics = defaultdict(int)
    
    def initialize(self, context: 'StreamContext'):
        self.context = context
        self.state_store = StateStore(context.state_backend, self.operator_id)
    
    @abstractmethod
    def process(self, element: StreamElement[T]) -> Iterator[StreamElement[R]]:
        pass
    
    def process_watermark(self, watermark: int):
        """Process watermark for time-based operations"""
        pass
    
    def checkpoint(self) -> bytes:
        """Create operator checkpoint"""
        if self.state_store:
            self.state_store.flush()
        return pickle.dumps(self.metrics)
    
    def restore(self, checkpoint: bytes):
        """Restore from checkpoint"""
        self.metrics = pickle.loads(checkpoint)
    
    def emit(self, element: StreamElement[R]):
        """Emit element to downstream operators"""
        for operator in self.downstream:
            for output in operator.process(element):
                operator.emit(output)
    
    def close(self):
        """Cleanup resources"""
        if self.state_store:
            self.state_store.flush()


class MapOperator(Operator[T, R]):
    """Stateless map transformation"""
    
    def __init__(self, map_func: Callable[[T], R], name: str = None):
        super().__init__(name)
        self.map_func = map_func
    
    def process(self, element: StreamElement[T]) -> Iterator[StreamElement[R]]:
        try:
            result = self.map_func(element.value)
            output = StreamElement(result, element.timestamp, element.key)
            self.metrics['processed'] += 1
            yield output
        except Exception as e:
            self.metrics['errors'] += 1
            raise


class FilterOperator(Operator[T, T]):
    """Filter elements based on predicate"""
    
    def __init__(self, predicate: Callable[[T], bool], name: str = None):
        super().__init__(name)
        self.predicate = predicate
    
    def process(self, element: StreamElement[T]) -> Iterator[StreamElement[T]]:
        if self.predicate(element.value):
            self.metrics['passed'] += 1
            yield element
        else:
            self.metrics['filtered'] += 1


class KeyByOperator(Operator[T, T]):
    """Partition stream by key"""
    
    def __init__(self, key_func: Callable[[T], K], name: str = None):
        super().__init__(name)
        self.key_func = key_func
    
    def process(self, element: StreamElement[T]) -> Iterator[StreamElement[T]]:
        key = self.key_func(element.value)
        element.key = str(key)
        yield element


class WindowOperator(Operator[T, List[T]]):
    """Window aggregation operator"""
    
    def __init__(self, 
                 window_size: int,
                 window_slide: Optional[int] = None,
                 window_type: WindowType = WindowType.TUMBLING,
                 trigger_func: Optional[Callable] = None,
                 name: str = None):
        super().__init__(name)
        self.window_size = window_size
        self.window_slide = window_slide or window_size
        self.window_type = window_type
        self.trigger_func = trigger_func
        self.windows = defaultdict(lambda: defaultdict(list))
        self.timers = []
        self.watermark = 0
    
    def process(self, element: StreamElement[T]) -> Iterator[StreamElement[List[T]]]:
        # Assign element to windows
        windows = self._assign_windows(element)
        
        for window in windows:
            key = element.key or 'global'
            self.windows[key][window].append(element.value)
            
            # Register timer for window
            heapq.heappush(self.timers, (window.end, key, window))
            
            # Check trigger
            if self.trigger_func and self.trigger_func(self.windows[key][window], window):
                yield from self._emit_window(key, window)
    
    def process_watermark(self, watermark: int):
        """Emit windows when watermark passes window end"""
        self.watermark = watermark
        
        while self.timers and self.timers[0][0] <= watermark:
            _, key, window = heapq.heappop(self.timers)
            if key in self.windows and window in self.windows[key]:
                yield from self._emit_window(key, window)
    
    def _assign_windows(self, element: StreamElement[T]) -> List[Window]:
        """Assign element to windows based on window type"""
        timestamp = element.timestamp
        windows = []
        
        if self.window_type == WindowType.TUMBLING:
            start = (timestamp // self.window_size) * self.window_size
            windows.append(Window(start, start + self.window_size, self.window_type))
            
        elif self.window_type == WindowType.SLIDING:
            first_start = timestamp - (timestamp % self.window_slide)
            for start in range(first_start, timestamp + 1, self.window_slide):
                if start + self.window_size > timestamp:
                    windows.append(Window(start, start + self.window_size, self.window_type))
        
        elif self.window_type == WindowType.SESSION:
            # Session windows require gap detection
            key = element.key or 'global'
            existing_windows = list(self.windows[key].keys())
            
            merged = False
            for window in existing_windows:
                if abs(window.end - timestamp) < self.window_size:
                    # Extend session window
                    new_window = Window(
                        min(window.start, timestamp),
                        max(window.end, timestamp + self.window_size),
                        self.window_type
                    )
                    self.windows[key][new_window] = self.windows[key][window] + [element.value]
                    del self.windows[key][window]
                    windows.append(new_window)
                    merged = True
                    break
            
            if not merged:
                windows.append(Window(timestamp, timestamp + self.window_size, self.window_type))
        
        return windows
    
    def _emit_window(self, key: str, window: Window) -> Iterator[StreamElement[List[T]]]:
        """Emit window contents and clean up"""
        if key in self.windows and window in self.windows[key]:
            elements = self.windows[key][window]
            output = StreamElement(elements, window.end - 1, key)
            del self.windows[key][window]
            
            if not self.windows[key]:
                del self.windows[key]
            
            self.metrics['windows_emitted'] += 1
            yield output


class JoinOperator(Operator[T, Tuple[T, T]]):
    """Stream-stream join with windowing"""
    
    def __init__(self,
                 other_stream: 'DataStream',
                 join_func: Callable[[T, T], bool],
                 window_size: int,
                 name: str = None):
        super().__init__(name)
        self.other_stream = other_stream
        self.join_func = join_func
        self.window_size = window_size
        self.left_buffer = defaultdict(lambda: deque(maxlen=1000))
        self.right_buffer = defaultdict(lambda: deque(maxlen=1000))
    
    def process(self, element: StreamElement[T]) -> Iterator[StreamElement[Tuple[T, T]]]:
        key = element.key or 'global'
        is_left = element.headers.get('stream_side', 'left') == 'left'
        
        if is_left:
            self.left_buffer[key].append((element.timestamp, element.value))
            
            # Join with right buffer
            for r_timestamp, r_value in self.right_buffer[key]:
                if abs(element.timestamp - r_timestamp) <= self.window_size:
                    if self.join_func(element.value, r_value):
                        output = StreamElement(
                            (element.value, r_value),
                            max(element.timestamp, r_timestamp),
                            key
                        )
                        self.metrics['joined'] += 1
                        yield output
        else:
            self.right_buffer[key].append((element.timestamp, element.value))
            
            # Join with left buffer
            for l_timestamp, l_value in self.left_buffer[key]:
                if abs(element.timestamp - l_timestamp) <= self.window_size:
                    if self.join_func(l_value, element.value):
                        output = StreamElement(
                            (l_value, element.value),
                            max(element.timestamp, l_timestamp),
                            key
                        )
                        self.metrics['joined'] += 1
                        yield output
        
        # Clean old entries
        self._clean_buffers(key, element.timestamp)
    
    def _clean_buffers(self, key: str, current_time: int):
        """Remove old entries outside join window"""
        cutoff = current_time - self.window_size
        
        while self.left_buffer[key] and self.left_buffer[key][0][0] < cutoff:
            self.left_buffer[key].popleft()
        
        while self.right_buffer[key] and self.right_buffer[key][0][0] < cutoff:
            self.right_buffer[key].popleft()


class AggregateOperator(Operator[List[T], V]):
    """Stateful aggregation operator"""
    
    def __init__(self,
                 init_func: Callable[[], V],
                 aggregate_func: Callable[[V, T], V],
                 name: str = None):
        super().__init__(name)
        self.init_func = init_func
        self.aggregate_func = aggregate_func
    
    def process(self, element: StreamElement[List[T]]) -> Iterator[StreamElement[V]]:
        key = element.key or 'global'
        
        # Get or initialize state
        state_key = f"agg_{key}"
        accumulator = self.state_store.get(state_key, self.init_func())
        
        # Aggregate all elements
        for value in element.value:
            accumulator = self.aggregate_func(accumulator, value)
        
        # Update state
        self.state_store.put(state_key, accumulator)
        
        # Emit result
        output = StreamElement(accumulator, element.timestamp, key)
        self.metrics['aggregated'] += 1
        yield output


class StreamContext:
    """Execution context for stream processing"""
    
    def __init__(self, 
                 state_backend: Optional[StateBackend] = None,
                 checkpoint_interval: int = 60000,
                 parallelism: int = 1):
        self.state_backend = state_backend or InMemoryStateBackend()
        self.checkpoint_interval = checkpoint_interval
        self.parallelism = parallelism
        self.operators = []
        self.sources = []
        self.sinks = []
        self.running = False
        self.checkpoint_task = None
    
    def register_operator(self, operator: Operator):
        self.operators.append(operator)
        operator.initialize(self)
    
    def register_source(self, source: 'Source'):
        self.sources.append(source)
    
    def register_sink(self, sink: 'Sink'):
        self.sinks.append(sink)
    
    async def start(self):
        """Start stream processing"""
        self.running = True
        
        # Start checkpoint task
        self.checkpoint_task = asyncio.create_task(self._checkpoint_loop())
        
        # Start sources
        tasks = []
        for source in self.sources:
            task = asyncio.create_task(source.run())
            tasks.append(task)
        
        await asyncio.gather(*tasks)
    
    async def stop(self):
        """Stop stream processing"""
        self.running = False
        
        if self.checkpoint_task:
            self.checkpoint_task.cancel()
        
        # Close all operators
        for operator in self.operators:
            operator.close()
        
        # Final checkpoint
        self.checkpoint()
    
    def checkpoint(self):
        """Create global checkpoint"""
        checkpoint_data = {}
        
        for operator in self.operators:
            checkpoint_data[operator.operator_id] = operator.checkpoint()
        
        checkpoint = pickle.dumps(checkpoint_data)
        self.state_backend.put('_checkpoint', checkpoint)
        
        if hasattr(self.state_backend, 'checkpoint'):
            self.state_backend.checkpoint()
    
    def restore(self):
        """Restore from checkpoint"""
        checkpoint = self.state_backend.get('_checkpoint')
        
        if checkpoint:
            checkpoint_data = pickle.loads(checkpoint)
            
            for operator in self.operators:
                if operator.operator_id in checkpoint_data:
                    operator.restore(checkpoint_data[operator.operator_id])
    
    async def _checkpoint_loop(self):
        """Periodic checkpoint task"""
        while self.running:
            await asyncio.sleep(self.checkpoint_interval / 1000)
            self.checkpoint()


class DataStream(Generic[T]):
    """Represents a stream of data"""
    
    def __init__(self, context: StreamContext, operator: Optional[Operator] = None):
        self.context = context
        self.operator = operator
        if operator:
            context.register_operator(operator)
    
    def map(self, func: Callable[[T], R]) -> 'DataStream[R]':
        """Apply map transformation"""
        map_op = MapOperator(func)
        if self.operator:
            self.operator.downstream.append(map_op)
        return DataStream(self.context, map_op)
    
    def filter(self, predicate: Callable[[T], bool]) -> 'DataStream[T]':
        """Filter elements"""
        filter_op = FilterOperator(predicate)
        if self.operator:
            self.operator.downstream.append(filter_op)
        return DataStream(self.context, filter_op)
    
    def key_by(self, key_func: Callable[[T], K]) -> 'DataStream[T]':
        """Partition by key"""
        keyby_op = KeyByOperator(key_func)
        if self.operator:
            self.operator.downstream.append(keyby_op)
        return DataStream(self.context, keyby_op)
    
    def window(self,
               size: int,
               slide: Optional[int] = None,
               window_type: WindowType = WindowType.TUMBLING) -> 'DataStream[List[T]]':
        """Apply windowing"""
        window_op = WindowOperator(size, slide, window_type)
        if self.operator:
            self.operator.downstream.append(window_op)
        return DataStream(self.context, window_op)
    
    def aggregate(self,
                  init_func: Callable[[], V],
                  agg_func: Callable[[V, T], V]) -> 'DataStream[V]':
        """Stateful aggregation"""
        agg_op = AggregateOperator(init_func, agg_func)
        if self.operator:
            self.operator.downstream.append(agg_op)
        return DataStream(self.context, agg_op)
    
    def join(self,
             other: 'DataStream[T]',
             join_func: Callable[[T, T], bool],
             window_size: int) -> 'DataStream[Tuple[T, T]]':
        """Stream-stream join"""
        join_op = JoinOperator(other, join_func, window_size)
        if self.operator:
            self.operator.downstream.append(join_op)
        if other.operator:
            other.operator.downstream.append(join_op)
        return DataStream(self.context, join_op)
    
    def sink(self, sink_func: Callable[[T], None]):
        """Write to sink"""
        class CustomSink(Operator[T, None]):
            def process(self, element: StreamElement[T]) -> Iterator[None]:
                sink_func(element.value)
                return iter([])
        
        sink_op = CustomSink()
        if self.operator:
            self.operator.downstream.append(sink_op)
        self.context.register_sink(sink_op)


class Source(ABC):
    """Base class for data sources"""
    
    @abstractmethod
    async def run(self):
        pass


class KafkaSource(Source):
    """Kafka source connector"""
    
    def __init__(self, topic: str, stream: DataStream, watermark_gen: WatermarkGenerator):
        self.topic = topic
        self.stream = stream
        self.watermark_gen = watermark_gen
    
    async def run(self):
        """Simulate Kafka consumption"""
        while True:
            # Simulate receiving messages
            await asyncio.sleep(0.01)
            
            # Generate mock data
            value = {'id': time.time(), 'data': 'test'}
            timestamp = self.watermark_gen.extract_timestamp(value)
            
            element = StreamElement(value, timestamp)
            
            # Process through stream
            if self.stream.operator:
                for output in self.stream.operator.process(element):
                    self.stream.operator.emit(output)
            
            # Generate watermark
            watermark = self.watermark_gen.get_watermark(timestamp)
            if watermark:
                self.stream.operator.process_watermark(watermark)


def example_word_count():
    """Example: Real-time word count with windowing"""
    
    async def run():
        # Create context
        context = StreamContext(
            state_backend=RocksDBStateBackend(),
            checkpoint_interval=10000
        )
        
        # Create stream
        stream = DataStream(context)
        
        # Define pipeline
        word_counts = (
            stream
            .map(lambda text: text.split())
            .map(lambda words: [(w, 1) for w in words])
            .map(lambda pairs: [p for pair in pairs for p in pair])  # Flatten
            .key_by(lambda pair: pair[0])
            .window(5000, window_type=WindowType.TUMBLING)
            .aggregate(
                lambda: defaultdict(int),
                lambda acc, pair: {**acc, pair[0]: acc[pair[0]] + pair[1]}
            )
        )
        
        # Add sink
        word_counts.sink(lambda counts: print(f"Word counts: {dict(counts)}"))
        
        # Start processing
        await context.start()
    
    # Run example
    asyncio.run(run())


def example_complex_pipeline():
    """Example: Complex event processing with joins and aggregations"""
    
    async def run():
        context = StreamContext(
            state_backend=RocksDBStateBackend(),
            checkpoint_interval=30000,
            parallelism=4
        )
        
        # Create streams for different event types
        orders = DataStream(context)
        payments = DataStream(context)
        
        # Process orders
        processed_orders = (
            orders
            .filter(lambda o: o['amount'] > 100)
            .key_by(lambda o: o['user_id'])
            .map(lambda o: {**o, 'processed_at': time.time()})
        )
        
        # Process payments
        processed_payments = (
            payments
            .filter(lambda p: p['status'] == 'success')
            .key_by(lambda p: p['user_id'])
        )
        
        # Join orders with payments
        matched = processed_orders.join(
            processed_payments,
            lambda o, p: o['order_id'] == p['order_id'],
            window_size=60000  # 1 minute window
        )
        
        # Aggregate by user
        user_totals = (
            matched
            .key_by(lambda pair: pair[0]['user_id'])
            .window(300000, window_type=WindowType.SLIDING, slide=60000)
            .aggregate(
                lambda: {'total': 0, 'count': 0},
                lambda acc, pair: {
                    'total': acc['total'] + pair[0]['amount'],
                    'count': acc['count'] + 1
                }
            )
        )
        
        # Output results
        user_totals.sink(lambda result: print(f"User totals: {result}"))
        
        await context.start()
    
    asyncio.run(run())


def benchmark_throughput():
    """Benchmark stream processing throughput"""
    
    import time
    import statistics
    
    class ThroughputSink(Operator[Any, None]):
        def __init__(self):
            super().__init__("ThroughputSink")
            self.count = 0
            self.start_time = time.time()
            self.latencies = deque(maxlen=10000)
        
        def process(self, element: StreamElement) -> Iterator[None]:
            self.count += 1
            latency = time.time() * 1000 - element.timestamp
            self.latencies.append(latency)
            
            if self.count % 10000 == 0:
                elapsed = time.time() - self.start_time
                throughput = self.count / elapsed
                avg_latency = statistics.mean(self.latencies)
                p99_latency = statistics.quantiles(self.latencies, n=100)[98]
                
                print(f"Throughput: {throughput:,.0f} msgs/sec")
                print(f"Avg latency: {avg_latency:.2f}ms")
                print(f"P99 latency: {p99_latency:.2f}ms")
                print("-" * 40)
            
            return iter([])
    
    async def run():
        context = StreamContext(
            state_backend=InMemoryStateBackend(),
            checkpoint_interval=60000
        )
        
        stream = DataStream(context)
        
        # Create pipeline
        pipeline = (
            stream
            .map(lambda x: x * 2)
            .filter(lambda x: x % 3 == 0)
            .key_by(lambda x: x % 10)
            .window(1000, window_type=WindowType.TUMBLING)
            .aggregate(
                lambda: 0,
                lambda acc, x: acc + x
            )
        )
        
        sink = ThroughputSink()
        pipeline.operator.downstream.append(sink)
        context.register_operator(sink)
        
        # Generate load
        async def generate_load():
            for i in range(100000):
                element = StreamElement(i, int(time.time() * 1000))
                for output in stream.operator.process(element):
                    stream.operator.emit(output)
                
                if i % 100 == 0:
                    await asyncio.sleep(0.001)
        
        await generate_load()
    
    print("Stream Processing Engine Benchmark")
    print("=" * 40)
    asyncio.run(run())


if __name__ == "__main__":
    print("Real-time Stream Processing Engine")
    print("=" * 40)
    print("\n1. Running word count example...")
    # example_word_count()
    
    print("\n2. Running complex pipeline example...")
    # example_complex_pipeline()
    
    print("\n3. Running throughput benchmark...")
    benchmark_throughput()
