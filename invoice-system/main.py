import sys
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
        selection_info = QLabel("選択: 0/0件")
        layout.addWidget(selection_info)
        bulk_approve_btn = QPushButton("一括承認")
        layout.addWidget(bulk_approve_btn)

        return left_panel

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
    app = QApplication(sys.argv)
    window = InvoiceStructuringSystem()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
