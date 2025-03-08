import os
import json
import time
from datetime import datetime
import schedule
import requests
from bs4 import BeautifulSoup
from pycoingecko import CoinGeckoAPI
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv()

class AITokenWatcher:
    def __init__(self):
        self.coingecko = CoinGeckoAPI()
        self.stockgeist_api_key = os.getenv("STOCKGEIST_API_KEY")
        self.reports_dir = "reports"
        os.makedirs(self.reports_dir, exist_ok=True)

    def get_coingecko_ai_tokens(self):
        """Fetch AI-related tokens from CoinGecko"""
        try:
            # Get trending coins
            trending = self.coingecko.get_search_trending()
            # Get tokens with 'ai' in their name or description
            search_results = self.coingecko.search('ai')
            
            tokens = []
            # Process trending coins
            for coin in trending['coins']:
                token_data = coin['item']
                tokens.append({
                    'name': token_data['name'],
                    'symbol': token_data['symbol'],
                    'market_cap_rank': token_data['market_cap_rank'],
                    'source': 'coingecko_trending'
                })
            
            # Process AI-related coins
            for coin in search_results['coins']:
                if 'ai' in coin['name'].lower() or 'ai' in coin['symbol'].lower():
                    tokens.append({
                        'name': coin['name'],
                        'symbol': coin['symbol'],
                        'market_cap_rank': coin['market_cap_rank'],
                        'source': 'coingecko_search'
                    })
            
            return tokens
        except Exception as e:
            print(f"Error fetching from CoinGecko: {e}")
            return []

    def get_coinmarketcap_ai_tokens(self):
        """Fetch AI-related tokens from CoinMarketCap"""
        try:
            url = "https://coinmarketcap.com/view/ai-crypto/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            tokens = []
            # Parse the webpage to extract token information
            table = soup.find('table')
            if table:
                rows = table.find_all('tr')[1:]  # Skip header row
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        tokens.append({
                            'name': cols[2].text.strip(),
                            'symbol': cols[3].text.strip(),
                            'source': 'coinmarketcap'
                        })
            
            return tokens
        except Exception as e:
            print(f"Error fetching from CoinMarketCap: {e}")
            return []

    def get_token_sentiment(self, token_symbol):
        """Get sentiment analysis from StockGeist.ai"""
        try:
            url = "https://api.stockgeist.ai/sentiment"
            headers = {
                "Authorization": f"Bearer {self.stockgeist_api_key}",
                "Content-Type": "application/json"
            }
            params = {
                "symbol": token_symbol,
                "asset_type": "crypto"
            }
            
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                return {
                    'sentiment_score': data.get('sentiment_score'),
                    'sentiment_label': data.get('sentiment_label'),
                    'social_volume': data.get('social_volume'),
                    'social_engagement': data.get('social_engagement'),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                print(f"Error getting sentiment for {token_symbol}: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error getting sentiment from StockGeist: {e}")
            return None

    def generate_daily_report(self):
        """Generate a daily report of AI tokens"""
        print("Generating daily report...")
        
        # Get tokens from both sources
        coingecko_tokens = self.get_coingecko_ai_tokens()
        cmc_tokens = self.get_coinmarketcap_ai_tokens()
        
        # Combine and deduplicate tokens
        all_tokens = []
        seen_symbols = set()
        
        for token in coingecko_tokens + cmc_tokens:
            if token['symbol'].lower() not in seen_symbols:
                seen_symbols.add(token['symbol'].lower())
                
                # Get additional details from CoinGecko
                try:
                    token_info = self.coingecko.get_coin_by_id(token['symbol'].lower())
                    price_data = {
                        'current_price': token_info['market_data']['current_price']['usd'],
                        'price_change_24h': token_info['market_data']['price_change_percentage_24h'],
                        'price_change_7d': token_info['market_data']['price_change_percentage_7d'],
                        'market_cap': token_info['market_data']['market_cap']['usd'],
                        'volume_24h': token_info['market_data']['total_volume']['usd']
                    }
                except:
                    price_data = None
                
                # Get social sentiment from StockGeist
                sentiment = self.get_token_sentiment(token['symbol'])
                
                token_data = {
                    **token,
                    'price_data': price_data,
                    'sentiment_data': sentiment
                }
                all_tokens.append(token_data)
        
        # Generate report
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_tokens_tracked': len(all_tokens),
            'tokens': all_tokens
        }
        
        # Save report
        filename = f"{self.reports_dir}/report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Report generated: {filename}")

def main():
    watcher = AITokenWatcher()
    
    # Schedule daily report generation
    schedule.every().day.at("00:00").do(watcher.generate_daily_report)
    
    # Generate initial report
    watcher.generate_daily_report()
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main() 