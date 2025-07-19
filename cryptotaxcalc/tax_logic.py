"""
Tax Logic Module for CryptoTaxCalc.

Handles IRS-compliant transaction type mapping, tax treatment classification,
and integration with FIFO manager for cryptocurrency tax calculations.
"""

import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any, NamedTuple
from enum import Enum
import logging
from dataclasses import dataclass

from .fifo_manager import FIFOManager, DisposalResult, Lot

# Configure logging
logger = logging.getLogger(__name__)


class TaxTreatment(Enum):
    """IRS tax treatment classifications for cryptocurrency transactions."""

    # Capital gains/losses
    SHORT_TERM_GAIN = "short_term_gain"
    SHORT_TERM_LOSS = "short_term_loss"
    LONG_TERM_GAIN = "long_term_gain"
    LONG_TERM_LOSS = "long_term_loss"

    # Ordinary income
    ORDINARY_INCOME = "ordinary_income"

    # Non-taxable events
    NON_TAXABLE = "non_taxable"

    # Special cases
    WASH_SALE = "wash_sale"
    LIKE_KIND_EXCHANGE = "like_kind_exchange"


class TransactionCategory(Enum):
    """High-level transaction categories for tax purposes."""

    ACQUISITION = "acquisition"  # Buying, receiving income, etc.
    DISPOSAL = "disposal"  # Selling, spending, etc.
    TRANSFER = "transfer"  # Moving between wallets/exchanges
    INCOME = "income"  # Staking, airdrops, etc.
    EXPENSE = "expense"  # Fees, losses, etc.


@dataclass
class TaxClassification:
    """Tax classification result for a transaction."""

    transaction_type: str
    tax_treatment: TaxTreatment
    category: TransactionCategory
    requires_fifo_processing: bool
    basis_adjustment: float = 0.0
    notes: str = ""


class TransactionTypeMapper:
    """
    Maps transaction types to IRS-compliant tax treatments.

    Provides comprehensive mapping for all supported transaction types
    according to current IRS cryptocurrency guidance.
    """

    def __init__(self):
        """Initialize the transaction type mapper."""
        self._initialize_mappings()

    def _initialize_mappings(self):
        """Initialize the transaction type to tax treatment mappings."""

        # Core transaction type mappings
        self.transaction_mappings = {
            # Trades (buy/sell)
            "Trade": {
                "tax_treatment": TaxTreatment.SHORT_TERM_GAIN,  # Default, will be adjusted by holding period
                "category": TransactionCategory.ACQUISITION,
                "requires_fifo": True,
                "description": "Cryptocurrency trade (buy/sell)",
            },
            # Spending
            "Spend": {
                "tax_treatment": TaxTreatment.SHORT_TERM_GAIN,  # Default, will be adjusted by holding period
                "category": TransactionCategory.DISPOSAL,
                "requires_fifo": True,
                "description": "Spending cryptocurrency (disposal event)",
            },
            # Income events (ordinary income)
            "Income": {
                "tax_treatment": TaxTreatment.ORDINARY_INCOME,
                "category": TransactionCategory.INCOME,
                "requires_fifo": False,
                "description": "Ordinary income (mining, etc.)",
            },
            "Staking": {
                "tax_treatment": TaxTreatment.ORDINARY_INCOME,
                "category": TransactionCategory.INCOME,
                "requires_fifo": False,
                "description": "Staking rewards (ordinary income)",
            },
            "Airdrop": {
                "tax_treatment": TaxTreatment.ORDINARY_INCOME,
                "category": TransactionCategory.INCOME,
                "requires_fifo": False,
                "description": "Airdrop (ordinary income at FMV)",
            },
            # Transfers (non-taxable)
            "Deposit": {
                "tax_treatment": TaxTreatment.NON_TAXABLE,
                "category": TransactionCategory.TRANSFER,
                "requires_fifo": False,
                "description": "Deposit to exchange (non-taxable transfer)",
            },
            "Withdrawal": {
                "tax_treatment": TaxTreatment.NON_TAXABLE,
                "category": TransactionCategory.TRANSFER,
                "requires_fifo": False,
                "description": "Withdrawal from exchange (non-taxable transfer)",
            },
            # Loss events
            "Lost": {
                "tax_treatment": TaxTreatment.SHORT_TERM_LOSS,  # Default, will be adjusted by holding period
                "category": TransactionCategory.EXPENSE,
                "requires_fifo": True,
                "description": "Lost cryptocurrency (theft/loss)",
            },
            # DeFi events
            "Borrow": {
                "tax_treatment": TaxTreatment.NON_TAXABLE,
                "category": TransactionCategory.TRANSFER,
                "requires_fifo": False,
                "description": "Borrowing against collateral (non-taxable)",
            },
            "Repay": {
                "tax_treatment": TaxTreatment.NON_TAXABLE,
                "category": TransactionCategory.TRANSFER,
                "requires_fifo": False,
                "description": "Repaying borrowed amount (non-taxable)",
            },
        }

    def classify_transaction(
        self,
        transaction_type: str,
        transaction_date: datetime,
        acquisition_date: Optional[datetime] = None,
    ) -> TaxClassification:
        """
        Classify a transaction for tax purposes.

        Args:
            transaction_type: The transaction type from the CSV
            transaction_date: Date of the transaction
            acquisition_date: Date of acquisition (for holding period calculation)

        Returns:
            TaxClassification with IRS-compliant tax treatment

        Raises:
            ValueError: If transaction type is not supported
        """
        if transaction_type not in self.transaction_mappings:
            raise ValueError(f"Unsupported transaction type: {transaction_type}")

        mapping = self.transaction_mappings[transaction_type]
        base_treatment = mapping["tax_treatment"]

        # Adjust tax treatment based on holding period for capital gains/losses
        if base_treatment in [
            TaxTreatment.SHORT_TERM_GAIN,
            TaxTreatment.SHORT_TERM_LOSS,
        ]:
            if acquisition_date and transaction_date:
                holding_period = (transaction_date - acquisition_date).days
                if holding_period >= 365:
                    # Convert to long-term
                    if base_treatment == TaxTreatment.SHORT_TERM_GAIN:
                        adjusted_treatment = TaxTreatment.LONG_TERM_GAIN
                    else:
                        adjusted_treatment = TaxTreatment.LONG_TERM_LOSS
                else:
                    adjusted_treatment = base_treatment
            else:
                adjusted_treatment = base_treatment
        else:
            adjusted_treatment = base_treatment

        return TaxClassification(
            transaction_type=transaction_type,
            tax_treatment=adjusted_treatment,
            category=mapping["category"],
            requires_fifo_processing=mapping["requires_fifo"],
            notes=mapping["description"],
        )

    def get_supported_types(self) -> List[str]:
        """Get list of supported transaction types."""
        return list(self.transaction_mappings.keys())

    def is_supported(self, transaction_type: str) -> bool:
        """Check if a transaction type is supported."""
        return transaction_type in self.transaction_mappings


class TaxProcessor:
    """
    Main tax processing engine that integrates transaction mapping with FIFO manager.

    Handles the complete tax calculation workflow for cryptocurrency transactions.
    """

    def __init__(self, fifo_manager: Optional[FIFOManager] = None):
        """
        Initialize the tax processor.

        Args:
            fifo_manager: Optional FIFO manager instance. If None, creates a new one.
        """
        self.fifo_manager = fifo_manager or FIFOManager()
        self.type_mapper = TransactionTypeMapper()
        self.processed_transactions: List[Dict[str, Any]] = []
        self.tax_summary: Dict[str, Any] = {}

    def process_transactions(
        self, transactions_df: pd.DataFrame
    ) -> List[DisposalResult]:
        """
        Process a DataFrame of transactions and return tax results.

        Args:
            transactions_df: DataFrame with transaction data from parser

        Returns:
            List of DisposalResult objects for all disposals processed
        """
        disposal_results = []

        # Sort transactions by date to ensure chronological processing
        sorted_df = transactions_df.sort_values("Date").copy()

        for idx, row in sorted_df.iterrows():
            try:
                transaction_type = row["Type"]
                date = row["Date"]

                # Classify the transaction
                classification = self.type_mapper.classify_transaction(
                    transaction_type=transaction_type, transaction_date=date
                )

                # Process based on classification
                if classification.requires_fifo_processing:
                    result = self._process_fifo_transaction(row, classification)
                    if result:
                        disposal_results.append(result)
                else:
                    self._process_non_fifo_transaction(row, classification)

                # Store processed transaction
                self.processed_transactions.append(
                    {
                        "index": idx,
                        "transaction_type": transaction_type,
                        "date": date,
                        "classification": classification,
                        "row_data": row.to_dict(),
                    }
                )

            except Exception as e:
                logger.error(f"Error processing transaction on {date}: {str(e)}")
                # Continue processing other transactions
                continue

        # Generate tax summary
        self._generate_tax_summary(disposal_results)

        return disposal_results

    def _process_fifo_transaction(
        self, row: pd.Series, classification: TaxClassification
    ) -> Optional[DisposalResult]:
        """
        Process a transaction that requires FIFO processing.

        Args:
            row: Transaction data row
            classification: Tax classification for the transaction

        Returns:
            DisposalResult if disposal occurred, None otherwise
        """
        transaction_type = row["Type"]
        date = row["Date"]

        if transaction_type in ["Trade", "Spend"]:
            # Handle disposals (sells)
            if row["SellAmount"] > 0 and row["SellCurrency"]:
                disposal_result = self.fifo_manager.process_disposal(
                    asset=row["SellCurrency"],
                    amount=row["SellAmount"],
                    proceeds=row["USDEquivalent"] or 0.0,
                    disposal_date=date,
                )
                return disposal_result

            # Handle acquisitions (buys)
            if row["BuyAmount"] > 0 and row["BuyCurrency"]:
                self.fifo_manager.add_acquisition(
                    asset=row["BuyCurrency"],
                    amount=row["BuyAmount"],
                    basis=row["USDEquivalent"] or 0.0,
                    acquisition_date=date,
                )

        elif transaction_type == "Lost":
            # Handle lost cryptocurrency (theft/loss)
            if row["SellAmount"] > 0 and row["SellCurrency"]:
                disposal_result = self.fifo_manager.process_disposal(
                    asset=row["SellCurrency"],
                    amount=row["SellAmount"],
                    proceeds=0.0,  # $0 proceeds for lost cryptocurrency
                    disposal_date=date,
                )
                return disposal_result

        return None

    def _process_non_fifo_transaction(
        self, row: pd.Series, classification: TaxClassification
    ) -> None:
        """
        Process a transaction that doesn't require FIFO processing.

        Args:
            row: Transaction data row
            classification: Tax classification for the transaction
        """
        transaction_type = row["Type"]
        date = row["Date"]

        if transaction_type in ["Income", "Staking", "Airdrop"]:
            # Handle income events (ordinary income with $0 basis)
            if row["BuyAmount"] > 0 and row["BuyCurrency"]:
                self.fifo_manager.add_acquisition(
                    asset=row["BuyCurrency"],
                    amount=row["BuyAmount"],
                    basis=0.0,  # $0 basis for income events
                    acquisition_date=date,
                )

        # Note: Deposit, Withdrawal, Borrow, Repay are non-taxable transfers
        # and don't require any FIFO processing

    def _generate_tax_summary(self, disposal_results: List[DisposalResult]) -> None:
        """
        Generate comprehensive tax summary from processed transactions.

        Args:
            disposal_results: List of disposal results from FIFO processing
        """
        # Get FIFO manager summary
        fifo_summary = self.fifo_manager.get_disposal_summary()

        # Calculate totals by tax treatment
        treatment_totals = {
            "short_term_gain": 0.0,
            "short_term_loss": 0.0,
            "long_term_gain": 0.0,
            "long_term_loss": 0.0,
            "ordinary_income": 0.0,
        }

        # Process disposal results
        for result in disposal_results:
            if result.short_term_gain_loss > 0:
                treatment_totals["short_term_gain"] += result.short_term_gain_loss
            elif result.short_term_gain_loss < 0:
                treatment_totals["short_term_loss"] += abs(result.short_term_gain_loss)

            if result.long_term_gain_loss > 0:
                treatment_totals["long_term_gain"] += result.long_term_gain_loss
            elif result.long_term_gain_loss < 0:
                treatment_totals["long_term_loss"] += abs(result.long_term_gain_loss)

        # Calculate ordinary income from non-FIFO transactions
        for transaction in self.processed_transactions:
            if (
                transaction["classification"].tax_treatment
                == TaxTreatment.ORDINARY_INCOME
            ):
                row_data = transaction["row_data"]
                if row_data.get("USDEquivalent"):
                    treatment_totals["ordinary_income"] += row_data["USDEquivalent"]

        self.tax_summary = {
            "fifo_summary": fifo_summary,
            "treatment_totals": treatment_totals,
            "total_transactions_processed": len(self.processed_transactions),
            "disposal_count": len(disposal_results),
            "net_short_term_gain_loss": treatment_totals["short_term_gain"]
            - treatment_totals["short_term_loss"],
            "net_long_term_gain_loss": treatment_totals["long_term_gain"]
            - treatment_totals["long_term_loss"],
            "total_ordinary_income": treatment_totals["ordinary_income"],
        }

    def get_tax_summary(self) -> Dict[str, Any]:
        """Get the current tax summary."""
        return self.tax_summary.copy()

    def get_processed_transactions(self) -> List[Dict[str, Any]]:
        """Get list of all processed transactions with classifications."""
        return self.processed_transactions.copy()

    def reset(self) -> None:
        """Reset the processor state."""
        self.fifo_manager = FIFOManager()
        self.processed_transactions.clear()
        self.tax_summary.clear()


def create_tax_processor(fifo_manager: Optional[FIFOManager] = None) -> TaxProcessor:
    """
    Convenience function to create a new tax processor.

    Args:
        fifo_manager: Optional FIFO manager instance

    Returns:
        New TaxProcessor instance
    """
    return TaxProcessor(fifo_manager)


if __name__ == "__main__":
    # Example usage
    import sys

    print("Tax Logic Module for CryptoTaxCalc")
    print(
        "This module provides IRS-compliant transaction type mapping and tax processing."
    )
    print("Use as part of the CryptoTaxCalc package.")
