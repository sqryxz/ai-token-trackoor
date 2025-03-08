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
from textblob import TextBlob
import cryptocompare
import re
from urllib.parse import quote_plus

# Load environment variables
load_dotenv()

class AITokenWatcher:
    def __init__(self):
        self.coingecko = CoinGeckoAPI()
        self.reports_dir = "reports"
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # Initialize CryptoCompare
        cryptocompare.cryptocompare._set_api_key_parameter(os.getenv("CRYPTOCOMPARE_API_KEY"))
        
        # Headers for web scraping
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

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
        """Get sentiment from Reddit posts using web scraping"""
        try:
            # Search in relevant subreddits
            subreddits = ['CryptoCurrency', 'CryptoMarkets', 'AltStreetBets', 'CryptoTechnology']
            posts_data = []
            
            for subreddit in subreddits:
                # Create search URL
                search_query = quote_plus(f"{token_name} OR {token_symbol}")
                url = f"https://www.reddit.com/r/{subreddit}/search/?q={search_query}&restrict_sr=1&t=week&sort=top"
                
                try:
                    response = requests.get(url, headers=self.headers)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Find all post containers
                        posts = soup.find_all('div', {'data-testid': 'post-container'})
                        for post in posts[:25]:  # Limit to top 25 posts per subreddit
                            try:
                                # Extract post title
                                title = post.find('h3')
                                if title:
                                    title_text = title.text.strip()
                                    
                                    # Extract upvotes
                                    upvotes = post.find('div', {'data-testid': 'post-score'})
                                    upvote_count = 0
                                    if upvotes:
                                        upvote_text = upvotes.text.strip()
                                        if 'k' in upvote_text.lower():
                                            upvote_count = int(float(upvote_text.replace('k', '')) * 1000)
                                        else:
                                            upvote_count = int(upvote_text)
                                    
                                    # Extract comments count
                                    comments = post.find('span', string=re.compile(r'\d+\s*comments?'))
                                    comment_count = 0
                                    if comments:
                                        comment_text = comments.text.strip()
                                        comment_count = int(re.search(r'\d+', comment_text).group())
                                    
                                    posts_data.append({
                                        'title': title_text,
                                        'upvotes': upvote_count,
                                        'comments': comment_count,
                                        'subreddit': subreddit
                                    })
                            except Exception as e:
                                print(f"Error processing post: {e}")
                                continue
                                
                except Exception as e:
                    print(f"Error fetching subreddit {subreddit}: {e}")
                    continue
                
                # Add delay between requests
                time.sleep(2)
            
            if not posts_data:
                return None
            
            # Analyze sentiment of posts
            sentiments = []
            total_score = 0
            total_comments = 0
            
            for post in posts_data:
                if post['title']:
                    sentiment = self.analyze_text_sentiment(post['title'])
                    if sentiment:
                        sentiments.append(sentiment['score'])
                
                total_score += post['upvotes']
                total_comments += post['comments']
            
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
                'social_volume': len(posts_data),
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
            # Get news articles using the correct CryptoCompare endpoint
            url = f"https://min-api.cryptocompare.com/data/v2/news/?lang=EN&api_key={os.getenv('CRYPTOCOMPARE_API_KEY')}"
            response = requests.get(url)
            if response.status_code != 200:
                print(f"Error fetching news: {response.status_code}")
                return None
                
            news_data = response.json()
            if not news_data.get('Data'):
                return None
                
            relevant_news = []
            # Filter news related to the token
            for article in news_data['Data']:
                # Check if token is mentioned in title, body or categories
                if (token_symbol.lower() in article['title'].lower() or
                    'ai' in article['title'].lower() or
                    'artificial intelligence' in article['title'].lower() or
                    token_symbol.lower() in article.get('body', '').lower() or
                    any(cat.lower() == 'ai' for cat in article.get('categories', '').split('|'))):
                    relevant_news.append(article)
            
            if not relevant_news:
                return None
            
            # Analyze sentiment of news articles
            sentiments = []
            for article in relevant_news:
                title_sentiment = self.analyze_text_sentiment(article['title'])
                if title_sentiment:
                    sentiments.append(title_sentiment['score'])
                
                # Also analyze body text if available
                if article.get('body'):
                    body_sentiment = self.analyze_text_sentiment(article['body'])
                    if body_sentiment:
                        sentiments.append(body_sentiment['score'])
            
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
            
            # Get newly listed tokens (last 14 days)
            newly_listed = []
            try:
                # Get latest coins with 'ai' filter
                new_coins = self.coingecko.get_coins_markets(
                    vs_currency='usd',
                    order='id_desc',  # Latest first
                    per_page=50,  # Reduced from 250 to 50 since we only need 5
                    sparkline=False
                )
                two_weeks_ago = datetime.now() - timedelta(days=14)
                newly_listed = [
                    coin for coin in new_coins 
                    if coin.get('genesis_date') and datetime.strptime(coin['genesis_date'], '%Y-%m-%d') > two_weeks_ago
                ][:5]  # Limit to 5 newest coins
            except Exception as e:
                print(f"Error fetching new coins: {e}")
            
            # Get AI-related tokens
            search_results = self.coingecko.search('ai')
            
            tokens = []
            # Process trending coins (limit to 5)
            for coin in trending['coins'][:5]:
                token_data = coin['item']
                tokens.append({
                    'name': token_data['name'],
                    'symbol': token_data['symbol'],
                    'market_cap_rank': token_data['market_cap_rank'],
                    'coingecko_id': token_data.get('id'),
                    'source': 'coingecko_trending'
                })
            
            # Process newly listed coins (already limited to 5)
            for coin in newly_listed:
                # Check if it's AI-related
                if any(term in coin['name'].lower() or term in coin['symbol'].lower() 
                      for term in ['ai', 'artificial', 'intelligence', 'neural', 'machine', 'learn']):
                    tokens.append({
                        'name': coin['name'],
                        'symbol': coin['symbol'],
                        'market_cap_rank': coin['market_cap_rank'],
                        'coingecko_id': coin['id'],
                        'source': 'coingecko_new'
                    })
            
            # Process AI-related coins (limit to 5)
            ai_tokens_added = 0
            for coin in search_results['coins']:
                if ai_tokens_added >= 5:
                    break
                if any(term in coin['name'].lower() or term in coin['symbol'].lower() 
                      for term in ['ai', 'artificial', 'intelligence', 'neural', 'machine', 'learn']):
                    tokens.append({
                        'name': coin['name'],
                        'symbol': coin['symbol'],
                        'market_cap_rank': coin['market_cap_rank'],
                        'coingecko_id': coin.get('id'),
                        'source': 'coingecko_search'
                    })
                    ai_tokens_added += 1
            
            # Remove duplicates based on coingecko_id
            unique_tokens = {token['coingecko_id']: token for token in tokens if token['coingecko_id']}.values()
            tokens = list(unique_tokens)
            
            print(f"Found {len(tokens)} tokens from CoinGecko")
            return tokens
        except Exception as e:
            print(f"Error fetching from CoinGecko: {e}")
            return []

    def get_coinmarketcap_ai_tokens(self):
        """Fetch AI-related tokens from CoinMarketCap"""
        try:
            print("Fetching data from CoinMarketCap...")
            
            # Fetch from AI crypto category
            ai_url = "https://coinmarketcap.com/view/ai-crypto/"
            trending_url = "https://coinmarketcap.com/trending-cryptocurrencies/"
            new_url = "https://coinmarketcap.com/new/"
            
            tokens = []
            
            # Helper function to fetch and parse tokens from a URL
            def fetch_tokens_from_url(url, source_tag):
                tokens_from_source = 0
                try:
                    response = requests.get(url, headers=self.headers)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find all token rows
                    table = soup.find('table')
                    if table:
                        rows = table.find_all('tr')[1:]  # Skip header row
                        for row in rows:
                            if tokens_from_source >= 5:  # Limit to 5 tokens per source
                                break
                            cols = row.find_all('td')
                            if len(cols) >= 3:
                                name_col = cols[2].text.strip()
                                symbol_col = cols[3].text.strip()
                                
                                # Only add if it's AI-related for trending and new tokens
                                if (source_tag == 'coinmarketcap_ai' or 
                                    any(term in name_col.lower() or term in symbol_col.lower() 
                                        for term in ['ai', 'artificial', 'intelligence', 'neural', 'machine', 'learn'])):
                                    tokens.append({
                                        'name': name_col,
                                        'symbol': symbol_col,
                                        'source': source_tag
                                    })
                                    tokens_from_source += 1
                except Exception as e:
                    print(f"Error fetching from {url}: {e}")
            
            # Fetch from all sources
            fetch_tokens_from_url(ai_url, 'coinmarketcap_ai')
            fetch_tokens_from_url(trending_url, 'coinmarketcap_trending')
            fetch_tokens_from_url(new_url, 'coinmarketcap_new')
            
            # Remove duplicates based on symbol
            unique_tokens = {token['symbol']: token for token in tokens}.values()
            tokens = list(unique_tokens)
            
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