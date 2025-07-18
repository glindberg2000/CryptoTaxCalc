# CryptoTaxCalc Product Requirements Document (PRD)

## 1. Document Information
- **Version:** 1.1
- **Date:** July 17, 2025
- **Author:** Grok 4 (xAI), Updated by ManagerAI
- **Status:** Approved for Development
- **Purpose:** This PRD expands on the initial summary provided, incorporating detailed specifications for functionality, architecture, team structure, and implementation considerations. The previous summary was high-level and suitable as a starting point, but this full-featured PRD is designed to be comprehensive enough for direct hand-off to an AI development team, enabling iterative development without further clarification.

## 2. Product Overview
CryptoTaxCalc is a Python-based application designed to automate the calculation of cryptocurrency tax liabilities for the 2024 tax year (and extensible to future years). It processes raw transaction data from CSV files, applies FIFO (First-In-First-Out) lot matching for capital gains/losses, handles DeFi-specific events (e.g., staking rewards as ordinary income with $0 cost basis), and generates compliant reports for IRS Form 8949 and Schedule D. The app supports multi-chain data (e.g., ETH, Base, OP, BSC) and filters out spam/irrelevant transactions.

Key differentiators:
- Blockchain-accurate FMV (Fair Market Value) fetching for precise calculations.
- Modular design for integration into GUI apps or batch processing.
- Focus on user privacy: All processing is local/offline where possible.

## 3. Objectives and Goals
- **Business Objectives:**
  - Simplify crypto tax compliance for individual users, reducing manual effort and errors.
  - Ensure accuracy in classifying short-term (<1 year) vs. long-term (>1 year) gains.
  - Support scalability for high-volume transaction data (up to 10,000+ rows per CSV).

- **User Goals:**
  - Upload CSV and pre-2024 holdings; receive detailed gain/loss and income reports.
  - Handle complex events like swaps (treated as sell/buy), LP additions/removals (as FMV exchanges), and harvests (as income).

- **Technical Goals:**
  - Build a core parser as an importable Python module for reuse.
  - Enable batch job execution via CLI for automated outputs (CSV/JSON/PDF).
  - Minimize dependencies while ensuring robustness for blockchain data analysis.

- **Success Metrics:**
  - 95% accuracy in sample tax calculations (validated against manual audits).
  - Processing time <5 minutes for 5,000 transactions.
  - User feedback: Net Promoter Score >8/10 in beta testing.

## 4. Target Audience
- Individual crypto investors/traders with moderate to high transaction volumes.
- DeFi users involved in staking, liquidity provision, and farming.
- Tax professionals seeking a tool for client data processing.
- Assumptions: Users provide complete CSVs; app is not for enterprise-scale (single-user focus).

## 5. Key Features
### 5.1 Core Processing
- Parse CSV transactions chronologically for 2024 (15-column format with enhanced validation).
- Build/update FIFO queues per asset, incorporating pre-2024 holdings (from user-provided CSV/JSON).
- Import pre-2024 FIFO state from year-end reports; validate totals match holdings data.
- Match disposals to acquisitions using FIFO for gain/loss calculation.
- Classify gains: Short-term (hold <365 days) vs. long-term.

**Transaction Type Mapping (IRS-Compliant):**
- **Deposit**: Non-taxable if internal transfer; taxable as income if received as payment/reward
- **Withdrawal**: Non-taxable transfer; taxable disposal if to third party or for fiat/goods
- **Trade**: Standard buy/sell with FIFO lot matching for capital gains/losses
- **Spend**: Taxable disposal at FMV (treat as sale)
- **Income/Staking/Airdrop**: Ordinary income at FMV on receipt, $0 cost basis
- **Lost**: Deductible as capital loss if proven (theft); otherwise flag for user review
- **Borrow/Repay**: Non-taxable; track interest as potential income/expense if applicable

### 5.2 Filtering and Validation
- Spam filtering: Exclude zero-value tx, flagged keywords (e.g., "spam", "airdrop scam"), or user-defined patterns.
- **Enhanced Data Quality Rules:**
  - Missing USDEquivalent/FMV: Fetch from fallback APIs; flag and estimate if unavailable
  - Dust Amounts: Round/ignore below $0.01 USD equivalent to avoid noise
  - Negative Quantities: Flag as errors; halt processing and notify user for correction
- Edge cases: Multi-chain tx IDs, date format variations.
- Add 2024 date filter: Process only transactions within 2024 tax year.
- Multi-chain filtering: Process all supported chains but log chain-specific nuances.

### 5.3 FMV Handling
- Primary: Fetch historical USD FMVs from blockchain explorers (e.g., Etherscan API for ETH tx timestamps).
- Fallback: CoinGecko historical API or web scraping for non-supported chains.
- Cache FMVs locally to avoid repeated queries.

### 5.4 Fee Handling
- **Fee Integration**: Add fees to cost basis for acquisitions; subtract from proceeds for disposals
- **Currency Conversion**: Convert FeeAmount in FeeCurrency to USD at transaction FMV
- **Tax Treatment**: Do not deduct separately as business expenses (investor focus)
- **Multi-Currency Support**: Handle fees in different currencies from main transaction

### 5.5 Outputs
- Tables: Gains/losses by date/asset (qty, proceeds, basis, gain/loss, term).
- Summaries: Total short/long-term gains, ordinary income, unrealized holdings.
- Exports: CSV, JSON, PDF (with IRS-formatted reports).
- Visuals: Charts for gain distribution (using Matplotlib).

### 5.6 Extensibility
- Modular parser: Importable as `cryptotaxcalc.parser` for GUI integrations (e.g., Streamlit app).
- Batch mode: CLI command like `python -m cryptotaxcalc --input tx.csv --output report.json`.

## 6. Functional Requirements
- **Input Requirements:**
  - Enhanced CSV format (15 columns): Type, BuyAmount, BuyCurrency, SellAmount, SellCurrency, FeeAmount, FeeCurrency, Exchange, ExchangeId, Group, Import, Comment, Date, USDEquivalent, UpdatedAt
  - Pre-2024 FIFO state (CSV: from year-end report 2023) and Holdings data (CSV: asset quantities and values)
  - 2024 date filtering: Process only transactions with Date in 2024 tax year

- **Enhanced Processing Flow:**
  1. Load and validate 15-column CSV (Pandas DataFrame).
  2. Apply 2024 date filter and data quality checks.
  3. Sort by Date chronologically.
  4. Import and validate pre-2024 FIFO queues from year-end data.
  5. Iterate 2024 transactions with enhanced type mapping:
     - Acquisitions: Add to FIFO with FMV basis (including fees).
     - Disposals: Match to oldest lots; calculate gain (subtracting fees).
     - Income: Log as ordinary income with $0 basis.
     - Complex types: Handle per IRS mapping rules.
  6. Fetch missing FMVs from APIs with fallback.
  7. Generate comprehensive reports with fee integration.

- **Error Handling:**
  - Graceful failures: Log issues (e.g., missing FMV) and continue with estimates.
  - User notifications: Console/GUI alerts for data gaps.

## 7. Non-Functional Requirements
- **Performance:** Handle 10,000+ rows in <10 minutes on standard hardware.
- **Security:** Local processing; no cloud uploads without consent.
- **Usability:** CLI intuitive; future GUI simple.
- **Compliance:** Align with IRS guidelines (e.g., FIFO default); disclaimer for professional advice.
- **Maintainability:** Modular code; 80% test coverage.
- **Scalability:** Single-user; no multi-tenant needs.

## 8. Technical Architecture
### 8.1 High-Level Architecture
- **Layers:**
  - **Input Layer:** CSV/JSON loaders (Pandas for data handling).
  - **Core Logic Layer:** Parser module (FIFO queues via collections.deque; tax calculators).
  - **Data Access Layer:** Local DB for caching (e.g., transaction history, FMVs).
  - **Integration Layer:** API wrappers for FMV fetching (e.g., requests for Etherscan).
  - **Output Layer:** Report generators (Pandas for tables, ReportLab for PDF).
  - **UI Layer:** CLI (argparse); optional Streamlit for GUI.

- **Data Flow:**
  - User → Input Files → Parser → DB Cache → Calculations → Outputs.

- **Modular Design:**
  - Core as PyPI-style package: `cryptotaxcalc/` with `__init__.py`, `parser.py`, `fmv_fetcher.py`, `reporter.py`.
  - Submodule for blockchain utils (if needed beyond CSV).

### 8.2 Database Considerations
- **Recommendation:** Use SQLite for the MVP. It's lightweight, embedded (no server needed), and sufficient for single-user, read-heavy workloads (e.g., storing 10k+ transactions and FMV cache). Supports SQL queries for efficient FIFO management.
- **Why not Postgres?** Overkill for personal app; adds deployment complexity (server setup). Switch to Postgres if evolving to multi-user/web app (e.g., for concurrency).
- **Schema Example:**
  - Transactions: id, type, amount, currency, date, usd_equiv, tx_id.
  - FIFO_Queues: asset, acquisition_date, qty, basis.
  - FMV_Cache: asset, timestamp, usd_value.

### 8.3 Additional Python Modules
- **CSV Sufficiency:** The provided CSV is mostly sufficient (has USDEquivalent, dates), but for robustness:
  - Fetch real-time/historical FMVs if CSV values are outdated/inaccurate.
  - Handle blockchain data: If needing tx verification beyond CSV, integrate web3.py (for ETH/Base/OP/BSC interactions) or ccxt (for exchange prices).
- **Recommended Modules (All Pre-Installed in Env):**
  - **Core:** pandas (dataframes), numpy (calculations), collections (queues).
  - **Fetching:** requests (APIs), beautifulsoup4 (scraping if API fails).
  - **Blockchain:** web3 (tx queries), but minimize—CSV is primary.
  - **Reporting:** matplotlib (charts), reportlab (PDF).
  - **Utils:** datetime (timestamps), logging (errors), pytest (testing).
- **No New Installs:** Stick to available libs; avoid heavy ML/physics ones unless needed.

## 9. Development Team Structure
- **Human Oversight:** One human (product owner) for final reviews, approvals, and real-world testing.
- **AI Teams:** Organized into specialized roles/teams using different models for efficiency. Communication via dedicated chat channels (e.g., Discord/Slack with threads) and Git repo (GitHub/GitLab) for code versioning, issues, and PRs. This isolates context/memory: Each AI role pulls/pushes to Git branches, discusses in chats.
  - **Team 1: Architecture & Planning (Lead by High-Capacity Models)**
    - **Lead Architect:** Grok 4 Heavy (handles complex system design, DB schema).
    - **Requirements Analyst:** Claude Sonnet 4 (refines PRD, edge cases).
    - Communication: Weekly chat syncs; Git issues for specs.

  - **Team 2: Core Development (Balanced Coders)**
    - **Parser Developer:** Grok 4 (implements FIFO, tax logic).
    - **Integrator:** GPT-4.1 (modules, CLI/GUI hooks).
    - **Fetcher Specialist:** o3 Mini (FMV APIs, lightweight tasks).
    - Communication: Daily Git PRs; chat for code reviews.

  - **Team 3: Testing & QA (Efficient Models)**
    - **Unit Tester:** o3 Mini (automated tests).
    - **Integration Tester:** GPT-4.1 (end-to-end, sample CSVs).
    - **Security Reviewer:** Claude Sonnet 4 (privacy checks).
    - Communication: Git issues for bugs; chat post-merge.

  - **Cross-Team Coordination:** Human monitors chats; AIs use Git for memory (e.g., commit messages preserve decisions). Roles isolated via model-specific branches (e.g., grok4/parser-branch).

- **Workflow:** Agile sprints (1-week); Start with MVP (CLI parser), iterate to GUI.

## 10. Technology Stack
- **Language:** Python 3.12.3.
- **Libraries:** As listed in 8.3; no extras.
- **Tools:** Git for VCS; Pytest for testing; Sphinx for docs.
- **Deployment:** Local script/package; future PyPI upload.

## 11. Development Roadmap
- **Phase 1A (2 days):** Enhanced CSV parser, 2024 filter, basic validation.
- **Phase 1B (3 days):** FIFO integration with 2023 data, queue reconstruction.
- **Phase 1C (3 days):** Complex transaction handlers, fee processing.
- **Phase 2 (1 week):** FMV fetching, DB integration.
- **Phase 3 (1 week):** Reporting, CLI batch job.
- **Phase 4 (1 week):** Testing, GUI prototype.
- **Phase 5:** Beta release, human feedback.
- **Target MVP CLI:** 2 weeks from start (July 25, 2025).

## 12. Risks and Mitigations
- **Risk:** Inaccurate FMVs → Mitigation: Multi-source fallbacks, user overrides.
- **Risk:** Data Gaps in CSV → Mitigation: Flagging, partial reports.
- **Risk:** AI Coordination Issues → Mitigation: Strict Git protocols, human arbitration.
- **Risk:** Compliance Changes → Mitigation: Versioned for tax years; disclaimers.

## 13. Appendix
- **Assumptions:** CSV format consistent; users handle backups.
- **Next Steps:** Hand off to AI teams via shared Git repo and chat setup.