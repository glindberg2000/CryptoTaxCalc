"""
Tests for the tax logic module.

Tests transaction type mapping, tax treatment classification,
and integration with FIFO manager for cryptocurrency tax calculations.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any

from cryptotaxcalc.tax_logic import (
    TaxTreatment,
    TransactionCategory,
    TaxClassification,
    TransactionTypeMapper,
    TaxProcessor,
    create_tax_processor,
)
from cryptotaxcalc.fifo_manager import FIFOManager, DisposalResult, Lot


class TestTaxTreatment:
    """Test tax treatment enum values."""

    def test_tax_treatment_values(self):
        """Test that all tax treatment values are valid."""
        assert TaxTreatment.SHORT_TERM_GAIN.value == "short_term_gain"
        assert TaxTreatment.SHORT_TERM_LOSS.value == "short_term_loss"
        assert TaxTreatment.LONG_TERM_GAIN.value == "long_term_gain"
        assert TaxTreatment.LONG_TERM_LOSS.value == "long_term_loss"
        assert TaxTreatment.ORDINARY_INCOME.value == "ordinary_income"
        assert TaxTreatment.NON_TAXABLE.value == "non_taxable"
        assert TaxTreatment.WASH_SALE.value == "wash_sale"
        assert TaxTreatment.LIKE_KIND_EXCHANGE.value == "like_kind_exchange"


class TestTransactionCategory:
    """Test transaction category enum values."""

    def test_transaction_category_values(self):
        """Test that all transaction category values are valid."""
        assert TransactionCategory.ACQUISITION.value == "acquisition"
        assert TransactionCategory.DISPOSAL.value == "disposal"
        assert TransactionCategory.TRANSFER.value == "transfer"
        assert TransactionCategory.INCOME.value == "income"
        assert TransactionCategory.EXPENSE.value == "expense"


class TestTaxClassification:
    """Test tax classification dataclass."""

    def test_tax_classification_creation(self):
        """Test creating a tax classification."""
        classification = TaxClassification(
            transaction_type="Trade",
            tax_treatment=TaxTreatment.SHORT_TERM_GAIN,
            category=TransactionCategory.ACQUISITION,
            requires_fifo_processing=True,
            basis_adjustment=0.0,
            notes="Test classification",
        )

        assert classification.transaction_type == "Trade"
        assert classification.tax_treatment == TaxTreatment.SHORT_TERM_GAIN
        assert classification.category == TransactionCategory.ACQUISITION
        assert classification.requires_fifo_processing is True
        assert classification.basis_adjustment == 0.0
        assert classification.notes == "Test classification"

    def test_tax_classification_defaults(self):
        """Test tax classification with default values."""
        classification = TaxClassification(
            transaction_type="Trade",
            tax_treatment=TaxTreatment.SHORT_TERM_GAIN,
            category=TransactionCategory.ACQUISITION,
            requires_fifo_processing=True,
        )

        assert classification.basis_adjustment == 0.0
        assert classification.notes == ""


class TestTransactionTypeMapper:
    """Test transaction type mapper functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mapper = TransactionTypeMapper()

    def test_initialization(self):
        """Test that mapper initializes correctly."""
        assert hasattr(self.mapper, "transaction_mappings")
        assert len(self.mapper.transaction_mappings) > 0

    def test_supported_transaction_types(self):
        """Test that all expected transaction types are supported."""
        expected_types = [
            "Trade",
            "Spend",
            "Income",
            "Staking",
            "Airdrop",
            "Deposit",
            "Withdrawal",
            "Lost",
            "Borrow",
            "Repay",
        ]

        supported_types = self.mapper.get_supported_types()
        for expected_type in expected_types:
            assert expected_type in supported_types

    def test_classify_trade_transaction(self):
        """Test classifying a trade transaction."""
        date = datetime(2024, 1, 15)
        classification = self.mapper.classify_transaction(
            transaction_type="Trade", transaction_date=date
        )

        assert classification.transaction_type == "Trade"
        assert classification.tax_treatment == TaxTreatment.SHORT_TERM_GAIN
        assert classification.category == TransactionCategory.ACQUISITION
        assert classification.requires_fifo_processing is True

    def test_classify_income_transaction(self):
        """Test classifying an income transaction."""
        date = datetime(2024, 1, 15)
        classification = self.mapper.classify_transaction(
            transaction_type="Income", transaction_date=date
        )

        assert classification.transaction_type == "Income"
        assert classification.tax_treatment == TaxTreatment.ORDINARY_INCOME
        assert classification.category == TransactionCategory.INCOME
        assert classification.requires_fifo_processing is False

    def test_classify_staking_transaction(self):
        """Test classifying a staking transaction."""
        date = datetime(2024, 1, 15)
        classification = self.mapper.classify_transaction(
            transaction_type="Staking", transaction_date=date
        )

        assert classification.transaction_type == "Staking"
        assert classification.tax_treatment == TaxTreatment.ORDINARY_INCOME
        assert classification.category == TransactionCategory.INCOME
        assert classification.requires_fifo_processing is False

    def test_classify_airdrop_transaction(self):
        """Test classifying an airdrop transaction."""
        date = datetime(2024, 1, 15)
        classification = self.mapper.classify_transaction(
            transaction_type="Airdrop", transaction_date=date
        )

        assert classification.transaction_type == "Airdrop"
        assert classification.tax_treatment == TaxTreatment.ORDINARY_INCOME
        assert classification.category == TransactionCategory.INCOME
        assert classification.requires_fifo_processing is False

    def test_classify_spend_transaction(self):
        """Test classifying a spend transaction."""
        date = datetime(2024, 1, 15)
        classification = self.mapper.classify_transaction(
            transaction_type="Spend", transaction_date=date
        )

        assert classification.transaction_type == "Spend"
        assert classification.tax_treatment == TaxTreatment.SHORT_TERM_GAIN
        assert classification.category == TransactionCategory.DISPOSAL
        assert classification.requires_fifo_processing is True

    def test_classify_transfer_transactions(self):
        """Test classifying transfer transactions."""
        date = datetime(2024, 1, 15)

        # Test deposit
        deposit_classification = self.mapper.classify_transaction(
            transaction_type="Deposit", transaction_date=date
        )
        assert deposit_classification.tax_treatment == TaxTreatment.NON_TAXABLE
        assert deposit_classification.category == TransactionCategory.TRANSFER
        assert deposit_classification.requires_fifo_processing is False

        # Test withdrawal
        withdrawal_classification = self.mapper.classify_transaction(
            transaction_type="Withdrawal", transaction_date=date
        )
        assert withdrawal_classification.tax_treatment == TaxTreatment.NON_TAXABLE
        assert withdrawal_classification.category == TransactionCategory.TRANSFER
        assert withdrawal_classification.requires_fifo_processing is False

    def test_classify_lost_transaction(self):
        """Test classifying a lost transaction."""
        date = datetime(2024, 1, 15)
        classification = self.mapper.classify_transaction(
            transaction_type="Lost", transaction_date=date
        )

        assert classification.transaction_type == "Lost"
        assert classification.tax_treatment == TaxTreatment.SHORT_TERM_LOSS
        assert classification.category == TransactionCategory.EXPENSE
        assert classification.requires_fifo_processing is True

    def test_classify_defi_transactions(self):
        """Test classifying DeFi transactions."""
        date = datetime(2024, 1, 15)

        # Test borrow
        borrow_classification = self.mapper.classify_transaction(
            transaction_type="Borrow", transaction_date=date
        )
        assert borrow_classification.tax_treatment == TaxTreatment.NON_TAXABLE
        assert borrow_classification.category == TransactionCategory.TRANSFER
        assert borrow_classification.requires_fifo_processing is False

        # Test repay
        repay_classification = self.mapper.classify_transaction(
            transaction_type="Repay", transaction_date=date
        )
        assert repay_classification.tax_treatment == TaxTreatment.NON_TAXABLE
        assert repay_classification.category == TransactionCategory.TRANSFER
        assert repay_classification.requires_fifo_processing is False

    def test_holding_period_adjustment_short_term(self):
        """Test that short-term holding period is maintained."""
        acquisition_date = datetime(2024, 1, 1)
        transaction_date = datetime(2024, 6, 1)  # 152 days later

        classification = self.mapper.classify_transaction(
            transaction_type="Trade",
            transaction_date=transaction_date,
            acquisition_date=acquisition_date,
        )

        assert classification.tax_treatment == TaxTreatment.SHORT_TERM_GAIN

    def test_holding_period_adjustment_long_term(self):
        """Test that long-term holding period is applied."""
        acquisition_date = datetime(2023, 1, 1)
        transaction_date = datetime(2024, 6, 1)  # 517 days later

        classification = self.mapper.classify_transaction(
            transaction_type="Trade",
            transaction_date=transaction_date,
            acquisition_date=acquisition_date,
        )

        assert classification.tax_treatment == TaxTreatment.LONG_TERM_GAIN

    def test_holding_period_adjustment_loss(self):
        """Test holding period adjustment for losses."""
        acquisition_date = datetime(2023, 1, 1)
        transaction_date = datetime(2024, 6, 1)  # 517 days later

        classification = self.mapper.classify_transaction(
            transaction_type="Lost",
            transaction_date=transaction_date,
            acquisition_date=acquisition_date,
        )

        assert classification.tax_treatment == TaxTreatment.LONG_TERM_LOSS

    def test_unsupported_transaction_type(self):
        """Test that unsupported transaction types raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported transaction type"):
            self.mapper.classify_transaction(
                transaction_type="InvalidType", transaction_date=datetime(2024, 1, 15)
            )

    def test_is_supported_method(self):
        """Test the is_supported method."""
        assert self.mapper.is_supported("Trade") is True
        assert self.mapper.is_supported("Income") is True
        assert self.mapper.is_supported("InvalidType") is False


class TestTaxProcessor:
    """Test tax processor functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.fifo_manager = FIFOManager()
        self.processor = TaxProcessor(self.fifo_manager)

    def test_initialization(self):
        """Test that processor initializes correctly."""
        assert hasattr(self.processor, "fifo_manager")
        assert hasattr(self.processor, "type_mapper")
        assert hasattr(self.processor, "processed_transactions")
        assert hasattr(self.processor, "tax_summary")
        assert isinstance(self.processor.type_mapper, TransactionTypeMapper)

    def test_create_tax_processor(self):
        """Test creating a tax processor with convenience function."""
        processor = create_tax_processor()
        assert isinstance(processor, TaxProcessor)
        assert processor.fifo_manager is not None

    def test_create_tax_processor_with_fifo(self):
        """Test creating a tax processor with existing FIFO manager."""
        fifo_manager = FIFOManager()
        processor = create_tax_processor(fifo_manager)
        assert processor.fifo_manager is fifo_manager

    def test_process_single_trade_transaction(self):
        """Test processing a single trade transaction."""
        # Create test transaction data
        transaction_data = {
            "Type": "Trade",
            "BuyAmount": 1.0,
            "BuyCurrency": "BTC",
            "SellAmount": 0.0,
            "SellCurrency": "",
            "FeeAmount": 0.0,
            "FeeCurrency": "",
            "Exchange": "TestExchange",
            "ExchangeId": "123",
            "Group": "",
            "Import": "",
            "Comment": "",
            "Date": datetime(2024, 1, 15),
            "USDEquivalent": 45000.0,
            "UpdatedAt": datetime(2024, 1, 15),
        }

        df = pd.DataFrame([transaction_data])
        disposal_results = self.processor.process_transactions(df)

        # Should be no disposals for a buy-only trade
        assert len(disposal_results) == 0

        # Check that transaction was processed
        assert len(self.processor.processed_transactions) == 1
        processed = self.processor.processed_transactions[0]
        assert processed["transaction_type"] == "Trade"
        assert processed["classification"].requires_fifo_processing is True

    def test_process_trade_with_disposal(self):
        """Test processing a trade transaction with disposal."""
        # First add some BTC to the FIFO queue
        self.fifo_manager.add_acquisition(
            asset="BTC",
            amount=1.0,
            basis=40000.0,
            acquisition_date=datetime(2024, 1, 1),
        )

        # Create test transaction data for selling
        transaction_data = {
            "Type": "Trade",
            "BuyAmount": 0.0,
            "BuyCurrency": "",
            "SellAmount": 0.5,
            "SellCurrency": "BTC",
            "FeeAmount": 0.0,
            "FeeCurrency": "",
            "Exchange": "TestExchange",
            "ExchangeId": "123",
            "Group": "",
            "Import": "",
            "Comment": "",
            "Date": datetime(2024, 6, 1),
            "USDEquivalent": 25000.0,
            "UpdatedAt": datetime(2024, 6, 1),
        }

        df = pd.DataFrame([transaction_data])
        disposal_results = self.processor.process_transactions(df)

        # Should have one disposal result
        assert len(disposal_results) == 1
        disposal = disposal_results[0]
        assert disposal.asset == "BTC"
        assert disposal.disposal_amount == 0.5
        assert disposal.total_proceeds == 25000.0
        assert disposal.total_basis == 20000.0  # Half of original basis
        assert disposal.total_gain_loss == 5000.0  # 25000 - 20000

    def test_process_income_transaction(self):
        """Test processing an income transaction."""
        transaction_data = {
            "Type": "Income",
            "BuyAmount": 10.0,
            "BuyCurrency": "ETH",
            "SellAmount": 0.0,
            "SellCurrency": "",
            "FeeAmount": 0.0,
            "FeeCurrency": "",
            "Exchange": "TestExchange",
            "ExchangeId": "123",
            "Group": "",
            "Import": "",
            "Comment": "",
            "Date": datetime(2024, 1, 15),
            "USDEquivalent": 30000.0,
            "UpdatedAt": datetime(2024, 1, 15),
        }

        df = pd.DataFrame([transaction_data])
        disposal_results = self.processor.process_transactions(df)

        # Should be no disposals for income
        assert len(disposal_results) == 0

        # Check that transaction was processed
        assert len(self.processor.processed_transactions) == 1
        processed = self.processor.processed_transactions[0]
        assert processed["transaction_type"] == "Income"
        assert processed["classification"].tax_treatment == TaxTreatment.ORDINARY_INCOME
        assert processed["classification"].requires_fifo_processing is False

    def test_process_staking_transaction(self):
        """Test processing a staking transaction."""
        transaction_data = {
            "Type": "Staking",
            "BuyAmount": 5.0,
            "BuyCurrency": "ADA",
            "SellAmount": 0.0,
            "SellCurrency": "",
            "FeeAmount": 0.0,
            "FeeCurrency": "",
            "Exchange": "TestExchange",
            "ExchangeId": "123",
            "Group": "",
            "Import": "",
            "Comment": "",
            "Date": datetime(2024, 1, 15),
            "USDEquivalent": 2500.0,
            "UpdatedAt": datetime(2024, 1, 15),
        }

        df = pd.DataFrame([transaction_data])
        disposal_results = self.processor.process_transactions(df)

        # Should be no disposals for staking
        assert len(disposal_results) == 0

        # Check that transaction was processed
        assert len(self.processor.processed_transactions) == 1
        processed = self.processor.processed_transactions[0]
        assert processed["transaction_type"] == "Staking"
        assert processed["classification"].tax_treatment == TaxTreatment.ORDINARY_INCOME
        assert processed["classification"].requires_fifo_processing is False

    def test_process_transfer_transactions(self):
        """Test processing transfer transactions."""
        # Test deposit
        deposit_data = {
            "Type": "Deposit",
            "BuyAmount": 1.0,
            "BuyCurrency": "BTC",
            "SellAmount": 0.0,
            "SellCurrency": "",
            "FeeAmount": 0.0,
            "FeeCurrency": "",
            "Exchange": "TestExchange",
            "ExchangeId": "123",
            "Group": "",
            "Import": "",
            "Comment": "",
            "Date": datetime(2024, 1, 15),
            "USDEquivalent": 45000.0,
            "UpdatedAt": datetime(2024, 1, 15),
        }

        df = pd.DataFrame([deposit_data])
        disposal_results = self.processor.process_transactions(df)

        # Should be no disposals for transfers
        assert len(disposal_results) == 0

        # Check that transaction was processed
        assert len(self.processor.processed_transactions) == 1
        processed = self.processor.processed_transactions[0]
        assert processed["transaction_type"] == "Deposit"
        assert processed["classification"].tax_treatment == TaxTreatment.NON_TAXABLE
        assert processed["classification"].requires_fifo_processing is False

    def test_process_lost_transaction(self):
        """Test processing a lost transaction."""
        # First add some BTC to the FIFO queue
        self.fifo_manager.add_acquisition(
            asset="BTC",
            amount=1.0,
            basis=40000.0,
            acquisition_date=datetime(2024, 1, 1),
        )

        # Create test transaction data for lost BTC
        transaction_data = {
            "Type": "Lost",
            "BuyAmount": 0.0,
            "BuyCurrency": "",
            "SellAmount": 0.5,
            "SellCurrency": "BTC",
            "FeeAmount": 0.0,
            "FeeCurrency": "",
            "Exchange": "TestExchange",
            "ExchangeId": "123",
            "Group": "",
            "Import": "",
            "Comment": "",
            "Date": datetime(2024, 6, 1),
            "USDEquivalent": 0.0,  # $0 proceeds for lost cryptocurrency
            "UpdatedAt": datetime(2024, 6, 1),
        }

        df = pd.DataFrame([transaction_data])
        disposal_results = self.processor.process_transactions(df)

        # Should have one disposal result
        assert len(disposal_results) == 1
        disposal = disposal_results[0]
        assert disposal.asset == "BTC"
        assert disposal.disposal_amount == 0.5
        assert disposal.total_proceeds == 0.0  # $0 proceeds
        assert disposal.total_basis == 20000.0  # Half of original basis
        assert disposal.total_gain_loss == -20000.0  # 0 - 20000 = loss

    def test_tax_summary_generation(self):
        """Test that tax summary is generated correctly."""
        # Add some acquisitions
        self.fifo_manager.add_acquisition(
            asset="BTC",
            amount=1.0,
            basis=40000.0,
            acquisition_date=datetime(2024, 1, 1),
        )

        # Process a disposal
        transaction_data = {
            "Type": "Trade",
            "BuyAmount": 0.0,
            "BuyCurrency": "",
            "SellAmount": 0.5,
            "SellCurrency": "BTC",
            "FeeAmount": 0.0,
            "FeeCurrency": "",
            "Exchange": "TestExchange",
            "ExchangeId": "123",
            "Group": "",
            "Import": "",
            "Comment": "",
            "Date": datetime(2024, 6, 1),
            "USDEquivalent": 25000.0,
            "UpdatedAt": datetime(2024, 6, 1),
        }

        df = pd.DataFrame([transaction_data])
        disposal_results = self.processor.process_transactions(df)

        # Get tax summary
        summary = self.processor.get_tax_summary()

        assert "fifo_summary" in summary
        assert "treatment_totals" in summary
        assert "total_transactions_processed" in summary
        assert "disposal_count" in summary
        assert "net_short_term_gain_loss" in summary
        assert "net_long_term_gain_loss" in summary
        assert "total_ordinary_income" in summary

        assert summary["total_transactions_processed"] == 1
        assert summary["disposal_count"] == 1
        assert summary["net_short_term_gain_loss"] == 5000.0  # 25000 - 20000

    def test_reset_functionality(self):
        """Test that reset functionality works correctly."""
        # Add some data
        self.fifo_manager.add_acquisition(
            asset="BTC",
            amount=1.0,
            basis=40000.0,
            acquisition_date=datetime(2024, 1, 1),
        )

        transaction_data = {
            "Type": "Trade",
            "BuyAmount": 0.0,
            "BuyCurrency": "",
            "SellAmount": 0.5,
            "SellCurrency": "BTC",
            "FeeAmount": 0.0,
            "FeeCurrency": "",
            "Exchange": "TestExchange",
            "ExchangeId": "123",
            "Group": "",
            "Import": "",
            "Comment": "",
            "Date": datetime(2024, 6, 1),
            "USDEquivalent": 25000.0,
            "UpdatedAt": datetime(2024, 6, 1),
        }

        df = pd.DataFrame([transaction_data])
        self.processor.process_transactions(df)

        # Verify data exists
        assert len(self.processor.processed_transactions) > 0
        assert len(self.processor.tax_summary) > 0

        # Reset
        self.processor.reset()

        # Verify data is cleared
        assert len(self.processor.processed_transactions) == 0
        assert len(self.processor.tax_summary) == 0

        # Verify FIFO manager is reset
        fifo_summary = self.processor.fifo_manager.get_disposal_summary()
        assert fifo_summary["total_disposals"] == 0


class TestTaxProcessorIntegration:
    """Test tax processor integration with real data scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = TaxProcessor()

    def test_complex_trading_scenario(self):
        """Test a complex trading scenario with multiple transactions."""
        # Create a series of transactions
        transactions = [
            # Buy BTC
            {
                "Type": "Trade",
                "BuyAmount": 1.0,
                "BuyCurrency": "BTC",
                "SellAmount": 0.0,
                "SellCurrency": "",
                "FeeAmount": 0.0,
                "FeeCurrency": "",
                "Exchange": "Exchange1",
                "ExchangeId": "1",
                "Group": "",
                "Import": "",
                "Comment": "",
                "Date": datetime(2024, 1, 1),
                "USDEquivalent": 40000.0,
                "UpdatedAt": datetime(2024, 1, 1),
            },
            # Receive staking rewards
            {
                "Type": "Staking",
                "BuyAmount": 0.1,
                "BuyCurrency": "BTC",
                "SellAmount": 0.0,
                "SellCurrency": "",
                "FeeAmount": 0.0,
                "FeeCurrency": "",
                "Exchange": "Exchange1",
                "ExchangeId": "2",
                "Group": "",
                "Import": "",
                "Comment": "",
                "Date": datetime(2024, 2, 1),
                "USDEquivalent": 4500.0,
                "UpdatedAt": datetime(2024, 2, 1),
            },
            # Sell some BTC
            {
                "Type": "Trade",
                "BuyAmount": 0.0,
                "BuyCurrency": "",
                "SellAmount": 0.5,
                "SellCurrency": "BTC",
                "FeeAmount": 0.0,
                "FeeCurrency": "",
                "Exchange": "Exchange1",
                "ExchangeId": "3",
                "Group": "",
                "Import": "",
                "Comment": "",
                "Date": datetime(2024, 6, 1),
                "USDEquivalent": 25000.0,
                "UpdatedAt": datetime(2024, 6, 1),
            },
        ]

        df = pd.DataFrame(transactions)
        disposal_results = self.processor.process_transactions(df)

        # Should have one disposal
        assert len(disposal_results) == 1

        # Check FIFO summary
        fifo_summary = self.processor.fifo_manager.get_disposal_summary()
        assert fifo_summary["total_disposals"] == 1
        assert fifo_summary["total_proceeds"] == 25000.0

        # Check tax summary
        tax_summary = self.processor.get_tax_summary()
        assert tax_summary["total_transactions_processed"] == 3
        assert tax_summary["disposal_count"] == 1
        assert tax_summary["total_ordinary_income"] == 4500.0  # Staking rewards

    def test_error_handling(self):
        """Test that errors are handled gracefully."""
        # Create transaction with invalid data
        transaction_data = {
            "Type": "Trade",
            "BuyAmount": 1.0,
            "BuyCurrency": "BTC",
            "SellAmount": 0.0,
            "SellCurrency": "",
            "FeeAmount": 0.0,
            "FeeCurrency": "",
            "Exchange": "TestExchange",
            "ExchangeId": "123",
            "Group": "",
            "Import": "",
            "Comment": "",
            "Date": datetime(2024, 1, 15),
            "USDEquivalent": 45000.0,
            "UpdatedAt": datetime(2024, 1, 15),
        }

        df = pd.DataFrame([transaction_data])

        # This should not raise an exception
        disposal_results = self.processor.process_transactions(df)

        # Should process successfully
        assert len(self.processor.processed_transactions) == 1


if __name__ == "__main__":
    pytest.main([__file__])
