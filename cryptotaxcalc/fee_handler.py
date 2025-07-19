"""
Fee Handler Module for CryptoTaxCalc.

Handles transaction fee processing, USD equivalent calculation,
fee adjustments to cost basis and proceeds, and integration with FIFO manager.
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


class FeeType(Enum):
    """Types of fees that can be processed."""

    TRADING_FEE = "trading_fee"  # Exchange trading fees
    NETWORK_FEE = "network_fee"  # Blockchain network fees
    WITHDRAWAL_FEE = "withdrawal_fee"  # Exchange withdrawal fees
    DEPOSIT_FEE = "deposit_fee"  # Exchange deposit fees
    STAKING_FEE = "staking_fee"  # Staking platform fees
    UNKNOWN_FEE = "unknown_fee"  # Unclassified fees


class FeeTreatment(Enum):
    """How fees should be treated for tax purposes."""

    ADD_TO_BASIS = "add_to_basis"  # Add to cost basis (acquisitions)
    REDUCE_PROCEEDS = "reduce_proceeds"  # Reduce proceeds (disposals)
    DEDUCTIBLE_EXPENSE = "deductible"  # Deductible business expense
    NON_DEDUCTIBLE = "non_deductible"  # Non-deductible personal expense


@dataclass
class FeeInfo:
    """Information about a transaction fee."""

    amount: float
    currency: str
    usd_equivalent: float
    fee_type: FeeType
    treatment: FeeTreatment
    transaction_date: datetime
    asset: str
    notes: str = ""


@dataclass
class FeeAdjustment:
    """Result of fee adjustment calculation."""

    original_amount: float
    original_usd: float
    fee_amount: float
    fee_usd: float
    adjusted_amount: float
    adjusted_usd: float
    adjustment_type: FeeTreatment
    notes: str = ""


class FeeProcessor:
    """
    Processes transaction fees and calculates USD equivalents.

    Handles fee extraction, classification, USD conversion, and
    integration with FIFO manager for basis/proceeds adjustments.
    """

    def __init__(self):
        """Initialize the fee processor."""
        self._initialize_fee_mappings()
        self.processed_fees: List[FeeInfo] = []
        self.fee_statistics: Dict[str, Any] = {}

    def _initialize_fee_mappings(self):
        """Initialize fee type and treatment mappings."""

        # Fee type mappings based on transaction context
        self.fee_type_mappings = {
            # Trading fees
            "Trade": {
                "default_type": FeeType.TRADING_FEE,
                "default_treatment": FeeTreatment.ADD_TO_BASIS,  # For buys
                "disposal_treatment": FeeTreatment.REDUCE_PROCEEDS,  # For sells
            },
            # Spending fees
            "Spend": {
                "default_type": FeeType.NETWORK_FEE,
                "default_treatment": FeeTreatment.REDUCE_PROCEEDS,
                "disposal_treatment": FeeTreatment.REDUCE_PROCEEDS,
            },
            # Transfer fees
            "Deposit": {
                "default_type": FeeType.DEPOSIT_FEE,
                "default_treatment": FeeTreatment.NON_DEDUCTIBLE,
                "disposal_treatment": FeeTreatment.NON_DEDUCTIBLE,
            },
            "Withdrawal": {
                "default_type": FeeType.WITHDRAWAL_FEE,
                "default_treatment": FeeTreatment.NON_DEDUCTIBLE,
                "disposal_treatment": FeeTreatment.NON_DEDUCTIBLE,
            },
            # Income fees
            "Staking": {
                "default_type": FeeType.STAKING_FEE,
                "default_treatment": FeeTreatment.DEDUCTIBLE_EXPENSE,
                "disposal_treatment": FeeTreatment.DEDUCTIBLE_EXPENSE,
            },
            # Default for other transaction types
            "default": {
                "default_type": FeeType.UNKNOWN_FEE,
                "default_treatment": FeeTreatment.NON_DEDUCTIBLE,
                "disposal_treatment": FeeTreatment.NON_DEDUCTIBLE,
            },
        }

    def extract_fees_from_transaction(self, row: pd.Series) -> Optional[FeeInfo]:
        """
        Extract and process fees from a transaction row.

        Args:
            row: Transaction data row from parser

        Returns:
            FeeInfo if fees found, None otherwise
        """
        fee_amount = row.get("FeeAmount", 0.0) or 0.0
        fee_currency = row.get("FeeCurrency", "")

        if fee_amount <= 0 or not fee_currency:
            return None

        # Determine fee type and treatment based on transaction type
        transaction_type = row.get("Type", "default")
        mapping = self.fee_type_mappings.get(
            transaction_type, self.fee_type_mappings["default"]
        )

        # Determine if this is a disposal (sell) or acquisition (buy)
        is_disposal = (row.get("SellAmount", 0.0) or 0.0) > 0

        fee_type = mapping["default_type"]
        treatment = (
            mapping["disposal_treatment"]
            if is_disposal
            else mapping["default_treatment"]
        )

        # Calculate USD equivalent
        usd_equivalent = self._calculate_fee_usd_equivalent(
            row, fee_amount, fee_currency
        )

        # Determine asset for fee tracking
        asset = (
            row.get("SellCurrency", "") if is_disposal else row.get("BuyCurrency", "")
        )

        fee_info = FeeInfo(
            amount=fee_amount,
            currency=fee_currency,
            usd_equivalent=usd_equivalent,
            fee_type=fee_type,
            treatment=treatment,
            transaction_date=row.get("Date", datetime.now()),
            asset=asset,
        )

        self.processed_fees.append(fee_info)
        return fee_info

    def _calculate_fee_usd_equivalent(
        self, row: pd.Series, fee_amount: float, fee_currency: str
    ) -> float:
        """
        Calculate USD equivalent of a fee.

        Args:
            row: Transaction data row
            fee_amount: Fee amount in original currency
            fee_currency: Fee currency

        Returns:
            USD equivalent of the fee
        """
        if fee_amount <= 0 or not fee_currency:
            return 0.0

        # If fee currency is USD or USD-pegged, return the amount directly
        if fee_currency.upper() in ["USD", "USDT", "USDC", "BUSD", "DAI"]:
            return fee_amount

        # If fee currency matches the transaction currency, use transaction USD value
        transaction_usd = row.get("USDEquivalent", 0.0) or 0.0
        if transaction_usd > 0:
            # Calculate fee as proportion of transaction value
            if row.get("SellAmount", 0.0) > 0:
                # For disposals, fee reduces proceeds
                sell_amount = row.get("SellAmount", 0.0)
                if sell_amount > 0:
                    return fee_amount * (transaction_usd / sell_amount)
            elif row.get("BuyAmount", 0.0) > 0:
                # For acquisitions, fee adds to basis
                buy_amount = row.get("BuyAmount", 0.0)
                if buy_amount > 0:
                    return fee_amount * (transaction_usd / buy_amount)

        # Fallback: estimate based on typical fee rates
        # This is a rough approximation - Phase 2 will improve with real FMV data
        estimated_usd_rate = self._estimate_usd_rate(fee_currency)
        return fee_amount * estimated_usd_rate

    def _estimate_usd_rate(self, currency: str) -> float:
        """
        Estimate USD rate for a currency (fallback method).

        Args:
            currency: Currency symbol

        Returns:
            Estimated USD rate
        """
        # Common cryptocurrency USD rates (approximate, will be replaced by Phase 2 FMV)
        rate_estimates = {
            "BTC": 45000.0,
            "ETH": 3000.0,
            "BNB": 300.0,
            "ADA": 0.5,
            "DOT": 7.0,
            "LINK": 15.0,
            "LTC": 70.0,
            "BCH": 250.0,
            "XRP": 0.6,
            "SOL": 100.0,
            "MATIC": 0.8,
            "AVAX": 25.0,
            "UNI": 7.0,
            "ATOM": 10.0,
            "FTM": 0.4,
            "NEAR": 3.0,
            "ALGO": 0.2,
            "VET": 0.03,
            "ICP": 12.0,
            "FIL": 5.0,
        }

        return rate_estimates.get(currency.upper(), 1.0)  # Default to 1:1 if unknown

    def calculate_fee_adjustment(
        self, original_amount: float, original_usd: float, fee_info: FeeInfo
    ) -> FeeAdjustment:
        """
        Calculate how fees affect the original amount and USD value.

        Args:
            original_amount: Original transaction amount
            original_usd: Original USD value
            fee_info: Fee information

        Returns:
            FeeAdjustment with adjusted values
        """
        if fee_info.treatment == FeeTreatment.ADD_TO_BASIS:
            # For acquisitions: fee increases cost basis
            adjusted_amount = original_amount
            adjusted_usd = original_usd + fee_info.usd_equivalent

        elif fee_info.treatment == FeeTreatment.REDUCE_PROCEEDS:
            # For disposals: fee reduces proceeds
            adjusted_amount = original_amount
            adjusted_usd = original_usd - fee_info.usd_equivalent

        else:
            # For deductible/non-deductible: no adjustment to basis/proceeds
            adjusted_amount = original_amount
            adjusted_usd = original_usd

        return FeeAdjustment(
            original_amount=original_amount,
            original_usd=original_usd,
            fee_amount=fee_info.amount,
            fee_usd=fee_info.usd_equivalent,
            adjusted_amount=adjusted_amount,
            adjusted_usd=adjusted_usd,
            adjustment_type=fee_info.treatment,
            notes=f"Fee adjustment: {fee_info.fee_type.value}",
        )

    def process_fees_for_fifo(
        self, row: pd.Series, fifo_manager: FIFOManager
    ) -> Optional[FeeAdjustment]:
        """
        Process fees and apply adjustments to FIFO manager.

        Args:
            row: Transaction data row
            fifo_manager: FIFO manager instance

        Returns:
            FeeAdjustment if fees were processed, None otherwise
        """
        fee_info = self.extract_fees_from_transaction(row)
        if not fee_info:
            return None

        transaction_type = row.get("Type", "")
        date = row.get("Date", datetime.now())

        # Handle acquisitions (buys)
        if row.get("BuyAmount", 0.0) > 0 and row.get("BuyCurrency"):
            buy_amount = row.get("BuyAmount", 0.0)
            buy_currency = row.get("BuyCurrency", "")
            original_usd = row.get("USDEquivalent", 0.0) or 0.0

            # Calculate fee adjustment
            adjustment = self.calculate_fee_adjustment(
                original_amount=buy_amount, original_usd=original_usd, fee_info=fee_info
            )

            # Add acquisition with fee-adjusted basis
            fifo_manager.add_acquisition(
                asset=buy_currency,
                amount=buy_amount,
                basis=adjustment.adjusted_usd,
                acquisition_date=date,
            )

            return adjustment

        # Handle disposals (sells)
        elif row.get("SellAmount", 0.0) > 0 and row.get("SellCurrency"):
            sell_amount = row.get("SellAmount", 0.0)
            sell_currency = row.get("SellCurrency", "")
            original_usd = row.get("USDEquivalent", 0.0) or 0.0

            # Calculate fee adjustment
            adjustment = self.calculate_fee_adjustment(
                original_amount=sell_amount,
                original_usd=original_usd,
                fee_info=fee_info,
            )

            # Process disposal with fee-adjusted proceeds
            fifo_manager.process_disposal(
                asset=sell_currency,
                amount=sell_amount,
                proceeds=adjustment.adjusted_usd,
                disposal_date=date,
            )

            return adjustment

        return None

    def get_fee_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive fee processing statistics.

        Returns:
            Dictionary with fee statistics
        """
        if not self.processed_fees:
            return {
                "total_fees": 0,
                "total_fee_usd": 0.0,
                "fee_types": {},
                "treatments": {},
                "assets": {},
                "average_fee_usd": 0.0,
            }

        total_fees = len(self.processed_fees)
        total_fee_usd = sum(fee.usd_equivalent for fee in self.processed_fees)

        # Count by fee type
        fee_types = {}
        for fee in self.processed_fees:
            fee_type = fee.fee_type.value
            fee_types[fee_type] = fee_types.get(fee_type, 0) + 1

        # Count by treatment
        treatments = {}
        for fee in self.processed_fees:
            treatment = fee.treatment.value
            treatments[treatment] = treatments.get(treatment, 0) + 1

        # Count by asset
        assets = {}
        for fee in self.processed_fees:
            asset = fee.asset
            if asset:
                assets[asset] = assets.get(asset, 0) + 1

        self.fee_statistics = {
            "total_fees": total_fees,
            "total_fee_usd": total_fee_usd,
            "fee_types": fee_types,
            "treatments": treatments,
            "assets": assets,
            "average_fee_usd": total_fee_usd / total_fees if total_fees > 0 else 0.0,
        }

        return self.fee_statistics.copy()

    def get_processed_fees(self) -> List[FeeInfo]:
        """Get list of all processed fees."""
        return self.processed_fees.copy()

    def reset(self) -> None:
        """Reset the fee processor state."""
        self.processed_fees.clear()
        self.fee_statistics.clear()


class FeeHandler:
    """
    Main fee handling engine that integrates with FIFO manager.

    Provides comprehensive fee processing capabilities for the tax calculation system.
    """

    def __init__(self, fifo_manager: Optional[FIFOManager] = None):
        """
        Initialize the fee handler.

        Args:
            fifo_manager: Optional FIFO manager instance. If None, creates a new one.
        """
        self.fifo_manager = fifo_manager or FIFOManager()
        self.fee_processor = FeeProcessor()
        self.fee_adjustments: List[FeeAdjustment] = []

    def process_transaction_with_fees(self, row: pd.Series) -> Optional[FeeAdjustment]:
        """
        Process a transaction with fee handling.

        Args:
            row: Transaction data row

        Returns:
            FeeAdjustment if fees were processed, None otherwise
        """
        # Extract and process fees
        fee_adjustment = self.fee_processor.process_fees_for_fifo(
            row, self.fifo_manager
        )

        if fee_adjustment:
            self.fee_adjustments.append(fee_adjustment)

        return fee_adjustment

    def process_transactions_dataframe(
        self, transactions_df: pd.DataFrame
    ) -> List[FeeAdjustment]:
        """
        Process a DataFrame of transactions with fee handling.

        Args:
            transactions_df: DataFrame with transaction data

        Returns:
            List of FeeAdjustment objects for all fee adjustments
        """
        fee_adjustments = []

        # Sort transactions by date to ensure chronological processing
        sorted_df = transactions_df.sort_values("Date").copy()

        for _, row in sorted_df.iterrows():
            try:
                fee_adjustment = self.process_transaction_with_fees(row)
                if fee_adjustment:
                    fee_adjustments.append(fee_adjustment)

            except Exception as e:
                logger.error(
                    f"Error processing fees for transaction on {row.get('Date')}: {str(e)}"
                )
                # Continue processing other transactions
                continue

        return fee_adjustments

    def get_fee_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive fee processing summary.

        Returns:
            Dictionary with fee summary information
        """
        fee_stats = self.fee_processor.get_fee_statistics()

        return {
            "fee_statistics": fee_stats,
            "total_adjustments": len(self.fee_adjustments),
            "fifo_manager_summary": self.fifo_manager.get_disposal_summary(),
            "fifo_queues_summary": self.fifo_manager.get_all_summaries(),
        }

    def get_fifo_manager(self) -> FIFOManager:
        """Get the FIFO manager instance."""
        return self.fifo_manager

    def get_fee_processor(self) -> FeeProcessor:
        """Get the fee processor instance."""
        return self.fee_processor

    def reset(self) -> None:
        """Reset the fee handler state."""
        self.fifo_manager = FIFOManager()
        self.fee_processor.reset()
        self.fee_adjustments.clear()


def create_fee_handler(fifo_manager: Optional[FIFOManager] = None) -> FeeHandler:
    """
    Convenience function to create a new fee handler.

    Args:
        fifo_manager: Optional FIFO manager instance

    Returns:
        New FeeHandler instance
    """
    return FeeHandler(fifo_manager)


if __name__ == "__main__":
    # Example usage
    import sys

    print("Fee Handler Module for CryptoTaxCalc")
    print(
        "This module provides comprehensive fee processing and integration with FIFO manager."
    )
    print("Use as part of the CryptoTaxCalc package.")
