"""
Constants and IRS rules for CryptoTaxCalc.

Contains IRS guidelines, validation rules, and configuration constants
for cryptocurrency tax calculations.
"""

from typing import Dict, List, Any
from datetime import date

# IRS Constants for Cryptocurrency Taxation
IRS_CONSTANTS = {
    # Capital gains holding period (in days)
    "SHORT_TERM_THRESHOLD_DAYS": 365,
    # Tax year configuration
    "CURRENT_TAX_YEAR": 2024,
    "SUPPORTED_TAX_YEARS": [2023, 2024, 2025],
    # Minimum amounts for reporting
    "MINIMUM_REPORTABLE_AMOUNT": 0.01,  # $0.01 USD
    # Dust filtering threshold
    "DUST_THRESHOLD_USD": 0.01,
    # Fee handling rules
    "INCLUDE_FEES_IN_BASIS": True,
    "SUBTRACT_FEES_FROM_PROCEEEDS": True,
    # Income event basis
    "INCOME_EVENT_BASIS": 0.0,  # $0 basis for staking, airdrops, etc.
    # Form requirements
    "FORM_8949_REQUIRED": True,
    "SCHEDULE_D_REQUIRED": True,
    # Reporting thresholds
    "REPORTING_THRESHOLD_USD": 600.0,  # Minimum for 1099 reporting
}

# Valid transaction types and their IRS classifications
TRANSACTION_TYPES = {
    # Standard transactions
    "Trade": {
        "category": "capital_gain_loss",
        "description": "Standard buy/sell transaction",
        "irs_treatment": "Capital asset transaction with FIFO lot matching",
        "requires_fifo": True,
        "fee_handling": "add_to_basis_for_buy_subtract_from_proceeds_for_sell",
    },
    # Disposal transactions
    "Spend": {
        "category": "disposal",
        "description": "Spending cryptocurrency for goods/services",
        "irs_treatment": "Disposal at fair market value",
        "requires_fifo": True,
        "fee_handling": "subtract_from_proceeds",
    },
    # Income events
    "Income": {
        "category": "ordinary_income",
        "description": "Income from mining, rewards, or other sources",
        "irs_treatment": "Ordinary income at fair market value on receipt",
        "requires_fifo": False,
        "fee_handling": "none",
    },
    "Staking": {
        "category": "ordinary_income",
        "description": "Staking rewards and validator income",
        "irs_treatment": "Ordinary income with $0 cost basis",
        "requires_fifo": False,
        "fee_handling": "none",
    },
    "Airdrop": {
        "category": "ordinary_income",
        "description": "Airdropped tokens and rewards",
        "irs_treatment": "Ordinary income with $0 cost basis",
        "requires_fifo": False,
        "fee_handling": "none",
    },
    # Transfer transactions
    "Deposit": {
        "category": "transfer",
        "description": "Deposit to exchange or wallet",
        "irs_treatment": "Non-taxable transfer unless received as payment",
        "requires_fifo": False,
        "fee_handling": "none",
    },
    "Withdrawal": {
        "category": "transfer",
        "description": "Withdrawal from exchange or wallet",
        "irs_treatment": "Non-taxable transfer unless to third party for goods",
        "requires_fifo": False,
        "fee_handling": "none",
    },
    # Loss events
    "Lost": {
        "category": "capital_loss",
        "description": "Lost or stolen cryptocurrency",
        "irs_treatment": "Capital loss if proven theft, otherwise flag for review",
        "requires_fifo": True,
        "fee_handling": "subtract_from_proceeds",
    },
    # DeFi transactions
    "Borrow": {
        "category": "non_taxable",
        "description": "Borrowing against collateral",
        "irs_treatment": "Non-taxable loan transaction",
        "requires_fifo": False,
        "fee_handling": "none",
    },
    "Repay": {
        "category": "non_taxable",
        "description": "Repaying borrowed cryptocurrency",
        "irs_treatment": "Non-taxable loan repayment",
        "requires_fifo": False,
        "fee_handling": "none",
    },
}

# Tax year configurations
TAX_YEARS = {
    2023: {
        "start_date": date(2023, 1, 1),
        "end_date": date(2023, 12, 31),
        "short_term_threshold": 365,
        "supported": True,
    },
    2024: {
        "start_date": date(2024, 1, 1),
        "end_date": date(2024, 12, 31),
        "short_term_threshold": 365,
        "supported": True,
    },
    2025: {
        "start_date": date(2025, 1, 1),
        "end_date": date(2025, 12, 31),
        "short_term_threshold": 365,
        "supported": True,
    },
}

# Validation rules for data quality
VALIDATION_RULES = {
    # Date validation
    "date_format": "%Y-%m-%d",
    "min_date": date(2020, 1, 1),
    "max_date": date(2030, 12, 31),
    # Amount validation
    "min_amount": 0.0,
    "max_amount": 1000000000.0,  # 1 billion USD equivalent
    # Currency validation
    "valid_currencies": [
        "BTC",
        "ETH",
        "USDT",
        "USDC",
        "USD",
        "ADA",
        "DOT",
        "LINK",
        "LTC",
        "BCH",
        "XRP",
        "EOS",
        "TRX",
        "XLM",
        "VET",
        "MATIC",
        "AVAX",
        "SOL",
        "ATOM",
        "FTM",
    ],
    # Exchange validation
    "valid_exchanges": [
        "Coinbase",
        "Binance",
        "Kraken",
        "Gemini",
        "FTX",
        "KuCoin",
        "Huobi",
        "Bitfinex",
        "Bitstamp",
        "Coinbase Pro",
        "Binance US",
        "Kraken Pro",
    ],
    # Required fields for different transaction types
    "required_fields": {
        "Trade": [
            "Type",
            "BuyAmount",
            "BuyCurrency",
            "SellAmount",
            "SellCurrency",
            "Date",
        ],
        "Spend": ["Type", "SellAmount", "SellCurrency", "Date"],
        "Income": ["Type", "BuyAmount", "BuyCurrency", "Date"],
        "Staking": ["Type", "BuyAmount", "BuyCurrency", "Date"],
        "Airdrop": ["Type", "BuyAmount", "BuyCurrency", "Date"],
        "Deposit": ["Type", "BuyAmount", "BuyCurrency", "Date"],
        "Withdrawal": ["Type", "SellAmount", "SellCurrency", "Date"],
        "Lost": ["Type", "SellAmount", "SellCurrency", "Date"],
        "Borrow": ["Type", "BuyAmount", "BuyCurrency", "Date"],
        "Repay": ["Type", "SellAmount", "SellCurrency", "Date"],
    },
}

# Fee handling rules
FEE_HANDLING_RULES = {
    "add_to_basis_for_buy": {
        "description": "Add fees to cost basis for acquisitions",
        "applies_to": ["Trade", "Income", "Staking", "Airdrop"],
        "calculation": "basis = transaction_value + fee_usd_equivalent",
    },
    "subtract_from_proceeds": {
        "description": "Subtract fees from proceeds for disposals",
        "applies_to": ["Trade", "Spend", "Lost"],
        "calculation": "proceeds = transaction_value - fee_usd_equivalent",
    },
    "none": {
        "description": "No fee handling required",
        "applies_to": ["Deposit", "Withdrawal", "Borrow", "Repay"],
        "calculation": "no_fee_impact",
    },
}

# Error messages and validation messages
ERROR_MESSAGES = {
    "invalid_transaction_type": "Invalid transaction type: {type}",
    "missing_required_field": "Missing required field '{field}' for transaction type '{type}'",
    "invalid_amount": "Invalid amount: {amount}",
    "invalid_date": "Invalid date: {date}",
    "invalid_currency": "Invalid currency: {currency}",
    "insufficient_lots": "Insufficient lots available for disposal",
    "fee_calculation_error": "Error calculating fee USD equivalent",
    "fifo_integration_error": "Error integrating with FIFO manager",
}

# Success messages
SUCCESS_MESSAGES = {
    "transaction_processed": "Transaction processed successfully",
    "fifo_integration_complete": "FIFO integration completed",
    "tax_calculation_complete": "Tax calculations completed",
    "fee_processing_complete": "Fee processing completed",
}
