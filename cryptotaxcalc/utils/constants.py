"""
Constants and configuration for CryptoTaxCalc.

Contains IRS rules, transaction types, validation rules, and other constants
used throughout the tax calculation system.
"""

from typing import Dict, List, Set, Any
from enum import Enum


# IRS Constants
class IRSConstants:
    """IRS rules and constants for cryptocurrency taxation."""

    # Holding period for long-term capital gains
    LONG_TERM_HOLDING_DAYS = 365

    # Maximum capital loss deduction per year
    MAX_CAPITAL_LOSS_DEDUCTION = 3000.0

    # Wash sale period (days)
    WASH_SALE_PERIOD = 30

    # Like-kind exchange deadline (ended 2017)
    LIKE_KIND_EXCHANGE_DEADLINE = "2017-12-31"

    # Minimum transaction value for reporting (dust threshold)
    MIN_REPORTABLE_VALUE_USD = 0.01

    # Standard deduction amounts (2024)
    STANDARD_DEDUCTION_SINGLE = 14600.0
    STANDARD_DEDUCTION_MARRIED = 29200.0
    STANDARD_DEDUCTION_HEAD_OF_HOUSEHOLD = 21900.0


# Transaction Types
class TransactionTypes:
    """Valid transaction types supported by the system."""

    # Core transaction types
    TRADE = "Trade"
    SPEND = "Spend"
    INCOME = "Income"
    STAKING = "Staking"
    AIRDROP = "Airdrop"

    # Transfer types
    DEPOSIT = "Deposit"
    WITHDRAWAL = "Withdrawal"

    # Loss events
    LOST = "Lost"

    # DeFi types
    BORROW = "Borrow"
    REPAY = "Repay"

    # Get all valid types
    @classmethod
    def get_all_types(cls) -> List[str]:
        """Get list of all valid transaction types."""
        return [
            cls.TRADE,
            cls.SPEND,
            cls.INCOME,
            cls.STAKING,
            cls.AIRDROP,
            cls.DEPOSIT,
            cls.WITHDRAWAL,
            cls.LOST,
            cls.BORROW,
            cls.REPAY,
        ]

    @classmethod
    def is_valid(cls, transaction_type: str) -> bool:
        """Check if a transaction type is valid."""
        return transaction_type in cls.get_all_types()


# Tax Treatment Mappings
class TaxTreatmentMappings:
    """Mappings from transaction types to tax treatments."""

    # Capital gains/losses (require FIFO processing)
    CAPITAL_GAIN_LOSS_TYPES = {
        TransactionTypes.TRADE,
        TransactionTypes.SPEND,
        TransactionTypes.LOST,
    }

    # Ordinary income (no FIFO processing needed)
    ORDINARY_INCOME_TYPES = {
        TransactionTypes.INCOME,
        TransactionTypes.STAKING,
        TransactionTypes.AIRDROP,
    }

    # Non-taxable transfers
    NON_TAXABLE_TYPES = {
        TransactionTypes.DEPOSIT,
        TransactionTypes.WITHDRAWAL,
        TransactionTypes.BORROW,
        TransactionTypes.REPAY,
    }

    @classmethod
    def requires_fifo_processing(cls, transaction_type: str) -> bool:
        """Check if a transaction type requires FIFO processing."""
        return transaction_type in cls.CAPITAL_GAIN_LOSS_TYPES

    @classmethod
    def is_ordinary_income(cls, transaction_type: str) -> bool:
        """Check if a transaction type is ordinary income."""
        return transaction_type in cls.ORDINARY_INCOME_TYPES

    @classmethod
    def is_non_taxable(cls, transaction_type: str) -> bool:
        """Check if a transaction type is non-taxable."""
        return transaction_type in cls.NON_TAXABLE_TYPES


# Fee Handling Rules
class FeeHandlingRules:
    """Rules for handling different types of fees."""

    # Fee types and their treatments
    FEE_TREATMENTS = {
        "trading_fee": {
            "acquisition": "add_to_basis",
            "disposal": "reduce_proceeds",
            "description": "Exchange trading fees",
        },
        "network_fee": {
            "acquisition": "add_to_basis",
            "disposal": "reduce_proceeds",
            "description": "Blockchain network fees",
        },
        "withdrawal_fee": {
            "acquisition": "non_deductible",
            "disposal": "non_deductible",
            "description": "Exchange withdrawal fees",
        },
        "deposit_fee": {
            "acquisition": "non_deductible",
            "disposal": "non_deductible",
            "description": "Exchange deposit fees",
        },
        "staking_fee": {
            "acquisition": "deductible_expense",
            "disposal": "deductible_expense",
            "description": "Staking platform fees",
        },
    }

    # USD-pegged currencies (1:1 conversion)
    USD_PEGGED_CURRENCIES = {
        "USD",
        "USDT",
        "USDC",
        "BUSD",
        "DAI",
        "TUSD",
        "FRAX",
        "USDP",
    }

    # Common cryptocurrency symbols for rate estimation
    COMMON_CRYPTOCURRENCIES = {
        "BTC",
        "ETH",
        "BNB",
        "ADA",
        "DOT",
        "LINK",
        "LTC",
        "BCH",
        "XRP",
        "SOL",
        "MATIC",
        "AVAX",
        "UNI",
        "ATOM",
        "FTM",
        "NEAR",
        "ALGO",
        "VET",
        "ICP",
        "FIL",
        "TRX",
        "XLM",
        "EOS",
        "XMR",
        "DASH",
    }


# Validation Rules
class ValidationRules:
    """Validation rules for transaction data."""

    # Required columns for CSV files
    REQUIRED_COLUMNS = [
        "Type",
        "BuyAmount",
        "BuyCurrency",
        "SellAmount",
        "SellCurrency",
        "FeeAmount",
        "FeeCurrency",
        "Exchange",
        "ExchangeId",
        "Group",
        "Import",
        "Comment",
        "Date",
        "USDEquivalent",
        "UpdatedAt",
    ]

    # Date format patterns
    DATE_FORMATS = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y", "%d/%m/%Y"]

    # Minimum values
    MIN_AMOUNT = 0.0
    MIN_USD_VALUE = 0.0

    # Maximum values (reasonable limits)
    MAX_AMOUNT = 1e12  # 1 trillion
    MAX_USD_VALUE = 1e12  # 1 trillion USD

    # Currency validation
    CURRENCY_PATTERN = r"^[A-Z]{2,10}$"  # 2-10 uppercase letters

    # Exchange name validation
    EXCHANGE_PATTERN = r"^[A-Za-z0-9\s\-_\.]{1,50}$"  # Alphanumeric, spaces, hyphens, underscores, dots

    @classmethod
    def validate_amount(cls, amount: float) -> bool:
        """Validate transaction amount."""
        return cls.MIN_AMOUNT <= amount <= cls.MAX_AMOUNT

    @classmethod
    def validate_usd_value(cls, usd_value: float) -> bool:
        """Validate USD value."""
        return cls.MIN_USD_VALUE <= usd_value <= cls.MAX_USD_VALUE

    @classmethod
    def validate_currency(cls, currency: str) -> bool:
        """Validate currency symbol."""
        import re

        return bool(re.match(cls.CURRENCY_PATTERN, currency))

    @classmethod
    def validate_exchange(cls, exchange: str) -> bool:
        """Validate exchange name."""
        import re

        return bool(re.match(cls.EXCHANGE_PATTERN, exchange))


# Error Messages
class ErrorMessages:
    """Standard error messages for the system."""

    # Validation errors
    INVALID_TRANSACTION_TYPE = "Invalid transaction type: {type}"
    INVALID_AMOUNT = "Invalid amount: {amount}"
    INVALID_USD_VALUE = "Invalid USD value: {value}"
    INVALID_CURRENCY = "Invalid currency: {currency}"
    INVALID_DATE = "Invalid date: {date}"
    INVALID_EXCHANGE = "Invalid exchange: {exchange}"

    # Processing errors
    INSUFFICIENT_LOTS = "Insufficient {asset} available for disposal. Requested: {requested}, Available: {available}"
    PROCESSING_ERROR = "Error processing transaction on {date}: {error}"
    FEE_PROCESSING_ERROR = "Error processing fees for transaction on {date}: {error}"

    # File errors
    FILE_NOT_FOUND = "File not found: {file_path}"
    INVALID_CSV_FORMAT = "Invalid CSV format: {error}"
    MISSING_COLUMNS = "Missing required columns: {columns}"

    # FIFO errors
    FIFO_QUEUE_ERROR = "FIFO queue error for {asset}: {error}"
    LOT_MATCHING_ERROR = "Error matching lots for {asset}: {error}"

    # Tax calculation errors
    TAX_CALCULATION_ERROR = "Error calculating tax for transaction: {error}"
    HOLDING_PERIOD_ERROR = "Error calculating holding period: {error}"


# Logging Configuration
class LoggingConfig:
    """Logging configuration constants."""

    # Log levels
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

    # Log formats
    DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DETAILED_FORMAT = (
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    )

    # Log file paths
    DEFAULT_LOG_FILE = "cryptotaxcalc.log"
    ERROR_LOG_FILE = "cryptotaxcalc_errors.log"
    DEBUG_LOG_FILE = "cryptotaxcalc_debug.log"


# Performance Constants
class PerformanceConstants:
    """Performance-related constants."""

    # Batch processing
    DEFAULT_BATCH_SIZE = 1000
    MAX_BATCH_SIZE = 10000

    # Memory limits
    MAX_MEMORY_USAGE_MB = 1024  # 1GB
    WARNING_MEMORY_USAGE_MB = 512  # 512MB

    # Timeout values (seconds)
    DEFAULT_TIMEOUT = 300  # 5 minutes
    LONG_TIMEOUT = 1800  # 30 minutes

    # Cache settings
    CACHE_SIZE = 1000
    CACHE_TTL = 3600  # 1 hour


# File Paths and Extensions
class FilePaths:
    """File path and extension constants."""

    # File extensions
    CSV_EXTENSION = ".csv"
    JSON_EXTENSION = ".json"
    LOG_EXTENSION = ".log"

    # Default directories
    DEFAULT_OUTPUT_DIR = "output"
    DEFAULT_LOG_DIR = "logs"
    DEFAULT_DATA_DIR = "data"

    # Default filenames
    DEFAULT_OUTPUT_FILE = "tax_report.csv"
    DEFAULT_SUMMARY_FILE = "tax_summary.json"
    DEFAULT_LOG_FILE = "cryptotaxcalc.log"


# API Constants (for future Phase 2 integration)
class APIConstants:
    """API-related constants for future FMV integration."""

    # Rate limiting
    DEFAULT_RATE_LIMIT = 100  # requests per minute
    MAX_RATE_LIMIT = 1000  # requests per minute

    # Timeout values
    DEFAULT_REQUEST_TIMEOUT = 30  # seconds
    MAX_REQUEST_TIMEOUT = 300  # seconds

    # Retry settings
    DEFAULT_RETRY_ATTEMPTS = 3
    DEFAULT_RETRY_DELAY = 1  # seconds

    # Cache settings
    DEFAULT_CACHE_TTL = 3600  # 1 hour
    MAX_CACHE_TTL = 86400  # 24 hours


# Export all constants for easy import
__all__ = [
    "IRSConstants",
    "TransactionTypes",
    "TaxTreatmentMappings",
    "FeeHandlingRules",
    "ValidationRules",
    "ErrorMessages",
    "LoggingConfig",
    "PerformanceConstants",
    "FilePaths",
    "APIConstants",
]
