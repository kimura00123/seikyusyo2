# 請求書構造化システム

## 概要
請求書PDFファイルから必要な情報を自動抽出し、L-NET売上管理システムで利用可能な形式に変換するシステムです。

## 機能
- PDF解析：請求書PDFからテキストと位置情報を抽出
- 構造化：抽出したテキストをJSON形式に変換
- バリデーション：抽出データの検証と正規化
- 画像化：請求書明細部分の画像抽出
- エクセル出力：構造化データの出力
- UI：請求書処理の操作・管理画面

## システム要件
- Python 3.10以上
- Windows 10以上

## 主要な依存関係
- PySide6: GUIフレームワーク
- FastAPI: WebフレームワークAPI
- PDFMiner.six: PDF解析
- PyMuPDF: PDF画像抽出
- Azure OpenAI API: テキスト構造化
- OpenPyXL: Excel操作

## セットアップ
1. Ryeのインストール
2. 依存関係のインストール
   ```powershell
   rye sync
   ```
3. 環境変数の設定
   ```powershell
   cp src/.env.example src/.env
   # .envファイルを編集して必要な値を設定
   ```

## 使用方法
1. バックエンドサーバーの起動
   ```powershell
   python src/startup.py
   ```

2. フロントエンドの起動
   ```powershell
   python invoice-system/main.py
   ```

## プロジェクト構成
```
takatuski/
├── src/                   # バックエンドソース
│   ├── api/              # APIエンドポイント
│   ├── core/            # コアロジック
│   ├── models/          # データモデル
│   └── utils/           # ユーティリティ
├── invoice-system/      # フロントエンド
└── tests/              # テストコード
    ├── unit/           # ユニットテスト
    ├── integration/    # 統合テスト
    └── e2e/           # E2Eテスト
```

## 開発環境
- IDE: Visual Studio Code
- パッケージ管理: Rye
- テストフレームワーク: pytest
- コード品質: flake8, black, isort

## ライセンス
All rights reserved.
