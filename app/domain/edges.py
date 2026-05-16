from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field, model_validator, field_validator
import uuid

class ConnectionType(str, Enum):
    SYNC = "sync" # http, grpc, rpc
    ASYNC = "async" # mq, event bus
    STREAM = "stream" # kafka, websocket
    CACHE_READ = "cache_read" 
    CACHE_WRITE = "cache_write"
    DATABASE = "database" # db query

class Edge(BaseModel):
    edge_id: str = Field(
        default_factory=lambda: f"edge_{uuid.uuid4().hex[:8]}"
    ) 
    source_id: str = Field(
        ...,
        description="node_id of the upstream component"
    )
    target_id: str = Field(
        ...,
        description="node_id of the downstream component"
    )
    
    # connection
    connection_type: ConnectionType = Field(
        default=ConnectionType.SYNC,
        description="How these components communicate"
    )

    bidirectional:bool = Field(
        default=False,
        description= "Data flowing uni/bi directional"
    )

    # traffic
    max_rps:int = Field(
        default=1000,
        ge=0, #ingress
        description="Max traffic connection is designed to carry"
    )

    latency_ms:int = Field(
        default=5,
        ge=0,
        le=60000,
        description="Network Latency for the hop"
    )

    bandwidth_mbps: int = Field(
        default=1000,
        ge=1,
        description="Available bandwidth in mbps"
    )

    # sre
    has_circuit_breaker:bool = Field(
        default=False,
        description="Is Connection has DB"
    )

    has_retry:bool = Field(
        default=False,
        description="Is Automatic retries configured"
    )

    has_timeout: bool = Field(
        default=True,
        description="Is timeout configured"
    )

    timeout_ms:int | None = Field(
        default=None,
        description="Request timeout in ms"
    )

    retry_count:int | None = Field(
        default=0,
        ge=0,
        le=10,
        description="# retry attempts"
    )

    # scaling
    load_balanced:bool = Field(
        default=False,
        description="Is req distributed accross"
    )

    sticky_session: bool = Field(
        default= False,
        description="Consistent Hashing needed"
    )

    # meta data
    label: str = Field(
        default="",
        max_length=100,
        description="Label for the edge"
    )

    description: str = Field(
        default="",
        max_length=500,
        description="Describe what data flows over this connection"
    )