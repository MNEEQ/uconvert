import re
from PyQt5.QtWidgets import QComboBox
from widgets.numbered_text_edit import NumberedTextEdit

class FindReplace:
    def __init__(self, text_edit: NumberedTextEdit, combo_box_find: QComboBox, combo_box_replace: QComboBox):
        self.text_edit = text_edit
        self.combo_box_find = combo_box_find
        self.combo_box_replace = combo_box_replace
        self.current_find_index = -1  # Индекс текущего найденного слова

    def find_next(self):
        text_to_find = self.combo_box_find.currentText()
        if not text_to_find:
            return

        # Получаем текст из текстового поля
        text = self.text_edit.toPlainText()
        
        # Находим позиции всех вхождений
        positions = [i.start() for i in re.finditer(re.escape(text_to_find), text)]
        
        if positions:
            # Если индекс -1, это означает, что мы ищем первый элемент
            if self.current_find_index == -1:
                self.current_find_index = 0
            else:
                # Увеличиваем индекс, и если он выходит за пределы, сбрасываем его
                self.current_find_index = (self.current_find_index + 1) % len(positions)

            # Снимаем выделение с предыдущего слова
            cursor = self.text_edit.textCursor()
            cursor.setPosition(positions[self.current_find_index])
            cursor.movePosition(cursor.Right, cursor.KeepAnchor, len(text_to_find))
            self.text_edit.setTextCursor(cursor)
        else:
            # Если не найдено вхождений, сбрасываем индекс
            self.current_find_index = -1

    def find_all(self):
        text_to_find = self.combo_box_find.currentText()
        if not text_to_find:
            return

        # Получаем текст из текстового поля
        text = self.text_edit.toPlainText()
        cursor = self.text_edit.textCursor()
        cursor.setPosition(0)  # Начинаем с начала текста
        self.text_edit.setTextCursor(cursor)

        # Снимаем выделение
        self.text_edit.setTextCursor(cursor)

        # Найдем все вхождения
        while True:
            cursor = self.text_edit.textCursor()
            cursor = self.text_edit.find(text_to_find, cursor)
            if cursor.isNull():
                break
            cursor.movePosition(cursor.Right, cursor.KeepAnchor, len(text_to_find))
            self.text_edit.setTextCursor(cursor)

    def replace(self):
        text_to_find = self.combo_box_find.currentText()
        text_to_replace = self.combo_box_replace.currentText()

        if not text_to_find:
            return

        cursor = self.text_edit.textCursor()

        # Проверяем, есть ли выделение
        if cursor.hasSelection():
            # Получаем выделенный текст
            selected_text = cursor.selectedText()

            # Проверяем, совпадает ли выделенный текст с текстом, который мы ищем
            if selected_text == text_to_find:
                cursor.insertText(text_to_replace)

                # Обновляем текстовое поле
                updated_text = self.text_edit.toPlainText()

                # Обновляем список позиций для нового текста
                self.positions = [m.start() for m in re.finditer(re.escape(text_to_find), updated_text)]
                self.current_find_index = -1  # Сбрасываем индекс

        # Теперь вызываем find_next для выделения следующего вхождения
        self.find_next()

    def replace_all(self):
        text_to_find = self.combo_box_find.currentText()
        text_to_replace = self.combo_box_replace.currentText()

        if not text_to_find:
            return

        text = self.text_edit.toPlainText()
        new_text = text.replace(text_to_find, text_to_replace)
        self.text_edit.setPlainText(new_text)