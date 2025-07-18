"""
Core CSV parser for CryptoTaxCalc.

Handles loading, validation, and filtering of cryptocurrency transaction data
with support for the enhanced 15-column format and 2024 tax year filtering.
"""

import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
import logging
from pathlib import Path
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Expected CSV columns (15-column format)
EXPECTED_COLUMNS = [
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

# Valid transaction types based on ManagerAI clarifications
VALID_TRANSACTION_TYPES = {
    "Deposit",
    "Withdrawal",
    "Trade",
    "Spend",
    "Income",
    "Staking",
    "Airdrop",
    "Lost",
    "Borrow",
    "Repay",
}

# Minimum USD value threshold for dust filtering
DUST_THRESHOLD_USD = 0.01


class TransactionParser:
    """
    Enhanced CSV parser for cryptocurrency transaction data.

    Supports 15-column format, 2024 filtering, data validation,
    and transaction type mapping according to IRS guidelines.
    """

    def __init__(
        self,
        enable_2024_filter: bool = True,
        dust_threshold: float = DUST_THRESHOLD_USD,
    ):
        """
        Initialize the transaction parser.

        Args:
            enable_2024_filter: Whether to filter for 2024 transactions only
            dust_threshold: Minimum USD value to avoid dust transactions
        """
        self.enable_2024_filter = enable_2024_filter
        self.dust_threshold = dust_threshold
        self.validation_errors: List[str] = []
        self.validation_warnings: List[str] = []

    def load_csv(self, file_path: str) -> pd.DataFrame:
        """
        Load and validate CSV file.

        Args:
            file_path: Path to the CSV file

        Returns:
            DataFrame with loaded and validated transaction data

        Raises:
            ValueError: If file cannot be loaded or has invalid format
        """
        try:
            # Load CSV file
            df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} rows from {file_path}")

            # Validate and clean the data
            df = self._validate_csv_structure(df)
            df = self._clean_data_types(df)
            df = self._apply_filters(df)
            df = self._validate_data_quality(df)

            logger.info(f"Processed {len(df)} valid transactions")
            return df

        except Exception as e:
            logger.error(f"Error loading CSV file {file_path}: {str(e)}")
            raise ValueError(f"Failed to load CSV: {str(e)}")

    def _validate_csv_structure(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate that CSV has expected structure and columns.

        Args:
            df: Raw DataFrame from CSV

        Returns:
            DataFrame with validated structure

        Raises:
            ValueError: If structure is invalid
        """
        # Check if we have the expected columns
        missing_columns = set(EXPECTED_COLUMNS) - set(df.columns)
        extra_columns = set(df.columns) - set(EXPECTED_COLUMNS)

        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        if extra_columns:
            logger.warning(f"Extra columns found (will be ignored): {extra_columns}")

        # Select only the expected columns in the correct order
        df = df[EXPECTED_COLUMNS].copy()

        logger.info(
            f"CSV structure validated: {len(df)} rows, {len(EXPECTED_COLUMNS)} columns"
        )
        return df

    def _clean_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and convert data types for proper processing.

        Args:
            df: DataFrame with validated structure

        Returns:
            DataFrame with cleaned data types
        """
        df = df.copy()

        # Clean numeric columns (remove currency symbols, commas)
        numeric_columns = ["BuyAmount", "SellAmount", "FeeAmount"]
        for col in numeric_columns:
            if col in df.columns:
                # Convert to string first, then clean
                df[col] = df[col].astype(str)
                # Remove currency symbols and commas
                df[col] = df[col].str.replace(r"[$,]", "", regex=True)
                # Convert to numeric, invalid values become NaN
                df[col] = pd.to_numeric(df[col], errors="coerce")
                # Fill NaN with 0 for amounts
                df[col] = df[col].fillna(0)

        # Clean USDEquivalent column
        if "USDEquivalent" in df.columns:
            df["USDEquivalent"] = df["USDEquivalent"].astype(str)
            df["USDEquivalent"] = df["USDEquivalent"].str.replace(
                r"[$,]", "", regex=True
            )
            df["USDEquivalent"] = pd.to_numeric(df["USDEquivalent"], errors="coerce")

        # Parse dates
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["UpdatedAt"] = pd.to_datetime(df["UpdatedAt"], errors="coerce")

        # Clean string columns
        string_columns = [
            "Type",
            "BuyCurrency",
            "SellCurrency",
            "FeeCurrency",
            "Exchange",
            "Comment",
        ]
        for col in string_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                # Replace 'nan' string with empty string
                df[col] = df[col].replace("nan", "")

        logger.info("Data types cleaned and converted")
        return df

    def _apply_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply filtering based on configuration.

        Args:
            df: DataFrame with cleaned data

        Returns:
            Filtered DataFrame
        """
        original_count = len(df)

        # Filter for 2024 transactions if enabled
        if self.enable_2024_filter:
            df = df[df["Date"].dt.year == 2024].copy()
            logger.info(
                f"2024 filter applied: {len(df)} transactions (from {original_count})"
            )

        # Filter out dust transactions
        if self.dust_threshold > 0:
            # Consider a transaction as dust if USD equivalent is below threshold
            dust_mask = (df["USDEquivalent"].fillna(0) >= self.dust_threshold) | df[
                "USDEquivalent"
            ].isna()
            dust_filtered = df[dust_mask].copy()
            dust_count = len(df) - len(dust_filtered)
            if dust_count > 0:
                logger.info(
                    f"Filtered out {dust_count} dust transactions (< ${self.dust_threshold})"
                )
            df = dust_filtered

        # Filter out invalid transaction types
        valid_type_mask = df["Type"].isin(VALID_TRANSACTION_TYPES)
        invalid_types = df[~valid_type_mask]["Type"].unique()
        if len(invalid_types) > 0:
            logger.warning(f"Found invalid transaction types: {invalid_types}")
            self.validation_warnings.append(
                f"Invalid transaction types found: {invalid_types}"
            )

        df = df[valid_type_mask].copy()

        return df

    def _validate_data_quality(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate data quality and flag issues.

        Args:
            df: Filtered DataFrame

        Returns:
            DataFrame with validation flags
        """
        # Check for negative quantities
        negative_buy = df["BuyAmount"] < 0
        negative_sell = df["SellAmount"] < 0
        negative_fee = df["FeeAmount"] < 0

        if negative_buy.any():
            count = negative_buy.sum()
            self.validation_errors.append(
                f"Found {count} transactions with negative BuyAmount"
            )
            logger.error(f"CRITICAL: {count} transactions have negative BuyAmount")

        if negative_sell.any():
            count = negative_sell.sum()
            self.validation_errors.append(
                f"Found {count} transactions with negative SellAmount"
            )
            logger.error(f"CRITICAL: {count} transactions have negative SellAmount")

        if negative_fee.any():
            count = negative_fee.sum()
            self.validation_errors.append(
                f"Found {count} transactions with negative FeeAmount"
            )
            logger.error(f"CRITICAL: {count} transactions have negative FeeAmount")

        # Check for missing critical data
        missing_date = df["Date"].isna()
        missing_type = df["Type"].isna() | (df["Type"] == "")

        if missing_date.any():
            count = missing_date.sum()
            self.validation_errors.append(
                f"Found {count} transactions with missing dates"
            )
            logger.error(f"CRITICAL: {count} transactions missing dates")

        if missing_type.any():
            count = missing_type.sum()
            self.validation_errors.append(
                f"Found {count} transactions with missing type"
            )
            logger.error(f"CRITICAL: {count} transactions missing type")

        # Check for missing USD equivalent (warning only)
        missing_usd = df["USDEquivalent"].isna()
        if missing_usd.any():
            count = missing_usd.sum()
            self.validation_warnings.append(
                f"Found {count} transactions with missing USDEquivalent"
            )
            logger.warning(
                f"WARNING: {count} transactions missing USDEquivalent (will need FMV lookup)"
            )

        # Stop processing if critical errors found
        if self.validation_errors:
            error_msg = "Critical validation errors found:\n" + "\n".join(
                self.validation_errors
            )
            raise ValueError(error_msg)

        return df

    def get_transaction_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate summary statistics for loaded transactions.

        Args:
            df: Processed DataFrame

        Returns:
            Dictionary with summary statistics
        """
        if df.empty:
            return {"error": "No transactions to analyze"}

        summary = {
            "total_transactions": len(df),
            "date_range": {
                "start": (
                    df["Date"].min().strftime("%Y-%m-%d")
                    if not df["Date"].min() is pd.NaT
                    else None
                ),
                "end": (
                    df["Date"].max().strftime("%Y-%m-%d")
                    if not df["Date"].max() is pd.NaT
                    else None
                ),
            },
            "transaction_types": df["Type"].value_counts().to_dict(),
            "exchanges": df["Exchange"].value_counts().head(10).to_dict(),
            "currencies": {
                "buy_currencies": df["BuyCurrency"].value_counts().head(10).to_dict(),
                "sell_currencies": df["SellCurrency"].value_counts().head(10).to_dict(),
            },
            "value_stats": {
                "total_usd_equivalent": (
                    df["USDEquivalent"].sum()
                    if not df["USDEquivalent"].isna().all()
                    else 0
                ),
                "missing_usd_count": df["USDEquivalent"].isna().sum(),
                "avg_transaction_value": (
                    df["USDEquivalent"].mean()
                    if not df["USDEquivalent"].isna().all()
                    else 0
                ),
            },
            "validation": {
                "errors": self.validation_errors,
                "warnings": self.validation_warnings,
            },
        }

        return summary

    def save_processed_data(self, df: pd.DataFrame, output_path: str) -> None:
        """
        Save processed transaction data to CSV.

        Args:
            df: Processed DataFrame
            output_path: Path for output file
        """
        try:
            df.to_csv(output_path, index=False)
            logger.info(f"Processed data saved to {output_path}")
        except Exception as e:
            logger.error(f"Error saving processed data: {str(e)}")
            raise


def parse_transaction_file(
    file_path: str,
    enable_2024_filter: bool = True,
    dust_threshold: float = DUST_THRESHOLD_USD,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Convenience function to parse a transaction file.

    Args:
        file_path: Path to the CSV file
        enable_2024_filter: Whether to filter for 2024 only
        dust_threshold: Minimum USD value threshold

    Returns:
        Tuple of (processed DataFrame, summary statistics)
    """
    parser = TransactionParser(
        enable_2024_filter=enable_2024_filter, dust_threshold=dust_threshold
    )

    df = parser.load_csv(file_path)
    summary = parser.get_transaction_summary(df)

    return df, summary


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        try:
            df, summary = parse_transaction_file(file_path)
            print(f"\n=== Transaction Summary ===")
            print(f"Total transactions: {summary['total_transactions']}")
            print(
                f"Date range: {summary['date_range']['start']} to {summary['date_range']['end']}"
            )
            print(f"Transaction types: {summary['transaction_types']}")

            if summary["validation"]["warnings"]:
                print(f"\nWarnings: {summary['validation']['warnings']}")

        except Exception as e:
            print(f"Error: {str(e)}")
    else:
        print("Usage: python parser.py <csv_file_path>")
