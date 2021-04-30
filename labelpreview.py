#!/usr/bin/python3

import io
import os.path
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import sys


class LabelPreview(object):
    def __init__(self, category, title, subtitle, qrfilename='qr.png'):
        self.category = category
        self.title = title
        self.subtitle = subtitle
        self.qrfilename = qrfilename


    def __eq__(A, B):
        fields = ('category', 'title', 'subtitle', 'qrfilename')

        try:
            return all(
                    getattr(A, k) == getattr(B, k)
                    for k in fields
                    )
        except AttributeError:
            return False


    def __ne__(A, B):
        return not (A == B)


    def draw_text(self, area_size, font_size):
        parts = (
                (self.category, 'FreeSans', 0.8),
                (self.title, 'FreeMonoBold', 1.0),
                (self.subtitle, 'FreeSansBold', 0.8),
                )

        text_image = PIL.Image.new('RGB', area_size, color='white')

        draw = PIL.ImageDraw.Draw(text_image)


        used_size = [0, 0]

        for text, font_name, scale in parts:
            font = PIL.ImageFont.truetype(font_name, size=round(font_size*scale))

            text_size = draw.textsize(text, font=font)

            used_size[0] = max(used_size[0], text_size[0])
            used_size[1] += text_size[1] * 1.1

        if not all(a <= b for a, b in zip(used_size, area_size)):
            return None


        x, y = (0, (area_size[1] - used_size[1]) // 4)

        for text, font_name, scale in parts:
            font = PIL.ImageFont.truetype(font_name, size=round(font_size*scale))

            text_size = draw.textsize(text, font=font)
            draw.text((x, y), text, fill='black', font=font)

            y += text_size[1] * 1.1

        if y > area_size[1]:
            return None

        return text_image


    def draw(self, outfile, format, size=(650, 200), subparts=1):
        width, height = size

        if subparts > 1:
            margin = width // (subparts * 20)
            subwidth = (width - ((subparts - 1) * margin)) // subparts

            with io.BytesIO() as subfile:
                self.draw(subfile, format, size=(subwidth, height), subparts=1)

                subfile.seek(0)
                sub_image = PIL.Image.open(subfile)

                full_image = PIL.Image.new('RGB', size, color='white')

                x = 0
                for i in range(subparts):
                    full_image.paste(sub_image, (x, 0))
                    x += subwidth + margin

                full_image.save(outfile, format)
                return True


        image = PIL.Image.new('RGB', size, color='white')

        if self.qrfilename:
            qr = PIL.Image.open(self.qrfilename)
            image.paste(qr, (width - qr.width, (height - qr.height) // 2))
        else:
            class EmptyQR(object):
                width = 0
                height = 0
            qr = EmptyQR()


        text_max_size = [width - qr.width, height]

        rotate = (text_max_size[0] < text_max_size[1])

        if rotate:
            text_max_size.reverse()


        text_image = None

        font_size = 256
        for attempt in range(50):
            text_image = self.draw_text(text_max_size, font_size)

            if text_image:
                break

            font_size = 7 * font_size // 8

        if not text_image:
            return False

        if rotate:
            text_image = text_image.rotate(90, expand=1)

        image.paste(text_image, (0, 0))

        image.save(outfile, format)

        return True


if __name__ == '__main__':
    category, title, subtitle, qrfilename, filename = sys.argv[1:]

    LP = LabelPreview(category, title, subtitle, qrfilename=qrfilename)


    file_base, ext = os.path.splitext(filename)

    for i in range(1, 3):
        full_filename = '{:}-{:}{:}'.format(file_base, i, ext)

        LP.draw(full_filename, ext.strip('.'), subparts=i)
