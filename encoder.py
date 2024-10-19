import struct


class QoiEncoder:
    def __init__(self):
        self.QOI_OP_INDEX = 0x00
        self.QOI_OP_DIFF = 0x40
        self.QOI_OP_LUMA = 0x80
        self.QOI_OP_RUN = 0xC0
        self.QOI_OP_RGB = 0xFE
        self.QOI_OP_RGBA = 0xFF
        self.QOI_MASK_2 = 0xC0

    def headers(self, width, height, channels, colorspace):
        return struct.pack(">IIBB", width, height, channels, colorspace)

    def encode(self, pixels, width, height, channels, colorspace):
        index = [[0, 0, 0, 255]] * 64
        data = bytearray(b"qoif")
        data += self.headers(width, height, channels, colorspace)
        run = 0
        previous_pixel = [0, 0, 0, 255]

        for pixel in pixels:
            if channels == 3:
                pixel = list(pixel) + [255]

            if pixel == previous_pixel:
                run += 1
                if run == 62:
                    data.append(self.QOI_OP_RUN | 61)
                    run = 0
            else:
                if run > 0:
                    data.append(self.QOI_OP_RUN | (run - 1))
                    run = 0

                index_pos = (
                    pixel[0] * 3 + pixel[1] * 5 + pixel[2] * 7 + pixel[3] * 11
                ) % 64
                if pixel == index[index_pos]:
                    data.append(self.QOI_OP_INDEX | index_pos)
                else:
                    index[index_pos] = pixel

                    dr = pixel[0] - previous_pixel[0]
                    dg = pixel[1] - previous_pixel[1]
                    db = pixel[2] - previous_pixel[2]
                    da = pixel[3] - previous_pixel[3]

                    if -2 <= dr <= 1 and -2 <= dg <= 1 and -2 <= db <= 1 and da == 0:
                        data.append(
                            self.QOI_OP_DIFF
                            | ((dr + 2) << 4)
                            | ((dg + 2) << 2)
                            | (db + 2)
                        )
                    elif (
                        -32 <= dg <= 31
                        and -8 <= dr - dg <= 7
                        and -8 <= db - dg <= 7
                        and da == 0
                    ):
                        data.append(self.QOI_OP_LUMA | (dg + 32))
                        data.append(((dr - dg + 8) << 4) | (db - dg + 8))
                    elif da == 0:
                        data.append(self.QOI_OP_RGB)
                        data.append(pixel[0])
                        data.append(pixel[1])
                        data.append(pixel[2])
                    else:
                        data.append(self.QOI_OP_RGBA)
                        data.append(pixel[0])
                        data.append(pixel[1])
                        data.append(pixel[2])
                        data.append(pixel[3])

            previous_pixel = pixel

        if run > 0:
            data.append(self.QOI_OP_RUN | (run - 1))

        data += b"\x00\x00\x00\x00\x00\x00\x00\x00"

        return data
