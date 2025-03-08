# AI Token Watcher

A Python-based tool that monitors and analyzes AI-related cryptocurrency tokens, providing sentiment analysis from multiple sources and tracking market performance.

## Features

- **Multi-Source Token Discovery**
  - Tracks trending AI tokens from CoinGecko and CoinMarketCap
  - Identifies newly listed AI-related tokens
  - Monitors specific AI token categories
  - Limited to top 5 tokens per source for focused analysis

- **Comprehensive Data Collection**
  - Price and market cap tracking
  - 24h and 7d price changes
  - Trading volume monitoring
  - Market cap ranking

- **Sentiment Analysis**
  - Reddit community sentiment
  - Crypto news sentiment via CryptoCompare
  - Combined sentiment scoring
  - Social engagement metrics

- **Automated Reporting**
  - Daily report generation
  - JSON format for easy integration
  - Historical data storage
  - Top tokens summary

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-token-watcher.git
cd ai-token-watcher
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Add your API keys:
     - CryptoCompare API key
     - (Optional) Additional API keys as needed

## Usage

Run the script:
```bash
python main.py
```

The script will:
1. Fetch AI-related tokens from multiple sources
2. Analyze sentiment from Reddit and crypto news
3. Generate a daily report in the `reports` directory
4. Continue running and update daily at midnight

## Configuration

### Environment Variables

Create a `.env` file with the following variables:
```
CRYPTOCOMPARE_API_KEY=your_api_key_here
```

### Customization

You can modify the following parameters in the code:
- Number of tokens per source (default: 5)
- Sentiment analysis thresholds
- Report generation frequency
- Token filtering criteria

## Output

Reports are generated in JSON format in the `reports` directory with the following structure:
```json
{
    "timestamp": "ISO-8601-timestamp",
    "total_tokens_tracked": "number",
    "tokens": [
        {
            "name": "Token Name",
            "symbol": "SYMBOL",
            "market_cap_rank": "rank",
            "price_data": {
                "current_price": "usd_price",
                "price_change_24h": "percentage",
                "price_change_7d": "percentage",
                "market_cap": "usd_value",
                "volume_24h": "usd_value"
            },
            "sentiment_data": {
                "reddit": {
                    "sentiment_score": "float",
                    "sentiment_label": "bullish/bearish/neutral",
                    "social_volume": "number",
                    "social_engagement": "number"
                },
                "news": {
                    "sentiment_score": "float",
                    "sentiment_label": "bullish/bearish/neutral",
                    "articles_count": "number"
                },
                "combined": {
                    "sentiment_score": "float",
                    "sentiment_label": "bullish/bearish/neutral"
                }
            }
        }
    ]
}
```

## Dependencies

- `requests`: HTTP requests
- `beautifulsoup4`: Web scraping
- `python-dotenv`: Environment variable management
- `pandas`: Data manipulation
- `schedule`: Task scheduling
- `pycoingecko`: CoinGecko API client
- `textblob`: Sentiment analysis
- `cryptocompare`: CryptoCompare API client

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for informational purposes only. Not financial advice. Always do your own research before making any investment decisions. 