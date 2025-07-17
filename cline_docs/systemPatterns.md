# System Patterns

## Architecture Overview
**Pattern**: Layered Architecture with Modular Components  
**Approach**: Separation of concerns with clear data flow between layers

### Layer Structure
```
UI Layer (CLI/Future GUI)
    ↓
Output Layer (Report Generators)
    ↓
Core Logic Layer (Parser, Tax Calculator)
    ↓
Data Access Layer (SQLite Cache)
    ↓
Integration Layer (API Wrappers)
    ↓
Input Layer (CSV/JSON Loaders)
```

## Key Technical Decisions

### Database Choice: SQLite
**Decision**: Use SQLite for MVP instead of PostgreSQL  
**Rationale**: 
- Lightweight, embedded database (no server setup)
- Sufficient for single-user, local processing
- Good performance for read-heavy workloads
- Easy deployment and backup

**Schema Design**:
- `transactions`: Core transaction data with normalized fields
- `fifo_queues`: Asset holdings with acquisition dates and basis
- `fmv_cache`: Historical price data to avoid repeated API calls

### FIFO Implementation Pattern
**Pattern**: Queue-based lot matching using `collections.deque`  
**Benefits**:
- Efficient O(1) append/pop operations
- Natural FIFO ordering
- Memory efficient for large transaction volumes

### Data Processing Flow
**Pattern**: Pipeline processing with validation gates
```
CSV Input → Validation → Sorting → FIFO Processing → Tax Calculation → Report Generation
```

Each stage validates data integrity before passing to next stage.

### Error Handling Strategy
**Pattern**: Graceful degradation with logging  
- Log errors but continue processing where possible
- Provide partial results with clear indication of data gaps
- User notifications for critical missing data (e.g., missing FMV)

### API Integration Pattern
**Primary**: Blockchain explorer APIs (Etherscan, etc.)  
**Fallback**: CoinGecko historical API  
**Caching**: Local SQLite cache to minimize API calls  
**Rate Limiting**: Respect API limits with exponential backoff

## Modular Design Patterns

### Core Module Structure
```
cryptotaxcalc/
├── __init__.py          # Package initialization
├── parser.py            # Main transaction parser
├── fifo_manager.py      # FIFO queue management
├── fmv_fetcher.py       # Fair Market Value fetching
├── tax_calculator.py    # Tax computation logic
├── reporter.py          # Report generation
└── utils.py            # Common utilities
```

### Import Strategy
- Core parser importable as `cryptotaxcalc.parser`
- Each module has clear, documented public interface
- Internal implementation details kept private

### Configuration Management
**Pattern**: Configuration objects with environment overrides
- Default settings in code
- User overrides via config files
- Environment variable support for sensitive data (API keys)

## Testing Patterns
**Strategy**: Pyramid testing approach
- **Unit Tests**: Core logic functions (80% of tests)
- **Integration Tests**: Module interactions (15% of tests)  
- **End-to-End Tests**: Full CSV processing workflows (5% of tests)

### Test Data Strategy
- Sample CSV files with known expected outcomes
- Edge case scenarios (missing data, spam transactions)
- Performance benchmarks with large datasets

## Performance Patterns
**Target**: Handle 10,000+ transactions in <10 minutes

### Optimization Strategies
- **Batch Processing**: Process transactions in batches to reduce memory usage
- **Lazy Loading**: Load FMV data only when needed
- **Caching**: Aggressive caching of computed values and API responses
- **Indexing**: SQLite indexes on frequently queried fields (date, asset)

## Security and Privacy Patterns
**Principle**: Local-first processing with minimal external dependencies

### Data Handling
- No cloud uploads without explicit user consent
- Local SQLite database for all persistent data
- API keys stored in environment variables
- Transaction data never leaves user's machine

### Input Validation
- Sanitize all CSV inputs
- Validate transaction amounts and dates
- Filter out potentially malicious data patterns 