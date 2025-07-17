"""
Pytest configuration and fixtures for CryptoTaxCalc tests.
"""

import pytest
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Any


@pytest.fixture
def sample_csv_data() -> str:
    """Sample CSV transaction data for testing."""
    return """Type,Date,BuyAmount,BuyCurrency,SellAmount,SellCurrency,USDEquivalent,TxID
Buy,2024-01-15,1.5,ETH,0,USD,3000.00,tx_001
Sell,2024-02-20,0.5,ETH,1000,USD,1000.00,tx_002
Receive,2024-03-10,100,USDC,0,USD,100.00,tx_003
Swap,2024-04-05,0.1,ETH,200,USDC,200.00,tx_004"""


@pytest.fixture
def sample_holdings_data() -> Dict[str, List[Dict[str, Any]]]:
    """Sample pre-2024 holdings data for testing."""
    return {
        "ETH": [
            {"date": "2023-06-15", "qty": 2.0, "basis": 2000.0},
            {"date": "2023-12-01", "qty": 1.0, "basis": 2500.0},
        ],
        "USDC": [
            {"date": "2023-11-01", "qty": 500.0, "basis": 500.0},
        ],
    }


@pytest.fixture
def temp_db_path() -> str:
    """Create a temporary database path for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def temp_csv_file(sample_csv_data: str) -> str:
    """Create a temporary CSV file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(sample_csv_data)
        csv_path = f.name

    yield csv_path

    # Cleanup
    if os.path.exists(csv_path):
        os.unlink(csv_path)


@pytest.fixture
def temp_output_dir() -> str:
    """Create a temporary output directory for testing."""
    temp_dir = tempfile.mkdtemp()

    yield temp_dir

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_api_responses() -> Dict[str, Any]:
    """Mock API responses for FMV fetching."""
    return {
        "ETH": {
            "2024-01-15": 2000.0,
            "2024-02-20": 2000.0,
            "2024-03-10": 2100.0,
            "2024-04-05": 2200.0,
        },
        "USDC": {
            "2024-01-15": 1.0,
            "2024-02-20": 1.0,
            "2024-03-10": 1.0,
            "2024-04-05": 1.0,
        },
    }


@pytest.fixture
def sample_transaction_data() -> List[Dict[str, Any]]:
    """Sample transaction data as dictionaries."""
    return [
        {
            "type": "Buy",
            "date": "2024-01-15",
            "buy_amount": 1.5,
            "buy_currency": "ETH",
            "sell_amount": 0,
            "sell_currency": "USD",
            "usd_equivalent": 3000.0,
            "tx_id": "tx_001",
        },
        {
            "type": "Sell",
            "date": "2024-02-20",
            "buy_amount": 0,
            "buy_currency": "USD",
            "sell_amount": 0.5,
            "sell_currency": "ETH",
            "usd_equivalent": 1000.0,
            "tx_id": "tx_002",
        },
        {
            "type": "Receive",
            "date": "2024-03-10",
            "buy_amount": 100,
            "buy_currency": "USDC",
            "sell_amount": 0,
            "sell_currency": "USD",
            "usd_equivalent": 100.0,
            "tx_id": "tx_003",
        },
        {
            "type": "Swap",
            "date": "2024-04-05",
            "buy_amount": 200,
            "buy_currency": "USDC",
            "sell_amount": 0.1,
            "sell_currency": "ETH",
            "usd_equivalent": 200.0,
            "tx_id": "tx_004",
        },
    ]


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location."""
    for item in items:
        # Mark tests in test_integration.py as integration tests
        if "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        # Mark tests in test_performance.py as slow tests
        elif "test_performance" in item.nodeid:
            item.add_marker(pytest.mark.slow)
        # Default to unit tests
        else:
            item.add_marker(pytest.mark.unit)
