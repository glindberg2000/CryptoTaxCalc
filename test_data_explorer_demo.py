#!/usr/bin/env python3
"""Demo script for DataExplorer functionality."""

import pandas as pd
import numpy as np
from cryptotaxcalc.data_explorer import analyze_transaction_data


def main():
    """Demonstrate DataExplorer functionality."""
    print("=== CryptoTaxCalc Data Explorer Demo ===\n")

    # Create sample transaction data (similar to real data)
    data = {
        "Type": [
            "Trade",
            "Trade",
            "Deposit",
            "Withdrawal",
            "Income",
            "Trade",
            "Trade",
            "Staking",
        ],
        "BuyAmount": [1.5, 0.0, 10.0, 0.0, 0.0, 2.0, 0.5, 0.0],
        "BuyCurrency": ["BTC", "ETH", "ETH", "BTC", "USDC", "LTC", "ADA", "SOL"],
        "SellAmount": [0.0, 1.0, 0.0, 5.0, 0.0, 0.0, 0.0, 0.0],
        "SellCurrency": ["", "BTC", "", "ETH", "", "", "", ""],
        "FeeAmount": [0.001, 0.0005, 0.0, 0.01, 0.0, 0.002, 0.001, 0.0],
        "FeeCurrency": ["BTC", "BTC", "", "ETH", "", "LTC", "ADA", ""],
        "Exchange": [
            "Binance",
            "Binance",
            "Coinbase",
            "Coinbase",
            "Airdrop",
            "Kraken",
            "Binance",
            "Stake",
        ],
        "ExchangeId": ["", "", "", "", "", "", "", ""],
        "Group": ["", "", "", "", "", "", "", ""],
        "Import": ["", "", "", "", "", "", "", ""],
        "Comment": ["", "", "", "", "", "", "", ""],
        "Date": [
            "2024-01-15",
            "2024-02-20",
            "2024-03-10",
            "2024-04-05",
            "2024-05-12",
            "2024-06-18",
            "2024-07-01",
            "2024-08-15",
        ],
        "USDEquivalent": [
            45000.0,
            np.nan,
            15000.0,
            np.nan,
            np.nan,
            120.0,
            np.nan,
            50.0,
        ],
        "UpdatedAt": [
            "2024-01-15 10:30:00",
            "2024-02-20 14:45:00",
            "2024-03-10 09:15:00",
            "2024-04-05 16:20:00",
            "2024-05-12 11:00:00",
            "2024-06-18 13:30:00",
            "2024-07-01 08:30:00",
            "2024-08-15 12:00:00",
        ],
    }

    df = pd.DataFrame(data)
    df["Date"] = pd.to_datetime(df["Date"])
    df["UpdatedAt"] = pd.to_datetime(df["UpdatedAt"])

    print(f"Sample Data Overview:")
    print(f"Total Transactions: {len(df)}")
    print(f"Missing FMV: {df['USDEquivalent'].isna().sum()}")
    print(f"Available FMV: {len(df) - df['USDEquivalent'].isna().sum()}")
    print(
        f"Missing Percentage: {(df['USDEquivalent'].isna().sum() / len(df)) * 100:.1f}%\n"
    )

    # Analyze the data
    print("Analyzing missing FMV patterns...\n")
    analysis = analyze_transaction_data(
        df,
        output_report_path="demo_missing_fmv_report.txt",
        output_missing_data_path="demo_missing_fmv_data.csv",
    )

    # Display key findings
    summary = analysis["summary"]
    print(f"=== Analysis Results ===")
    print(f"Total Transactions: {summary['total_transactions']}")
    print(
        f"Missing FMV: {summary['missing_fmv_count']} ({summary['missing_fmv_percentage']:.1f}%)"
    )
    print(f"Available FMV: {summary['available_fmv_count']}")

    # Show missing FMV patterns
    missing_analysis = analysis["missing_fmv_analysis"]
    print(f"\n=== Missing FMV Patterns ===")
    print(f"Transaction Types: {list(missing_analysis['transaction_types'].keys())}")
    print(f"Top Buy Currencies: {list(missing_analysis['buy_currencies'].keys())[:3]}")
    print(f"Top Exchanges: {list(missing_analysis['exchanges'].keys())[:3]}")

    # Show recommendations
    recommendations = analysis["recommendations"]
    print(f"\n=== Phase 2 Recommendations ===")
    print(f"Priority Currencies: {recommendations['priority_currencies'][:5]}")
    print(f"Priority Exchanges: {recommendations['priority_exchanges'][:3]}")

    strategy = recommendations["fmv_fetching_strategy"]
    print(f"Strategy Priority: {strategy['priority_level']}")
    print(f"Recommended Sources: {strategy['recommended_sources'][:2]}")

    effort = recommendations["estimated_effort"]
    print(f"Estimated API Calls: {effort['estimated_api_calls']}")
    print(f"Estimated Time: {effort['estimated_time_hours']} hours")
    print(f"Estimated Cost: ${effort['estimated_cost_usd']}")
    print(f"Complexity: {effort['complexity']}")

    print(f"\n=== Generated Files ===")
    print(f"Report: demo_missing_fmv_report.txt")
    print(f"Missing Data: demo_missing_fmv_data.csv")

    print(f"\n=== Demo Complete ===")
    print(f"The Data Explorer has successfully analyzed the missing FMV patterns")
    print(f"and generated recommendations for Phase 2 FMV fetching implementation.")


if __name__ == "__main__":
    main()
