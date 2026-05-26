import asyncio
import logging
from typing import Set
from app.domain.architecture import ArchitectureGraph
from app.domain.nodes import Node, NodeType, ScalingStrategy
from app.domain.edges import Edge, ConnectionType

logger = logging.getLogger(__name__)

KEYWORD_PATTERNS = {
    "chat": {
        "description": "Real-time messaging",
        "services": ["Message Service", "Presence Service"],
        "storage": ["PostgreSQL"],
        "cache": ["Redis"],
    },
    "video": {
        "description": "Video streaming",
        "services": ["Transcoding Service", "Streaming Service"],
        "storage": ["S3"],
        "cdn": ["CloudFront"],
    },
    "payment": {
        "description": "Payment processing",
        "services": ["Payment Service"],
        "storage": ["PostgreSQL"],
        "external": ["Stripe API"],
    },
    "search": {
        "description": "Search functionality",
        "services": ["Search Service"],
        "storage": ["PostgreSQL"],
        "cache": ["Redis"],
    },
    "real-time": {
        "services": ["WebSocket Server"],
        "connection_type": "stream",
    },
    "million": {"scale_factor": 10},
    "100k": {"scale_factor": 5},
}
 
 
COMPONENT_TEMPLATES = {
    "API Gateway": {
        "node_type": NodeType.GATEWAY,
        "max_rps": 5000,
        "replicas": 2,
        "latency_ms": 10,
        "scaling_strategy": ScalingStrategy.HORIZONTAL,
        "critical": True,
    },
    "Message Service": {
        "node_type": NodeType.SERVICE,
        "max_rps": 5000,
        "replicas": 2,
        "latency_ms": 50,
        "scaling_strategy": ScalingStrategy.HORIZONTAL,
    },
    "Presence Service": {
        "node_type": NodeType.SERVICE,
        "max_rps": 10000,
        "replicas": 2,
        "latency_ms": 20,
        "scaling_strategy": ScalingStrategy.HORIZONTAL,
    },
    "WebSocket Server": {
        "node_type": NodeType.SERVICE,
        "max_rps": 20000,
        "replicas": 3,
        "latency_ms": 50,
        "scaling_strategy": ScalingStrategy.HORIZONTAL,
    },
    "Payment Service": {
        "node_type": NodeType.SERVICE,
        "max_rps": 1000,
        "replicas": 2,
        "latency_ms": 200,
        "scaling_strategy": ScalingStrategy.HORIZONTAL,
        "critical": True,
    },
    "Transcoding Service": {
        "node_type": NodeType.SERVICE,
        "max_rps": 500,
        "replicas": 2,
        "latency_ms": 5000,
        "scaling_strategy": ScalingStrategy.HORIZONTAL,
    },
    "Streaming Service": {
        "node_type": NodeType.SERVICE,
        "max_rps": 10000,
        "replicas": 3,
        "latency_ms": 50,
        "scaling_strategy": ScalingStrategy.HORIZONTAL,
    },
    "Search Service": {
        "node_type": NodeType.SERVICE,
        "max_rps": 5000,
        "replicas": 2,
        "latency_ms": 100,
        "scaling_strategy": ScalingStrategy.HORIZONTAL,
    },
    "PostgreSQL": {
        "node_type": NodeType.DATABASE,
        "max_rps": 1000,
        "replicas": 1,
        "latency_ms": 15,
        "scaling_strategy": ScalingStrategy.VERTICAL,
        "critical": True,
    },
    "Redis": {
        "node_type": NodeType.CACHE,
        "max_rps": 30000,
        "replicas": 2,
        "latency_ms": 2,
        "scaling_strategy": ScalingStrategy.HORIZONTAL,
    },
    "CloudFront": {
        "node_type": NodeType.CDN,
        "max_rps": 100000,
        "replicas": 1,
        "latency_ms": 10,
        "scaling_strategy": ScalingStrategy.NONE,
    },
    "S3": {
        "node_type": NodeType.STORAGE,
        "max_rps": 5000,
        "replicas": 1,
        "latency_ms": 50,
        "scaling_strategy": ScalingStrategy.NONE,
    },
    "Stripe API": {
        "node_type": NodeType.EXTERNAL,
        "max_rps": 100,
        "replicas": 1,
        "latency_ms": 500,
        "scaling_strategy": ScalingStrategy.NONE,
    },
}

class MockArchitecturePlanner:
    async def plan(self, prompt : str) ->ArchitectureGraph:
        await asyncio.sleep(0.1)

        prompt_lower = prompt.lower()
        features = self._extract_features(prompt_lower)
        scale_factor = self._extract_scale(prompt_lower)
 
        arch = ArchitectureGraph(
            name=self._generate_name(features),
            description=self._generate_description(features),
            source_prompt=prompt,
            ai_generated=False,
        )
 
        self._add_entry_point(arch)
        self._add_services(arch, features, scale_factor)
        self._add_storage(arch, features)
        self._connect_components(arch)
 
        logger.info(f"Mock planner: {arch.name} ({arch.node_count} nodes)")
        return arch    
    
    def extract_features(self,prompt:str) -> Set[str]:
        return {kw for kw in KEYWORD_PATTERNS.keys() if kw in prompt}
    
    def extract_scale(self, prompt: str) -> int:
        scale = 1
        for kw in ["million","100k"]:
            if kw in prompt and kw in KEYWORD_PATTERNS:
                scale = max(scale,KEYWORD_PATTERNS[kw].get("scale_factor",1))
        return scale
    
    def generate_name(self, features: Set[str]) -> str:
        if "chat" in features:
            return "Real time chat system"
        elif "video" in features:
            return "Video Streaming Platform"
        elif "payment" in features:
            return "Payment Processing System"
        else:
            return "Scalable System"
        
    def generate_description(self, features: Set[str]) -> str:
        descs = [
            KEYWORD_PATTERNS[f].get("description",f)
            for f in features
            if f in KEYWORD_PATTERNS
        ]
        return ".".join(descs) if descs else "Scalable system"
    
    def add_entry_point(self, arch: ArchitectureGraph)-> None:
        client = Node(
            name="Client",
            node_type=NodeType.CLIENT,
            description="User-facing client",
            max_rps=1,
        )

        arch.add_node(client)

        gateway = Node(
            name="API Gateway",
            node_type=NodeType.GATEWAY,
            description="Routes requests",
            max_rps=5000,
            replicas=2,
            scaling_strategy=ScalingStrategy.HORIZONTAL,
            critcal=True,
        )

        arch.add_node(gateway)

        arch.add_edge(
            Edge(
                source_id=client.node_id,
                target_id=gateway.node_id,
                connection_type=ConnectionType.SYNC,
                max_rps=5000,
                label="HTTP Requests",
                has_timeout=True,
                timeout_ms=5000,
            )
        )

    def add_services(self, arch:ArchitectureGraph, features:Set[str],scale:int)->None:
        services = set()
        for f in features:
            if f in KEYWORD_PATTERNS:
                services.update(KEYWORD_PATTERNS[f].get("services", []))
 
        if not services:
            services.add("User Service")
 
        gateway_id = next(
            n.node_id for n in arch.iter_nodes() if "Gateway" in n.name
        )
 
        for svc_name in services:
            if svc_name not in COMPONENT_TEMPLATES:
                continue
 
            template = COMPONENT_TEMPLATES[svc_name]
            svc = Node(
                name=svc_name,
                node_type=template["node_type"],
                max_rps=template["max_rps"],
                replicas=template["replicas"] * scale,
                latency_ms=template["latency_ms"],
                scaling_strategy=template["scaling_strategy"],
                critical=template.get("critical", False),
            )
            arch.add_node(svc)
 
            arch.add_edge(
                Edge(
                    source_id=gateway_id,
                    target_id=svc.node_id,
                    connection_type=ConnectionType.SYNC,
                    max_rps=template["max_rps"],
                    label=f"route to {svc_name}",
                    has_circuit_breaker=True,
                    has_timeout=True,
                    timeout_ms=5000,
                )
            )
        
    def add_storage(self, arch: ArchitectureGraph, features: Set[str]) -> None:
        storage_items = set()
        for f in features:
            if f in KEYWORD_PATTERNS:
                storage_items.update(KEYWORD_PATTERNS[f].get("storage", []))
                storage_items.update(KEYWORD_PATTERNS[f].get("cache", []))
                storage_items.update(KEYWORD_PATTERNS[f].get("cdn", []))
                storage_items.update(KEYWORD_PATTERNS[f].get("external", []))
    
        if not storage_items:
            storage_items = {"PostgreSQL", "Redis"}
    
        for item in storage_items:
            if item not in COMPONENT_TEMPLATES:
                continue
    
            template = COMPONENT_TEMPLATES[item]
            node = Node(
                    name=item,
                    node_type=template["node_type"],
                    max_rps=template["max_rps"],
                    replicas=template.get("replicas", 1),
                    latency_ms=template["latency_ms"],
                    scaling_strategy=template["scaling_strategy"],
                    critical=template.get("critical", False),
                )
            arch.add_node(node)
    
    def connect_components(self, arch: ArchitectureGraph) -> None:
        services = [node for node in arch.iter_nodes() if node.node_type == NodeType.SERVICE]
        dbs = [node for node in arch.iter_nodes() if node.node_type == NodeType.DATABASE]
        caches = [node for node in arch.iter_nodes() if node.node_type == NodeType.CACHE]
 
        for svc in services:
            for db in dbs:
                arch.add_edge(
                    Edge(
                        source_id=svc.node_id,
                        target_id=db.node_id,
                        connection_type=ConnectionType.DATABASE,
                        max_rps=db.max_rps,
                        label=f"query {db.name}",
                        has_circuit_breaker=True,
                        has_timeout=True,
                        timeout_ms=10000,
                    )
                )
 
            for cache in caches:
                arch.add_edge(
                    Edge(
                        source_id=svc.node_id,
                        target_id=cache.node_id,
                        connection_type=ConnectionType.CACHE_READ,
                        max_rps=cache.max_rps,
                        label=f"read from {cache.name}",
                        has_timeout=True,
                        timeout_ms=100,
                    )
                )