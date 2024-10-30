from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QColor, QFont, QPainter
from PyQt5.QtWidgets import QPlainTextEdit, QTextEdit, QWidget

class LineNumberArea(QWidget):
    def __init__(self, parent=None):
        super(LineNumberArea, self).__init__(parent)
        self.line_number_font = QFont("Consolas", 8)
        self.light_background_color = QColor("#C0C0C0")  # Цвет для светлой темы
        self.dark_background_color = QColor("#2A2A2A")  # Цвет для темной темы
        self.light_font_color = QColor("#000000")  # Цвет нумерации для светлой темы
        self.dark_font_color = QColor("#FFFFFF")  # Цвет нумерации для темной темы
        self.is_dark_mode = False  # Устанавливаем флаг для темной темы
        self.rightRectColor = None  # Переменная для кастомного цвета

    def setRightRectColor(self, color: QColor):
        # Установка кастомного цвета для правого текстового поля
        self.rightRectColor = color
        self.update()  # Обновляем область нумерации

    def setDarkMode(self, dark_mode: bool):
        self.is_dark_mode = dark_mode
        self.update()  # Обновляем область нумерации

    def sizeHint(self):
        return self.parent().lineNumberAreaSize()  # Убедитесь, что метод lineNumberAreaSize() определен в родительском классе

    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Если установлен кастомный цвет для правого поля
        if self.rightRectColor:
            background_color = self.rightRectColor
        else:
            background_color = self.dark_background_color if self.is_dark_mode else self.light_background_color
        
        painter.fillRect(event.rect(), background_color)
        painter.setPen(self.dark_font_color if self.is_dark_mode else self.light_font_color)

        parent = self.parent()
        block = parent.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = parent.blockBoundingGeometry(block).translated(parent.contentOffset()).top()
        bottom = top + parent.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                rect = QRect(0, int(top), self.width() - 6, int(parent.fontMetrics().height()))
                painter.drawText(rect, Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + parent.blockBoundingRect(block).height()
            blockNumber += 1

class NumberedTextEdit(QPlainTextEdit):
    def __init__(self, parent=None):
        super(NumberedTextEdit, self).__init__(parent)
        self.lineNumberArea = LineNumberArea(self)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)

        self.setLineWrapMode(QPlainTextEdit.NoWrap)

    def lineNumberAreaWidth(self):
        digits = len(str(self.blockCount()))
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits + 4
        return space

    def updateLineNumberAreaWidth(self):
        self.setViewportMargins(self.lineNumberAreaWidth() + 4, 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberAreaWidth() + 4, rect.height())

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth()

    def highlightCurrentLine(self):
        extraSelections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            lineColor = QColor(Qt.yellow).lighter(160)
            selection.format.setBackground(lineColor)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

    def resizeEvent(self, event):
        super(NumberedTextEdit, self).resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(cr.x(), cr.y(), self.lineNumberAreaWidth() + 4, cr.height())
        self.setViewportMargins(self.lineNumberAreaWidth() + 4, 0, 0, 0)