from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QColor, QFont, QPainter, QTextFormat
from PyQt5.QtWidgets import QPlainTextEdit, QTextEdit, QWidget

class LineNumberArea(QWidget):
    def __init__(self, parent=None):
        super(LineNumberArea, self).__init__(parent)
        self.line_number_font = QFont("Consolas", 8)

    def sizeHint(self):
        return self.editor.lineNumberAreaSize()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(event.rect(), Qt.lightGray)
        painter.setFont(self.line_number_font)
        block = self.parent().firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.parent().blockBoundingGeometry(block).translated(self.parent().contentOffset()).top()
        bottom = top + self.parent().blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(Qt.black)
                rect = QRect(0, int(top), self.width() - 6, int(self.parent().fontMetrics().height()))
                painter.drawText(rect, Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + self.parent().blockBoundingRect(block).height()
            blockNumber += 1

class NumberedTextEdit(QPlainTextEdit):
    def __init__(self, parent=None):
        super(NumberedTextEdit, self).__init__(parent)
        self.lineNumberArea = LineNumberArea(self)
        self.lineNumberArea.setStyleSheet("background-color: lightgray; border: 12px solid gray")
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