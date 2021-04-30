#!/usr/bin/python3

import io
import sys

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from labelwindow import Ui_LabelerWindow

import labelpreview


class LabelerWindow(QtWidgets.QMainWindow, Ui_LabelerWindow):
    _placeholder_style = "color: gray; font-style: italic"

    def __init__(self, parent=None):
        super(LabelerWindow, self).__init__(parent)
        self.setupUi(self)

        self.leCategory.textChanged.connect(self.leCategory_changed)
        self.leTitle.textChanged.connect(self.leTitle_changed)
        self.leSubtitle.textChanged.connect(self.leSubtitle_changed)
        self.teDescription.textChanged.connect(self.teDescription_changed)
        self.lePlainText.textChanged.connect(self.lePlainText_changed)

        self.leCategory_changed('')
        self.leTitle_changed('')
        self.leSubtitle_changed('')
        self.teDescription_changed()
        self.lePlainText_changed('')

        self.pbNormalSingle.toggled.connect(self.label_type_changed)
        self.pbNormalDouble.toggled.connect(self.label_type_changed)
        self.pbHighDurabilitySingle.toggled.connect(self.label_type_changed)
        self.pbNormalDouble.toggled.connect(self.label_type_changed)

        self.sbLabels.valueChanged.connect(self.label_count_changed)

        self.label_type_changed(True)

        self.pbPrint.clicked.connect(self.print)
        self.pbReset.clicked.connect(self.reset)


        self._preview_cache = None

        self.timPreview = QtCore.QTimer(interval=300)
        self.timPreview.timeout.connect(self.update_preview)
        self.timPreview.start()


    @QtCore.pyqtSlot('QString')
    def leCategory_changed(self, text):
        if text:
            self.leCategory.setStyleSheet("")
        else:
            self.leCategory.setStyleSheet(self._placeholder_style)


    @QtCore.pyqtSlot('QString')
    def leTitle_changed(self, text):
        if text:
            self.leTitle.setStyleSheet("")
        else:
            self.leTitle.setStyleSheet(self._placeholder_style)


    @QtCore.pyqtSlot('QString')
    def leSubtitle_changed(self, text):
        if text:
            self.leSubtitle.setStyleSheet("")
        else:
            self.leSubtitle.setStyleSheet(self._placeholder_style)


    @QtCore.pyqtSlot()
    def teDescription_changed(self):
        if self.teDescription.toPlainText():
            self.teDescription.setStyleSheet("")
        else:
            self.teDescription.setStyleSheet(self._placeholder_style)


    @QtCore.pyqtSlot('QString')
    def lePlainText_changed(self, text):
        if text:
            self.lePlainText.setStyleSheet("")
        else:
            self.lePlainText.setStyleSheet(self._placeholder_style)


    @QtCore.pyqtSlot(bool)
    def label_type_changed(self, _):
        self.update_copies()


    @QtCore.pyqtSlot(int)
    def label_count_changed(self, _):
        self.update_copies()


    def update_copies(self):
        per_sticker = None

        if self.pbNormalSingle.isChecked():
            per_sticker = 1
        elif self.pbNormalDouble.isChecked():
            per_sticker = 2
        elif self.pbHighDurabilitySingle.isChecked():
            per_sticker = 1
        elif self.pbHighDurabilityDouble.isChecked():
            per_sticker = 2

        if not per_sticker:
            self.message('Could not determine label count!')
            return

        num_labels = self.sbLabels.value()

        if (num_labels % per_sticker) != 0:
            new_count = num_labels + per_sticker - (num_labels % per_sticker)
            self.sbLabels.setValue(new_count)

        self.sbLabels.setSingleStep(per_sticker)
        self.sbLabels.setMinimum(per_sticker)
        self.sbLabels.setMaximum(per_sticker * 20)

        num_labels = self.sbLabels.value()
        num_stickers = num_labels // per_sticker

        label = 'label' if (num_labels == 1) else 'labels'
        sticker = 'sticker' if (num_stickers == 1) else 'stickers'

        text = (
                '{num_labels} {label} '
                '/ {per_sticker} per sticker '
                '= {num_stickers} {sticker}'
                ).format(
                        num_labels=num_labels,
                        label=label,
                        per_sticker=per_sticker,
                        num_stickers=num_stickers,
                        sticker=sticker,
                        )
        self.lblOutputCount.setText(text)


    def is_inventory(self):
        return 'Inventory' in self.tabs.tabText(self.tabs.currentIndex())


    def is_plain(self):
        return 'Plain' in self.tabs.tabText(self.tabs.currentIndex())


    @QtCore.pyqtSlot()
    def update_preview(self):
        if self.is_inventory():
            category = self.leCategory.text()
            title = self.leTitle.text()
            subtitle = self.leSubtitle.text()

            if self.pbSerial.isChecked():
                title += '1234'

            preview = labelpreview.LabelPreview(category, title, subtitle)

        elif self.is_plain():
            plain = self.lePlainText.text()

            preview = labelpreview.LabelPreview('', plain, '', qrfilename=None)

        else:
            self.message('Tell Daniel that APPLE APPLE PENGUIN')
            return


        if preview == self._preview_cache:
            return

        self._preview_cache = preview


        for widget, per_sticker in (
                (self.pbNormalSingle, 1),
                (self.pbNormalDouble, 2),
                (self.pbHighDurabilitySingle, 1),
                (self.pbHighDurabilityDouble, 2),
                ):
            icon_size = widget.iconSize()
            width = icon_size.width()
            height = icon_size.height()
            size = (width, height)

            with io.BytesIO() as icon_file:
                preview.draw(icon_file, 'png', size=size, subparts=per_sticker)
                icon_file.seek(0)

                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(icon_file.read(), 'png')

                widget.setIcon(QtGui.QIcon(pixmap))


    @QtCore.pyqtSlot()
    def print(self):
        if self.is_inventory():
            return self.print_inventory()
        elif self.is_plain():
            return self.print_plain()

        self.message('Tell Daniel that BANANA BANANA CHEESECAKE')


    def print_inventory(self):
        category = self.leCategory.text().strip()
        title = self.leTitle.text().strip()
        subtitle = self.leSubtitle.text().strip()
        description = self.teDescription.toPlainText().strip()

        if not category:
            self.message('Category must not be blank!')
            return False
        if not title:
            self.message('Title must not be blank!')
            return False

        text = 'Printing {category} / {title} / {subtitle}...'.format(
                category=category,
                title=title,
                subtitle=subtitle,
                )
        self.message(text)

        return True


    def print_plain(self):
        plain = self.lePlainText.text().strip()

        if not plain:
            self.message('Label must not be blank!')
            return False

        text = 'Printing {plain}...'.format(plain=plain)
        self.message(text)

        return True


    @QtCore.pyqtSlot()
    def reset(self):
        self.tabs.setCurrentIndex(0)
        self.leCategory.setText('')
        self.leTitle.setText('')
        self.leSubtitle.setText('')
        self.teDescription.clear()
        self.lePlainText.setText('')
        self.pbNormalSingle.setChecked(True)
        self.sbLabels.setValue(1)


    def message(self, content, timeout=5000):
        self.statusbar.showMessage(content, timeout)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setAttribute(
            Qt.AA_UseStyleSheetPropagationInWidgetStyles,
            True
            )
    app.setStyleSheet("""
    * {
        font-size: 40;
        font-family: "Sans";
        }
    """)
    win = LabelerWindow()
    win.show()
    app.aboutToQuit.connect(win.timPreview.stop)
    sys.exit(app.exec_())
