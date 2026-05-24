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
    
    @property
    def effective_capacity(self)->int:
        return self.max_rps * self.replicas
    
    @property
    def is_stateful(self)->bool:
        return self.node_type in {
            NodeType.DATABASE,
            NodeType.CACHE,
            NodeType.STORAGE
        }
    
    @property
    def is_scalable(self)->bool:
        return self.scaling_strategy != ScalingStrategy.NONE

    @property
    def single_instance_latency(self)->int:
        return self.latency_ms

    def model_post_init(self, __context:Any)->None:
        type_defaults: dict[NodeType,dict[str,Any]]={
            NodeType.SERVICE:{
                "max_rps":2000,
                "latency_ms":50,
                "scaling_strategy": ScalingStrategy.HORIZONTAL,
            },
            NodeType.DATABASE: {
                "max_rps": 500,
                "latency_ms": 10,
                "scaling_strategy": ScalingStrategy.VERTICAL,
            },
            NodeType.CACHE: {
                "max_rps": 50000,
                "latency_ms": 1,
                "scaling_strategy": ScalingStrategy.HORIZONTAL,
            },
            NodeType.QUEUE: {
                "max_rps": 10000,
                "latency_ms": 5,
                "scaling_strategy": ScalingStrategy.HORIZONTAL,
            },
            NodeType.GATEWAY: {
                "max_rps": 10000,
                "latency_ms": 10,
                "scaling_strategy": ScalingStrategy.HORIZONTAL,
            },
            NodeType.CDN: {
                "max_rps": 100000,
                "latency_ms": 5,
                "scaling_strategy": ScalingStrategy.NONE,  # managed by provider
            },
            NodeType.STORAGE: {
                "max_rps": 5000,
                "latency_ms": 20,
                "scaling_strategy": ScalingStrategy.NONE,
            },
            NodeType.CLIENT: {
                "max_rps": 0,  # client doesn't process load
                "latency_ms": 0,
                "scaling_strategy": ScalingStrategy.NONE,
            },
            NodeType.EXTERNAL: {
                "max_rps": 100, 
                "latency_ms": 200,
                "scaling_strategy": ScalingStrategy.NONE,
            },
        }

        if self.node_type in type_defaults:
            defaults = type_defaults[self.node_type]
            for field_name, default_value in defaults.items():
                current_value = getattr(self,field_name)
                field_info = self.model_fields[field_name]
                global_default = field_info.default

                if current_value == global_default:
                    object.__setattr__(self,field_name,default_value)


    def with_metadata(self, **kwargs:Any) -> "Node":
        self.metadata.update(kwargs)
        return self 
    
    def add_tag(self,tag:str) ->"Node":
        normalized = tag.lower().strip()
        if normalized and normalized not in self.tags: # avoid dups
            self.tags.append(normalized)
        return self
    
    def has_tag(self, tag:str) -> bool:
        return tag.lower() in self.tags