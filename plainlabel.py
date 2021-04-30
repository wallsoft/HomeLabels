#!/usr/bin/python3

import itertools
import reportlab
import sys


from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Frame, Image


class LabelPage(object):
    def __init__(self, labels=None):
        if labels:
            self.labels = list(labels)
        else:
            self.labels = []


    def make_page(
            self,
            filename,
            pagesize=letter,
            label_section_size=(208 * mm, 254 * mm),
            cols=2,
            rows=6,
            ):
        canvas = Canvas(filename, pagesize=pagesize)

        margin_x, margin_y = (
                (full - printable) / 2
                for full, printable in zip(pagesize, label_section_size)
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

        frame_size = (width, height)

        frame = Frame(
                0,
                0,
                *frame_size,
                leftPadding=0,
                bottomPadding=0,
                rightPadding=0,
                topPadding=0,
                )

        font_size = 32
        for attempt in range(50):
            style = ParagraphStyle(
                    'name',
                    fontName='Courier-Bold',
                    fontSize=font_size,
                    leading=font_size,
                    textColor=(0.0, 0.0, 0.0),
                    )

            if frame.add(Paragraph(str(label), style), canvas):
                break

            font_size = font_size * 0.95


if __name__ == '__main__':
    filename = sys.argv[1]

    labels = []

    for label in sys.argv[2:]:
        labels.append(label)

    page = LabelPage(labels)

    page.make_page(filename)
