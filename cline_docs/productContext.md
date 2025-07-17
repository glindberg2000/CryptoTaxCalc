# Product Context

## Why This Project Exists
CryptoTaxCalc addresses the complex challenge of cryptocurrency tax compliance for individual investors and DeFi users. Manual calculation of crypto taxes is error-prone, time-consuming, and increasingly difficult as transaction volumes grow and DeFi activities become more complex.

## Problems It Solves
- **Manual Tax Calculation Burden**: Automates the tedious process of calculating capital gains/losses from crypto transactions
- **FIFO Lot Matching Complexity**: Handles First-In-First-Out matching of crypto disposals to acquisitions automatically
- **DeFi Tax Complexity**: Properly categorizes staking rewards, liquidity provision, and other DeFi activities for tax purposes
- **Multi-Chain Transaction Management**: Processes transactions across multiple blockchains (ETH, Base, OP, BSC)
- **IRS Compliance**: Generates reports that comply with IRS Form 8949 and Schedule D requirements
- **Data Accuracy**: Fetches accurate Fair Market Values (FMV) from blockchain sources rather than relying on potentially outdated CSV data

## How It Should Work
### Core Functionality
- **Input Processing**: Accept CSV transaction files and pre-2024 holdings data
- **FIFO Queue Management**: Maintain separate FIFO queues for each cryptocurrency asset
- **Transaction Classification**: 
  - Acquisitions (buys, receives) → Add to FIFO queue with FMV basis
  - Disposals (sells, swaps) → Match against oldest holdings for gain/loss calculation
  - Income events (staking, airdrops) → Record as ordinary income with $0 cost basis
- **Tax Calculations**: Distinguish short-term (<365 days) vs long-term capital gains
- **Report Generation**: Output IRS-compliant reports in CSV, JSON, and PDF formats

### Key Features
- **Privacy-Focused**: All processing done locally/offline where possible
- **Spam Filtering**: Exclude zero-value transactions and flagged spam tokens
- **FMV Accuracy**: Fetch historical USD values from blockchain explorers with fallbacks
- **Modular Design**: Core parser importable for GUI applications or batch processing
- **Scalability**: Handle 10,000+ transactions efficiently

### User Experience
1. User provides CSV transaction file and optional pre-2024 holdings
2. System processes transactions chronologically, building FIFO queues
3. System calculates gains/losses and categorizes income events
4. User receives detailed reports showing all tax implications
5. Reports are formatted for direct use with tax preparation software or manual filing

## Success Criteria
- 95% accuracy in tax calculations (validated against manual audits)
- Process 5,000 transactions in under 5 minutes
- User satisfaction: Net Promoter Score >8/10 in beta testing 