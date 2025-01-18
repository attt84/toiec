import google.generativeai as genai
from datetime import datetime
import os
from dotenv import load_dotenv
import json
import requests
from bs4 import BeautifulSoup
import re

load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

def search_web_articles(category):
    """Search for articles using web search"""
    try:
        # Define search queries for each category
        category_queries = {
            'IT': 'latest technology news artificial intelligence',
            'Economics': 'latest business economics news market',
            'Politics': 'latest international politics news'
        }
        
        # Get search query
        query = category_queries.get(category, 'latest technology news')
        
        # Use requests to get Google search results
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Try different news sources
        news_sites = [
            'https://techcrunch.com',
            'https://www.theverge.com',
            'https://www.bbc.com/news',
            'https://www.reuters.com',
            'https://apnews.com'
        ]
        
        for site in news_sites:
            try:
                response = requests.get(site, headers=headers, timeout=5)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Remove unwanted elements
                    for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', '.ad', '.advertisement', '.social-share']):
                        if element:
                            element.decompose()
                    
                    # Find article content
                    article = None
                    
                    # Try different article selectors
                    for selector in ['article', '.article', '.post', '.story', 'main', '.main-content']:
                        articles = soup.select(selector)
                        if articles:
                            article = articles[0]
                            break
                    
                    if article:
                        # Extract title
                        title = None
                        for title_tag in ['h1', 'h2', '.title', '.article-title']:
                            title_elem = article.select_one(title_tag)
                            if title_elem:
                                title = title_elem.get_text().strip()
                                break
                        
                        # Extract content
                        content_parts = []
                        
                        # Try to get article body
                        body_selectors = [
                            '.article-body',
                            '.story-body',
                            '.post-content',
                            '.content',
                            'article p',
                            '.article p',
                            '.story p'
                        ]
                        
                        for selector in body_selectors:
                            paragraphs = article.select(selector)
                            if paragraphs:
                                for p in paragraphs:
                                    text = p.get_text().strip()
                                    if len(text.split()) > 10:  # Only include substantial paragraphs
                                        content_parts.append(text)
                                break
                        
                        # If no content found through selectors, try getting all paragraphs
                        if not content_parts:
                            paragraphs = article.find_all('p')
                            for p in paragraphs:
                                text = p.get_text().strip()
                                if len(text.split()) > 10:
                                    content_parts.append(text)
                        
                        # Combine content
                        if title and content_parts:
                            content = ' '.join(content_parts)
                            content = clean_text(content)
                            
                            # Ensure appropriate content length (200-350 words)
                            word_count = len(content.split())
                            if 200 <= word_count <= 350:
                                return {
                                    'title': clean_text(title),
                                    'content': content
                                }
                            elif word_count > 350:
                                words = content.split()[:350]
                                content = ' '.join(words)
                                # Add the rest of the current sentence
                                if not content.endswith('.'):
                                    remaining = ' '.join(words[350:])
                                    next_period = remaining.find('.')
                                    if next_period != -1:
                                        content += remaining[:next_period + 1]
                                return {
                                    'title': clean_text(title),
                                    'content': content
                                }
            
            except Exception as e:
                print(f"Error fetching from {site}: {e}")
                continue
        
        return None
        
    except Exception as e:
        print(f"Error in web search: {e}")
        return None

def clean_text(text):
    """Clean and format text content"""
    # Remove extra whitespace
    text = ' '.join(text.split())
    # Remove URLs
    text = re.sub(r'http\S+|www.\S+', '', text)
    # Remove special characters
    text = re.sub(r'[^\w\s.,!?-]', ' ', text)
    # Clean up spaces
    text = ' '.join(text.split())
    return text

def translate_and_extract_vocabulary(title, content):
    """Translate text and extract vocabulary using Gemini"""
    try:
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        Translate this English article and extract TOEIC vocabulary:

        Title: {title}
        Content: {content}

        Format the response as JSON:
        {{
            "title_ja": "Japanese title",
            "content_ja": "Japanese content",
            "vocabulary": [
                {{
                    "word": "English word",
                    "meaning": "Japanese meaning",
                    "example": "Example sentence from the article",
                    "part_of_speech": "品詞 (例: 動詞、名詞、形容詞)",
                    "level": "TOEIC level (例: 400-600, 600-800, 800+)"
                }}
            ]
        }}

        Requirements:
        1. Natural Japanese translation
        2. Extract 10 TOEIC-level vocabulary words
        3. Use actual sentences from the article as examples
        4. Focus on business and technical vocabulary
        5. Include a mix of different difficulty levels
        6. Add part of speech for each word
        """

        response = model.generate_content(prompt)
        if not response or not response.text:
            return None

        # Parse the response
        response_text = response.text.strip()
        response_text = response_text.replace('```json', '').replace('```', '').strip()
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"Error parsing translation JSON: {e}")
            return None

    except Exception as e:
        print(f"Error in translation: {e}")
        return None

def process_news_article(category):
    """Process a news article: search, translate, and extract vocabulary"""
    try:
        # Search for article
        article = search_web_articles(category)
        if not article:
            return None

        # Translate and extract vocabulary
        result = translate_and_extract_vocabulary(article['title'], article['content'])
        if not result:
            return None

        # Combine all information
        return {
            'category': category,
            'title_en': article['title'],
            'content_en': article['content'],
            'title_ja': result['title_ja'],
            'content_ja': result['content_ja'],
            'vocabulary': result['vocabulary']
        }

    except Exception as e:
        print(f"Error processing article: {e}")
        return None
