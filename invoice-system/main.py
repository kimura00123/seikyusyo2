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
from PySide6.QtCore import Qt, Signal, QSize, QKeyCombination
from PySide6.QtGui import QIcon, QPixmap, QKeySequence, QShortcut, QColor
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
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("準備完了")

        # サンプルデータの設定
        self._setup_sample_data()

    def _create_left_panel(self):
        left_panel = QWidget()
        left_panel.setFixedWidth(250)  # 幅を250pxに固定
        layout = QVBoxLayout(left_panel)

        # フィルターグループ
        filter_group = QGroupBox("フィルター")
        filter_group.setStyleSheet(
            """
            QGroupBox {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                margin-top: 1em;
                padding-top: 0.5em;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px;
                background: white;
                color: #1976d2;
                font-weight: bold;
            }
        """
        )
        filter_layout = QVBoxLayout(filter_group)
        filter_layout.setContentsMargins(8, 8, 8, 8)
        filter_layout.setSpacing(4)

        # ラジオボタンのスタイル設定
        radio_style = """
            QRadioButton {
                padding: 4px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #bdbdbd;
                border-radius: 8px;
            }
            QRadioButton::indicator:checked {
                border: 2px solid #1976d2;
                background-color: #1976d2;
            }
            QRadioButton::indicator:unchecked:hover {
                border: 2px solid #1976d2;
            }
        """

        self.radio_all = QRadioButton("すべて")
        self.radio_unconfirmed = QRadioButton("未確認のみ")
        self.radio_all.setStyleSheet(radio_style)
        self.radio_unconfirmed.setStyleSheet(radio_style)
        self.radio_all.setChecked(True)

        filter_layout.addWidget(self.radio_all)
        filter_layout.addWidget(self.radio_unconfirmed)
        layout.addWidget(filter_group)

        # 検索ボックス
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("顧客名または商品名で検索...")
        self.search_box.setStyleSheet(
            """
            QLineEdit {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 8px;
                padding-left: 32px;  /* アイコンのスペース */
                background: white;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #1976d2;
                background: #e3f2fd;
            }
            QLineEdit:hover {
                border: 1px solid #1976d2;
            }
        """
        )

        # 検索ボックスコンテナ（アイコン表示用）
        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(8, 0, 8, 0)
        search_layout.setSpacing(0)

        # 検索アイコン
        search_icon = QLabel()
        search_icon.setFixedSize(16, 16)
        search_icon.setStyleSheet(
            """
            QLabel {
                color: #757575;
            }
        """
        )
        search_icon.setText("🔍")

        search_layout.addWidget(search_icon)
        search_layout.addWidget(self.search_box)
        layout.addWidget(search_container)

        # 明細一覧
        self.detail_list = QListWidget()
        self.detail_list.setStyleSheet(
            """
            QListWidget::item {
                border-bottom: 1px solid #e0e0e0;
                padding: 4px;
            }
            QListWidget::item:selected {
                background: #e3f2fd;
                color: #000000;
            }
            QListWidget::item:hover {
                background: #f5f5f5;
            }
        """
        )
        layout.addWidget(self.detail_list)

        # 選択状況
        selection_container = QWidget()
        selection_container.setStyleSheet(
            """
            QWidget {
                background: #f5f5f5;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 4px;
            }
        """
        )
        selection_layout = QHBoxLayout(selection_container)
        selection_layout.setContentsMargins(8, 4, 8, 4)

        # 選択アイコン
        selection_icon = QLabel("✓")
        selection_icon.setStyleSheet(
            """
            QLabel {
                color: #1976d2;
                font-weight: bold;
                font-size: 14px;
            }
        """
        )
        selection_icon.setFixedSize(16, 16)

        # 選択情報
        self.selection_info = QLabel("選択: 0/0件")
        self.selection_info.setStyleSheet(
            """
            QLabel {
                color: #424242;
                font-size: 13px;
            }
        """
        )

        selection_layout.addWidget(selection_icon)
        selection_layout.addWidget(self.selection_info)
        layout.addWidget(selection_container)

        # 一括承認ボタン
        self.bulk_approve_btn = QPushButton("一括承認")
        self.bulk_approve_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
            QPushButton:disabled {
                background-color: #bbdefb;
                color: #90caf9;
            }
        """
        )
        self.bulk_approve_btn.clicked.connect(self._on_bulk_approve)
        self.bulk_approve_btn.setEnabled(False)  # 初期状態は無効
        layout.addWidget(self.bulk_approve_btn)

        # シグナル接続
        self.radio_all.toggled.connect(self._on_filter_changed)
        self.radio_unconfirmed.toggled.connect(self._on_filter_changed)
        self.search_box.textChanged.connect(self._on_search_text_changed)
        self.detail_list.itemSelectionChanged.connect(self._on_selection_changed)

        # ショートカットの設定
        self._setup_shortcuts()

        return left_panel

    def _setup_shortcuts(self):
        """キーボードショートカットの設定"""
        # 移動ショートカット
        QShortcut(
            QKeySequence(Qt.AltModifier | Qt.Key_Up), self, self._select_previous_item
        )
        QShortcut(
            QKeySequence(Qt.AltModifier | Qt.Key_Down), self, self._select_next_item
        )

        # 選択ショートカット
        QShortcut(QKeySequence(Qt.Key_Space), self, self._toggle_current_item_selection)
        QShortcut(QKeySequence(Qt.AltModifier | Qt.Key_A), self, self._select_all_items)
        QShortcut(
            QKeySequence(Qt.AltModifier | Qt.Key_D), self, self._deselect_all_items
        )

        # 承認ショートカット
        QShortcut(QKeySequence(Qt.Key_Return), self, self._approve_current_item)
        QShortcut(
            QKeySequence(Qt.AltModifier | Qt.Key_Return), self, self._on_bulk_approve
        )

    def _select_previous_item(self):
        """前の明細を選択"""
        current_row = self.detail_list.currentRow()
        if current_row > 0:
            self.detail_list.setCurrentRow(current_row - 1)
            self.status_bar.showMessage("前の明細に移動しました")
            logger.info("前の明細に移動しました")

    def _select_next_item(self):
        """次の明細を選択"""
        current_row = self.detail_list.currentRow()
        if current_row < self.detail_list.count() - 1:
            self.detail_list.setCurrentRow(current_row + 1)
            self.status_bar.showMessage("次の明細に移動しました")
            logger.info("次の明細に移動しました")

    def _toggle_current_item_selection(self):
        """現在の明細の選択状態を切り替え"""
        current_item = self.detail_list.currentItem()
        if current_item:
            current_item.setSelected(not current_item.isSelected())
            no = current_item.detail_data["no"]
            status = "選択" if current_item.isSelected() else "選択解除"
            self.status_bar.showMessage(f"明細 {no} を{status}しました")
            logger.info(f"明細の選択状態を切り替えました: {no}")

    def _select_all_items(self):
        """すべての明細を選択"""
        for i in range(self.detail_list.count()):
            self.detail_list.item(i).setSelected(True)
        self.status_bar.showMessage("すべての明細を選択しました")
        logger.info("すべての明細を選択しました")

    def _deselect_all_items(self):
        """すべての明細の選択を解除"""
        self.detail_list.clearSelection()
        self.status_bar.showMessage("すべての明細の選択を解除しました")
        logger.info("すべての明細の選択を解除しました")

    def _approve_current_item(self):
        """現在の明細を承認"""
        current_item = self.detail_list.currentItem()
        if current_item:
            current_item.detail_data["status"] = "approved"
            current_item.update_display()
            no = current_item.detail_data["no"]
            self.status_bar.showMessage(f"明細 {no} を承認しました")
            logger.info(f"明細を承認しました: {no}")

    def _on_filter_changed(self):
        """フィルター変更時の処理"""
        show_unconfirmed = self.radio_unconfirmed.isChecked()
        status = "未確認のみ表示" if show_unconfirmed else "すべて表示"
        self.status_bar.showMessage(f"フィルター: {status}")
        logger.info(f"フィルター条件が変更されました: {status}")
        self._apply_filters()

    def _on_search_text_changed(self, text: str):
        """検索テキスト変更時の処理"""
        if text:
            self.status_bar.showMessage(f"検索: {text}")
        else:
            self.status_bar.showMessage("検索クリア")
        logger.info(f"検索テキストが変更されました: {text}")
        self._apply_filters()

    def _on_selection_changed(self):
        """明細選択変更時の処理"""
        selected_items = self.detail_list.selectedItems()
        total_items = self.detail_list.count()
        self.selection_info.setText(f"選択: {len(selected_items)}/{total_items}件")

        # 一括承認ボタンの有効/無効を切り替え
        self.bulk_approve_btn.setEnabled(len(selected_items) > 0)

        if selected_items:
            item = selected_items[0]
            self._update_detail_view(item.detail_data)

    def _on_bulk_approve(self):
        """一括承認処理"""
        selected_items = self.detail_list.selectedItems()
        if not selected_items:
            self.status_bar.showMessage("承認対象の明細が選択されていません")
            logger.warning("承認対象の明細が選択されていません")
            self.bulk_approve_btn.setEnabled(False)
            return

        count = len(selected_items)
        logger.info(f"{count}件の明細を一括承認します")
        for item in selected_items:
            item.detail_data["status"] = "approved"
            item.update_display()

        self.status_bar.showMessage(f"{count}件の明細を一括承認しました")

    def _apply_filters(self):
        """フィルターとサーチを適用"""
        search_text = self.search_box.text().lower()
        show_unconfirmed_only = self.radio_unconfirmed.isChecked()

        visible_count = 0
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
            is_visible = text_match and status_match
            item.setHidden(not is_visible)
            if is_visible:
                visible_count += 1

        # フィルター結果をステータスバーに表示
        if search_text or show_unconfirmed_only:
            self.status_bar.showMessage(f"フィルター結果: {visible_count}件表示")

    def _update_detail_view(self, detail_data: dict):
        """詳細表示の更新"""
        logger.info(f"明細詳細を表示: {detail_data['no']}")
        self.status_bar.showMessage(f"明細 {detail_data['no']} の詳細を表示中")

        # グリッドをクリア
        self.data_grid.setRowCount(0)

        # 基本情報
        fields = [
            ("明細番号", detail_data["no"]),
            ("顧客名", detail_data["customer"]),
            ("商品名", detail_data["product"]),
            ("数量", str(detail_data["quantity"])),
            ("単価", f"¥{detail_data['price']:,}"),
            ("税率", f"{detail_data['tax_rate']}%"),
            ("金額", f"¥{detail_data['quantity'] * detail_data['price']:,}"),
        ]

        # 在庫情報
        stock = detail_data["stock"]
        stock_fields = [
            ("繰越在庫", str(stock["carryover"])),
            ("入庫数", str(stock["incoming"])),
            ("出庫数", str(stock["outgoing"])),
            ("在庫残高", str(stock["balance"])),
        ]
        fields.extend(stock_fields)

        # グリッドにデータを表示
        for i, (label, value) in enumerate(fields):
            row = i // 2
            col = (i % 2) * 2

            # 行の追加が必要な場合
            if row >= self.data_grid.rowCount():
                self.data_grid.insertRow(row)

            # セルの作成と設定
            label_item = QTableWidgetItem(label)
            value_item = QTableWidgetItem(value)

            # ラベルセルは編集不可に設定
            label_item.setFlags(label_item.flags() & ~Qt.ItemIsEditable)

            # 在庫情報のセルの背景色を設定
            if label in ["繰越在庫", "入庫数", "出庫数", "在庫残高"]:
                label_item.setBackground(QColor(240, 240, 255))  # 薄い青色
                value_item.setBackground(QColor(240, 240, 255))

            self.data_grid.setItem(row, col, label_item)
            self.data_grid.setItem(row, col + 1, value_item)

    def _create_right_panel(self):
        right_panel = QWidget()
        layout = QVBoxLayout(right_panel)

        # ショートカット情報
        shortcut_container = QWidget()
        shortcut_container.setStyleSheet(
            """
            QWidget {
                background: #e8f5e9;
                border: 1px solid #c8e6c9;
                border-radius: 4px;
                padding: 8px;
            }
        """
        )
        shortcut_layout = QHBoxLayout(shortcut_container)
        shortcut_layout.setContentsMargins(8, 4, 8, 4)

        # キーボードアイコン
        keyboard_icon = QLabel("⌨")
        keyboard_icon.setStyleSheet(
            """
            QLabel {
                color: #43a047;
                font-size: 14px;
            }
        """
        )
        keyboard_icon.setFixedSize(16, 16)

        # ショートカット情報
        shortcut_label = QLabel("Alt+↑↓: 移動  Space: 選択  Enter: 承認")
        shortcut_label.setStyleSheet(
            """
            QLabel {
                color: #2e7d32;
                font-size: 13px;
            }
        """
        )

        shortcut_layout.addWidget(keyboard_icon)
        shortcut_layout.addWidget(shortcut_label)
        layout.addWidget(shortcut_container)

        # 明細行状態バー
        status_bar = QStatusBar()
        layout.addWidget(status_bar)

        # クロップ画像表示エリア
        self.image_view = QGraphicsView()
        self.image_view.setMinimumHeight(200)
        self.image_view.setStyleSheet(
            """
            QGraphicsView {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background: #fafafa;
            }
        """
        )

        # 画像表示エリアのプレースホルダー
        placeholder_container = QWidget()
        placeholder_container.setStyleSheet(
            """
            QWidget {
                background: transparent;
            }
        """
        )
        placeholder_layout = QVBoxLayout(placeholder_container)
        placeholder_layout.setAlignment(Qt.AlignCenter)

        # プレースホルダーアイコン
        placeholder_icon = QLabel("📄")
        placeholder_icon.setStyleSheet(
            """
            QLabel {
                color: #bdbdbd;
                font-size: 32px;
            }
        """
        )
        placeholder_layout.addWidget(placeholder_icon, alignment=Qt.AlignCenter)

        # プレースホルダーテキスト
        placeholder_text = QLabel("明細画像")
        placeholder_text.setStyleSheet(
            """
            QLabel {
                color: #757575;
                font-size: 13px;
            }
        """
        )
        placeholder_layout.addWidget(placeholder_text, alignment=Qt.AlignCenter)

        # プレースホルダーをビューに設定
        self.image_view.setScene(QGraphicsScene())
        self.image_view.scene().addWidget(placeholder_container)
        layout.addWidget(self.image_view)

        # 構造化データグリッド
        self.data_grid = QTableWidget()
        self.data_grid.setColumnCount(4)
        self.data_grid.setHorizontalHeaderLabels(["項目", "値", "項目", "値"])
        self.data_grid.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.data_grid.setStyleSheet(
            """
            QTableWidget {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background: white;
            }
            QHeaderView::section {
                background: #f5f5f5;
                padding: 8px;
                border: none;
                border-right: 1px solid #e0e0e0;
                border-bottom: 1px solid #e0e0e0;
                font-weight: bold;
                color: #424242;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
                border-bottom: 1px solid #e0e0e0;
            }
            QTableWidget::item:selected {
                background: #e3f2fd;
                color: #000000;
            }
        """
        )
        layout.addWidget(self.data_grid)

        return right_panel

    def _setup_sample_data(self):
        # サンプルデータ（ステータスのバリエーションを含む）
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
            {
                "id": "3",
                "no": "No.3",
                "customer": "顧客C",
                "product": "製品C",
                "quantity": 150,
                "price": 1500,
                "status": "unconfirmed",
                "tax_rate": 8,
                "stock": {
                    "carryover": 80,
                    "incoming": 40,
                    "outgoing": 20,
                    "balance": 100,
                },
            },
            {
                "id": "4",
                "no": "No.4",
                "customer": "顧客D",
                "product": "製品D",
                "quantity": 300,
                "price": 3000,
                "status": "pending",
                "tax_rate": 10,
                "stock": {
                    "carryover": 200,
                    "incoming": 100,
                    "outgoing": 50,
                    "balance": 250,
                },
            },
            {
                "id": "5",
                "no": "No.5",
                "customer": "顧客E",
                "product": "製品E",
                "quantity": 250,
                "price": 2500,
                "status": "unconfirmed",
                "tax_rate": 8,
                "stock": {
                    "carryover": 120,
                    "incoming": 60,
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
