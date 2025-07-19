"""
Tests for the Data Explorer module.

Tests the missing FMV analysis functionality for Phase 2 planning.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, date
from pathlib import Path
import tempfile
import os

from cryptotaxcalc.data_explorer import DataExplorer, analyze_transaction_data


class TestDataExplorer:
    """Test cases for DataExplorer class."""

    @pytest.fixture
    def sample_data(self):
        """Create sample transaction data for testing."""
        data = {
            "Type": ["Trade", "Trade", "Deposit", "Withdrawal", "Income", "Trade"],
            "BuyAmount": [1.5, 0.0, 10.0, 0.0, 0.0, 2.0],
            "BuyCurrency": ["BTC", "ETH", "ETH", "BTC", "USDC", "LTC"],
            "SellAmount": [0.0, 1.0, 0.0, 5.0, 0.0, 0.0],
            "SellCurrency": ["", "BTC", "", "ETH", "", ""],
            "FeeAmount": [0.001, 0.0005, 0.0, 0.01, 0.0, 0.002],
            "FeeCurrency": ["BTC", "BTC", "", "ETH", "", "LTC"],
            "Exchange": [
                "Binance",
                "Binance",
                "Coinbase",
                "Coinbase",
                "Airdrop",
                "Kraken",
            ],
            "ExchangeId": ["", "", "", "", "", ""],
            "Group": ["", "", "", "", "", ""],
            "Import": ["", "", "", "", "", ""],
            "Comment": ["", "", "", "", "", ""],
            "Date": [
                "2024-01-15",
                "2024-02-20",
                "2024-03-10",
                "2024-04-05",
                "2024-05-12",
                "2024-06-18",
            ],
            "USDEquivalent": [45000.0, np.nan, 15000.0, np.nan, np.nan, 120.0],
            "UpdatedAt": [
                "2024-01-15 10:30:00",
                "2024-02-20 14:45:00",
                "2024-03-10 09:15:00",
                "2024-04-05 16:20:00",
                "2024-05-12 11:00:00",
                "2024-06-18 13:30:00",
            ],
        }
        df = pd.DataFrame(data)
        df["Date"] = pd.to_datetime(df["Date"])
        df["UpdatedAt"] = pd.to_datetime(df["UpdatedAt"])
        return df

    @pytest.fixture
    def explorer(self):
        """Create a DataExplorer instance for testing."""
        return DataExplorer()

    def test_initialization(self, explorer):
        """Test DataExplorer initialization."""
        assert explorer.analysis_results == {}
        assert explorer.missing_fmv_data is None
        assert explorer.available_fmv_data is None

    def test_analyze_missing_fmv_basic(self, explorer, sample_data):
        """Test basic missing FMV analysis."""
        analysis = explorer.analyze_missing_fmv(sample_data)

        # Check summary
        assert analysis["summary"]["total_transactions"] == 6
        assert analysis["summary"]["missing_fmv_count"] == 3
        assert analysis["summary"]["available_fmv_count"] == 3
        assert analysis["summary"]["missing_fmv_percentage"] == 50.0

        # Check that data was split correctly
        assert len(explorer.missing_fmv_data) == 3
        assert len(explorer.available_fmv_data) == 3

    def test_analyze_missing_fmv_empty_data(self, explorer):
        """Test analysis with empty DataFrame."""
        empty_df = pd.DataFrame()
        analysis = explorer.analyze_missing_fmv(empty_df)

        assert analysis["summary"]["total_transactions"] == 0
        assert analysis["summary"]["missing_fmv_count"] == 0
        assert analysis["summary"]["available_fmv_count"] == 0
        assert analysis["summary"]["missing_fmv_percentage"] == 0.0

    def test_analyze_missing_fmv_all_missing(self, explorer):
        """Test analysis when all FMV data is missing."""
        data = {
            "Type": ["Trade", "Deposit"],
            "BuyAmount": [1.0, 10.0],
            "BuyCurrency": ["BTC", "ETH"],
            "SellAmount": [0.0, 0.0],
            "SellCurrency": ["", ""],
            "FeeAmount": [0.001, 0.0],
            "FeeCurrency": ["BTC", ""],
            "Exchange": ["Binance", "Coinbase"],
            "ExchangeId": ["", ""],
            "Group": ["", ""],
            "Import": ["", ""],
            "Comment": ["", ""],
            "Date": ["2024-01-15", "2024-02-20"],
            "USDEquivalent": [np.nan, np.nan],
            "UpdatedAt": ["2024-01-15 10:30:00", "2024-02-20 14:45:00"],
        }
        df = pd.DataFrame(data)
        df["Date"] = pd.to_datetime(df["Date"])
        df["UpdatedAt"] = pd.to_datetime(df["UpdatedAt"])

        analysis = explorer.analyze_missing_fmv(df)

        assert analysis["summary"]["missing_fmv_percentage"] == 100.0
        assert len(explorer.missing_fmv_data) == 2
        assert len(explorer.available_fmv_data) == 0

    def test_analyze_missing_fmv_all_available(self, explorer):
        """Test analysis when all FMV data is available."""
        data = {
            "Type": ["Trade", "Deposit"],
            "BuyAmount": [1.0, 10.0],
            "BuyCurrency": ["BTC", "ETH"],
            "SellAmount": [0.0, 0.0],
            "SellCurrency": ["", ""],
            "FeeAmount": [0.001, 0.0],
            "FeeCurrency": ["BTC", ""],
            "Exchange": ["Binance", "Coinbase"],
            "ExchangeId": ["", ""],
            "Group": ["", ""],
            "Import": ["", ""],
            "Comment": ["", ""],
            "Date": ["2024-01-15", "2024-02-20"],
            "USDEquivalent": [45000.0, 15000.0],
            "UpdatedAt": ["2024-01-15 10:30:00", "2024-02-20 14:45:00"],
        }
        df = pd.DataFrame(data)
        df["Date"] = pd.to_datetime(df["Date"])
        df["UpdatedAt"] = pd.to_datetime(df["UpdatedAt"])

        analysis = explorer.analyze_missing_fmv(df)

        assert analysis["summary"]["missing_fmv_percentage"] == 0.0
        assert len(explorer.missing_fmv_data) == 0
        assert len(explorer.available_fmv_data) == 2

    def test_missing_patterns_analysis(self, explorer, sample_data):
        """Test missing patterns analysis."""
        explorer.analyze_missing_fmv(sample_data)
        missing_analysis = explorer.analysis_results["missing_fmv_analysis"]

        # Check transaction types
        assert "Trade" in missing_analysis["transaction_types"]
        assert "Withdrawal" in missing_analysis["transaction_types"]
        assert "Income" in missing_analysis["transaction_types"]

        # Check currencies
        assert "BTC" in missing_analysis["buy_currencies"]
        assert "ETH" in missing_analysis["sell_currencies"]

        # Check exchanges
        assert "Binance" in missing_analysis["exchanges"]
        assert "Coinbase" in missing_analysis["exchanges"]

    def test_available_patterns_analysis(self, explorer, sample_data):
        """Test available patterns analysis."""
        explorer.analyze_missing_fmv(sample_data)
        available_analysis = explorer.analysis_results["available_fmv_analysis"]

        # Check transaction types
        assert "Trade" in available_analysis["transaction_types"]
        assert "Deposit" in available_analysis["transaction_types"]

        # Check USD value stats
        usd_stats = available_analysis["usd_value_stats"]
        assert usd_stats["total_value"] == 60120.0  # 45000 + 15000 + 120
        assert usd_stats["mean_value"] == 20040.0  # 60120 / 3

    def test_date_patterns_analysis(self, explorer, sample_data):
        """Test date patterns analysis."""
        explorer.analyze_missing_fmv(sample_data)
        missing_analysis = explorer.analysis_results["missing_fmv_analysis"]
        date_patterns = missing_analysis["date_patterns"]

        # Check date range
        assert date_patterns["date_range"]["start"] == "2024-02-20"
        assert date_patterns["date_range"]["end"] == "2024-05-12"

        # Check day of week distribution
        assert "Tuesday" in date_patterns["day_of_week_distribution"]
        assert "Friday" in date_patterns["day_of_week_distribution"]
        assert "Sunday" in date_patterns["day_of_week_distribution"]

    def test_value_patterns_analysis(self, explorer, sample_data):
        """Test value patterns analysis."""
        explorer.analyze_missing_fmv(sample_data)
        missing_analysis = explorer.analysis_results["missing_fmv_analysis"]
        value_patterns = missing_analysis["value_patterns"]

        # Check buy amount stats
        buy_stats = value_patterns["buy_amount_stats"]
        assert buy_stats["total_buy_amount"] == 0.0  # Only 0 values in missing data
        assert buy_stats["zero_buy_amount_count"] == 3

        # Check sell amount stats
        sell_stats = value_patterns["sell_amount_stats"]
        assert sell_stats["total_sell_amount"] == 6.0  # 1.0 + 5.0
        assert sell_stats["zero_sell_amount_count"] == 1

    def test_recommendations_generation(self, explorer, sample_data):
        """Test recommendations generation."""
        explorer.analyze_missing_fmv(sample_data)
        recommendations = explorer.analysis_results["recommendations"]

        # Check priority currencies
        assert "BTC" in recommendations["priority_currencies"]
        assert "ETH" in recommendations["priority_currencies"]

        # Check priority exchanges
        assert "Binance" in recommendations["priority_exchanges"]
        assert "Coinbase" in recommendations["priority_exchanges"]

        # Check FMV strategy
        strategy = recommendations["fmv_fetching_strategy"]
        assert strategy["priority_level"] == "HIGH"  # 50% missing
        assert "CoinGecko API (primary)" in strategy["recommended_sources"]

        # Check effort estimation
        effort = recommendations["estimated_effort"]
        assert effort["estimated_api_calls"] == 3  # 3 * 1.2 = 3.6, int(3.6) = 3
        assert effort["complexity"] == "MEDIUM"

    def test_report_generation(self, explorer, sample_data):
        """Test report generation."""
        explorer.analyze_missing_fmv(sample_data)
        report = explorer.generate_report()

        # Check report content
        assert "CRYPTOTAXCALC - MISSING FMV DATA ANALYSIS REPORT" in report
        assert "Total Transactions: 6" in report
        assert "Missing FMV: 3 (50.0%)" in report
        assert "RECOMMENDATIONS FOR PHASE 2" in report

    def test_report_save_to_file(self, explorer, sample_data):
        """Test saving report to file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            report_path = f.name

        try:
            explorer.analyze_missing_fmv(sample_data)
            explorer.generate_report(report_path)

            # Check file was created and has content
            assert os.path.exists(report_path)
            with open(report_path, "r") as f:
                content = f.read()
                assert "CRYPTOTAXCALC - MISSING FMV DATA ANALYSIS REPORT" in content
        finally:
            if os.path.exists(report_path):
                os.unlink(report_path)

    def test_save_missing_data(self, explorer, sample_data):
        """Test saving missing FMV data to CSV."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            explorer.analyze_missing_fmv(sample_data)
            explorer.save_missing_data(csv_path)

            # Check file was created
            assert os.path.exists(csv_path)

            # Check CSV content
            saved_df = pd.read_csv(csv_path)
            assert len(saved_df) == 3  # 3 missing FMV transactions
            assert saved_df["USDEquivalent"].isna().all()
        finally:
            if os.path.exists(csv_path):
                os.unlink(csv_path)

    def test_save_missing_data_empty(self, explorer):
        """Test saving missing data when none exists."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            # Create data with no missing FMV
            data = {
                "Type": ["Trade"],
                "BuyAmount": [1.0],
                "BuyCurrency": ["BTC"],
                "SellAmount": [0.0],
                "SellCurrency": [""],
                "FeeAmount": [0.001],
                "FeeCurrency": ["BTC"],
                "Exchange": ["Binance"],
                "ExchangeId": [""],
                "Group": [""],
                "Import": [""],
                "Comment": [""],
                "Date": ["2024-01-15"],
                "USDEquivalent": [45000.0],
                "UpdatedAt": ["2024-01-15 10:30:00"],
            }
            df = pd.DataFrame(data)
            df["Date"] = pd.to_datetime(df["Date"])
            df["UpdatedAt"] = pd.to_datetime(df["UpdatedAt"])

            explorer.analyze_missing_fmv(df)
            explorer.save_missing_data(csv_path)

            # File should not be created or should be empty
            if os.path.exists(csv_path):
                saved_df = pd.read_csv(csv_path)
                assert len(saved_df) == 0
        finally:
            if os.path.exists(csv_path):
                os.unlink(csv_path)


class TestAnalyzeTransactionData:
    """Test cases for the convenience function."""

    @pytest.fixture
    def sample_data(self):
        """Create sample transaction data for testing."""
        data = {
            "Type": ["Trade", "Trade", "Deposit"],
            "BuyAmount": [1.5, 0.0, 10.0],
            "BuyCurrency": ["BTC", "", "ETH"],
            "SellAmount": [0.0, 1.0, 0.0],
            "SellCurrency": ["", "BTC", ""],
            "FeeAmount": [0.001, 0.0005, 0.0],
            "FeeCurrency": ["BTC", "BTC", ""],
            "Exchange": ["Binance", "Binance", "Coinbase"],
            "ExchangeId": ["", "", ""],
            "Group": ["", "", ""],
            "Import": ["", "", ""],
            "Comment": ["", "", ""],
            "Date": ["2024-01-15", "2024-02-20", "2024-03-10"],
            "USDEquivalent": [45000.0, np.nan, 15000.0],
            "UpdatedAt": [
                "2024-01-15 10:30:00",
                "2024-02-20 14:45:00",
                "2024-03-10 09:15:00",
            ],
        }
        df = pd.DataFrame(data)
        df["Date"] = pd.to_datetime(df["Date"])
        df["UpdatedAt"] = pd.to_datetime(df["UpdatedAt"])
        return df

    def test_analyze_transaction_data_basic(self, sample_data):
        """Test basic functionality of analyze_transaction_data."""
        analysis = analyze_transaction_data(sample_data)

        assert analysis["summary"]["total_transactions"] == 3
        assert analysis["summary"]["missing_fmv_count"] == 1
        assert analysis["summary"]["missing_fmv_percentage"] == pytest.approx(
            33.33, abs=0.01
        )

    def test_analyze_transaction_data_with_output_files(self, sample_data):
        """Test analyze_transaction_data with output files."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            report_path = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            analysis = analyze_transaction_data(
                sample_data,
                output_report_path=report_path,
                output_missing_data_path=csv_path,
            )

            # Check analysis results
            assert analysis["summary"]["total_transactions"] == 3

            # Check report file
            assert os.path.exists(report_path)
            with open(report_path, "r") as f:
                content = f.read()
                assert "CRYPTOTAXCALC - MISSING FMV DATA ANALYSIS REPORT" in content

            # Check CSV file
            assert os.path.exists(csv_path)
            saved_df = pd.read_csv(csv_path)
            assert len(saved_df) == 1  # 1 missing FMV transaction
        finally:
            if os.path.exists(report_path):
                os.unlink(report_path)
            if os.path.exists(csv_path):
                os.unlink(csv_path)

    def test_analyze_transaction_data_no_output_files(self, sample_data):
        """Test analyze_transaction_data without output files."""
        analysis = analyze_transaction_data(sample_data)

        assert analysis["summary"]["total_transactions"] == 3
        assert analysis["summary"]["missing_fmv_count"] == 1


if __name__ == "__main__":
    pytest.main([__file__])
