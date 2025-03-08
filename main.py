import os
import json
import time
from datetime import datetime, timedelta
import schedule
import requests
from bs4 import BeautifulSoup
from pycoingecko import CoinGeckoAPI
from dotenv import load_dotenv
import pandas as pd
import praw
from textblob import TextBlob
import cryptocompare

# Load environment variables
load_dotenv()

class AITokenWatcher:
    def __init__(self):
        self.coingecko = CoinGeckoAPI()
        self.reports_dir = "reports"
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # Initialize Reddit client
        self.reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT")
        )
        
        # Initialize CryptoCompare
        cryptocompare.cryptocompare._set_api_key_parameter(os.getenv("CRYPTOCOMPARE_API_KEY"))

    def analyze_text_sentiment(self, text):
        """Analyze sentiment of a text using TextBlob"""
        try:
            analysis = TextBlob(text)
            # Get polarity score (-1 to 1)
            polarity = analysis.sentiment.polarity
            
            # Convert polarity to label
            if polarity > 0.1:
                label = "bullish"
            elif polarity < -0.1:
                label = "bearish"
            else:
                label = "neutral"
                
            return {
                'score': polarity,
                'label': label
            }
        except:
            return None

    def get_reddit_sentiment(self, token_name, token_symbol, limit=100):
        """Get sentiment from Reddit posts and comments"""
        try:
            # Search in relevant subreddits
            subreddits = ['CryptoCurrency', 'CryptoMarkets', 'AltStreetBets', 'CryptoTechnology']
            posts = []
            
            for subreddit in subreddits:
                # Search for posts containing token name or symbol
                search_query = f"{token_name} OR {token_symbol}"
                subreddit_posts = self.reddit.subreddit(subreddit).search(
                    search_query,
                    time_filter='week',
                    limit=25
                )
                posts.extend(subreddit_posts)
            
            if not posts:
                return None
            
            # Analyze sentiment of posts and comments
            sentiments = []
            total_score = 0  # Combined upvotes
            total_comments = 0
            
            for post in posts:
                # Analyze post title and body
                if post.title:
                    title_sentiment = self.analyze_text_sentiment(post.title)
                    if title_sentiment:
                        sentiments.append(title_sentiment['score'])
                
                if post.selftext:
                    body_sentiment = self.analyze_text_sentiment(post.selftext)
                    if body_sentiment:
                        sentiments.append(body_sentiment['score'])
                
                total_score += post.score
                total_comments += post.num_comments
                
                # Get top comments
                post.comments.replace_more(limit=0)
                for comment in post.comments.list()[:10]:
                    if comment.body:
                        comment_sentiment = self.analyze_text_sentiment(comment.body)
                        if comment_sentiment:
                            sentiments.append(comment_sentiment['score'])
            
            if not sentiments:
                return None
            
            # Calculate average sentiment
            avg_sentiment = sum(sentiments) / len(sentiments)
            
            # Determine sentiment label
            if avg_sentiment > 0.1:
                sentiment_label = "bullish"
            elif avg_sentiment < -0.1:
                sentiment_label = "bearish"
            else:
                sentiment_label = "neutral"
            
            return {
                'sentiment_score': avg_sentiment,
                'sentiment_label': sentiment_label,
                'social_volume': len(posts),
                'social_engagement': total_score + total_comments,
                'source': 'reddit',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error getting Reddit sentiment for {token_symbol}: {e}")
            return None

    def get_news_sentiment(self, token_symbol):
        """Get news sentiment from CryptoCompare"""
        try:
            # Get news articles
            news = cryptocompare.get_news_articles(feeds='all')
            relevant_news = []
            
            # Filter news related to the token
            for article in news:
                if (token_symbol.lower() in article['title'].lower() or 
                    'ai' in article['title'].lower() or 
                    'artificial intelligence' in article['title'].lower()):
                    relevant_news.append(article)
            
            if not relevant_news:
                return None
            
            # Analyze sentiment of news articles
            sentiments = []
            for article in relevant_news:
                title_sentiment = self.analyze_text_sentiment(article['title'])
                if title_sentiment:
                    sentiments.append(title_sentiment['score'])
            
            if not sentiments:
                return None
            
            # Calculate average sentiment
            avg_sentiment = sum(sentiments) / len(sentiments)
            
            return {
                'sentiment_score': avg_sentiment,
                'sentiment_label': 'bullish' if avg_sentiment > 0.1 else 'bearish' if avg_sentiment < -0.1 else 'neutral',
                'articles_count': len(relevant_news),
                'source': 'news',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error getting news sentiment for {token_symbol}: {e}")
            return None

    def get_token_sentiment(self, token_name, token_symbol):
        """Get combined sentiment analysis from multiple sources"""
        try:
            # Get sentiment from different sources
            reddit_sentiment = self.get_reddit_sentiment(token_name, token_symbol)
            news_sentiment = self.get_news_sentiment(token_symbol)
            
            if not reddit_sentiment and not news_sentiment:
                print(f"No sentiment data found for {token_symbol}")
                return None
            
            # Combine sentiment data
            sentiment_data = {
                'reddit': reddit_sentiment,
                'news': news_sentiment,
                'timestamp': datetime.now().isoformat()
            }
            
            # Calculate combined sentiment
            scores = []
            if reddit_sentiment:
                scores.append(reddit_sentiment['sentiment_score'])
            if news_sentiment:
                scores.append(news_sentiment['sentiment_score'])
            
            if scores:
                avg_score = sum(scores) / len(scores)
                sentiment_data['combined'] = {
                    'sentiment_score': avg_score,
                    'sentiment_label': 'bullish' if avg_score > 0.1 else 'bearish' if avg_score < -0.1 else 'neutral'
                }
            
            print(f"Sentiment data fetched successfully for {token_symbol}")
            return sentiment_data
            
        except Exception as e:
            print(f"Error getting combined sentiment: {e}")
            return None

    def get_coingecko_ai_tokens(self):
        """Fetch AI-related tokens from CoinGecko"""
        try:
            print("Fetching data from CoinGecko...")
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
                    'coingecko_id': token_data.get('id'),
                    'source': 'coingecko_trending'
                })
            
            # Process AI-related coins
            for coin in search_results['coins']:
                if 'ai' in coin['name'].lower() or 'ai' in coin['symbol'].lower():
                    tokens.append({
                        'name': coin['name'],
                        'symbol': coin['symbol'],
                        'market_cap_rank': coin['market_cap_rank'],
                        'coingecko_id': coin.get('id'),
                        'source': 'coingecko_search'
                    })
            
            print(f"Found {len(tokens)} tokens from CoinGecko")
            return tokens
        except Exception as e:
            print(f"Error fetching from CoinGecko: {e}")
            return []

    def get_coinmarketcap_ai_tokens(self):
        """Fetch AI-related tokens from CoinMarketCap"""
        try:
            print("Fetching data from CoinMarketCap...")
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
            
            print(f"Found {len(tokens)} tokens from CoinMarketCap")
            return tokens
        except Exception as e:
            print(f"Error fetching from CoinMarketCap: {e}")
            return []

    def get_token_price_data(self, token):
        """Get price data for a token from CoinGecko"""
        try:
            # Try using coingecko_id if available
            token_id = token.get('coingecko_id')
            if not token_id:
                # Try searching for the token
                search_result = self.coingecko.search(token['symbol'])
                if search_result and search_result['coins']:
                    token_id = search_result['coins'][0]['id']
            
            if token_id:
                token_info = self.coingecko.get_coin_by_id(token_id)
                price_data = {
                    'current_price': token_info['market_data']['current_price']['usd'],
                    'price_change_24h': token_info['market_data']['price_change_percentage_24h'],
                    'price_change_7d': token_info['market_data']['price_change_percentage_7d'],
                    'market_cap': token_info['market_data']['market_cap']['usd'],
                    'volume_24h': token_info['market_data']['total_volume']['usd']
                }
                print(f"Price data fetched successfully")
                return price_data
            else:
                print(f"Could not find CoinGecko ID for {token['symbol']}")
                return None
        except Exception as e:
            print(f"Error fetching price data: {e}")
            return None

    def generate_daily_report(self):
        """Generate a daily report of AI tokens"""
        print("\nGenerating daily report...")
        
        # Get tokens from both sources
        coingecko_tokens = self.get_coingecko_ai_tokens()
        cmc_tokens = self.get_coinmarketcap_ai_tokens()
        
        # Combine and deduplicate tokens
        all_tokens = []
        seen_symbols = set()
        
        print("\nProcessing tokens and fetching additional data...")
        for token in coingecko_tokens + cmc_tokens:
            if token['symbol'].lower() not in seen_symbols:
                seen_symbols.add(token['symbol'].lower())
                
                print(f"\nProcessing {token['name']} ({token['symbol']})...")
                
                # Get price data
                price_data = self.get_token_price_data(token)
                
                # Get sentiment data
                sentiment = self.get_token_sentiment(token['name'], token['symbol'])
                
                token_data = {
                    **token,
                    'price_data': price_data,
                    'sentiment_data': sentiment
                }
                all_tokens.append(token_data)
        
        # Sort tokens by market cap rank
        all_tokens.sort(key=lambda x: x.get('market_cap_rank', float('inf')))
        
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
        
        print(f"\nReport generated successfully: {filename}")
        print(f"Total tokens tracked: {len(all_tokens)}")
        
        # Print summary of top 5 tokens
        print("\nTop 5 AI Tokens Summary:")
        for token in all_tokens[:5]:
            print(f"\n{token['name']} ({token['symbol']})")
            if token['price_data']:
                print(f"Price: ${token['price_data']['current_price']:.2f}")
                print(f"24h Change: {token['price_data']['price_change_24h']:.2f}%")
            if token['sentiment_data'] and token['sentiment_data'].get('combined'):
                print(f"Overall Sentiment: {token['sentiment_data']['combined']['sentiment_label']}")
                if token['sentiment_data'].get('reddit'):
                    print(f"Reddit Activity: {token['sentiment_data']['reddit']['social_volume']} posts")
                if token['sentiment_data'].get('news'):
                    print(f"News Coverage: {token['sentiment_data']['news']['articles_count']} articles")

def main():
    try:
        watcher = AITokenWatcher()
        
        # Schedule daily report generation
        schedule.every().day.at("00:00").do(watcher.generate_daily_report)
        
        # Generate initial report
        watcher.generate_daily_report()
        
        print("\nScript is running. Press Ctrl+C to stop.")
        # Keep the script running
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nScript stopped by user")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main() 