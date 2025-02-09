import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QRadioButton,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QGroupBox,
    QStatusBar,
    QGraphicsView,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QPixmap
from icons import StatusIcon


# ログ設定
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# ファイルハンドラの設定
file_handler = logging.FileHandler(log_dir / "invoice_system.log", encoding="utf-8")
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)

# コンソールハンドラの設定
console_handler = logging.StreamHandler()
console_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)

# ロガーの設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# 既存のハンドラをクリア（重複を防ぐため）
logging.getLogger().handlers.clear()


class DetailListItem(QListWidgetItem):
    def __init__(self, detail_data):
        super().__init__()
        self.detail_data = detail_data
        self.update_display()

    def update_display(self):
        # 明細行の表示形式を設定
        display_text = f"{self.detail_data['no']} {self.detail_data['customer']} - {self.detail_data['product']}\n"
        display_text += (
            f"{self.detail_data['quantity']} × ¥{self.detail_data['price']:,}"
        )
        self.setText(display_text)

        # ステータスに応じたアイコンを設定
        self.setIcon(StatusIcon.create(self.detail_data["status"]))


class InvoiceStructuringSystem(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.info("アプリケーションを起動しています...")
        self.setWindowTitle("請求書構造化システム")
        self.setMinimumSize(1280, 720)

        # メインウィジェットとレイアウトの設定
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # 左パネル（明細一覧）の設定
        left_panel = self._create_left_panel()
        main_layout.addWidget(left_panel)

        # 右パネル（詳細表示）の設定
        right_panel = self._create_right_panel()
        main_layout.addWidget(right_panel)

        # ステータスバーの設定
        self.statusBar().showMessage("準備完了")

        # サンプルデータの設定
        self._setup_sample_data()

    def _create_left_panel(self):
        left_panel = QWidget()
        left_panel.setFixedWidth(250)  # 幅を250pxに固定
        layout = QVBoxLayout(left_panel)

        # フィルターグループ
        filter_group = QGroupBox("フィルター")
        filter_layout = QVBoxLayout(filter_group)
        self.radio_all = QRadioButton("すべて")
        self.radio_unconfirmed = QRadioButton("未確認のみ")
        self.radio_all.setChecked(True)
        filter_layout.addWidget(self.radio_all)
        filter_layout.addWidget(self.radio_unconfirmed)
        layout.addWidget(filter_group)

        # 検索ボックス
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("顧客名または商品名で検索...")
        layout.addWidget(self.search_box)

        # 明細一覧
        self.detail_list = QListWidget()
        layout.addWidget(self.detail_list)

        # 選択状況と一括承認ボタン
        self.selection_info = QLabel("選択: 0/0件")
        layout.addWidget(self.selection_info)
        self.bulk_approve_btn = QPushButton("一括承認")
        self.bulk_approve_btn.clicked.connect(self._on_bulk_approve)
        layout.addWidget(self.bulk_approve_btn)

        # シグナル接続
        self.radio_all.toggled.connect(self._on_filter_changed)
        self.radio_unconfirmed.toggled.connect(self._on_filter_changed)
        self.search_box.textChanged.connect(self._on_search_text_changed)
        self.detail_list.itemSelectionChanged.connect(self._on_selection_changed)

        return left_panel

    def _on_filter_changed(self):
        """フィルター変更時の処理"""
        logger.info("フィルター条件が変更されました")
        self._apply_filters()

    def _on_search_text_changed(self, text: str):
        """検索テキスト変更時の処理"""
        logger.info(f"検索テキストが変更されました: {text}")
        self._apply_filters()

    def _on_selection_changed(self):
        """明細選択変更時の処理"""
        selected_items = self.detail_list.selectedItems()
        total_items = self.detail_list.count()
        self.selection_info.setText(f"選択: {len(selected_items)}/{total_items}件")

        if selected_items:
            item = selected_items[0]
            self._update_detail_view(item.detail_data)

    def _on_bulk_approve(self):
        """一括承認処理"""
        selected_items = self.detail_list.selectedItems()
        if not selected_items:
            logger.warning("承認対象の明細が選択されていません")
            return

        logger.info(f"{len(selected_items)}件の明細を一括承認します")
        for item in selected_items:
            item.detail_data["status"] = "approved"
            item.update_display()

    def _apply_filters(self):
        """フィルターとサーチを適用"""
        search_text = self.search_box.text().lower()
        show_unconfirmed_only = self.radio_unconfirmed.isChecked()

        for i in range(self.detail_list.count()):
            item = self.detail_list.item(i)
            detail = item.detail_data

            # 検索テキストでフィルタリング
            text_match = (
                search_text in detail["customer"].lower()
                or search_text in detail["product"].lower()
            )

            # 状態でフィルタリング
            status_match = (
                not show_unconfirmed_only or detail["status"] == "unconfirmed"
            )

            # アイテムの表示/非表示を設定
            item.setHidden(not (text_match and status_match))

    def _update_detail_view(self, detail_data: dict):
        """詳細表示の更新"""
        logger.info(f"明細詳細を表示: {detail_data['no']}")

        # グリッドをクリア
        self.data_grid.setRowCount(0)

        # データを表示
        fields = [
            ("明細番号", detail_data["no"]),
            ("顧客名", detail_data["customer"]),
            ("商品名", detail_data["product"]),
            ("数量", str(detail_data["quantity"])),
            ("単価", f"¥{detail_data['price']:,}"),
            ("税率", f"{detail_data['tax_rate']}%"),
            ("金額", f"¥{detail_data['quantity'] * detail_data['price']:,}"),
        ]

        for i, (label, value) in enumerate(fields):
            row = i // 2
            col = (i % 2) * 2

            self.data_grid.insertRow(row)
            self.data_grid.setItem(row, col, QTableWidgetItem(label))
            self.data_grid.setItem(row, col + 1, QTableWidgetItem(value))

    def _create_right_panel(self):
        right_panel = QWidget()
        layout = QVBoxLayout(right_panel)

        # ショートカット情報
        shortcut_label = QLabel("Alt+↑↓: 移動 Space: 選択 Enter: 承認")
        layout.addWidget(shortcut_label)

        # 明細行状態バー
        status_bar = QStatusBar()
        layout.addWidget(status_bar)

        # クロップ画像表示エリア
        self.image_view = QGraphicsView()
        self.image_view.setMinimumHeight(200)
        layout.addWidget(self.image_view)

        # 構造化データグリッド
        self.data_grid = QTableWidget()
        self.data_grid.setColumnCount(4)
        self.data_grid.setHorizontalHeaderLabels(["項目", "値", "項目", "値"])
        self.data_grid.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.data_grid)

        return right_panel

    def _setup_sample_data(self):
        # サンプルデータ
        sample_details = [
            {
                "id": "1",
                "no": "No.1",
                "customer": "顧客A",
                "product": "製品A",
                "quantity": 100,
                "price": 1000,
                "status": "approved",
                "tax_rate": 10,
                "stock": {
                    "carryover": 100,
                    "incoming": 50,
                    "outgoing": 30,
                    "balance": 120,
                },
            },
            {
                "id": "2",
                "no": "No.2",
                "customer": "顧客B",
                "product": "製品B",
                "quantity": 200,
                "price": 2000,
                "status": "error",
                "tax_rate": 10,
                "stock": {
                    "carryover": 150,
                    "incoming": 30,
                    "outgoing": 40,
                    "balance": 140,
                },
            },
        ]

        # 明細一覧にデータを追加
        for detail in sample_details:
            item = DetailListItem(detail)
            self.detail_list.addItem(item)


def main():
    try:
        logger.info("アプリケーションのメイン処理を開始します")
        app = QApplication(sys.argv)
        window = InvoiceStructuringSystem()
        window.show()
        logger.info("メインウィンドウを表示しました")
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"予期せぬエラーが発生しました: {e}", exc_info=True)


if __name__ == "__main__":
    main()
