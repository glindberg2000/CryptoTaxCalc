# CryptoTaxCalc

A Python-based application for automating cryptocurrency tax calculations with IRS compliance for individual investors and DeFi users.

## 🎯 Overview

CryptoTaxCalc automates the complex process of calculating cryptocurrency tax liabilities for the 2024 tax year (extensible to future years). It processes raw transaction data from CSV files, applies FIFO (First-In-First-Out) lot matching for capital gains/losses, handles DeFi-specific events, and generates compliant reports for IRS Form 8949 and Schedule D.

### Key Features

- **Automated FIFO Lot Matching**: Handles First-In-First-Out matching of crypto disposals to acquisitions
- **Multi-Chain Support**: Processes transactions across ETH, Base, OP, BSC, and other EVM chains
- **DeFi Event Handling**: Properly categorizes staking rewards, liquidity provision, swaps, and farming activities
- **Accurate FMV Fetching**: Retrieves historical Fair Market Values from blockchain explorers and price APIs
- **IRS Compliance**: Generates reports compatible with Form 8949 and Schedule D
- **Privacy-Focused**: All processing done locally/offline where possible
- **Spam Filtering**: Automatically excludes zero-value transactions and flagged spam tokens

## 🚀 Quick Start

> **Note**: This project is currently in development. Installation and usage instructions will be updated as the project progresses.

### Prerequisites

- Python 3.12.3 or higher
- Git (for development)

### Installation (Coming Soon)

```bash
# Clone the repository
git clone https://github.com/your-username/CryptoTaxCalc.git
cd CryptoTaxCalc

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m cryptotaxcalc --help
```

## 📊 How It Works

### Input Processing
1. **CSV Transaction Data**: Upload your transaction history from exchanges/wallets
2. **Pre-2024 Holdings**: Optional file with your crypto holdings from before 2024

### Processing Flow
1. **Data Validation**: Clean and validate transaction data
2. **Chronological Sorting**: Order transactions by date for accurate FIFO processing
3. **FIFO Queue Management**: Build separate queues for each cryptocurrency asset
4. **Tax Calculations**: 
   - Acquisitions → Add to FIFO queue with FMV basis
   - Disposals → Match against oldest holdings for gain/loss calculation
   - Income events → Record as ordinary income with $0 cost basis
5. **Classification**: Distinguish short-term (<365 days) vs long-term capital gains

### Output Generation
- **IRS-Compatible Reports**: Form 8949 and Schedule D ready formats
- **Multiple Export Formats**: CSV, JSON, and PDF reports
- **Detailed Summaries**: Gain/loss breakdowns, ordinary income totals, unrealized holdings

## 🏗️ Technical Architecture

### Core Components
- **Parser Module**: Main transaction processing engine
- **FIFO Manager**: Queue-based lot matching using `collections.deque`
- **FMV Fetcher**: Historical price data from Etherscan, CoinGecko APIs
- **Tax Calculator**: Capital gains/loss and income categorization logic
- **Reporter**: Multi-format report generation (CSV, JSON, PDF)

### Technology Stack
- **Language**: Python 3.12.3
- **Data Processing**: pandas, numpy
- **Database**: SQLite (for caching and storage)
- **APIs**: requests (Etherscan, CoinGecko)
- **Reporting**: matplotlib, reportlab
- **Testing**: pytest

### Database Schema
- **Transactions**: Core transaction data with normalized fields
- **FIFO Queues**: Asset holdings with acquisition dates and basis
- **FMV Cache**: Historical price data to minimize API calls

## 📋 Supported Transaction Types

### Standard Operations
- **Buys/Sells**: Direct crypto purchases and sales
- **Transfers**: Wallet-to-wallet movements (non-taxable)
- **Swaps**: Treat as simultaneous sell/buy at Fair Market Value

### DeFi Activities
- **Staking Rewards**: Ordinary income at $0 cost basis
- **Liquidity Provision**: LP token additions/removals at FMV
- **Farming/Yield**: Harvest events as ordinary income
- **Airdrops**: Income events (filtered for spam)

## 🔒 Privacy & Security

- **Local Processing**: All calculations performed on your device
- **No Cloud Uploads**: Transaction data never leaves your machine without consent
- **API Key Security**: Environment variables only, never hardcoded
- **Data Ownership**: You maintain full control of your transaction data

## 📈 Development Status

**Current Phase**: Project Initialization (5% complete)

### Completed ✅
- Product Requirements Document (PRD)
- Technical architecture design
- Memory bank documentation system
- Project repository setup

### In Progress 🔄
- Core parser module development
- FIFO queue implementation
- CSV processing foundation

### Planned 📅
- **Phase 1** (1-2 weeks): Core parser and FIFO logic
- **Phase 2** (1 week): FMV integration and database setup
- **Phase 3** (1 week): Report generation and CLI interface
- **Phase 4** (1 week): Testing and documentation
- **Phase 5** (Future): GUI interface with Streamlit

## 🤝 Contributing

This project uses an AI-driven development approach with human oversight. Contributions are welcome through:

- **Issue Reports**: Bug reports and feature requests
- **Pull Requests**: Code improvements and fixes
- **Documentation**: Help improve user guides and technical docs
- **Testing**: Sample data and edge case validation

## ⚖️ Legal Disclaimer

**Important**: This software is for informational purposes only and does not constitute tax advice. Always consult with a qualified tax professional for your specific situation. The accuracy of calculations depends on the quality and completeness of input data.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Useful Links

- **Product Requirements**: [PRD Document](PRDs/# CryptoTaxCalc Product Requirements Doc.md)
- **Technical Documentation**: [Memory Bank](cline_docs/)
- **IRS Resources**: [Form 8949](https://www.irs.gov/forms-pubs/about-form-8949), [Schedule D](https://www.irs.gov/forms-pubs/about-schedule-d-form-1040)

## 📞 Support

For questions, issues, or feature requests, please:
1. Check the [documentation](cline_docs/) first
2. Search [existing issues](../../issues)
3. Create a [new issue](../../issues/new) if needed

---

**Status**: 🚧 Under Active Development | **Version**: Pre-Alpha | **Target Release**: Q1 2025 