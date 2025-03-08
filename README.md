# AI Token Trackoor 🤖💰

A Python-based cryptocurrency tracking tool that aggregates information about newly listed and trending AI-related tokens. The tool scrapes data from multiple sources and provides daily summaries of token performance and social sentiment analysis.

## 🌟 Features

- **Multi-Source Data Aggregation**
  - Scrapes data from CoinGecko API
  - Monitors CoinMarketCap's AI crypto section
  - Automatically deduplicates tokens from multiple sources

- **AI Token Detection**
  - Tracks trending coins with AI capabilities
  - Identifies tokens with AI-related names or descriptions
  - Monitors market cap rankings for AI tokens

- **Comprehensive Price Analysis**
  - Current price in USD
  - 24-hour price changes
  - 7-day price movement trends
  - Trading volume analysis
  - Market capitalization tracking

- **Advanced Sentiment Analysis**
  - Integration with StockGeist.ai
  - Real-time sentiment scoring
  - Social media engagement metrics
  - Volume of social discussions
  - Sentiment trend analysis

- **Automated Reporting**
  - Daily report generation
  - JSON format for easy parsing
  - Historical data tracking
  - Timestamp-based organization

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- StockGeist.ai API key

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/sqryxz/ai-token-trackoor.git
   cd ai-token-trackoor
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your StockGeist.ai API key:
   ```
   STOCKGEIST_API_KEY=your_stockgeist_api_key_here
   ```

### Usage

Run the script:
```bash
python main.py
```

The script will:
- Start monitoring AI-related tokens immediately
- Generate an initial report
- Continue running and generate daily reports at midnight
- Store reports in the `reports` directory

## 📊 Report Structure

Reports are generated in JSON format with the following structure:
```json
{
    "timestamp": "2024-03-21T00:00:00.000Z",
    "total_tokens_tracked": 25,
    "tokens": [
        {
            "name": "AI Token Name",
            "symbol": "AIT",
            "market_cap_rank": 123,
            "source": "coingecko_trending",
            "price_data": {
                "current_price": 1.23,
                "price_change_24h": 5.67,
                "price_change_7d": -2.34,
                "market_cap": 1000000,
                "volume_24h": 500000
            },
            "sentiment_data": {
                "sentiment_score": 0.75,
                "sentiment_label": "bullish",
                "social_volume": 1500,
                "social_engagement": 25000,
                "timestamp": "2024-03-21T00:00:00.000Z"
            }
        }
    ]
}
```

## 📅 Scheduling

- Reports are generated daily at midnight (00:00)
- Each report is saved with a timestamp-based filename
- Historical reports are preserved for trend analysis

## 🔒 Security

- API keys are stored in `.env` file (not tracked by Git)
- Reports directory is excluded from Git tracking
- Sensitive data is not logged or exposed

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is open source and available under the MIT License.

## ⚠️ Disclaimer

This tool is for informational purposes only. Not financial advice. Always do your own research before making investment decisions. 