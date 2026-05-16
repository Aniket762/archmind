from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel,Field,field_validator
import uuid

class NodeType(str, Enum):
    SERVICE = "service"
    DATABASE = "database"
    CACHE = "cache"
    QUEUE = "queue"
    GATEWAY = "gateway"
    CDN = "cdn"
    CLIENT = "client"
    EXTERNAL = "external"
    STORAGE = "storage"

class ScalingStrategy(str, Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    NONE="none"

class DatabaseMetadata:
    CONNECTION_POOL_SIZE="connection_pool_size"
    READ_REPLICAS ="read_replicas"
    SHARD_COUNT="shared_count"
    PERSISTENCE="persistence_type" #disk,memory

class CacheMetadata:
    EVICTION_POLICY = "eviction_policy" #lru,lfu,ttl
    MEMORY_GB="memory_gb"
    HIT_RATE="cache_hit_rate"

class QueueMetadata:
    MAX_QUEUE_DEPTH="max_queue_depth"
    RETENTION_HOURS = "message_retention_hours"
    ORDERING_GUARANTEE = "odering_guarantee" #fifo

class Node(BaseModel):
    node_id:str = Field(
        default_factory=lambda: f"node_{uuid.uuid4().hex[:8]}",
        description="Id for this node in the graph"
    )

    name:str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Component name"
    )

    node_type:NodeType = Field(
        ...,
        description="Category of component"
    )

