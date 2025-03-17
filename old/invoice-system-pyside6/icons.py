from PySide6.QtGui import QIcon, QPixmap, QColor, QPainter
from PySide6.QtCore import Qt, QSize


class StatusIcon:
    """ステータスアイコンを生成するクラス"""

    @staticmethod
    def create(status: str) -> QIcon:
        """ステータスに応じたアイコンを生成"""
        # アイコンのサイズ設定
        size = QSize(16, 16)
        pixmap = QPixmap(size)
        pixmap.fill(Qt.transparent)

        # 描画設定
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # ステータスに応じた色とスタイルの設定
        if status == "approved":
            # 承認済み: 緑色のチェックマーク
            color = QColor(76, 175, 80)  # Material Design Green
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(2, 2, 12, 12)

            # チェックマークを描画
            painter.setPen(Qt.white)
            painter.drawLine(4, 8, 7, 11)
            painter.drawLine(7, 11, 12, 5)

        elif status == "error":
            # エラー: 赤色の感嘆符
            color = QColor(244, 67, 54)  # Material Design Red
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(2, 2, 12, 12)

            # 感嘆符を描画
            painter.setPen(Qt.white)
            painter.drawLine(8, 4, 8, 9)
            painter.drawEllipse(7, 10, 2, 2)

        elif status == "pending":
            # 処理中: 青色の回転アイコン
            color = QColor(33, 150, 243)  # Material Design Blue
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(2, 2, 12, 12)

            # 回転アイコンを描画
            painter.setPen(Qt.white)
            painter.drawArc(4, 4, 8, 8, 0 * 16, 270 * 16)

        else:  # unconfirmed
            # 未確認: グレーの横線
            color = QColor(158, 158, 158)  # Material Design Grey
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(2, 2, 12, 12)

            # 横線を描画
            painter.setPen(Qt.white)
            painter.drawLine(4, 8, 12, 8)

        painter.end()
        return QIcon(pixmap)
