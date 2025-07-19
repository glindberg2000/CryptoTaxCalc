"""
FIFO Manager for CryptoTaxCalc.

Handles First-In-First-Out (FIFO) queue management for cryptocurrency transactions,
including lot matching, basis tracking, and capital gains/loss calculations.
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Any, NamedTuple
from collections import deque
import logging
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class Lot:
    """
    Represents a lot of cryptocurrency with acquisition details.
    
    A lot is a specific quantity of cryptocurrency acquired at a specific time
    with a specific cost basis, used for FIFO lot matching.
    """
    amount: float
    basis: float
    acquisition_date: datetime
    asset: str
    lot_id: Optional[str] = None
    
    def __post_init__(self):
        """Validate lot data after initialization."""
        if self.amount <= 0:
            raise ValueError(f"Lot amount must be positive, got {self.amount}")
        if self.basis < 0:
            raise ValueError(f"Lot basis cannot be negative, got {self.basis}")
        if not self.asset:
            raise ValueError("Asset cannot be empty")
        
        # Generate lot_id if not provided
        if self.lot_id is None:
            self.lot_id = f"{self.asset}_{self.acquisition_date.strftime('%Y%m%d_%H%M%S')}_{self.amount}"


@dataclass
class DisposalResult:
    """
    Result of a disposal operation with matched lots and tax calculations.
    """
    disposal_amount: float
    disposal_date: datetime
    asset: str
    matched_lots: List[Tuple[Lot, float]]  # (lot, amount_used)
    total_proceeds: float
    total_basis: float
    total_gain_loss: float
    short_term_gain_loss: float
    long_term_gain_loss: float
    remaining_amount: float  # Amount that couldn't be matched


class FIFOQueue:
    """
    FIFO queue for a specific cryptocurrency asset.
    
    Manages lots of a single asset using a deque for efficient FIFO operations.
    """
    
    def __init__(self, asset: str):
        """
        Initialize FIFO queue for a specific asset.
        
        Args:
            asset: The cryptocurrency asset symbol (e.g., 'BTC', 'ETH')
        """
        self.asset = asset
        self.lots: deque[Lot] = deque()
        self.total_amount: float = 0.0
        self.total_basis: float = 0.0
        
    def add_lot(self, lot: Lot) -> None:
        """
        Add a new lot to the FIFO queue.
        
        Args:
            lot: The lot to add
        """
        if lot.asset != self.asset:
            raise ValueError(f"Lot asset {lot.asset} doesn't match queue asset {self.asset}")
        
        self.lots.append(lot)
        self.total_amount += lot.amount
        self.total_basis += lot.basis
        
        logger.debug(f"Added lot to {self.asset} queue: {lot.amount} @ ${lot.basis:.2f}")
        
    def get_available_amount(self) -> float:
        """Get total available amount in the queue."""
        return self.total_amount
    
    def get_total_basis(self) -> float:
        """Get total cost basis of all lots in the queue."""
        return self.total_basis
    
    def is_empty(self) -> bool:
        """Check if the queue is empty."""
        return len(self.lots) == 0
    
    def __len__(self) -> int:
        """Get number of lots in the queue."""
        return len(self.lots)
    
    def __repr__(self) -> str:
        return f"FIFOQueue({self.asset}, lots={len(self.lots)}, total_amount={self.total_amount:.6f})"


class FIFOManager:
    """
    Manages FIFO queues for multiple cryptocurrency assets.
    
    Handles lot matching, disposal calculations, and tax categorization
    according to IRS guidelines.
    """
    
    def __init__(self):
        """Initialize the FIFO manager."""
        self.queues: Dict[str, FIFOQueue] = {}
        self.disposal_history: List[DisposalResult] = []
        
    def get_or_create_queue(self, asset: str) -> FIFOQueue:
        """
        Get existing queue for asset or create a new one.
        
        Args:
            asset: The cryptocurrency asset symbol
            
        Returns:
            FIFOQueue for the specified asset
        """
        if asset not in self.queues:
            self.queues[asset] = FIFOQueue(asset)
            logger.info(f"Created new FIFO queue for {asset}")
        
        return self.queues[asset]
    
    def add_acquisition(self, asset: str, amount: float, basis: float, 
                       acquisition_date: datetime, lot_id: Optional[str] = None) -> None:
        """
        Add an acquisition to the appropriate FIFO queue.
        
        Args:
            asset: The cryptocurrency asset
            amount: Quantity acquired
            basis: Cost basis in USD
            acquisition_date: Date of acquisition
            lot_id: Optional lot identifier
        """
        if amount <= 0:
            raise ValueError(f"Acquisition amount must be positive, got {amount}")
        if basis < 0:
            raise ValueError(f"Acquisition basis cannot be negative, got {basis}")
        
        lot = Lot(
            amount=amount,
            basis=basis,
            acquisition_date=acquisition_date,
            asset=asset,
            lot_id=lot_id
        )
        
        queue = self.get_or_create_queue(asset)
        queue.add_lot(lot)
        
        logger.info(f"Added acquisition: {amount} {asset} @ ${basis:.2f} on {acquisition_date.strftime('%Y-%m-%d')}")
    
    def process_disposal(self, asset: str, amount: float, proceeds: float, 
                        disposal_date: datetime) -> DisposalResult:
        """
        Process a disposal using FIFO lot matching.
        
        Args:
            asset: The cryptocurrency asset being disposed
            amount: Quantity being disposed
            proceeds: Total proceeds in USD
            disposal_date: Date of disposal
            
        Returns:
            DisposalResult with matched lots and tax calculations
            
        Raises:
            ValueError: If insufficient lots available for disposal
        """
        if amount <= 0:
            raise ValueError(f"Disposal amount must be positive, got {amount}")
        if proceeds < 0:
            raise ValueError(f"Disposal proceeds cannot be negative, got {proceeds}")
        
        queue = self.get_or_create_queue(asset)
        
        if queue.get_available_amount() < amount:
            raise ValueError(
                f"Insufficient {asset} available for disposal. "
                f"Requested: {amount}, Available: {queue.get_available_amount()}"
            )
        
        # Match lots using FIFO
        remaining_amount = amount
        matched_lots = []
        total_basis = 0.0
        short_term_gain_loss = 0.0
        long_term_gain_loss = 0.0
        
        # Create a copy of lots to avoid modifying the original during iteration
        lots_to_process = list(queue.lots)
        
        for lot in lots_to_process:
            if remaining_amount <= 0:
                break
                
            # Calculate how much of this lot to use
            amount_to_use = min(lot.amount, remaining_amount)
            basis_used = (amount_to_use / lot.amount) * lot.basis
            
            # Calculate gain/loss for this portion
            proceeds_portion = (amount_to_use / amount) * proceeds
            gain_loss = proceeds_portion - basis_used
            
            # Determine if short-term or long-term
            holding_period = disposal_date - lot.acquisition_date
            is_short_term = holding_period.days < 365
            
            if is_short_term:
                short_term_gain_loss += gain_loss
            else:
                long_term_gain_loss += gain_loss
            
            matched_lots.append((lot, amount_to_use))
            total_basis += basis_used
            remaining_amount -= amount_to_use
            
            # Update the lot in the queue
            if amount_to_use == lot.amount:
                # Lot fully consumed, remove it
                queue.lots.remove(lot)
                queue.total_amount -= lot.amount
                queue.total_basis -= lot.basis
            else:
                # Lot partially consumed, update it
                lot.amount -= amount_to_use
                lot.basis -= basis_used
                queue.total_amount -= amount_to_use
                queue.total_basis -= basis_used
        
        # Create disposal result
        disposal_result = DisposalResult(
            disposal_amount=amount - remaining_amount,
            disposal_date=disposal_date,
            asset=asset,
            matched_lots=matched_lots,
            total_proceeds=proceeds,
            total_basis=total_basis,
            total_gain_loss=short_term_gain_loss + long_term_gain_loss,
            short_term_gain_loss=short_term_gain_loss,
            long_term_gain_loss=long_term_gain_loss,
            remaining_amount=remaining_amount
        )
        
        self.disposal_history.append(disposal_result)
        
        logger.info(
            f"Processed disposal: {amount} {asset} for ${proceeds:.2f}. "
            f"Gain/Loss: ${disposal_result.total_gain_loss:.2f} "
            f"(ST: ${short_term_gain_loss:.2f}, LT: ${long_term_gain_loss:.2f})"
        )
        
        return disposal_result
    
    def get_queue_summary(self, asset: str) -> Dict[str, Any]:
        """
        Get summary information for a specific asset queue.
        
        Args:
            asset: The cryptocurrency asset
            
        Returns:
            Dictionary with queue summary information
        """
        if asset not in self.queues:
            return {
                "asset": asset,
                "total_amount": 0.0,
                "total_basis": 0.0,
                "lot_count": 0,
                "average_basis": 0.0
            }
        
        queue = self.queues[asset]
        total_amount = queue.get_available_amount()
        total_basis = queue.get_total_basis()
        
        return {
            "asset": asset,
            "total_amount": total_amount,
            "total_basis": total_basis,
            "lot_count": len(queue.lots),
            "average_basis": total_basis / total_amount if total_amount > 0 else 0.0
        }
    
    def get_all_summaries(self) -> Dict[str, Dict[str, Any]]:
        """
        Get summaries for all asset queues.
        
        Returns:
            Dictionary mapping asset symbols to their summaries
        """
        summaries = {}
        for asset in self.queues:
            summaries[asset] = self.get_queue_summary(asset)
        return summaries
    
    def get_disposal_summary(self) -> Dict[str, Any]:
        """
        Get summary of all disposals processed.
        
        Returns:
            Dictionary with disposal summary statistics
        """
        if not self.disposal_history:
            return {
                "total_disposals": 0,
                "total_proceeds": 0.0,
                "total_basis": 0.0,
                "total_gain_loss": 0.0,
                "short_term_gain_loss": 0.0,
                "long_term_gain_loss": 0.0,
                "assets_disposed": []
            }
        
        total_proceeds = sum(d.total_proceeds for d in self.disposal_history)
        total_basis = sum(d.total_basis for d in self.disposal_history)
        total_gain_loss = sum(d.total_gain_loss for d in self.disposal_history)
        short_term_gain_loss = sum(d.short_term_gain_loss for d in self.disposal_history)
        long_term_gain_loss = sum(d.long_term_gain_loss for d in self.disposal_history)
        assets_disposed = list(set(d.asset for d in self.disposal_history))
        
        return {
            "total_disposals": len(self.disposal_history),
            "total_proceeds": total_proceeds,
            "total_basis": total_basis,
            "total_gain_loss": total_gain_loss,
            "short_term_gain_loss": short_term_gain_loss,
            "long_term_gain_loss": long_term_gain_loss,
            "assets_disposed": assets_disposed
        }
    
    def import_2023_year_end_data(self, holdings_data: Dict[str, List[Dict[str, Any]]]) -> None:
        """
        Import pre-2024 holdings data to initialize FIFO queues.
        
        Args:
            holdings_data: Dictionary mapping asset symbols to lists of holdings
                          Each holding should have 'date', 'qty', and 'basis' keys
        """
        for asset, holdings in holdings_data.items():
            for holding in holdings:
                # Parse date
                if isinstance(holding['date'], str):
                    acquisition_date = datetime.strptime(holding['date'], '%Y-%m-%d')
                else:
                    acquisition_date = holding['date']
                
                self.add_acquisition(
                    asset=asset,
                    amount=holding['qty'],
                    basis=holding['basis'],
                    acquisition_date=acquisition_date,
                    lot_id=f"2023_ye_{asset}_{acquisition_date.strftime('%Y%m%d')}"
                )
        
        logger.info(f"Imported 2023 year-end data for {len(holdings_data)} assets")
    
    def process_transactions(self, transactions_df: pd.DataFrame) -> List[DisposalResult]:
        """
        Process a DataFrame of transactions and return disposal results.
        
        Args:
            transactions_df: DataFrame with transaction data (from parser)
            
        Returns:
            List of DisposalResult objects for all disposals processed
        """
        disposal_results = []
        
        # Sort transactions by date to ensure chronological processing
        sorted_df = transactions_df.sort_values('Date').copy()
        
        for _, row in sorted_df.iterrows():
            try:
                transaction_type = row['Type']
                date = row['Date']
                
                if transaction_type in ['Trade', 'Spend']:
                    # Handle disposals (sells)
                    if row['SellAmount'] > 0 and row['SellCurrency']:
                        disposal_result = self.process_disposal(
                            asset=row['SellCurrency'],
                            amount=row['SellAmount'],
                            proceeds=row['USDEquivalent'] or 0.0,
                            disposal_date=date
                        )
                        disposal_results.append(disposal_result)
                    
                    # Handle acquisitions (buys)
                    if row['BuyAmount'] > 0 and row['BuyCurrency']:
                        self.add_acquisition(
                            asset=row['BuyCurrency'],
                            amount=row['BuyAmount'],
                            basis=row['USDEquivalent'] or 0.0,
                            acquisition_date=date
                        )
                
                elif transaction_type in ['Income', 'Staking', 'Airdrop']:
                    # Handle income events (ordinary income with $0 basis)
                    if row['BuyAmount'] > 0 and row['BuyCurrency']:
                        self.add_acquisition(
                            asset=row['BuyCurrency'],
                            amount=row['BuyAmount'],
                            basis=0.0,  # $0 basis for income events
                            acquisition_date=date
                        )
                
                # Note: Other transaction types (Deposit, Withdrawal, etc.) 
                # may need special handling based on specific requirements
                
            except Exception as e:
                logger.error(f"Error processing transaction on {date}: {str(e)}")
                # Continue processing other transactions
                continue
        
        return disposal_results


def create_fifo_manager() -> FIFOManager:
    """
    Convenience function to create a new FIFO manager.
    
    Returns:
        New FIFOManager instance
    """
    return FIFOManager()


if __name__ == "__main__":
    # Example usage
    import sys
    
    print("FIFO Manager for CryptoTaxCalc")
    print("This module provides FIFO queue management for cryptocurrency transactions.")
    print("Use as part of the CryptoTaxCalc package.")
