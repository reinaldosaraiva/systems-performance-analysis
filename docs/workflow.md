# Workflow Documentation - Systems Performance Analysis

## System Architecture Workflow

```mermaid
graph TD
    A[CLI Trigger] --> B{Scheduler?}
    B -->|No| C[Immediate Analysis]
    B -->|Yes| D[Wait for Scheduled Time]
    D --> C
    
    C --> E[Metrics Collection]
    E --> F[CPU Metrics]
    E --> G[Memory Metrics]
    E --> H[Disk Metrics]
    E --> I[Network Metrics]
    
    F --> J[USE Method Analysis]
    G --> J
    H --> J
    I --> J
    
    J --> K[Latency Analysis]
    K --> L[Percentile Calculation]
    L --> M[Heatmap Generation]
    
    M --> N[Report Generation]
    N --> O[HTML Report]
    N --> P[Markdown Report]
    N --> Q[JSON Export]
    
    O --> R[Save to reports/]
    P --> R
    Q --> R
    
    R --> S[Notification/Alert]
    S --> T[End]
```

## USE Method Analysis Flow

```mermaid
graph LR
    A[Raw Metrics] --> B[Utilization Check]
    A --> C[Saturation Check]
    A --> D[Errors Check]
    
    B --> E{U > 80%?}
    C --> F{S > 20%?}
    D --> G{E > 0%?}
    
    E -->|Yes| H[WARNING]
    E -->|No| I[OK]
    F -->|Yes| H
    F -->|No| I
    G -->|Yes| J[CRITICAL]
    G -->|No| I
    
    H --> K[Score Calculation]
    I --> K
    J --> K
    
    K --> L[Overall Status]
    L --> M[Recommendations]
```

## Context Engineering Workflow

```mermaid
graph TD
    A[Development Task] --> B{Complexity?}
    B -->|Simple| C[Tier 1 Context]
    B -->|Component| D[Tier 1 + 2 Context]
    B -->|Complex| E[Tier 1 + 2 + 3 Context]
    
    C --> F[Foundation Docs]
    D --> F
    D --> G[Component Docs]
    E --> F
    E --> G
    E --> H[Feature Docs]
    
    F --> I[README.md]
    F --> J[CLAUDE.md]
    F --> K[ADRs]
    
    G --> L[Component CLAUDE.md]
    G --> M[API Docs]
    
    H --> N[Implementation Details]
    H --> O[Test Cases]
    
    I --> P[Optimized Prompt]
    J --> P
    K --> P
    L --> P
    M --> P
    N --> P
    O --> P
    
    P --> Q[AI Generation]
    Q --> R[Code Implementation]
    R --> S[Validation]
```

## Data Pipeline Architecture

```mermaid
graph TB
    subgraph "Collection Layer"
        A[psutil CPU] --> D[Metrics Aggregator]
        B[psutil Memory] --> D
        C[psutil Disk/Network] --> D
        E[/proc filesystem] --> D
    end
    
    subgraph "Processing Layer"
        D --> F[USE Method Engine]
        F --> G[Latency Analyzer]
        G --> H[Score Calculator]
    end
    
    subgraph "Output Layer"
        H --> I[Report Generator]
        I --> J[HTML Template]
        I --> K[Markdown Template]
        I --> L[JSON Export]
        
        J --> M[matplotlib Charts]
        K --> N[Table Generation]
        L --> O[API Integration]
    end
    
    subgraph "Storage Layer"
        M --> P[reports/]
        N --> P
        O --> Q[Database/API]
    end
```

## MCP Integration Workflow

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Script as setup-mcp.py
    participant MCP as Context7 MCP
    participant Docs as docs/libs/
    
    Dev->>Script: uv run python scripts/setup-mcp.py
    Script->>MCP: claude mcp add context7
    MCP-->>Script: Server added successfully
    
    loop For each library
        Script->>MCP: Fetch library documentation
        MCP-->>Script: Raw documentation
        Script->>Docs: Generate MD file
    end
    
    Docs-->>Dev: PSUTIL.md, MATPLOTLIB.md, etc.
    Dev->>Docs: Reference during development
```

## Testing Strategy Workflow

```mermaid
graph TD
    A[Code Change] --> B[Unit Tests]
    B --> C{Pass?}
    C -->|No| D[Fix Code]
    D --> A
    C -->|Yes| E[Integration Tests]
    
    E --> F{Pass?}
    F -->|No| G[Fix Integration]
    G --> A
    F -->|Yes| H[End-to-End Tests]
    
    H --> I{Pass?}
    I -->|No| J[Fix Workflow]
    J --> A
    I -->|Yes| K[Coverage Check]
    
    K --> L{>80%?}
    L -->|No| M[Add Tests]
    M --> A
    L -->|Yes| N[Quality Gates]
    
    N --> O{PEP8? Type Hints?}
    O -->|No| P[Fix Style]
    P --> A
    O -->|Yes| Q[Deploy Ready]
```

## Scheduler Workflow

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Scheduled: schedule.every().day.at()
    Scheduled --> Collecting: Time reached
    Collecting --> Analyzing: Metrics collected
    Analyzing --> Reporting: Analysis complete
    Reporting --> Saving: Report generated
    Saving --> Idle: Saved successfully
    
    Collecting --> Error: Collection failed
    Analyzing --> Error: Analysis failed
    Reporting --> Error: Report failed
    Error --> Idle: Logged error
    
    note right of Idle
        Default state
        Waiting for trigger
    end note
    
    note right of Scheduled
        Waiting for
        scheduled time
    end note
```

## Error Handling Workflow

```mermaid
graph TD
    A[Operation] --> B{Success?}
    B -->|Yes| C[Continue Pipeline]
    B -->|No| D{Error Type?}
    
    D -->|Permission| E[Log Warning]
    D -->|Network| F[Retry 3x]
    D -->|System| G[Graceful Degradation]
    D -->|Unknown| H[Log Error + Exit]
    
    E --> I[Use Safe Metrics]
    F --> J{Retry Success?}
    J -->|Yes| C
    J -->|No| K[Log + Continue]
    
    G --> L[Fallback Methods]
    I --> C
    K --> C
    L --> C
    
    C --> M[Next Operation]
    H --> N[Pipeline Failed]
```

## Performance Optimization Workflow

```mermaid
graph LR
    subgraph "Collection Optimization"
        A[Batch Collection] --> B[Async I/O]
        B --> C[Minimal Intervals]
        C --> D[Smart Caching]
    end
    
    subgraph "Processing Optimization"
        E[Vector Operations] --> F[Memory Efficient]
        F --> G[Parallel Processing]
        G --> H[Early Termination]
    end
    
    subgraph "Output Optimization"
        I[Template Caching] --> J[Chart Pre-render]
        J --> K[Compression]
        K --> L[Lazy Loading]
    end
    
    D --> M[<5s Collection]
    H --> N[<30s Analysis]
    L --> O[<100MB Memory]
```

---

**Last Updated**: 2025-01-22
**Diagrams Generated**: Mermaid.js compatible
**View in**: GitHub, VSCode with Mermaid extension, or Mermaid Live Editor