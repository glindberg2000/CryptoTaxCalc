"""
Tests for the fee handler module.

Tests fee processing, USD equivalent calculation, fee adjustments,
and integration with FIFO manager for cryptocurrency transactions.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any

from cryptotaxcalc.fee_handler import (
    FeeType,
    FeeTreatment,
    FeeInfo,
    FeeAdjustment,
    FeeProcessor,
    FeeHandler,
    create_fee_handler,
)
from cryptotaxcalc.fifo_manager import FIFOManager, DisposalResult, Lot


class TestFeeType:
    """Test fee type enum values."""

    def test_fee_type_values(self):
        """Test that all fee type values are valid."""
        assert FeeType.TRADING_FEE.value == "trading_fee"
        assert FeeType.NETWORK_FEE.value == "network_fee"
        assert FeeType.WITHDRAWAL_FEE.value == "withdrawal_fee"
        assert FeeType.DEPOSIT_FEE.value == "deposit_fee"
        assert FeeType.STAKING_FEE.value == "staking_fee"
        assert FeeType.UNKNOWN_FEE.value == "unknown_fee"


class TestFeeTreatment:
    """Test fee treatment enum values."""

    def test_fee_treatment_values(self):
        """Test that all fee treatment values are valid."""
        assert FeeTreatment.ADD_TO_BASIS.value == "add_to_basis"
        assert FeeTreatment.REDUCE_PROCEEDS.value == "reduce_proceeds"
        assert FeeTreatment.DEDUCTIBLE_EXPENSE.value == "deductible"
        assert FeeTreatment.NON_DEDUCTIBLE.value == "non_deductible"


class TestFeeInfo:
    """Test fee info dataclass."""

    def test_fee_info_creation(self):
        """Test creating a fee info object."""
        fee_info = FeeInfo(
            amount=0.001,
            currency="BTC",
            usd_equivalent=45.0,
            fee_type=FeeType.TRADING_FEE,
            treatment=FeeTreatment.ADD_TO_BASIS,
            transaction_date=datetime(2024, 1, 15),
            asset="BTC",
            notes="Test fee",
        )

        assert fee_info.amount == 0.001
        assert fee_info.currency == "BTC"
        assert fee_info.usd_equivalent == 45.0
        assert fee_info.fee_type == FeeType.TRADING_FEE
        assert fee_info.treatment == FeeTreatment.ADD_TO_BASIS
        assert fee_info.asset == "BTC"
        assert fee_info.notes == "Test fee"

    def test_fee_info_defaults(self):
        """Test fee info with default values."""
        fee_info = FeeInfo(
            amount=0.001,
            currency="BTC",
            usd_equivalent=45.0,
            fee_type=FeeType.TRADING_FEE,
            treatment=FeeTreatment.ADD_TO_BASIS,
            transaction_date=datetime(2024, 1, 15),
            asset="BTC",
        )

        assert fee_info.notes == ""


class TestFeeAdjustment:
    """Test fee adjustment dataclass."""

    def test_fee_adjustment_creation(self):
        """Test creating a fee adjustment object."""
        adjustment = FeeAdjustment(
            original_amount=1.0,
            original_usd=45000.0,
            fee_amount=0.001,
            fee_usd=45.0,
            adjusted_amount=1.0,
            adjusted_usd=45045.0,
            adjustment_type=FeeTreatment.ADD_TO_BASIS,
            notes="Test adjustment",
        )

        assert adjustment.original_amount == 1.0
        assert adjustment.original_usd == 45000.0
        assert adjustment.fee_amount == 0.001
        assert adjustment.fee_usd == 45.0
        assert adjustment.adjusted_amount == 1.0
        assert adjustment.adjusted_usd == 45045.0
        assert adjustment.adjustment_type == FeeTreatment.ADD_TO_BASIS
        assert adjustment.notes == "Test adjustment"

    def test_fee_adjustment_defaults(self):
        """Test fee adjustment with default values."""
        adjustment = FeeAdjustment(
            original_amount=1.0,
            original_usd=45000.0,
            fee_amount=0.001,
            fee_usd=45.0,
            adjusted_amount=1.0,
            adjusted_usd=45045.0,
            adjustment_type=FeeTreatment.ADD_TO_BASIS,
        )

        assert adjustment.notes == ""


class TestFeeProcessor:
    """Test fee processor functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = FeeProcessor()

    def test_initialization(self):
        """Test that processor initializes correctly."""
        assert hasattr(self.processor, "fee_type_mappings")
        assert hasattr(self.processor, "processed_fees")
        assert hasattr(self.processor, "fee_statistics")
        assert len(self.processor.fee_type_mappings) > 0

    def test_extract_fees_no_fees(self):
        """Test extracting fees when no fees are present."""
        row = pd.Series(
            {
                "Type": "Trade",
                "FeeAmount": 0.0,
                "FeeCurrency": "",
                "Date": datetime(2024, 1, 15),
            }
        )

        fee_info = self.processor.extract_fees_from_transaction(row)
        assert fee_info is None

    def test_extract_fees_trade_transaction(self):
        """Test extracting fees from a trade transaction."""
        row = pd.Series(
            {
                "Type": "Trade",
                "BuyAmount": 1.0,
                "BuyCurrency": "BTC",
                "SellAmount": 0.0,
                "SellCurrency": "",
                "FeeAmount": 0.001,
                "FeeCurrency": "BTC",
                "USDEquivalent": 45000.0,
                "Date": datetime(2024, 1, 15),
            }
        )

        fee_info = self.processor.extract_fees_from_transaction(row)

        assert fee_info is not None
        assert fee_info.amount == 0.001
        assert fee_info.currency == "BTC"
        assert fee_info.fee_type == FeeType.TRADING_FEE
        assert fee_info.treatment == FeeTreatment.ADD_TO_BASIS  # For buy transaction
        assert fee_info.asset == "BTC"

    def test_extract_fees_spend_transaction(self):
        """Test extracting fees from a spend transaction."""
        row = pd.Series(
            {
                "Type": "Spend",
                "BuyAmount": 0.0,
                "BuyCurrency": "",
                "SellAmount": 0.5,
                "SellCurrency": "BTC",
                "FeeAmount": 0.0005,
                "FeeCurrency": "BTC",
                "USDEquivalent": 22500.0,
                "Date": datetime(2024, 1, 15),
            }
        )

        fee_info = self.processor.extract_fees_from_transaction(row)

        assert fee_info is not None
        assert fee_info.amount == 0.0005
        assert fee_info.currency == "BTC"
        assert fee_info.fee_type == FeeType.NETWORK_FEE
        assert (
            fee_info.treatment == FeeTreatment.REDUCE_PROCEEDS
        )  # For sell transaction
        assert fee_info.asset == "BTC"

    def test_extract_fees_deposit_transaction(self):
        """Test extracting fees from a deposit transaction."""
        row = pd.Series(
            {
                "Type": "Deposit",
                "BuyAmount": 1.0,
                "BuyCurrency": "BTC",
                "SellAmount": 0.0,
                "SellCurrency": "",
                "FeeAmount": 0.0001,
                "FeeCurrency": "BTC",
                "USDEquivalent": 45000.0,
                "Date": datetime(2024, 1, 15),
            }
        )

        fee_info = self.processor.extract_fees_from_transaction(row)

        assert fee_info is not None
        assert fee_info.fee_type == FeeType.DEPOSIT_FEE
        assert fee_info.treatment == FeeTreatment.NON_DEDUCTIBLE

    def test_extract_fees_withdrawal_transaction(self):
        """Test extracting fees from a withdrawal transaction."""
        row = pd.Series(
            {
                "Type": "Withdrawal",
                "BuyAmount": 0.0,
                "BuyCurrency": "",
                "SellAmount": 1.0,
                "SellCurrency": "BTC",
                "FeeAmount": 0.0005,
                "FeeCurrency": "BTC",
                "USDEquivalent": 45000.0,
                "Date": datetime(2024, 1, 15),
            }
        )

        fee_info = self.processor.extract_fees_from_transaction(row)

        assert fee_info is not None
        assert fee_info.fee_type == FeeType.WITHDRAWAL_FEE
        assert fee_info.treatment == FeeTreatment.NON_DEDUCTIBLE

    def test_extract_fees_staking_transaction(self):
        """Test extracting fees from a staking transaction."""
        row = pd.Series(
            {
                "Type": "Staking",
                "BuyAmount": 10.0,
                "BuyCurrency": "ADA",
                "SellAmount": 0.0,
                "SellCurrency": "",
                "FeeAmount": 0.5,
                "FeeCurrency": "ADA",
                "USDEquivalent": 2500.0,
                "Date": datetime(2024, 1, 15),
            }
        )

        fee_info = self.processor.extract_fees_from_transaction(row)

        assert fee_info is not None
        assert fee_info.fee_type == FeeType.STAKING_FEE
        assert fee_info.treatment == FeeTreatment.DEDUCTIBLE_EXPENSE

    def test_calculate_fee_usd_equivalent_usd_currency(self):
        """Test USD equivalent calculation for USD-pegged currencies."""
        row = pd.Series({"USDEquivalent": 45000.0, "BuyAmount": 1.0, "SellAmount": 0.0})

        # Test USD
        usd_equivalent = self.processor._calculate_fee_usd_equivalent(row, 10.0, "USD")
        assert usd_equivalent == 10.0

        # Test USDT
        usd_equivalent = self.processor._calculate_fee_usd_equivalent(row, 10.0, "USDT")
        assert usd_equivalent == 10.0

        # Test USDC
        usd_equivalent = self.processor._calculate_fee_usd_equivalent(row, 10.0, "USDC")
        assert usd_equivalent == 10.0

    def test_calculate_fee_usd_equivalent_buy_transaction(self):
        """Test USD equivalent calculation for buy transactions."""
        row = pd.Series({"USDEquivalent": 45000.0, "BuyAmount": 1.0, "SellAmount": 0.0})

        # Fee in same currency as buy
        usd_equivalent = self.processor._calculate_fee_usd_equivalent(row, 0.001, "BTC")
        expected = 0.001 * (45000.0 / 1.0)  # 45.0
        assert usd_equivalent == expected

    def test_calculate_fee_usd_equivalent_sell_transaction(self):
        """Test USD equivalent calculation for sell transactions."""
        row = pd.Series({"USDEquivalent": 22500.0, "BuyAmount": 0.0, "SellAmount": 0.5})

        # Fee in same currency as sell
        usd_equivalent = self.processor._calculate_fee_usd_equivalent(
            row, 0.0005, "BTC"
        )
        expected = 0.0005 * (22500.0 / 0.5)  # 22.5
        assert usd_equivalent == expected

    def test_calculate_fee_usd_equivalent_fallback(self):
        """Test USD equivalent calculation fallback for unknown currencies."""
        row = pd.Series({"USDEquivalent": 0.0, "BuyAmount": 0.0, "SellAmount": 0.0})

        # Test with known cryptocurrency
        usd_equivalent = self.processor._calculate_fee_usd_equivalent(row, 0.001, "ETH")
        expected = 0.001 * 3000.0  # From rate estimates
        assert usd_equivalent == expected

        # Test with unknown cryptocurrency
        usd_equivalent = self.processor._calculate_fee_usd_equivalent(
            row, 10.0, "UNKNOWN"
        )
        assert usd_equivalent == 10.0  # Default 1:1 rate

    def test_calculate_fee_adjustment_add_to_basis(self):
        """Test fee adjustment calculation for adding to basis."""
        fee_info = FeeInfo(
            amount=0.001,
            currency="BTC",
            usd_equivalent=45.0,
            fee_type=FeeType.TRADING_FEE,
            treatment=FeeTreatment.ADD_TO_BASIS,
            transaction_date=datetime(2024, 1, 15),
            asset="BTC",
        )

        adjustment = self.processor.calculate_fee_adjustment(
            original_amount=1.0, original_usd=45000.0, fee_info=fee_info
        )

        assert adjustment.original_amount == 1.0
        assert adjustment.original_usd == 45000.0
        assert adjustment.fee_amount == 0.001
        assert adjustment.fee_usd == 45.0
        assert adjustment.adjusted_amount == 1.0
        assert adjustment.adjusted_usd == 45045.0  # 45000 + 45
        assert adjustment.adjustment_type == FeeTreatment.ADD_TO_BASIS

    def test_calculate_fee_adjustment_reduce_proceeds(self):
        """Test fee adjustment calculation for reducing proceeds."""
        fee_info = FeeInfo(
            amount=0.0005,
            currency="BTC",
            usd_equivalent=22.5,
            fee_type=FeeType.NETWORK_FEE,
            treatment=FeeTreatment.REDUCE_PROCEEDS,
            transaction_date=datetime(2024, 1, 15),
            asset="BTC",
        )

        adjustment = self.processor.calculate_fee_adjustment(
            original_amount=0.5, original_usd=22500.0, fee_info=fee_info
        )

        assert adjustment.original_amount == 0.5
        assert adjustment.original_usd == 22500.0
        assert adjustment.fee_amount == 0.0005
        assert adjustment.fee_usd == 22.5
        assert adjustment.adjusted_amount == 0.5
        assert adjustment.adjusted_usd == 22477.5  # 22500 - 22.5
        assert adjustment.adjustment_type == FeeTreatment.REDUCE_PROCEEDS

    def test_calculate_fee_adjustment_non_deductible(self):
        """Test fee adjustment calculation for non-deductible fees."""
        fee_info = FeeInfo(
            amount=0.0001,
            currency="BTC",
            usd_equivalent=4.5,
            fee_type=FeeType.DEPOSIT_FEE,
            treatment=FeeTreatment.NON_DEDUCTIBLE,
            transaction_date=datetime(2024, 1, 15),
            asset="BTC",
        )

        adjustment = self.processor.calculate_fee_adjustment(
            original_amount=1.0, original_usd=45000.0, fee_info=fee_info
        )

        assert adjustment.original_amount == 1.0
        assert adjustment.original_usd == 45000.0
        assert adjustment.fee_amount == 0.0001
        assert adjustment.fee_usd == 4.5
        assert adjustment.adjusted_amount == 1.0
        assert adjustment.adjusted_usd == 45000.0  # No adjustment
        assert adjustment.adjustment_type == FeeTreatment.NON_DEDUCTIBLE

    def test_process_fees_for_fifo_buy_transaction(self):
        """Test processing fees for a buy transaction with FIFO manager."""
        fifo_manager = FIFOManager()

        row = pd.Series(
            {
                "Type": "Trade",
                "BuyAmount": 1.0,
                "BuyCurrency": "BTC",
                "SellAmount": 0.0,
                "SellCurrency": "",
                "FeeAmount": 0.001,
                "FeeCurrency": "BTC",
                "USDEquivalent": 45000.0,
                "Date": datetime(2024, 1, 15),
            }
        )

        adjustment = self.processor.process_fees_for_fifo(row, fifo_manager)

        assert adjustment is not None
        assert adjustment.adjusted_usd == 45045.0  # 45000 + 45

        # Check that acquisition was added to FIFO with fee-adjusted basis
        queue_summary = fifo_manager.get_queue_summary("BTC")
        assert queue_summary["total_amount"] == 1.0
        assert queue_summary["total_basis"] == 45045.0

    def test_process_fees_for_fifo_sell_transaction(self):
        """Test processing fees for a sell transaction with FIFO manager."""
        fifo_manager = FIFOManager()

        # First add some BTC to the FIFO queue
        fifo_manager.add_acquisition(
            asset="BTC",
            amount=1.0,
            basis=40000.0,
            acquisition_date=datetime(2024, 1, 1),
        )

        row = pd.Series(
            {
                "Type": "Trade",
                "BuyAmount": 0.0,
                "BuyCurrency": "",
                "SellAmount": 0.5,
                "SellCurrency": "BTC",
                "FeeAmount": 0.0005,
                "FeeCurrency": "BTC",
                "USDEquivalent": 22500.0,
                "Date": datetime(2024, 6, 1),
            }
        )

        adjustment = self.processor.process_fees_for_fifo(row, fifo_manager)

        assert adjustment is not None
        assert adjustment.adjusted_usd == 22477.5  # 22500 - 22.5

        # Check that disposal was processed with fee-adjusted proceeds
        disposal_summary = fifo_manager.get_disposal_summary()
        assert disposal_summary["total_disposals"] == 1
        assert disposal_summary["total_proceeds"] == 22477.5

    def test_get_fee_statistics_empty(self):
        """Test fee statistics when no fees have been processed."""
        stats = self.processor.get_fee_statistics()

        assert stats["total_fees"] == 0
        assert stats["total_fee_usd"] == 0.0
        assert stats["fee_types"] == {}
        assert stats["treatments"] == {}
        assert stats["assets"] == {}
        assert stats["average_fee_usd"] == 0.0

    def test_get_fee_statistics_with_fees(self):
        """Test fee statistics with processed fees."""
        # Process some fees
        row1 = pd.Series(
            {
                "Type": "Trade",
                "BuyAmount": 1.0,
                "BuyCurrency": "BTC",
                "SellAmount": 0.0,
                "SellCurrency": "",
                "FeeAmount": 0.001,
                "FeeCurrency": "BTC",
                "USDEquivalent": 45000.0,
                "Date": datetime(2024, 1, 15),
            }
        )

        row2 = pd.Series(
            {
                "Type": "Trade",
                "BuyAmount": 0.0,
                "BuyCurrency": "",
                "SellAmount": 0.5,
                "SellCurrency": "ETH",
                "FeeAmount": 0.01,
                "FeeCurrency": "ETH",
                "USDEquivalent": 1500.0,
                "Date": datetime(2024, 1, 16),
            }
        )

        self.processor.extract_fees_from_transaction(row1)
        self.processor.extract_fees_from_transaction(row2)

        stats = self.processor.get_fee_statistics()

        assert stats["total_fees"] == 2
        assert stats["total_fee_usd"] > 0.0
        assert "trading_fee" in stats["fee_types"]
        assert "add_to_basis" in stats["treatments"]
        assert "reduce_proceeds" in stats["treatments"]
        assert "BTC" in stats["assets"]
        assert "ETH" in stats["assets"]
        assert stats["average_fee_usd"] > 0.0

    def test_reset_functionality(self):
        """Test that reset functionality works correctly."""
        # Process some fees
        row = pd.Series(
            {
                "Type": "Trade",
                "BuyAmount": 1.0,
                "BuyCurrency": "BTC",
                "SellAmount": 0.0,
                "SellCurrency": "",
                "FeeAmount": 0.001,
                "FeeCurrency": "BTC",
                "USDEquivalent": 45000.0,
                "Date": datetime(2024, 1, 15),
            }
        )

        self.processor.extract_fees_from_transaction(row)

        # Verify data exists
        assert len(self.processor.processed_fees) > 0

        # Reset
        self.processor.reset()

        # Verify data is cleared
        assert len(self.processor.processed_fees) == 0
        assert len(self.processor.fee_statistics) == 0


class TestFeeHandler:
    """Test fee handler functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.fifo_manager = FIFOManager()
        self.handler = FeeHandler(self.fifo_manager)

    def test_initialization(self):
        """Test that handler initializes correctly."""
        assert hasattr(self.handler, "fifo_manager")
        assert hasattr(self.handler, "fee_processor")
        assert hasattr(self.handler, "fee_adjustments")
        assert isinstance(self.handler.fee_processor, FeeProcessor)

    def test_create_fee_handler(self):
        """Test creating a fee handler with convenience function."""
        handler = create_fee_handler()
        assert isinstance(handler, FeeHandler)
        assert handler.fifo_manager is not None

    def test_create_fee_handler_with_fifo(self):
        """Test creating a fee handler with existing FIFO manager."""
        fifo_manager = FIFOManager()
        handler = create_fee_handler(fifo_manager)
        assert handler.fifo_manager is fifo_manager

    def test_process_transaction_with_fees(self):
        """Test processing a single transaction with fees."""
        row = pd.Series(
            {
                "Type": "Trade",
                "BuyAmount": 1.0,
                "BuyCurrency": "BTC",
                "SellAmount": 0.0,
                "SellCurrency": "",
                "FeeAmount": 0.001,
                "FeeCurrency": "BTC",
                "USDEquivalent": 45000.0,
                "Date": datetime(2024, 1, 15),
            }
        )

        adjustment = self.handler.process_transaction_with_fees(row)

        assert adjustment is not None
        assert len(self.handler.fee_adjustments) == 1
        assert self.handler.fee_adjustments[0] is adjustment

    def test_process_transactions_dataframe(self):
        """Test processing a DataFrame of transactions with fees."""
        transactions = [
            {
                "Type": "Trade",
                "BuyAmount": 1.0,
                "BuyCurrency": "BTC",
                "SellAmount": 0.0,
                "SellCurrency": "",
                "FeeAmount": 0.001,
                "FeeCurrency": "BTC",
                "USDEquivalent": 45000.0,
                "Date": datetime(2024, 1, 15),
            },
            {
                "Type": "Trade",
                "BuyAmount": 0.0,
                "BuyCurrency": "",
                "SellAmount": 0.5,
                "SellCurrency": "BTC",
                "FeeAmount": 0.0005,
                "FeeCurrency": "BTC",
                "USDEquivalent": 22500.0,
                "Date": datetime(2024, 1, 16),
            },
        ]

        df = pd.DataFrame(transactions)
        adjustments = self.handler.process_transactions_dataframe(df)

        assert len(adjustments) == 2
        assert len(self.handler.fee_adjustments) == 2

    def test_get_fee_summary(self):
        """Test getting comprehensive fee summary."""
        # Process some transactions
        row = pd.Series(
            {
                "Type": "Trade",
                "BuyAmount": 1.0,
                "BuyCurrency": "BTC",
                "SellAmount": 0.0,
                "SellCurrency": "",
                "FeeAmount": 0.001,
                "FeeCurrency": "BTC",
                "USDEquivalent": 45000.0,
                "Date": datetime(2024, 1, 15),
            }
        )

        self.handler.process_transaction_with_fees(row)

        summary = self.handler.get_fee_summary()

        assert "fee_statistics" in summary
        assert "total_adjustments" in summary
        assert "fifo_manager_summary" in summary
        assert "fifo_queues_summary" in summary

        assert summary["total_adjustments"] == 1
        assert summary["fee_statistics"]["total_fees"] == 1

    def test_get_fifo_manager(self):
        """Test getting the FIFO manager instance."""
        fifo_manager = self.handler.get_fifo_manager()
        assert fifo_manager is self.fifo_manager

    def test_get_fee_processor(self):
        """Test getting the fee processor instance."""
        fee_processor = self.handler.get_fee_processor()
        assert isinstance(fee_processor, FeeProcessor)

    def test_reset_functionality(self):
        """Test that reset functionality works correctly."""
        # Process some transactions
        row = pd.Series(
            {
                "Type": "Trade",
                "BuyAmount": 1.0,
                "BuyCurrency": "BTC",
                "SellAmount": 0.0,
                "SellCurrency": "",
                "FeeAmount": 0.001,
                "FeeCurrency": "BTC",
                "USDEquivalent": 45000.0,
                "Date": datetime(2024, 1, 15),
            }
        )

        self.handler.process_transaction_with_fees(row)

        # Verify data exists
        assert len(self.handler.fee_adjustments) > 0

        # Reset
        self.handler.reset()

        # Verify data is cleared
        assert len(self.handler.fee_adjustments) == 0

        # Verify FIFO manager is reset
        fifo_summary = self.handler.fifo_manager.get_disposal_summary()
        assert fifo_summary["total_disposals"] == 0


class TestFeeHandlerIntegration:
    """Test fee handler integration with real data scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = FeeHandler()

    def test_complex_trading_scenario_with_fees(self):
        """Test a complex trading scenario with multiple fees."""
        # Create a series of transactions with fees
        transactions = [
            # Buy BTC with trading fee
            {
                "Type": "Trade",
                "BuyAmount": 1.0,
                "BuyCurrency": "BTC",
                "SellAmount": 0.0,
                "SellCurrency": "",
                "FeeAmount": 0.001,
                "FeeCurrency": "BTC",
                "USDEquivalent": 45000.0,
                "Date": datetime(2024, 1, 1),
            },
            # Sell BTC with network fee
            {
                "Type": "Trade",
                "BuyAmount": 0.0,
                "BuyCurrency": "",
                "SellAmount": 0.5,
                "SellCurrency": "BTC",
                "FeeAmount": 0.0005,
                "FeeCurrency": "BTC",
                "USDEquivalent": 22500.0,
                "Date": datetime(2024, 6, 1),
            },
            # Deposit with deposit fee
            {
                "Type": "Deposit",
                "BuyAmount": 0.1,
                "BuyCurrency": "ETH",
                "SellAmount": 0.0,
                "SellCurrency": "",
                "FeeAmount": 0.001,
                "FeeCurrency": "ETH",
                "USDEquivalent": 300.0,
                "Date": datetime(2024, 7, 1),
            },
        ]

        df = pd.DataFrame(transactions)
        adjustments = self.handler.process_transactions_dataframe(df)

        # Should have 3 fee adjustments
        assert len(adjustments) == 3

        # Check fee summary
        summary = self.handler.get_fee_summary()
        assert summary["total_adjustments"] == 3
        assert summary["fee_statistics"]["total_fees"] == 3

        # Check FIFO summary
        fifo_summary = self.handler.fifo_manager.get_disposal_summary()
        assert fifo_summary["total_disposals"] == 1  # Only the sell transaction

    def test_error_handling(self):
        """Test that errors are handled gracefully."""
        # Create transaction with invalid data
        transaction_data = {
            "Type": "Trade",
            "BuyAmount": 1.0,
            "BuyCurrency": "BTC",
            "SellAmount": 0.0,
            "SellCurrency": "",
            "FeeAmount": 0.001,
            "FeeCurrency": "BTC",
            "USDEquivalent": 45000.0,
            "Date": datetime(2024, 1, 15),
        }

        df = pd.DataFrame([transaction_data])

        # This should not raise an exception
        adjustments = self.handler.process_transactions_dataframe(df)

        # Should process successfully
        assert len(adjustments) == 1


if __name__ == "__main__":
    pytest.main([__file__])
