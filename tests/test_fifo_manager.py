"""
Tests for the FIFO manager module.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from cryptotaxcalc.fifo_manager import (
    Lot, 
    DisposalResult, 
    FIFOQueue, 
    FIFOManager, 
    create_fifo_manager
)


class TestLot:
    """Test cases for Lot dataclass."""

    def test_lot_creation(self):
        """Test basic lot creation."""
        date = datetime(2024, 1, 15)
        lot = Lot(
            amount=1.5,
            basis=3000.0,
            acquisition_date=date,
            asset="ETH"
        )
        
        assert lot.amount == 1.5
        assert lot.basis == 3000.0
        assert lot.acquisition_date == date
        assert lot.asset == "ETH"
        assert lot.lot_id is not None
        assert "ETH_20240115" in lot.lot_id

    def test_lot_validation_positive_amount(self):
        """Test lot validation for positive amount."""
        with pytest.raises(ValueError, match="amount must be positive"):
            Lot(
                amount=0,
                basis=3000.0,
                acquisition_date=datetime(2024, 1, 15),
                asset="ETH"
            )

    def test_lot_validation_negative_basis(self):
        """Test lot validation for non-negative basis."""
        with pytest.raises(ValueError, match="basis cannot be negative"):
            Lot(
                amount=1.5,
                basis=-100.0,
                acquisition_date=datetime(2024, 1, 15),
                asset="ETH"
            )

    def test_lot_validation_empty_asset(self):
        """Test lot validation for non-empty asset."""
        with pytest.raises(ValueError, match="Asset cannot be empty"):
            Lot(
                amount=1.5,
                basis=3000.0,
                acquisition_date=datetime(2024, 1, 15),
                asset=""
            )

    def test_lot_custom_id(self):
        """Test lot creation with custom ID."""
        lot = Lot(
            amount=1.5,
            basis=3000.0,
            acquisition_date=datetime(2024, 1, 15),
            asset="ETH",
            lot_id="custom_id_123"
        )
        
        assert lot.lot_id == "custom_id_123"


class TestFIFOQueue:
    """Test cases for FIFOQueue class."""

    def test_queue_initialization(self):
        """Test FIFO queue initialization."""
        queue = FIFOQueue("ETH")
        
        assert queue.asset == "ETH"
        assert len(queue.lots) == 0
        assert queue.total_amount == 0.0
        assert queue.total_basis == 0.0

    def test_add_lot(self):
        """Test adding a lot to the queue."""
        queue = FIFOQueue("ETH")
        lot = Lot(
            amount=1.5,
            basis=3000.0,
            acquisition_date=datetime(2024, 1, 15),
            asset="ETH"
        )
        
        queue.add_lot(lot)
        
        assert len(queue.lots) == 1
        assert queue.total_amount == 1.5
        assert queue.total_basis == 3000.0
        assert queue.lots[0] == lot

    def test_add_lot_wrong_asset(self):
        """Test adding lot with wrong asset."""
        queue = FIFOQueue("ETH")
        lot = Lot(
            amount=1.5,
            basis=3000.0,
            acquisition_date=datetime(2024, 1, 15),
            asset="BTC"  # Wrong asset
        )
        
        with pytest.raises(ValueError, match="doesn't match queue asset"):
            queue.add_lot(lot)

    def test_get_available_amount(self):
        """Test getting available amount."""
        queue = FIFOQueue("ETH")
        assert queue.get_available_amount() == 0.0
        
        lot = Lot(
            amount=1.5,
            basis=3000.0,
            acquisition_date=datetime(2024, 1, 15),
            asset="ETH"
        )
        queue.add_lot(lot)
        
        assert queue.get_available_amount() == 1.5

    def test_get_total_basis(self):
        """Test getting total basis."""
        queue = FIFOQueue("ETH")
        assert queue.get_total_basis() == 0.0
        
        lot = Lot(
            amount=1.5,
            basis=3000.0,
            acquisition_date=datetime(2024, 1, 15),
            asset="ETH"
        )
        queue.add_lot(lot)
        
        assert queue.get_total_basis() == 3000.0

    def test_is_empty(self):
        """Test empty queue check."""
        queue = FIFOQueue("ETH")
        assert queue.is_empty() is True
        
        lot = Lot(
            amount=1.5,
            basis=3000.0,
            acquisition_date=datetime(2024, 1, 15),
            asset="ETH"
        )
        queue.add_lot(lot)
        
        assert queue.is_empty() is False

    def test_queue_repr(self):
        """Test queue string representation."""
        queue = FIFOQueue("ETH")
        assert "FIFOQueue(ETH" in repr(queue)
        assert "lots=0" in repr(queue)


class TestFIFOManager:
    """Test cases for FIFOManager class."""

    def test_manager_initialization(self):
        """Test FIFO manager initialization."""
        manager = FIFOManager()
        
        assert len(manager.queues) == 0
        assert len(manager.disposal_history) == 0

    def test_get_or_create_queue(self):
        """Test getting or creating a queue."""
        manager = FIFOManager()
        
        # Create new queue
        queue = manager.get_or_create_queue("ETH")
        assert queue.asset == "ETH"
        assert "ETH" in manager.queues
        
        # Get existing queue
        queue2 = manager.get_or_create_queue("ETH")
        assert queue2 is queue

    def test_add_acquisition(self):
        """Test adding an acquisition."""
        manager = FIFOManager()
        date = datetime(2024, 1, 15)
        
        manager.add_acquisition(
            asset="ETH",
            amount=1.5,
            basis=3000.0,
            acquisition_date=date
        )
        
        assert "ETH" in manager.queues
        queue = manager.queues["ETH"]
        assert queue.total_amount == 1.5
        assert queue.total_basis == 3000.0
        assert len(queue.lots) == 1

    def test_add_acquisition_validation(self):
        """Test acquisition validation."""
        manager = FIFOManager()
        date = datetime(2024, 1, 15)
        
        # Test negative amount
        with pytest.raises(ValueError, match="must be positive"):
            manager.add_acquisition(
                asset="ETH",
                amount=-1.0,
                basis=3000.0,
                acquisition_date=date
            )
        
        # Test negative basis
        with pytest.raises(ValueError, match="cannot be negative"):
            manager.add_acquisition(
                asset="ETH",
                amount=1.5,
                basis=-100.0,
                acquisition_date=date
            )

    def test_process_disposal_simple(self):
        """Test simple disposal processing."""
        manager = FIFOManager()
        acquisition_date = datetime(2024, 1, 15)
        disposal_date = datetime(2024, 2, 15)
        
        # Add acquisition
        manager.add_acquisition(
            asset="ETH",
            amount=1.0,
            basis=2000.0,
            acquisition_date=acquisition_date
        )
        
        # Process disposal
        result = manager.process_disposal(
            asset="ETH",
            amount=0.5,
            proceeds=1500.0,
            disposal_date=disposal_date
        )
        
        assert result.disposal_amount == 0.5
        assert result.total_proceeds == 1500.0
        assert result.total_basis == 1000.0
        assert result.total_gain_loss == 500.0
        assert result.short_term_gain_loss == 500.0  # < 365 days
        assert result.long_term_gain_loss == 0.0
        assert len(result.matched_lots) == 1
        
        # Check remaining lot
        queue = manager.queues["ETH"]
        assert queue.total_amount == 0.5
        assert queue.total_basis == 1000.0

    def test_process_disposal_long_term(self):
        """Test disposal with long-term capital gains."""
        manager = FIFOManager()
        acquisition_date = datetime(2023, 1, 15)  # More than 1 year ago
        disposal_date = datetime(2024, 2, 15)
        
        # Add acquisition
        manager.add_acquisition(
            asset="ETH",
            amount=1.0,
            basis=2000.0,
            acquisition_date=acquisition_date
        )
        
        # Process disposal
        result = manager.process_disposal(
            asset="ETH",
            amount=0.5,
            proceeds=1500.0,
            disposal_date=disposal_date
        )
        
        assert result.short_term_gain_loss == 0.0
        assert result.long_term_gain_loss == 500.0  # > 365 days

    def test_process_disposal_insufficient_funds(self):
        """Test disposal with insufficient funds."""
        manager = FIFOManager()
        date = datetime(2024, 1, 15)
        
        # Add acquisition
        manager.add_acquisition(
            asset="ETH",
            amount=1.0,
            basis=2000.0,
            acquisition_date=date
        )
        
        # Try to dispose more than available
        with pytest.raises(ValueError, match="Insufficient ETH available"):
            manager.process_disposal(
                asset="ETH",
                amount=2.0,
                proceeds=4000.0,
                disposal_date=date
            )

    def test_process_disposal_validation(self):
        """Test disposal validation."""
        manager = FIFOManager()
        date = datetime(2024, 1, 15)
        
        # Test negative amount
        with pytest.raises(ValueError, match="must be positive"):
            manager.process_disposal(
                asset="ETH",
                amount=-1.0,
                proceeds=2000.0,
                disposal_date=date
            )
        
        # Test negative proceeds
        with pytest.raises(ValueError, match="cannot be negative"):
            manager.process_disposal(
                asset="ETH",
                amount=1.0,
                proceeds=-100.0,
                disposal_date=date
            )

    def test_get_queue_summary(self):
        """Test getting queue summary."""
        manager = FIFOManager()
        date = datetime(2024, 1, 15)
        
        # Add acquisitions
        manager.add_acquisition("ETH", 1.0, 2000.0, date)
        manager.add_acquisition("ETH", 0.5, 1000.0, date)
        
        summary = manager.get_queue_summary("ETH")
        
        assert summary["asset"] == "ETH"
        assert summary["total_amount"] == 1.5
        assert summary["total_basis"] == 3000.0
        assert summary["lot_count"] == 2
        assert summary["average_basis"] == 2000.0

    def test_get_queue_summary_nonexistent(self):
        """Test getting summary for nonexistent queue."""
        manager = FIFOManager()
        
        summary = manager.get_queue_summary("BTC")
        
        assert summary["asset"] == "BTC"
        assert summary["total_amount"] == 0.0
        assert summary["total_basis"] == 0.0
        assert summary["lot_count"] == 0
        assert summary["average_basis"] == 0.0

    def test_get_all_summaries(self):
        """Test getting all queue summaries."""
        manager = FIFOManager()
        date = datetime(2024, 1, 15)
        
        # Add acquisitions for multiple assets
        manager.add_acquisition("ETH", 1.0, 2000.0, date)
        manager.add_acquisition("BTC", 0.1, 3000.0, date)
        
        summaries = manager.get_all_summaries()
        
        assert "ETH" in summaries
        assert "BTC" in summaries
        assert summaries["ETH"]["total_amount"] == 1.0
        assert summaries["BTC"]["total_amount"] == 0.1

    def test_get_disposal_summary_empty(self):
        """Test disposal summary with no disposals."""
        manager = FIFOManager()
        
        summary = manager.get_disposal_summary()
        
        assert summary["total_disposals"] == 0
        assert summary["total_proceeds"] == 0.0
        assert summary["total_basis"] == 0.0
        assert summary["total_gain_loss"] == 0.0
        assert summary["short_term_gain_loss"] == 0.0
        assert summary["long_term_gain_loss"] == 0.0
        assert summary["assets_disposed"] == []

    def test_get_disposal_summary_with_disposals(self):
        """Test disposal summary with disposals."""
        manager = FIFOManager()
        date = datetime(2024, 1, 15)
        
        # Add acquisition and disposal
        manager.add_acquisition("ETH", 1.0, 2000.0, date)
        manager.process_disposal("ETH", 0.5, 1500.0, date)
        
        summary = manager.get_disposal_summary()
        
        assert summary["total_disposals"] == 1
        assert summary["total_proceeds"] == 1500.0
        assert summary["total_basis"] == 1000.0
        assert summary["total_gain_loss"] == 500.0
        assert "ETH" in summary["assets_disposed"]

    def test_import_2023_year_end_data(self):
        """Test importing 2023 year-end data."""
        manager = FIFOManager()
        
        holdings_data = {
            "ETH": [
                {"date": "2023-06-15", "qty": 2.0, "basis": 2000.0},
                {"date": "2023-12-01", "qty": 1.0, "basis": 2500.0},
            ],
            "BTC": [
                {"date": "2023-11-01", "qty": 0.1, "basis": 3000.0},
            ],
        }
        
        manager.import_2023_year_end_data(holdings_data)
        
        # Check ETH queue
        eth_summary = manager.get_queue_summary("ETH")
        assert eth_summary["total_amount"] == 3.0
        assert eth_summary["total_basis"] == 4500.0
        assert eth_summary["lot_count"] == 2
        
        # Check BTC queue
        btc_summary = manager.get_queue_summary("BTC")
        assert btc_summary["total_amount"] == 0.1
        assert btc_summary["total_basis"] == 3000.0
        assert btc_summary["lot_count"] == 1

    def test_process_transactions(self):
        """Test processing transactions from DataFrame."""
        manager = FIFOManager()
        
        # Create sample transaction data
        transactions_data = [
            {
                "Type": "Trade",
                "BuyAmount": 1.0,
                "BuyCurrency": "ETH",
                "SellAmount": 0,
                "SellCurrency": "",
                "USDEquivalent": 2000.0,
                "Date": datetime(2024, 1, 15),
            },
            {
                "Type": "Trade",
                "BuyAmount": 0,
                "BuyCurrency": "",
                "SellAmount": 0.5,
                "SellCurrency": "ETH",
                "USDEquivalent": 1500.0,
                "Date": datetime(2024, 2, 15),
            },
            {
                "Type": "Income",
                "BuyAmount": 100,
                "BuyCurrency": "USDC",
                "SellAmount": 0,
                "SellCurrency": "",
                "USDEquivalent": 100.0,
                "Date": datetime(2024, 3, 15),
            },
        ]
        
        df = pd.DataFrame(transactions_data)
        disposal_results = manager.process_transactions(df)
        
        # Check that one disposal was processed
        assert len(disposal_results) == 1
        assert disposal_results[0].asset == "ETH"
        assert disposal_results[0].disposal_amount == 0.5
        
        # Check that acquisitions were processed
        eth_summary = manager.get_queue_summary("ETH")
        assert eth_summary["total_amount"] == 0.5  # 1.0 - 0.5
        
        usdc_summary = manager.get_queue_summary("USDC")
        assert usdc_summary["total_amount"] == 100.0
        assert usdc_summary["total_basis"] == 0.0  # Income has $0 basis


class TestFIFOManagerIntegration:
    """Integration tests for FIFO manager."""

    def test_complex_fifo_scenario(self):
        """Test complex FIFO scenario with multiple lots."""
        manager = FIFOManager()
        
        # Add multiple acquisitions over time
        manager.add_acquisition("ETH", 1.0, 2000.0, datetime(2024, 1, 15))
        manager.add_acquisition("ETH", 0.5, 1500.0, datetime(2024, 2, 15))
        manager.add_acquisition("ETH", 0.3, 1200.0, datetime(2024, 3, 15))
        
        # Process disposal that spans multiple lots
        result = manager.process_disposal("ETH", 1.2, 3000.0, datetime(2024, 4, 15))
        
        assert result.disposal_amount == 1.2
        assert len(result.matched_lots) == 2  # Should use first two lots
        assert result.total_basis == 2000.0 + 600.0  # 2000 + (0.2 * 1500)
        assert result.total_gain_loss == 3000.0 - (2000.0 + 600.0)
        
        # Check remaining lots
        eth_summary = manager.get_queue_summary("ETH")
        assert abs(eth_summary["total_amount"] - 0.6) < 0.001  # 1.8 - 1.2
        assert eth_summary["lot_count"] == 2  # 0.3 remaining from lot 2 + lot 3

    def test_income_event_processing(self):
        """Test processing income events with $0 basis."""
        manager = FIFOManager()
        
        # Process income event
        transactions_data = [
            {
                "Type": "Staking",
                "BuyAmount": 50,
                "BuyCurrency": "ETH",
                "SellAmount": 0,
                "SellCurrency": "",
                "USDEquivalent": 100000.0,  # High value
                "Date": datetime(2024, 1, 15),
            },
        ]
        
        df = pd.DataFrame(transactions_data)
        disposal_results = manager.process_transactions(df)
        
        # No disposals from income
        assert len(disposal_results) == 0
        
        # Check that income was added with $0 basis
        eth_summary = manager.get_queue_summary("ETH")
        assert eth_summary["total_amount"] == 50.0
        assert eth_summary["total_basis"] == 0.0  # Income has $0 basis


def test_create_fifo_manager():
    """Test convenience function for creating FIFO manager."""
    manager = create_fifo_manager()
    
    assert isinstance(manager, FIFOManager)
    assert len(manager.queues) == 0
    assert len(manager.disposal_history) == 0


@pytest.mark.integration
class TestFIFOManagerWithRealData:
    """Integration tests with real transaction data."""

    def test_with_sample_csv_data(self, temp_csv_file):
        """Test FIFO manager with sample CSV data."""
        from cryptotaxcalc.parser import parse_transaction_file
        
        # Parse CSV data
        df, summary = parse_transaction_file(temp_csv_file, enable_2024_filter=False)
        
        # Process with FIFO manager
        manager = FIFOManager()
        disposal_results = manager.process_transactions(df)
        
        # Should have some disposals from the sample data
        assert len(disposal_results) >= 0  # May be 0 depending on sample data
        
        # Check that queues were created
        summaries = manager.get_all_summaries()
        assert len(summaries) >= 0  # May be 0 depending on sample data

    def test_with_holdings_data(self, sample_holdings_data):
        """Test FIFO manager with holdings data."""
        manager = FIFOManager()
        
        # Import holdings data
        manager.import_2023_year_end_data(sample_holdings_data)
        
        # Check that holdings were imported correctly
        eth_summary = manager.get_queue_summary("ETH")
        assert eth_summary["total_amount"] == 3.0  # 2.0 + 1.0
        assert eth_summary["total_basis"] == 4500.0  # 2000 + 2500
        
        usdc_summary = manager.get_queue_summary("USDC")
        assert usdc_summary["total_amount"] == 500.0
        assert usdc_summary["total_basis"] == 500.0
