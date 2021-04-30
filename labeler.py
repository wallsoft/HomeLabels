#!/usr/bin/python3

import io
import os.path
import subprocess
import sys

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from labelwindow import Ui_LabelerWindow

import inventory
import labelpreview


class LabelerWindow(QtWidgets.QMainWindow, Ui_LabelerWindow):
    _placeholder_style = "color: gray; font-style: italic"

    def __init__(self, creators, inventory_file, printer, parent=None):
        super(LabelerWindow, self).__init__(parent)

        self.inventory = inventory.Inventory(inventory_file)
        self.creators = creators
        self.printer = printer

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

        self.num_stickers = num_stickers

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
        self.update_copies()
        copies = self.num_stickers

        if self.is_inventory():
            return self.print_inventory(copies)
        elif self.is_plain():
            return self.print_plain(copies)

        self.message('Tell Daniel that BANANA BANANA CHEESECAKE')


    def print_inventory(self, copies):
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

        text = 'Preparing {category} / {title} / {subtitle}...'.format(
                category=category,
                title=title,
                subtitle=subtitle,
                )
        self.message(text)


        creator = self.creators['inventory']
        args = [creator, category, title, subtitle, description]

        result = subprocess.run(
                args,
                stdout=subprocess.PIPE,
                timeout=60,
                )

        if result.returncode != 0:
            text = 'Error preparing sticker!!! {:}'.format(result.returncode)
            self.message(text, timeout=10000)
            return False

        print_filename = None

        for line in result.stdout.split(b'\n'):
            if not line:
                continue

            if os.path.isfile(line):
                for ext in (b'.txt', b'.dat', b'.json'):
                    if line.lower().endswith(ext):
                        success = False
                        for attempt in range(10):
                            try:
                                self.inventory.append(str(line, 'utf-8'))
                                success = True
                            except BlockingIOError:
                                text = 'Waiting for inventory... {:}'.format(
                                        attempt,
                                        )
                                self.message(text)

                                wait_loop = QtCore.QEventLoop()
                                QtCore.QTimer.singleShot(200, wait_loop.quit)
                                wait_loop.exec_()

                        if not success:
                            with open('lost-inventory.txt', 'a') as F:
                                print(str(line, 'utf-8'), file=F)
                            text = ' '.join((
                                'Could not queue',
                                title,
                                'for inventory!',
                                ))
                            self.message(text, timeout=10000)
                            return False

                        break
                if line.lower().endswith(b'.pdf'):
                    print_filename = line

        return self.print_copies(print_filename, copies, title=title)


    def print_plain(self, copies):
        plain = self.lePlainText.text().strip()

        if not plain:
            self.message('Label must not be blank!')
            return False

        text = 'Preparing {plain}...'.format(plain=plain)
        self.message(text)


        creator = self.creators['plain']
        args = [creator, plain]

        result = subprocess.run(
                args,
                stdout=subprocess.PIPE,
                timeout=60,
                )

        if result.returncode != 0:
            text = 'Error preparing sticker!!! {:}'.format(result.returncode)
            self.message(text, timeout=10000)
            return False

        print_filename = result.stdout.strip(b'\n')

        if not os.path.isfile(print_filename):
            text = ''.join((
                'Could not determine output filename from ',
                creator,
                '!',
                ))
            self.message(text, timeout=10000)
            return False

        return self.print_copies(print_filename, copies, title=plain)


    def print_copies(self, filename, copies, title=None):
        for copy in range(1, copies + 1):
            text = 'Printing # {copy} of {copies}...'.format(
                    copy=copy,
                    copies=copies,
                    )
            self.message(text)

            args = ['echo', 'lp', '-d', self.printer, filename]

            result = subprocess.run(args, timeout=10)

            if result.returncode != 0:
                text = 'Error printing copy # {:}!!! {:}'.format(
                        copy,
                        result.returncode,
                        )
                self.message(text, timeout=10000)
                return False

        copy = 'copy' if copies == 1 else 'copies'
        text = 'Queued {copies} {copy}'.format(
                copies=copies,
                copy=copy,
                )
        if title:
            text += ' of ' + title
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
    (
            inventory_label_creator,
            plain_label_creator,
            inventory_file,
            printer,
            ) = sys.argv[-4:]

    creators = dict(
            inventory=inventory_label_creator,
            plain=plain_label_creator,
            )

    app = QtWidgets.QApplication(sys.argv[:-3])
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
    win = LabelerWindow(creators, inventory_file, printer)
    win.show()
    app.aboutToQuit.connect(win.timPreview.stop)
    sys.exit(app.exec_())
