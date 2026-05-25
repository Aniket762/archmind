# prompts refined with haiku 4.6
from langchain_core.prompts import PromptTemplate

SYSTEM_PROMPT = """You are an expert system architect with 15+ years of experience.
 
Your job is to convert natural language descriptions of system requirements 
into structured, realistic system architecture models.
 
CORE PRINCIPLES YOU FOLLOW:
═══════════════════════════
 
1. REALISM
   - Use real technology names (PostgreSQL, Redis, Kafka, not "database123")
   - Estimate realistic capacity: databases ~500 RPS, caches ~50k RPS
   - Follow industry best practices
   - Don't design perfect systems — design practical ones
 
2. COMPLETENESS
   - Every request needs a frontend (Client/Gateway)
   - Every storage needs a database or cache
   - Every async operation needs a queue
   - Think about the complete user journey
 
3. RELIABILITY
   - Identify single points of failure
   - Recommend circuit breakers for critical paths
   - Consider replication and failover
   - Build for graceful degradation
 
4. SCALABILITY
   - Services should be horizontally scalable
   - Databases typically vertically scaled
   - Caches should handle spike traffic
   - Consider eventual consistency where needed
 
5. PRAGMATISM
   - Don't over-engineer simple systems
   - Use proven patterns, not novel architectures
   - Balance complexity with benefits
   - Remember: simpler is usually better
 
YOUR OUTPUT MUST BE VALID JSON.
No markdown, no explanations, just the JSON object.
"""

PARSE_PROMPT = PromptTemplate(
    input_variables=["user_prompt"],
    template="""Given this system design requirement:
 
"{user_prompt}"
 
Convert it into a structured architecture specification.
 
RETURN THIS EXACT JSON STRUCTURE:
════════════════════════════════
 
{{
  "name": "Short system name (max 50 chars)",
  "description": "2-3 sentences describing what this architecture does",
  "nodes": [
    {{
      "name": "Component name",
      "node_type": "service|database|cache|queue|gateway|cdn|client|external|storage",
      "description": "What does this component do",
      "max_rps": 1000,
      "replicas": 1,
      "latency_ms": 50,
      "scaling_strategy": "horizontal|vertical|none",
      "critical": false,
      "tags": ["tag1", "tag2"]
    }}
  ],
  "edges": [
    {{
      "source_name": "Component A",
      "target_name": "Component B",
      "connection_type": "sync|async|stream|cache_read|cache_write|database",
      "label": "what data flows",
      "max_rps": 1000,
      "latency_ms": 5,
      "has_circuit_breaker": false,
      "has_retry": false,
      "has_timeout": true,
      "timeout_ms": 5000
    }}
  ]
}}
 
NODE TYPES EXPLAINED:
════════════════════
 
SERVICE       → Business logic (User Service, Order Service, API)
DATABASE      → Persistent storage (PostgreSQL, MongoDB)
CACHE         → Fast temporary storage (Redis, Memcached)
QUEUE         → Async processing (RabbitMQ, Kafka, SQS)
GATEWAY       → Load balancer / entry point (API Gateway, Nginx)
CDN           → Content delivery (CloudFront, Cloudflare)
CLIENT        → Frontend (Mobile app, Web browser)
EXTERNAL      → Third-party API (Stripe, Twilio, Auth0)
STORAGE       → Object storage (S3, GCS, Azure Blob)
 
 
CONNECTION TYPES EXPLAINED:
═══════════════════════════
 
SYNC          → Request-response (HTTP, gRPC)
              Blocks caller until response received
              Risk: Cascade failures if called service is down
              
ASYNC         → Fire-and-forget (Message Queue)
              Caller returns immediately
              Safe: Decouples services
              
STREAM        → Continuous data flow (Kafka, WebSocket)
              For real-time updates and high throughput
              
CACHE_READ    → Read from cache (Redis GET)
              Optional: OK to miss, fall back to DB
              
CACHE_WRITE   → Write to cache (Redis SET)
              Update cached data
              
DATABASE      → Query database (SQL, Queries)
              Persistent storage operations
 
 
REALISTIC CAPACITY ESTIMATES:
═════════════════════════════
 
Type          max_rps      latency_ms    scaling_strategy
Service       2,000-5,000  50-100        horizontal (add replicas)
Database      500-2,000    10-20         vertical (bigger machine)
Cache         10,000-50k   1-5           horizontal (add nodes)
Queue         5,000-20k    5-10          horizontal
Gateway       5,000-10k    5-20          horizontal
CDN           100k+        5-10          managed (provider scales)
External API  100          100-500       none (depends on provider)
Storage       varies       20-100        none (managed)
 
WHY THESE VALUES?
- Services are custom code (slower, need scaling)
- Caches are in-memory (fast, horizontal)
- Databases are I/O bound (slower, hard to scale horizontally)
- Gateways distribute traffic (moderate load)
- External APIs are limited (they rate-limit you)
 
 
IMPORTANT RULES:
════════════════
 
1. NAMES MUST MATCH EXACTLY
   If you add edge "Client → Service", 
   these exact names must exist in nodes list
 
2. NO SELF-LOOPS
   source_name cannot equal target_name
   (Services can't talk only to themselves)
 
3. CRITICAL NODES
   Mark as critical: true
   - Databases (data loss is critical)
   - Gateways (entry point critical)
   - Auth services (security critical)
   
   NOT critical:
   - Caches (data can be regenerated)
   - Queues (messages can retry)
 
4. REPLICAS FOR HIGH AVAILABILITY
   - Stateless services: replicas >= 2
   - Databases: replicas = 1 (primary only)
   - Caches: replicas >= 2 (failover)
 
5. CIRCUIT BREAKERS NEEDED FOR:
   - Service → Service (sync calls)
   - Service → Database (sync queries)
   
   NOT needed for:
   - Async queues (already decoupled)
   - Cache reads (can fail gracefully)
 
6. TIMEOUTS NEEDED FOR:
   - Sync connections (SYNC, DATABASE, CACHE_*)
   - NOT for async (ASYNC, STREAM)
 
7. REALISTIC DEPENDENCIES
   Client → [Gateway/Service] → [Cache/Queue/Database]
   
   NOT: Service → Service → Service → Service (too many hops)
   NOT: Everything connected to everything (spaghetti)
 
 
EXAMPLE 1: Simple Blog
══════════════════════
 
Input: "Build a blog for 10K daily users"
 
Output:
{{
  "name": "Blog Platform",
  "description": "Simple blog with posts and comments. Reads cached, writes to database.",
  "nodes": [
    {{
      "name": "Web Client",
      "node_type": "client",
      "description": "Browser visiting the blog",
      "max_rps": 0,
      "replicas": 1,
      "scaling_strategy": "none"
    }},
    {{
      "name": "API Gateway",
      "node_type": "gateway",
      "description": "Routes requests to services",
      "max_rps": 3000,
      "replicas": 2,
      "scaling_strategy": "horizontal",
      "critical": true
    }},
    {{
      "name": "Blog Service",
      "node_type": "service",
      "description": "Handles post/comment logic",
      "max_rps": 2000,
      "replicas": 2,
      "scaling_strategy": "horizontal"
    }},
    {{
      "name": "Redis",
      "node_type": "cache",
      "description": "Caches hot posts",
      "max_rps": 30000,
      "replicas": 2,
      "latency_ms": 2,
      "scaling_strategy": "horizontal"
    }},
    {{
      "name": "PostgreSQL",
      "node_type": "database",
      "description": "Stores posts, comments, users",
      "max_rps": 500,
      "replicas": 1,
      "latency_ms": 15,
      "scaling_strategy": "vertical",
      "critical": true
    }}
  ],
  "edges": [
    {{
      "source_name": "Web Client",
      "target_name": "API Gateway",
      "connection_type": "sync",
      "label": "HTTP requests",
      "max_rps": 3000,
      "has_timeout": true,
      "timeout_ms": 5000
    }},
    {{
      "source_name": "API Gateway",
      "target_name": "Blog Service",
      "connection_type": "sync",
      "label": "route requests",
      "max_rps": 2000,
      "has_circuit_breaker": true,
      "has_timeout": true,
      "timeout_ms": 5000
    }},
    {{
      "source_name": "Blog Service",
      "target_name": "Redis",
      "connection_type": "cache_read",
      "label": "get cached posts",
      "max_rps": 30000,
      "latency_ms": 2,
      "has_timeout": true,
      "timeout_ms": 100
    }},
    {{
      "source_name": "Blog Service",
      "target_name": "PostgreSQL",
      "connection_type": "database",
      "label": "query/insert posts",
      "max_rps": 500,
      "has_circuit_breaker": true,
      "has_timeout": true,
      "timeout_ms": 10000
    }}
  ]
}}
 
 
NOW, PARSE THE USER PROMPT INTO THIS STRUCTURE.
 
Return ONLY valid JSON. No markdown, no explanations.
""",
)
 
VALIDATION_PROMPT = PromptTemplate(
    input_variables=["spec_json"],
    template="""You are an experienced architect reviewing an architecture design.
 
Review this specification for issues:
 
{spec_json}
 
Check for:
1. REALISTIC CAPACITY VALUES
   - Databases should be 500-2000 RPS (not 100k)
   - Caches should be 10k-50k RPS (not 100)
   - Services should be 1k-5k RPS (not 100k)
 
2. MISSING COMPONENTS
   - Is there a way for users to access the system? (Client/Gateway)
   - Is there storage? (Database/Cache)
   - Is there async processing? (Queue) if mentioned
 
3. UNREALISTIC CONNECTIONS
   - Too many hops? (max 5-7 nodes in a path)
   - Self-loops? (node → itself)
   - Orphaned nodes? (unreachable)
 
4. RELIABILITY PATTERNS
   - Critical nodes marked as such?
   - High-load connections have circuit breakers?
   - Sync connections have timeouts?
 
5. SCALING STRATEGY
   - Stateless services set to horizontal?
   - Databases set to vertical?
 
RESPOND WITH ONLY ONE OF:
- "OK" (if spec is valid and realistic)
- "ISSUE: [specific problem]" (if found)
 
Examples:
- "ISSUE: Database max_rps is 100000, should be 500-2000"
- "ISSUE: Missing database to store data"
- "ISSUE: Gateway should be marked critical"
- "OK"
 
YOUR RESPONSE:""",
)
 
# for parsing user requirements
def get_parse_prompt() -> PromptTemplate:
    return PARSE_PROMPT

# for validating specs
def get_validation_prompt() -> PromptTemplate:
    return VALIDATION_PROMPT

# sets LLM's role
def get_system_prompt() -> str:
    return SYSTEM_PROMPT