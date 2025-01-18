from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from news_utils import process_news_article
from markupsafe import Markup
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///news.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Add nl2br filter
@app.template_filter('nl2br')
def nl2br(value):
    return Markup(value.replace('\n', '<br>\n'))

# Models
class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    title_en = db.Column(db.String(200), nullable=False)
    content_en = db.Column(db.Text, nullable=False)
    title_ja = db.Column(db.String(200), nullable=False)
    content_ja = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    vocabulary = db.relationship('Vocabulary', backref='article', lazy=True)

class Vocabulary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), nullable=False)
    meaning = db.Column(db.String(200), nullable=False)
    example = db.Column(db.Text, nullable=False)
    part_of_speech = db.Column(db.String(50))
    level = db.Column(db.String(50))
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)

# Create database tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    articles = Article.query.order_by(Article.created_at.desc()).all()
    return render_template('index.html', articles=articles)

@app.route('/article/<int:id>')
def article(id):
    article = Article.query.get_or_404(id)
    return render_template('article.html', article=article)

@app.route('/generate', methods=['POST'])
def generate_article():
    try:
        category = request.form.get('category')
        if not category:
            flash('カテゴリーを選択してください。', 'error')
            return redirect(url_for('index'))

        # Generate article
        result = process_news_article(category)
        if not result:
            flash('記事データが不完全です。もう一度お試しください。', 'error')
            return redirect(url_for('index'))

        # Create new article
        article = Article(
            category=result['category'],
            title_en=result['title_en'],
            content_en=result['content_en'],
            title_ja=result['title_ja'],
            content_ja=result['content_ja']
        )
        db.session.add(article)
        db.session.flush()  # Get article ID before committing

        # Add vocabulary items
        for vocab_data in result['vocabulary']:
            vocab = Vocabulary(
                word=vocab_data['word'],
                meaning=vocab_data['meaning'],
                example=vocab_data['example'],
                part_of_speech=vocab_data.get('part_of_speech', ''),
                level=vocab_data.get('level', ''),
                article_id=article.id
            )
            db.session.add(vocab)

        db.session.commit()
        flash('記事が生成されました。', 'success')
        return redirect(url_for('article', id=article.id))

    except Exception as e:
        db.session.rollback()
        print(f"Error generating article: {e}")
        flash('記事の生成中にエラーが発生しました。', 'error')
        return redirect(url_for('index'))

@app.route('/translate', methods=['POST'])
def translate_text():
    """Translate selected text using Gemini API"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400

        # Create translation prompt
        prompt = f"""
        Translate this English text to Japanese:
        "{text}"
        
        Requirements:
        1. Natural Japanese translation
        2. Keep it concise
        3. Return ONLY the translation, no explanations
        """
        
        # Get translation
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        if not response or not response.text:
            return jsonify({'error': 'Translation failed'}), 500
            
        translation = response.text.strip()
        # Remove any quotes if present
        translation = translation.strip('"\'')
        
        return jsonify({'translation': translation})
        
    except Exception as e:
        print(f"Translation error: {e}")
        return jsonify({'error': 'Translation failed'}), 500

if __name__ == '__main__':
    # Allow access from any device in the network
    # Note: Debug mode is disabled for security in production
    app.run(host='0.0.0.0', port=8080, debug=False)
