#!/usr/bin/python3

import itertools
import qrcode
import reportlab
import sys
import tempfile

import counter


from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Frame, Image


def make_qr_image(data):
    QR = qrcode.QRCode(
            error_correction=qrcode.ERROR_CORRECT_M,
            box_size=10,
            border=0,
            )

    QR.add_data(data)
    QR.make(fit=True)
    return QR.make_image(back_color='#202020', fill_color='white')


class Label(object):
    def __init__(self, name, add_serial=True):
        self.name = name

        if add_serial:
            C = counter.NotThreadSafeCounter('counter.txt')
            self.name += '{:03}'.format(C.inc())

    def __str__(self):
        return self.name

    def qr_data(self):
        return '\n'.join((
            self.name,
            'Seemuth',
            'I ADORE YOU!!!',
            ))


class LabelPage(object):
    def __init__(self, labels=None):
        if labels:
            self.labels = list(labels)
        else:
            self.labels = []


    def make_page(self, filename):
        canvas = Canvas(filename, pagesize=letter)
        label_section_size = (208 * mm, 254 * mm)
        cols = 2
        rows = 6

        margin_x, margin_y = (
                (full - printable) / 2
                for full, printable in zip(letter, label_section_size)
                )

        pitch_x, pitch_y = (
                printable / count
                for printable, count in zip(label_section_size, (cols, rows))
                )

        canvas.saveState()

        canvas.translate(margin_x, margin_y)

        iter_labels = iter(self.labels)

        for xindex, yindex in itertools.product(range(cols), range(rows)):
            try:
                label = next(iter_labels)
            except StopIteration:
                break

            canvas.saveState()

            canvas.translate(pitch_x * xindex, pitch_y * (rows - yindex - 1))

            LabelPage.draw_label(label, canvas, (pitch_x, pitch_y))

            canvas.restoreState()


        canvas.restoreState()

        canvas.save()


    @staticmethod
    def draw_label(label, canvas, size):
        width, height = size

        margin_x = 8 * mm
        margin_y = 6 * mm

        canvas.translate(margin_x, margin_y)

        width -= margin_x * 2
        height -= margin_y * 2

        qr_size = height
        qr_image = make_qr_image(label.qr_data())
        with tempfile.NamedTemporaryFile(suffix='.png') as F:
            qr_image.save(F.name)

            canvas.drawImage(
                    F.name,
                    width - qr_size,
                    0,
                    width=qr_size,
                    height=qr_size,
                    )

        spacing = 6 * mm
        frame_size = (width - qr_size - spacing, height)

        frame = Frame(
                0,
                0,
                *frame_size,
                leftPadding=0,
                bottomPadding=0,
                rightPadding=0,
                topPadding=0,
                )

        style = ParagraphStyle(
                'name',
                fontName='Courier-Bold',
                fontSize=32,
                leading=32,
                textColor=(0.2, 0.2, 0.2),
                )

        frame.add(Paragraph(str(label), style), canvas)


if __name__ == '__main__':
    filename = sys.argv[1]

    labels = []

    for label in sys.argv[2:]:
        labels.append(Label(label))

    page = LabelPage(labels)

    page.make_page(filename)
