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

    # capacity
    max_rps: int = Field(
        default=1000,
        ge=1,
        description="max req per sec node can handle"
    )

    replicas:int = Field(
        default=1,
        ge=1,
        le=1000,
        description="instances"
    )

    latency_ms: int = Field(
        default=50,
        ge=0,
        le=60000,
        description="Excepted processing latency ms"
    )

    # sre
    scaling_strategy: ScalingStrategy = Field(
        default= ScalingStrategy.NONE,
        description="how component responds to increase load"
    )

    critcal: bool = Field(
        default=False,
        description="Is component on critical path"
    )

    # meta data
    description: str = Field(
        default="",
        max_length=500,
        description="Describe component role"
    )

    tags: list[str]=Field(
        default_factory=list,
        max_length=20,
        description="Category tags"
    )

    metadata: dict[str,Any] = Field(
        default_factory=dict,
        description="type specific config"
    )

    @property
    def effective_capacity(self)->int:
        return self.max_rps*self.replicas
    
    @property
    def is_stateful(self)->bool:
        return self.node_type in {
            NodeType.DATABASE,
            NodeType.CACHE,
            NodeType.QUEUE,
            NodeType.STORAGE
        }

    @property
    def is_scalable(self)->bool:
        return self.scaling_strategy != ScalingStrategy.NONE
    
    @property
    def single_instance_latency(self) -> int:
        return self.latency_ms

    @field_validator('tags')
    @classmethod
    def tags_must_be_lowercase(cls, v: list[str]) -> list[str]:
        return [tag.lower().strip() for tag in v if tag.strip()]
 
    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Node name cannot be empty or whitespace")
        return stripped
    
    