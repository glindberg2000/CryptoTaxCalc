# Sample Data Directory

This directory contains sample data files for testing and development purposes.

## ⚠️ Important Notes

- **Never commit real user data** to this repository
- **All sample data should be anonymized** and contain no real transaction information
- **Use these samples for testing only** - they are not representative of real tax scenarios

## File Structure

```
data/samples/
├── README.md                    # This file
├── sample_transactions.csv      # Sample transaction data
├── sample_holdings.json         # Sample pre-2024 holdings
├── sample_config.json           # Sample configuration
└── expected_outputs/            # Expected test outputs
    ├── form_8949_sample.csv
    ├── schedule_d_sample.csv
    └── summary_sample.json
```

## Sample Files

### sample_transactions.csv
Contains anonymized transaction data with the following columns:
- Type: Transaction type (Buy, Sell, Swap, Receive, etc.)
- Date: Transaction date (YYYY-MM-DD)
- BuyAmount: Amount bought
- BuyCurrency: Currency bought
- SellAmount: Amount sold
- SellCurrency: Currency sold
- USDEquivalent: USD value at transaction time
- TxID: Transaction identifier

### sample_holdings.json
Contains sample pre-2024 holdings data in the format:
```json
{
  "ASSET": [
    {
      "date": "YYYY-MM-DD",
      "qty": 1.0,
      "basis": 1000.0
    }
  ]
}
```

### sample_config.json
Sample configuration file with API keys and settings.

## Usage in Tests

These sample files are used in the test suite to verify:
- CSV parsing functionality
- FIFO queue management
- Tax calculations
- Report generation
- Error handling

## Adding New Samples

When adding new sample data:
1. Ensure all data is completely anonymized
2. Use realistic but fake transaction amounts
3. Include edge cases and error conditions
4. Update this README with file descriptions
5. Add corresponding tests

## Security

- No real API keys or sensitive data
- No real transaction hashes or addresses
- No real user information
- All amounts and dates are fictional 