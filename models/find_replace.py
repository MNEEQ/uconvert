import re
from PyQt5.QtWidgets import QComboBox
from widgets.numbered_text_edit import NumberedTextEdit

class FindReplace:
    def __init__(self, text_edit: NumberedTextEdit, combo_box_find: QComboBox, combo_box_replace: QComboBox):
        self.text_edit = text_edit
        self.combo_box_find = combo_box_find
        self.combo_box_replace = combo_box_replace
        self.current_find_index = -1  # Индекс текущего найденного слова
        self.positions = []  # Позиции всех найденных вхождений

    def find_next(self):
        text_to_find = self.combo_box_find.currentText()
        if not text_to_find:
            return

        # Получаем текст из текстового поля
        text = self.text_edit.toPlainText()

        # Если мы еще не искали или текст изменился, обновляем список позиций
        if self.current_find_index == -1 or not self.positions:
            self.positions = [i.start() for i in re.finditer(re.escape(text_to_find), text)]

        if self.positions:
            # Увеличиваем индекс и сбрасываем его, если он выходит за пределы
            self.current_find_index = (self.current_find_index + 1) % len(self.positions)

            # Устанавливаем курсор на следующую позицию
            cursor = self.text_edit.textCursor()
            cursor.setPosition(self.positions[self.current_find_index])
            cursor.movePosition(cursor.Right, cursor.KeepAnchor, len(text_to_find))
            self.text_edit.setTextCursor(cursor)
        else:
            # Если вхождений не найдено, сбрасываем индекс
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
                # Заменяем текст
                cursor.insertText(text_to_replace)

                # Сохраняем текущую позицию курсора после замены
                current_position = cursor.position()

                # Обновляем текстовое поле
                updated_text = self.text_edit.toPlainText()

                # Обновляем список позиций для нового текста
                self.positions = [m.start() for m in re.finditer(re.escape(text_to_find), updated_text)]

                # Находим новое положение для текущего индекса, чтобы продолжить с того места
                # где курсор остановился
                self.current_find_index = -1  # Сброс индекса
                for i, pos in enumerate(self.positions):
                    if pos >= current_position:
                        self.current_find_index = i - 1  # Обновляем индекс для следующего поиска
                        break

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