"""
Data Explorer Tool for CryptoTaxCalc.

Analyzes missing FMV data patterns from Phase 1A parser output
to support Phase 2 FMV fetching strategy.
"""

import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
import logging
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataExplorer:
    """
    Data exploration tool for analyzing missing FMV data patterns.

    Focuses on analyzing the ~46% missing FMV rate from Phase 1A
    to support Phase 2 FMV fetching strategy.
    """

    def __init__(self):
        """Initialize the data explorer."""
        self.analysis_results: Dict[str, Any] = {}
        self.missing_fmv_data: pd.DataFrame = None
        self.available_fmv_data: pd.DataFrame = None

    def analyze_missing_fmv(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze missing FMV data patterns.

        Args:
            df: DataFrame from Phase 1A parser output

        Returns:
            Dictionary with comprehensive missing FMV analysis
        """
        logger.info(f"Starting missing FMV analysis for {len(df)} transactions")

        # Handle empty DataFrame
        if df.empty:
            return {
                "summary": {
                    "total_transactions": 0,
                    "missing_fmv_count": 0,
                    "available_fmv_count": 0,
                    "missing_fmv_percentage": 0.0,
                    "analysis_timestamp": datetime.now().isoformat(),
                },
                "missing_fmv_analysis": {"error": "No data to analyze"},
                "available_fmv_analysis": {"error": "No data to analyze"},
                "recommendations": {"error": "No data to analyze"},
            }

        # Check if USDEquivalent column exists
        if "USDEquivalent" not in df.columns:
            logger.error("USDEquivalent column not found in DataFrame")
            return {
                "summary": {
                    "total_transactions": len(df),
                    "missing_fmv_count": len(df),
                    "available_fmv_count": 0,
                    "missing_fmv_percentage": 100.0,
                    "analysis_timestamp": datetime.now().isoformat(),
                },
                "missing_fmv_analysis": {"error": "USDEquivalent column not found"},
                "available_fmv_analysis": {"error": "USDEquivalent column not found"},
                "recommendations": {"error": "USDEquivalent column not found"},
            }

        # Split data into missing and available FMV
        missing_mask = df["USDEquivalent"].isna()
        self.missing_fmv_data = df[missing_mask].copy()
        self.available_fmv_data = df[~missing_mask].copy()

        # Calculate basic statistics
        total_transactions = len(df)
        missing_count = len(self.missing_fmv_data)
        available_count = len(self.available_fmv_data)
        missing_percentage = (missing_count / total_transactions) * 100

        logger.info(
            f"Missing FMV: {missing_count}/{total_transactions} ({missing_percentage:.1f}%)"
        )

        # Perform detailed analysis
        missing_analysis = self._analyze_missing_patterns()
        available_analysis = self._analyze_available_patterns()

        analysis = {
            "summary": {
                "total_transactions": total_transactions,
                "missing_fmv_count": missing_count,
                "available_fmv_count": available_count,
                "missing_fmv_percentage": missing_percentage,
                "analysis_timestamp": datetime.now().isoformat(),
            },
            "missing_fmv_analysis": missing_analysis,
            "available_fmv_analysis": available_analysis,
            "recommendations": self._generate_recommendations_with_data(
                missing_analysis, total_transactions, missing_count
            ),
        }

        self.analysis_results = analysis
        return analysis

    def _analyze_missing_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in missing FMV data."""
        if self.missing_fmv_data.empty:
            return {"error": "No missing FMV data to analyze"}

        df = self.missing_fmv_data

        # Analyze by transaction type
        type_analysis = df["Type"].value_counts().to_dict()

        # Analyze by currency
        buy_currency_analysis = df["BuyCurrency"].value_counts().head(10).to_dict()
        sell_currency_analysis = df["SellCurrency"].value_counts().head(10).to_dict()

        # Analyze by exchange
        exchange_analysis = df["Exchange"].value_counts().head(10).to_dict()

        # Analyze by date patterns
        date_analysis = self._analyze_date_patterns(df)

        # Analyze by transaction value patterns
        value_analysis = self._analyze_value_patterns(df)

        return {
            "transaction_types": type_analysis,
            "buy_currencies": buy_currency_analysis,
            "sell_currencies": sell_currency_analysis,
            "exchanges": exchange_analysis,
            "date_patterns": date_analysis,
            "value_patterns": value_analysis,
        }

    def _analyze_available_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in available FMV data for comparison."""
        if self.available_fmv_data.empty:
            return {"error": "No available FMV data to analyze"}

        df = self.available_fmv_data

        # Analyze by transaction type
        type_analysis = df["Type"].value_counts().to_dict()

        # Analyze by currency
        buy_currency_analysis = df["BuyCurrency"].value_counts().head(10).to_dict()
        sell_currency_analysis = df["SellCurrency"].value_counts().head(10).to_dict()

        # Analyze by exchange
        exchange_analysis = df["Exchange"].value_counts().head(10).to_dict()

        # Analyze USD equivalent values
        usd_stats = {
            "total_value": df["USDEquivalent"].sum(),
            "mean_value": df["USDEquivalent"].mean(),
            "median_value": df["USDEquivalent"].median(),
            "min_value": df["USDEquivalent"].min(),
            "max_value": df["USDEquivalent"].max(),
            "std_value": df["USDEquivalent"].std(),
        }

        return {
            "transaction_types": type_analysis,
            "buy_currencies": buy_currency_analysis,
            "sell_currencies": sell_currency_analysis,
            "exchanges": exchange_analysis,
            "usd_value_stats": usd_stats,
        }

    def _analyze_date_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze date patterns in missing FMV data."""
        if df.empty or df["Date"].isna().all():
            return {"error": "No valid dates to analyze"}

        # Remove rows with missing dates
        df_with_dates = df.dropna(subset=["Date"])

        if df_with_dates.empty:
            return {"error": "No valid dates after filtering"}

        # Analyze by month
        df_with_dates["Month"] = df_with_dates["Date"].dt.to_period("M")
        monthly_counts = df_with_dates["Month"].value_counts().sort_index()

        # Analyze by day of week
        df_with_dates["DayOfWeek"] = df_with_dates["Date"].dt.day_name()
        day_of_week_counts = df_with_dates["DayOfWeek"].value_counts()

        # Analyze by hour (if available)
        hour_analysis = {}
        if (
            "UpdatedAt" in df_with_dates.columns
            and not df_with_dates["UpdatedAt"].isna().all()
        ):
            df_with_dates["Hour"] = df_with_dates["UpdatedAt"].dt.hour
            hour_analysis = df_with_dates["Hour"].value_counts().sort_index().to_dict()

        return {
            "monthly_distribution": monthly_counts.to_dict(),
            "day_of_week_distribution": day_of_week_counts.to_dict(),
            "hour_distribution": hour_analysis,
            "date_range": {
                "start": df_with_dates["Date"].min().strftime("%Y-%m-%d"),
                "end": df_with_dates["Date"].max().strftime("%Y-%m-%d"),
            },
        }

    def _analyze_value_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze value patterns in missing FMV data."""
        # Analyze BuyAmount patterns
        buy_amount_stats = {}
        if "BuyAmount" in df.columns and not df["BuyAmount"].isna().all():
            buy_amount_stats = {
                "total_buy_amount": df["BuyAmount"].sum(),
                "mean_buy_amount": df["BuyAmount"].mean(),
                "median_buy_amount": df["BuyAmount"].median(),
                "min_buy_amount": df["BuyAmount"].min(),
                "max_buy_amount": df["BuyAmount"].max(),
                "zero_buy_amount_count": (df["BuyAmount"] == 0).sum(),
            }

        # Analyze SellAmount patterns
        sell_amount_stats = {}
        if "SellAmount" in df.columns and not df["SellAmount"].isna().all():
            sell_amount_stats = {
                "total_sell_amount": df["SellAmount"].sum(),
                "mean_sell_amount": df["SellAmount"].mean(),
                "median_sell_amount": df["SellAmount"].median(),
                "min_sell_amount": df["SellAmount"].min(),
                "max_sell_amount": df["SellAmount"].max(),
                "zero_sell_amount_count": (df["SellAmount"] == 0).sum(),
            }

        # Analyze FeeAmount patterns
        fee_amount_stats = {}
        if "FeeAmount" in df.columns and not df["FeeAmount"].isna().all():
            fee_amount_stats = {
                "total_fee_amount": df["FeeAmount"].sum(),
                "mean_fee_amount": df["FeeAmount"].mean(),
                "median_fee_amount": df["FeeAmount"].median(),
                "min_fee_amount": df["FeeAmount"].min(),
                "max_fee_amount": df["FeeAmount"].max(),
                "zero_fee_amount_count": (df["FeeAmount"] == 0).sum(),
            }

        return {
            "buy_amount_stats": buy_amount_stats,
            "sell_amount_stats": sell_amount_stats,
            "fee_amount_stats": fee_amount_stats,
        }

    def _generate_recommendations(self) -> Dict[str, Any]:
        """Generate recommendations for Phase 2 FMV fetching strategy."""
        if not self.analysis_results:
            return {"error": "No analysis results available"}

        summary = self.analysis_results["summary"]
        missing_analysis = self.analysis_results["missing_fmv_analysis"]

        # Check if missing analysis has an error
        if "error" in missing_analysis:
            return {"error": f"Missing FMV analysis error: {missing_analysis['error']}"}

        # Check if we have valid missing FMV data
        if self.missing_fmv_data is None or self.missing_fmv_data.empty:
            return {"error": "No missing FMV data to analyze"}

        recommendations = {
            "priority_currencies": self._identify_priority_currencies(),
            "priority_exchanges": self._identify_priority_exchanges(),
            "priority_transaction_types": self._identify_priority_transaction_types(),
            "fmv_fetching_strategy": self._generate_fmv_strategy(),
            "estimated_effort": self._estimate_effort(),
        }

        return recommendations

    def _generate_recommendations_with_data(
        self,
        missing_analysis: Dict[str, Any],
        total_transactions: int,
        missing_count: int,
    ) -> Dict[str, Any]:
        """Generate recommendations for Phase 2 FMV fetching strategy."""
        if not missing_analysis:
            return {"error": "No missing FMV data to analyze"}

        # Check if missing analysis has an error
        if "error" in missing_analysis:
            return {"error": f"Missing FMV analysis error: {missing_analysis['error']}"}

        # Check if we have valid missing FMV data
        if self.missing_fmv_data is None or self.missing_fmv_data.empty:
            return {"error": "No missing FMV data to analyze"}

        missing_percentage = (missing_count / total_transactions) * 100

        recommendations = {
            "priority_currencies": self._identify_priority_currencies_with_data(
                missing_analysis
            ),
            "priority_exchanges": self._identify_priority_exchanges_with_data(
                missing_analysis
            ),
            "priority_transaction_types": self._identify_priority_transaction_types_with_data(
                missing_analysis
            ),
            "fmv_fetching_strategy": self._generate_fmv_strategy_with_data(
                missing_percentage
            ),
            "estimated_effort": self._estimate_effort_with_data(missing_count),
        }

        return recommendations

    def _generate_fmv_strategy_with_data(
        self, missing_percentage: float
    ) -> Dict[str, Any]:
        """Generate FMV fetching strategy recommendations."""
        strategy = {
            "overall_approach": "Multi-source FMV fetching with caching",
            "priority_level": "HIGH" if missing_percentage > 30 else "MEDIUM",
            "recommended_sources": [
                "CoinGecko API (primary)",
                "CoinMarketCap API (secondary)",
                "Etherscan API (for Ethereum tokens)",
                "Local cache database",
            ],
            "caching_strategy": "SQLite database with daily updates",
            "rate_limiting": "Implement exponential backoff for API calls",
            "fallback_strategy": "Use nearest available date FMV",
        }

        return strategy

    def _estimate_effort_with_data(self, missing_count: int) -> Dict[str, Any]:
        """Estimate effort required for Phase 2 FMV implementation."""
        # Rough estimates based on missing transaction count
        api_calls_needed = missing_count * 1.2  # 20% buffer for retries
        estimated_time_hours = max(
            1, missing_count / 1000
        )  # 1000 transactions per hour
        estimated_cost_usd = max(
            0, (api_calls_needed - 10000) * 0.0001
        )  # Free tier + paid

        return {
            "estimated_api_calls": int(api_calls_needed),
            "estimated_time_hours": round(estimated_time_hours, 1),
            "estimated_cost_usd": round(estimated_cost_usd, 2),
            "complexity": "MEDIUM" if missing_count < 5000 else "HIGH",
        }

    def _identify_priority_currencies_with_data(
        self, missing_analysis: Dict[str, Any]
    ) -> List[str]:
        """Identify priority currencies for FMV fetching."""
        if "buy_currencies" not in missing_analysis:
            return []

        buy_currencies = missing_analysis["buy_currencies"]
        sell_currencies = missing_analysis["sell_currencies"]

        # Combine and count all currencies
        all_currencies = Counter()
        all_currencies.update(buy_currencies)
        all_currencies.update(sell_currencies)

        # Return top 10 currencies by frequency
        return [currency for currency, count in all_currencies.most_common(10)]

    def _identify_priority_exchanges_with_data(
        self, missing_analysis: Dict[str, Any]
    ) -> List[str]:
        """Identify priority exchanges for FMV fetching."""
        if "exchanges" not in missing_analysis:
            return []

        exchanges = missing_analysis["exchanges"]
        return [exchange for exchange, count in exchanges.items() if count > 0]

    def _identify_priority_transaction_types_with_data(
        self, missing_analysis: Dict[str, Any]
    ) -> List[str]:
        """Identify priority transaction types for FMV fetching."""
        if "transaction_types" not in missing_analysis:
            return []

        transaction_types = missing_analysis["transaction_types"]
        return [tx_type for tx_type, count in transaction_types.items() if count > 0]

    def _generate_fmv_strategy(self) -> Dict[str, Any]:
        """Generate FMV fetching strategy recommendations."""
        missing_percentage = self.analysis_results["summary"]["missing_fmv_percentage"]

        strategy = {
            "overall_approach": "Multi-source FMV fetching with caching",
            "priority_level": "HIGH" if missing_percentage > 30 else "MEDIUM",
            "recommended_sources": [
                "CoinGecko API (primary)",
                "CoinMarketCap API (secondary)",
                "Etherscan API (for Ethereum tokens)",
                "Local cache database",
            ],
            "caching_strategy": "SQLite database with daily updates",
            "rate_limiting": "Implement exponential backoff for API calls",
            "fallback_strategy": "Use nearest available date FMV",
        }

        return strategy

    def _estimate_effort(self) -> Dict[str, Any]:
        """Estimate effort required for Phase 2 FMV implementation."""
        missing_count = self.analysis_results["summary"]["missing_fmv_count"]

        # Rough estimates based on missing transaction count
        api_calls_needed = missing_count * 1.2  # 20% buffer for retries
        estimated_time_hours = max(
            1, missing_count / 1000
        )  # 1000 transactions per hour
        estimated_cost_usd = max(
            0, (api_calls_needed - 10000) * 0.0001
        )  # Free tier + paid

        return {
            "estimated_api_calls": int(api_calls_needed),
            "estimated_time_hours": round(estimated_time_hours, 1),
            "estimated_cost_usd": round(estimated_cost_usd, 2),
            "complexity": "MEDIUM" if missing_count < 5000 else "HIGH",
        }

    def generate_report(self, output_path: Optional[str] = None) -> str:
        """
        Generate a comprehensive analysis report.

        Args:
            output_path: Optional path to save report

        Returns:
            Report content as string
        """
        if not self.analysis_results:
            return "No analysis results available. Run analyze_missing_fmv() first."

        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("CRYPTOTAXCALC - MISSING FMV DATA ANALYSIS REPORT")
        report_lines.append("=" * 60)
        report_lines.append(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        report_lines.append("")

        # Summary section
        summary = self.analysis_results["summary"]
        report_lines.append("SUMMARY")
        report_lines.append("-" * 20)
        report_lines.append(f"Total Transactions: {summary['total_transactions']:,}")
        report_lines.append(
            f"Missing FMV: {summary['missing_fmv_count']:,} ({summary['missing_fmv_percentage']:.1f}%)"
        )
        report_lines.append(f"Available FMV: {summary['available_fmv_count']:,}")
        report_lines.append("")

        # Missing FMV Analysis
        missing_analysis = self.analysis_results["missing_fmv_analysis"]
        if "error" not in missing_analysis:
            report_lines.append("MISSING FMV ANALYSIS")
            report_lines.append("-" * 25)

            # Transaction types
            if "transaction_types" in missing_analysis:
                report_lines.append("Top Transaction Types (Missing FMV):")
                for tx_type, count in list(
                    missing_analysis["transaction_types"].items()
                )[:5]:
                    report_lines.append(f"  {tx_type}: {count:,}")
                report_lines.append("")

            # Currencies
            if "buy_currencies" in missing_analysis:
                report_lines.append("Top Buy Currencies (Missing FMV):")
                for currency, count in list(missing_analysis["buy_currencies"].items())[
                    :5
                ]:
                    report_lines.append(f"  {currency}: {count:,}")
                report_lines.append("")

            # Exchanges
            if "exchanges" in missing_analysis:
                report_lines.append("Top Exchanges (Missing FMV):")
                for exchange, count in list(missing_analysis["exchanges"].items())[:5]:
                    report_lines.append(f"  {exchange}: {count:,}")
                report_lines.append("")

        # Recommendations
        recommendations = self.analysis_results["recommendations"]
        if "error" not in recommendations:
            report_lines.append("RECOMMENDATIONS FOR PHASE 2")
            report_lines.append("-" * 30)

            # Priority currencies
            if "priority_currencies" in recommendations:
                report_lines.append("Priority Currencies for FMV Fetching:")
                for currency in recommendations["priority_currencies"][:5]:
                    report_lines.append(f"  - {currency}")
                report_lines.append("")

            # FMV Strategy
            if "fmv_fetching_strategy" in recommendations:
                strategy = recommendations["fmv_fetching_strategy"]
                report_lines.append("Recommended FMV Fetching Strategy:")
                report_lines.append(f"  Approach: {strategy['overall_approach']}")
                report_lines.append(f"  Priority: {strategy['priority_level']}")
                report_lines.append("  Sources:")
                for source in strategy["recommended_sources"]:
                    report_lines.append(f"    - {source}")
                report_lines.append("")

            # Effort estimation
            if "estimated_effort" in recommendations:
                effort = recommendations["estimated_effort"]
                report_lines.append("Effort Estimation:")
                report_lines.append(
                    f"  API Calls Needed: {effort['estimated_api_calls']:,}"
                )
                report_lines.append(
                    f"  Estimated Time: {effort['estimated_time_hours']} hours"
                )
                report_lines.append(
                    f"  Estimated Cost: ${effort['estimated_cost_usd']}"
                )
                report_lines.append(f"  Complexity: {effort['complexity']}")
                report_lines.append("")

        report_lines.append("=" * 60)
        report_content = "\n".join(report_lines)

        # Save to file if path provided
        if output_path:
            try:
                with open(output_path, "w") as f:
                    f.write(report_content)
                logger.info(f"Report saved to {output_path}")
            except Exception as e:
                logger.error(f"Error saving report: {str(e)}")

        return report_content

    def save_missing_data(self, output_path: str) -> None:
        """
        Save missing FMV data to CSV for further analysis.

        Args:
            output_path: Path for output CSV file
        """
        if self.missing_fmv_data is None or self.missing_fmv_data.empty:
            logger.warning("No missing FMV data to save")
            # Create empty CSV file with headers
            try:
                empty_df = pd.DataFrame(
                    columns=(
                        self.available_fmv_data.columns
                        if self.available_fmv_data is not None
                        else []
                    )
                )
                empty_df.to_csv(output_path, index=False)
                logger.info(f"Empty missing FMV data file created at {output_path}")
            except Exception as e:
                logger.error(f"Error creating empty missing FMV data file: {str(e)}")
            return

        try:
            self.missing_fmv_data.to_csv(output_path, index=False)
            logger.info(f"Missing FMV data saved to {output_path}")
        except Exception as e:
            logger.error(f"Error saving missing FMV data: {str(e)}")
            raise


def analyze_transaction_data(
    df: pd.DataFrame,
    output_report_path: Optional[str] = None,
    output_missing_data_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convenience function to analyze transaction data for missing FMV.

    Args:
        df: DataFrame from Phase 1A parser output
        output_report_path: Optional path to save analysis report
        output_missing_data_path: Optional path to save missing FMV data

    Returns:
        Dictionary with analysis results
    """
    explorer = DataExplorer()
    analysis = explorer.analyze_missing_fmv(df)

    # Generate and save report
    if output_report_path:
        explorer.generate_report(output_report_path)

    # Save missing data
    if output_missing_data_path:
        explorer.save_missing_data(output_missing_data_path)

    return analysis


if __name__ == "__main__":
    # Example usage
    import sys
    from cryptotaxcalc.parser import parse_transaction_file

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        try:
            # Parse transaction file
            df, summary = parse_transaction_file(file_path)

            # Analyze missing FMV data
            analysis = analyze_transaction_data(
                df,
                output_report_path="missing_fmv_analysis_report.txt",
                output_missing_data_path="missing_fmv_transactions.csv",
            )

            # Print summary
            missing_percentage = analysis["summary"]["missing_fmv_percentage"]
            print(f"\n=== Missing FMV Analysis Complete ===")
            print(f"Missing FMV: {missing_percentage:.1f}% of transactions")
            print(f"Report saved to: missing_fmv_analysis_report.txt")
            print(f"Missing data saved to: missing_fmv_transactions.csv")

        except Exception as e:
            print(f"Error: {str(e)}")
    else:
        print("Usage: python data_explorer.py <csv_file_path>")
