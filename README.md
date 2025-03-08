# AI Token Watcher

A Python-based tool that aggregates information about newly listed and trending AI-related cryptocurrency tokens. The tool scrapes data from multiple sources and provides daily summaries of token performance and social sentiment.

## Features

- Scrapes data from CoinGecko and CoinMarketCap
- Tracks AI-related tokens
- Generates daily price movement summaries
- Includes social media sentiment analysis from StockGeist.ai
- Automated daily reports

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your API key:
   ```
   STOCKGEIST_API_KEY=your_stockgeist_api_key_here
   ```
4. Run the script:
   ```bash
   python main.py
   ```

## Output

The tool generates daily reports in the `reports` directory with information about:
- Token name and symbol
- Price changes (24h, 7d)
- Trading volume
- Social media sentiment (via StockGeist.ai)
  - Sentiment score and label
  - Social volume
  - Social engagement
- Market cap
- Notable mentions or news 