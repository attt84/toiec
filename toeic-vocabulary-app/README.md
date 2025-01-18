# TOEIC News & Vocabulary App

TOEICの学習に役立つニュース記事と語彙学習アプリケーション。

## 機能

- AI記事生成：最新のニュースを自動で取得し、TOEICレベルに適した記事を生成
- バイリンガル表示：英語と日本語で記事を表示
- インタラクティブ翻訳：テキストを選択するだけで即座に翻訳
- 語彙学習：各記事から重要な単語を抽出し、品詞、レベル、例文を提供

## 技術スタック

- Backend: Flask (Python)
- Database: SQLite
- AI: Google Gemini API
- Frontend: Bootstrap 5

## 環境変数

以下の環境変数を`.env`ファイルに設定してください：

```
GOOGLE_API_KEY=your_api_key_here
```

## ローカルでの実行方法

1. リポジトリをクローン
```bash
git clone [repository-url]
cd toeic-vocabulary-app
```

2. 依存関係をインストール
```bash
pip install -r requirements.txt
```

3. アプリケーションを実行
```bash
python app.py
```

4. ブラウザで http://localhost:8080 にアクセス

## デプロイ

このアプリケーションは[Render](https://render.com)にデプロイできます。

1. Renderでアカウントを作成
2. 新しいWebサービスを作成
3. このリポジトリを連携
4. 環境変数`GOOGLE_API_KEY`を設定
5. デプロイを実行

## ライセンス

MIT License
