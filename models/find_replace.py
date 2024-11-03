import re  # Добавьте этот импорт
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
        text = self.text_edit.toPlainText()

        # Если есть выделение, заменяем его
        if cursor.hasSelection():
            cursor.insertText(text_to_replace)
            # Обновляем текст после замены
            text = self.text_edit.toPlainText()
            # Сбрасываем индекс, так как мы заменили выделенный текст
            self.current_find_index = -1
            # Обновляем список позиций для нового текста
            self.positions = [m.start() for m in re.finditer(re.escape(text_to_find), text)]
            return

        # Если выделения нет, ищем следующее вхождение
        if self.current_find_index == -1:
            # Находим все позиции вхождений
            self.positions = [m.start() for m in re.finditer(re.escape(text_to_find), text)]
            self.current_find_index = 0  # Начинаем с первого вхождения

        # Проверяем, есть ли вхождения
        if self.positions:
            # Получаем позицию текущего вхождения
            current_position = self.positions[self.current_find_index]

            # Устанавливаем курсор на текущее вхождение
            cursor.setPosition(current_position)
            cursor.movePosition(cursor.Right, cursor.KeepAnchor, len(text_to_find))

            # Проверяем, правильно ли работает выделение
            self.text_edit.setTextCursor(cursor)

            # Заменяем текст
            cursor.insertText(text_to_replace)

            # Обновляем текстовое поле
            updated_text = self.text_edit.toPlainText()

            # После замены длина текста может измениться, корректируем смещение
            diff_length = len(text_to_replace) - len(text_to_find)

            # Обновляем список позиций с учетом смещения после каждой замены
            new_positions = []
            for pos in self.positions:
                # Корректируем позиции относительно текущего смещения
                if pos >= current_position + len(text_to_replace):
                    new_positions.append(pos + diff_length)
                else:
                    new_positions.append(pos)

            self.positions = new_positions

            # Переходим к следующему вхождению
            self.current_find_index += 1

            # Если индекс выходит за пределы, сбрасываем его
            if self.current_find_index >= len(self.positions):
                self.current_find_index = -1  # Сбрасываем индекс, если больше нет вхождений
            else:
                # Устанавливаем курсор на следующее вхождение для выделения
                next_position = self.positions[self.current_find_index]
                cursor.setPosition(next_position)
                cursor.movePosition(cursor.Right, cursor.KeepAnchor, len(text_to_find))
                self.text_edit.setTextCursor(cursor)  # Устанавливаем курсор на следующее вхождение
        else:
            # Если не найдено вхождений, сбрасываем индекс
            self.current_find_index = -1

    def replace_all(self):
        text_to_find = self.combo_box_find.currentText()
        text_to_replace = self.combo_box_replace.currentText()

        if not text_to_find:
            return

        text = self.text_edit.toPlainText()
        new_text = text.replace(text_to_find, text_to_replace)
        self.text_edit.setPlainText(new_text)