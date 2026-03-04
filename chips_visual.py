#The goal of this is to dynamically generate 'betting chips'
#The chips will be represented as circles with different colors and sizes based on their value.
#The chips will be displayed. We need to take into account 'stacks' of chips.
#Chips are in denominations of 1, 5, 10, 25, 50, 100, 500, 1000, 5000, 10000.
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QColor, QFont, QPainter, QPen
from PyQt5.QtWidgets import QSizePolicy, QWidget


class ChipsVisualWidget(QWidget):
	def __init__(self, parent=None, chip_values=None):
		super().__init__(parent)
		self._chip_values = list(chip_values) if chip_values else [10000, 5000, 1000, 500, 100, 50, 25, 10, 5, 1]
		self._chip_values = sorted([int(v) for v in self._chip_values if int(v) > 0], reverse=True)
		if not self._chip_values:
			self._chip_values = [1]

		self._chip_colors = {
			1: QColor("#f5f5f5"),
			5: QColor("#d9534f"),
			10: QColor("#5bc0de"),
			25: QColor("#5cb85c"),
			50: QColor("#337ab7"),
			100: QColor("#f0ad4e"),
			500: QColor("#8e44ad"),
			1000: QColor("#85c1e9"),
			5000: QColor("#c0392b"),
			10000: QColor("#f7dc6f"),
		}

		self._amount = 0
		self._stacks = []
		self.setMinimumSize(220, 90)
		self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
		self.set_amount(0)

	def sizeHint(self):
		return QSize(280, 90)

	def minimumSizeHint(self):
		return QSize(220, 90)

	def set_chip_values(self, chip_values):
		values = sorted([int(v) for v in chip_values if int(v) > 0], reverse=True)
		if not values:
			return
		self._chip_values = values
		self.set_amount(self._amount)

	def set_amount(self, amount):
		try:
			parsed = int(amount)
		except (TypeError, ValueError):
			parsed = 0
		self._amount = max(0, parsed)
		self._stacks = self._decompose_amount(self._amount)
		self.update()

	def amount(self):
		return self._amount

	def clear(self):
		self.set_amount(0)

	def _decompose_amount(self, amount):
		remaining = amount
		stacks = []
		for value in self._chip_values:
			count = remaining // value
			if count > 0:
				stacks.append((value, count))
				remaining -= count * value
		return stacks

	def _chip_color(self, value):
		if value in self._chip_colors:
			return self._chip_colors[value]
		palette = [
			QColor("#f39c12"), QColor("#3498db"), QColor("#2ecc71"),
			QColor("#9b59b6"), QColor("#e74c3c"), QColor("#1abc9c"),
		]
		return palette[abs(hash(value)) % len(palette)]

	def paintEvent(self, event):
		self.paintEventv1(event)

	def paintEventv1(self, event):
		painter = QPainter(self)
		painter.setRenderHint(QPainter.Antialiasing)

		rect = self.rect().adjusted(1, 1, -1, -1)
		painter.setPen(QPen(QColor("#888888"), 2))
		painter.setBrush(QColor("#bbbbbb"))
		painter.drawRoundedRect(rect, 8, 8)

		painter.setPen(QPen(QColor("#222222"), 1))
		painter.setFont(QFont("Arial", 9, QFont.Bold))
		painter.drawText(rect.adjusted(8, 4, -8, -4), Qt.AlignTop | Qt.AlignRight, f"${self._amount}")

		if not self._stacks:
			painter.setFont(QFont("Arial", 9))
			painter.drawText(rect, Qt.AlignCenter, "No chips")
			return

		margin_x = 12
		margin_bottom = 10
		top_reserved = 18
		chip_diameter = 24
		overlap = 5
		gap = 1
		max_visible = 7
		slot_step = chip_diameter + gap
		available_width = max(0, rect.width() - (2 * margin_x))
		max_slots = 1
		if available_width > chip_diameter:
			max_slots = 1 + ((available_width - chip_diameter) // slot_step)
		display_stacks = self._stacks[:max(1, max_slots)]

		center_x = rect.center().x() - (chip_diameter // 2)
		base_y = rect.bottom() - margin_bottom

		for index, (value, count) in enumerate(display_stacks):
			if index == 0:
				offset = 0
			else:
				step = (index + 1) // 2
				offset = -step if (index % 2 == 1) else step
			x = center_x + (offset * slot_step)
			visible = min(count, max_visible)
			color = self._chip_color(value)
			y_top = base_y - chip_diameter

			for layer in range(visible):
				y = y_top - layer * overlap
				if y < rect.top() + top_reserved:
					break
				painter.setPen(QPen(QColor("#1e1e1e"), 1))
				painter.setBrush(color)
				painter.drawEllipse(x, y, chip_diameter, chip_diameter)

				painter.setPen(QPen(QColor("#ffffff"), 1))
				painter.drawEllipse(x + 4, y + 4, chip_diameter - 8, chip_diameter - 8)

			top_visible_y = y_top - (visible - 1) * overlap
			painter.setPen(QPen(QColor("#111111"), 1))
			painter.setFont(QFont("Arial", 7, QFont.Bold))
			painter.drawText(x, top_visible_y, chip_diameter, chip_diameter, Qt.AlignCenter, str(value))

			if count > max_visible:
				painter.setFont(QFont("Arial", 7, QFont.Bold))
				label_y = max(rect.top() + top_reserved, top_visible_y - 12)
				painter.drawText(x - 2, label_y, chip_diameter + 4, 10, Qt.AlignCenter, f"x{count}")

if __name__ == "__main__":
	import sys
	from PyQt5.QtWidgets import QApplication

	app = QApplication(sys.argv)
	chips_widget = ChipsVisualWidget(chip_values=[1, 5, 10, 25, 50, 100, 500, 1000, 5000, 10000])
	chips_widget.set_amount(23789)
	chips_widget.show()
	sys.exit(app.exec_())