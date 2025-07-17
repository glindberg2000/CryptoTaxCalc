# Technical Context

## Technology Stack

### Core Language and Version
- **Python**: 3.12.3
- **Rationale**: Mature ecosystem for data processing, strong CSV/pandas support, extensive library availability

### Required Libraries (Pre-installed in Environment)
#### Data Processing
- **pandas**: DataFrame manipulation and CSV processing
- **numpy**: Numerical calculations and array operations
- **collections**: FIFO queue implementation with deque

#### API Integration
- **requests**: HTTP API calls for FMV fetching
- **beautifulsoup4**: Web scraping fallback for price data

#### Blockchain Integration (Minimal Use)
- **web3**: Ethereum/EVM chain interactions (for transaction verification if needed)
- **Note**: CSV is primary data source; blockchain calls minimized

#### Reporting and Output
- **matplotlib**: Chart generation for tax reports
- **reportlab**: PDF report generation

#### Development and Testing
- **pytest**: Unit and integration testing
- **logging**: Error tracking and debugging
- **datetime**: Timestamp handling and date calculations

#### Database
- **SQLite**: Built into Python standard library
- **No external database server required**

### Development Tools
- **Git**: Version control and team coordination
- **Sphinx**: Documentation generation (future)
- **argparse**: CLI interface (standard library)

## Development Environment Setup

### Prerequisites
- Python 3.12.3 installed
- Git configured for version control
- Text editor/IDE (VS Code, PyCharm, etc.)

### Project Structure
```
CryptoTaxCalc/
├── cryptotaxcalc/           # Main package
│   ├── __init__.py
│   ├── parser.py
│   ├── fifo_manager.py
│   ├── fmv_fetcher.py
│   ├── tax_calculator.py
│   ├── reporter.py
│   └── utils.py
├── tests/                   # Test suite
├── data/                    # Sample data and templates
├── docs/                    # Documentation
├── cline_docs/              # Memory bank documentation
├── requirements.txt         # Python dependencies
├── setup.py                 # Package configuration
├── README.md                # Project documentation
└── .gitignore              # Git ignore patterns
```

### Installation and Setup
```bash
# Clone repository
git clone <repo-url>
cd CryptoTaxCalc

# Install dependencies (when available)
pip install -r requirements.txt

# Run tests
pytest tests/

# Run CLI
python -m cryptotaxcalc --help
```

## Technical Constraints

### Performance Requirements
- **Transaction Volume**: Support up to 10,000+ transactions per processing run
- **Processing Time**: Complete analysis in <10 minutes for 5,000 transactions
- **Memory Usage**: Efficient handling of large CSV files without excessive RAM usage

### Platform Support
- **Primary**: macOS, Linux, Windows
- **Architecture**: x86_64, ARM64 (Apple Silicon)
- **Python**: 3.12+ required for optimal performance

### External Dependencies
#### API Rate Limits
- **Etherscan**: 5 calls/second (free tier)
- **CoinGecko**: 50 calls/minute (free tier)
- **Mitigation**: Local caching, batch requests, exponential backoff

#### Internet Connectivity
- **Required**: For FMV fetching from APIs
- **Fallback**: Use CSV USDEquivalent values if APIs unavailable
- **Offline Mode**: Process with existing cached data

### Data Constraints
#### CSV Format Requirements
- **Required Columns**: Type, BuyAmount, BuyCurrency, Date, USDEquivalent
- **Date Format**: ISO 8601 or common variants (YYYY-MM-DD)
- **Encoding**: UTF-8 support for international characters

#### Storage Limitations
- **SQLite**: Single file database, ~281TB theoretical limit
- **Practical**: Optimized for <1GB transaction databases
- **Backup**: Users responsible for data backup

### Security Constraints
- **Local Processing**: No cloud dependencies by default
- **API Keys**: Environment variables only, never hardcoded
- **User Data**: Never transmitted without explicit consent
- **Compliance**: No financial advice provided, tax professional disclaimer required

## Integration Considerations

### Future GUI Integration
- **Framework Options**: Streamlit, tkinter, or web-based
- **Design**: Core parser as importable module enables GUI wrapper
- **State Management**: SQLite database allows GUI to resume processing

### Batch Processing
- **CLI Interface**: Full automation via command-line arguments
- **Scripting**: Python imports allow custom automation scripts
- **Output Formats**: Multiple export formats (CSV, JSON, PDF) for integration

### API Extension Points
- **Custom FMV Sources**: Plugin architecture for additional price sources
- **Report Formats**: Extensible report generation for different tax software
- **Blockchain Support**: Additional chain support via modular fetchers

## Development Workflow

### Git Workflow
- **Main Branch**: Stable, deployable code
- **Feature Branches**: Individual feature development
- **Pull Requests**: Code review and integration
- **Commits**: Descriptive messages with issue references

### Testing Strategy
- **Unit Tests**: Individual function testing with pytest
- **Integration Tests**: Module interaction testing
- **Sample Data**: Real CSV samples with anonymized data
- **Performance Tests**: Benchmark large dataset processing

### Documentation
- **Code Comments**: Inline documentation for complex logic
- **Docstrings**: Python docstring format for all public functions
- **README**: User-facing setup and usage instructions
- **Memory Bank**: Technical documentation for development continuity 