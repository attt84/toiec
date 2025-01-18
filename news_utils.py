import os
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

def get_news_prompt(category):
    """Get category-specific prompt for news generation"""
    prompts = {
        'IT': """
        Create a technology news article about one of these trending topics:
        - Artificial Intelligence and Machine Learning
        - Cloud Computing and Digital Transformation
        - Cybersecurity and Privacy
        - Mobile Technology and 5G
        - Internet of Things (IoT)

        Requirements:
        1. Use TOEIC level vocabulary (400-800)
        2. Length: 200-350 words
        3. Include technical terms but explain them clearly
        4. Focus on business impact and practical applications
        """,
        
        'Business': """
        Create a business news article about one of these topics:
        - Global Market Trends
        - Corporate Strategy and Innovation
        - International Trade
        - Economic Policy
        - Business Leadership

        Requirements:
        1. Use TOEIC level vocabulary (400-800)
        2. Length: 200-350 words
        3. Include business terminology but keep it accessible
        4. Focus on real-world business implications
        """,
        
        'Science': """
        Create a science news article about one of these topics:
        - Medical Research and Healthcare
        - Environmental Science and Climate
        - Space Exploration
        - Biotechnology
        - Scientific Discoveries

        Requirements:
        1. Use TOEIC level vocabulary (400-800)
        2. Length: 200-350 words
        3. Explain scientific concepts in simple terms
        4. Focus on practical applications and societal impact
        """
    }
    return prompts.get(category, prompts['IT'])

def get_vocabulary_prompt(text):
    """Get prompt for vocabulary extraction"""
    return f"""
    Extract 10 important TOEIC vocabulary words from this text:
    {text}

    For each word, provide:
    1. The word itself
    2. Its meaning in Japanese
    3. Part of speech (noun, verb, adjective, etc.)
    4. TOEIC level (400-600, 600-800, 800+)
    5. Example sentence from the text or a similar context

    Format the output as a JSON array with these keys:
    [
        {{
            "word": "example",
            "meaning": "例",
            "part_of_speech": "noun",
            "level": "400-600",
            "example": "This is an example sentence."
        }},
        ...
    ]

    Requirements:
    1. Choose words that are commonly used in TOEIC
    2. Provide natural Japanese translations
    3. Make sure example sentences are clear and relevant
    4. Include a mix of different parts of speech
    5. Focus on business, technology, and academic vocabulary
    """

def process_news_article(category):
    """Generate a news article with vocabulary"""
    try:
        model = genai.GenerativeModel('gemini-pro')
        
        # Generate English article
        news_prompt = get_news_prompt(category)
        news_response = model.generate_content(news_prompt)
        if not news_response or not news_response.text:
            return None
            
        content_en = news_response.text.strip()
        
        # Generate title based on content
        title_prompt = f"""
        Create a concise and engaging title for this article:
        {content_en}
        
        Requirements:
        1. Maximum 10 words
        2. Capture the main point
        3. Use active voice
        4. Include a key term if relevant
        """
        
        title_response = model.generate_content(title_prompt)
        if not title_response or not title_response.text:
            return None
            
        title_en = title_response.text.strip()
        
        # Translate title and content to Japanese
        translate_prompt = f"""
        Translate this English article to natural Japanese:
        
        Title: {title_en}
        
        Content:
        {content_en}
        
        Requirements:
        1. Keep the translation natural and fluid
        2. Maintain the technical accuracy
        3. Use appropriate Japanese business/technical terms
        4. Format the output as:
        Title: [Japanese title]
        
        Content:
        [Japanese content]
        """
        
        translate_response = model.generate_content(translate_prompt)
        if not translate_response or not translate_response.text:
            return None
            
        translation = translate_response.text.strip()
        
        # Extract title and content from translation
        translation_parts = translation.split('\n\n', 1)
        if len(translation_parts) != 2:
            return None
            
        title_ja = translation_parts[0].replace('Title:', '').strip()
        content_ja = translation_parts[1].replace('Content:', '').strip()
        
        # Extract vocabulary
        vocab_prompt = get_vocabulary_prompt(content_en)
        vocab_response = model.generate_content(vocab_prompt)
        if not vocab_response or not vocab_response.text:
            return None
            
        # Parse vocabulary JSON
        import json
        try:
            vocabulary = json.loads(vocab_response.text)
        except json.JSONDecodeError:
            vocabulary = []
        
        return {
            'category': category,
            'title_en': title_en,
            'content_en': content_en,
            'title_ja': title_ja,
            'content_ja': content_ja,
            'vocabulary': vocabulary
        }
        
    except Exception as e:
        print(f"Error in process_news_article: {e}")
        return None
