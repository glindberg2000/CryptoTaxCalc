# CryptoTaxCalc Product Requirements Document (PRD)

## 1. Document Information
- **Version:** 1.0
- **Date:** July 17, 2025
- **Author:** Grok 4 (xAI)
- **Status:** Draft (Ready for Hand-Off to Development Team)
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
- Parse CSV transactions chronologically for 2024.
- Build/update FIFO queues per asset, incorporating pre-2024 holdings (from user-provided JSON/CSV).
- Match disposals (sells, swaps, withdrawals) to acquisitions for gain/loss calculation.
- Classify gains: Short-term (hold <365 days) vs. long-term.
- Handle special cases:
  - Income events (e.g., staking rewards, airdrops): $0 basis, ordinary income.
  - Swaps: Treat as sell of one asset and buy of another at FMV.
  - LP events: Calculate FMV of added/removed tokens.
  - Deposits/Withdrawals: Track as non-taxable transfers unless involving fiat.

### 5.2 Filtering and Validation
- Spam filtering: Exclude zero-value tx, flagged keywords (e.g., "spam", "airdrop scam"), or user-defined patterns.
- Data validation: Flag incomplete rows, truncated data, or inconsistencies (e.g., negative amounts).
- Edge cases: Dust rounding (e.g., <0.0001 units as zero), multi-chain tx IDs.

### 5.3 FMV Handling
- Primary: Fetch historical USD FMVs from blockchain explorers (e.g., Etherscan API for ETH tx timestamps).
- Fallback: CoinGecko historical API or web scraping for non-supported chains.
- Cache FMVs locally to avoid repeated queries.

### 5.4 Outputs
- Tables: Gains/losses by date/asset (qty, proceeds, basis, gain/loss, term).
- Summaries: Total short/long-term gains, ordinary income, unrealized holdings.
- Exports: CSV, JSON, PDF (with IRS-formatted reports).
- Visuals: Charts for gain distribution (using Matplotlib).

### 5.5 Extensibility
- Modular parser: Importable as `cryptotaxcalc.parser` for GUI integrations (e.g., Streamlit app).
- Batch mode: CLI command like `python -m cryptotaxcalc --input tx.csv --output report.json`.

## 6. Functional Requirements
- **Input Requirements:**
  - Raw CSV (as provided in sample: columns like Type, BuyAmount, BuyCurrency, etc.).
  - Pre-2024 holdings file (JSON: {asset: [{date, qty, basis}]} for FIFO queues).

- **Processing Flow:**
  1. Load and clean CSV (Pandas DataFrame).
  2. Sort by Date.
  3. Initialize FIFO queues from pre-2024 data.
  4. Iterate transactions:
     - Acquisitions: Add to FIFO with FMV basis.
     - Disposals: Match to oldest lots; calculate gain.
     - Income: Log separately.
  5. Fetch FMVs as needed.
  6. Generate reports.

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
- **Phase 1 (1-2 weeks):** Core parser module, FIFO logic, CSV parsing.
- **Phase 2 (1 week):** FMV fetching, DB integration.
- **Phase 3 (1 week):** Reporting, CLI batch job.
- **Phase 4 (1 week):** Testing, GUI prototype.
- **Phase 5:** Beta release, human feedback.

## 12. Risks and Mitigations
- **Risk:** Inaccurate FMVs → Mitigation: Multi-source fallbacks, user overrides.
- **Risk:** Data Gaps in CSV → Mitigation: Flagging, partial reports.
- **Risk:** AI Coordination Issues → Mitigation: Strict Git protocols, human arbitration.
- **Risk:** Compliance Changes → Mitigation: Versioned for tax years; disclaimers.

## 13. Appendix
- **Assumptions:** CSV format consistent; users handle backups.
- **Next Steps:** Hand off to AI teams via shared Git repo and chat setup.