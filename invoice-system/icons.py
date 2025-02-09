from PySide6.QtGui import QIcon, QPainter, QColor, QPixmap
from PySide6.QtCore import Qt, QSize


class StatusIcon:
    """ステータスアイコンを生成するクラス"""

    ICON_SIZE = 16  # アイコンサイズ（ピクセル）

    # ステータスごとの色定義
    COLORS = {
        "approved": QColor(76, 175, 80),  # 緑色
        "error": QColor(244, 67, 54),  # 赤色
        "pending": QColor(33, 150, 243),  # 青色
        "unconfirmed": QColor(158, 158, 158),  # グレー色
    }

    @classmethod
    def create(cls, status: str) -> QIcon:
        """
        指定されたステータスに対応するアイコンを生成

        Args:
            status: ステータス文字列（"approved", "error", "pending", "unconfirmed"）

        Returns:
            QIcon: 生成されたアイコン
        """
        # ピクスマップの作成
        pixmap = QPixmap(cls.ICON_SIZE, cls.ICON_SIZE)
        pixmap.fill(Qt.transparent)  # 背景を透明に

        # ペインターの設定
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)  # アンチエイリアシング有効化

        # 色の取得（未定義の場合はunconfirmedの色を使用）
        color = cls.COLORS.get(status, cls.COLORS["unconfirmed"])

        # アイコンの描画
        if status == "approved":
            cls._draw_check_mark(painter, color)
        elif status == "error":
            cls._draw_warning(painter, color)
        elif status == "pending":
            cls._draw_pending(painter, color)
        else:  # unconfirmed
            cls._draw_minus(painter, color)

        painter.end()
        return QIcon(pixmap)

    @classmethod
    def _draw_check_mark(cls, painter: QPainter, color: QColor):
        """チェックマークを描画"""
        painter.setPen(color)
        painter.setBrush(Qt.NoBrush)
        painter.drawLine(4, 8, 7, 11)  # チェックマークの左部分
        painter.drawLine(7, 11, 12, 5)  # チェックマークの右部分

    @classmethod
    def _draw_warning(cls, painter: QPainter, color: QColor):
        """警告マークを描画"""
        painter.setPen(color)
        painter.setBrush(Qt.NoBrush)
        # 三角形を描画
        painter.drawLine(8, 4, 4, 12)  # 左辺
        painter.drawLine(4, 12, 12, 12)  # 底辺
        painter.drawLine(12, 12, 8, 4)  # 右辺
        # 感嘆符を描画
        painter.drawLine(8, 7, 8, 9)  # 上部
        painter.drawPoint(8, 11)  # 下部の点

    @classmethod
    def _draw_pending(cls, painter: QPainter, color: QColor):
        """処理中マークを描画"""
        painter.setPen(color)
        painter.setBrush(Qt.NoBrush)
        # 円弧を描画（更新中を表す）
        painter.drawArc(4, 4, 8, 8, 0, 270 * 16)  # 角度は16分の1度単位

    @classmethod
    def _draw_minus(cls, painter: QPainter, color: QColor):
        """マイナスマークを描画"""
        painter.setPen(color)
        painter.setBrush(Qt.NoBrush)
        painter.drawLine(4, 8, 12, 8)  # 水平線
