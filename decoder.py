import struct


class QoiDecoder:
    def __init__(self):
        self.QOI_OP_INDEX = 0x00
        self.QOI_OP_DIFF = 0x40
        self.QOI_OP_LUMA = 0x80
        self.QOI_OP_RUN = 0xC0
        self.QOI_OP_RGB = 0xFE
        self.QOI_OP_RGBA = 0xFF
        self.QOI_MASK_2 = 0xC0

    class QoiHeader:
        def __init__(self, magic, width, height, channels, colorspace):
            self.magic = magic
            self.width = width
            self.height = height
            self.channels = channels
            self.colorspace = colorspace

    def headers(self, data):
        magic = data[:4]
        width, height, channels, colorspace = struct.unpack(">IIBB", data[4:14])
        return self.QoiHeader(magic, width, height, channels, colorspace)

    def all_pixels(self, data, headers):
        index = [0] * 64
        index[0] = [0, 0, 0, 255]
        pixels = []
        run = 0
        pixel_index = 14
        previous_pixel = [0, 0, 0, 255]

        for _ in range(headers.height):
            for _ in range(headers.width):
                if pixel_index >= len(data):
                    break
                if run > 0:
                    run -= 1
                    pixels.append(previous_pixel)
                    continue

                byte = data[pixel_index]
                pixel_index += 1

                match byte:
                    case self.QOI_OP_RGB:
                        r = data[pixel_index]
                        g = data[pixel_index + 1]
                        b = data[pixel_index + 2]
                        pixel_index += 3
                        pixel = [r, g, b, 255]
                    case self.QOI_OP_RGBA:
                        r = data[pixel_index]
                        g = data[pixel_index + 1]
                        b = data[pixel_index + 2]
                        a = data[pixel_index + 3]
                        pixel_index += 4
                        pixel = [r, g, b, a]
                    case _ if (byte & 0xC0) == self.QOI_OP_INDEX:
                        index_pos = byte & 0x3F
                        pixel = index[index_pos]
                    case _ if (byte & 0xC0) == self.QOI_OP_DIFF:
                        dr = ((byte >> 4) & 0x03) - 2
                        dg = ((byte >> 2) & 0x03) - 2
                        db = (byte & 0x03) - 2
                        pixel = [
                            (previous_pixel[0] + dr) & 0xFF,
                            (previous_pixel[1] + dg) & 0xFF,
                            (previous_pixel[2] + db) & 0xFF,
                            previous_pixel[3],
                        ]
                    case _ if (byte & 0xC0) == self.QOI_OP_LUMA:
                        dg = (byte & 0x3F) - 32
                        dr_dg = data[pixel_index]
                        pixel_index += 1
                        dr = (dr_dg >> 4) - 8 + dg
                        db = (dr_dg & 0x0F) - 8 + dg
                        pixel = [
                            (previous_pixel[0] + dr) & 0xFF,
                            (previous_pixel[1] + dg) & 0xFF,
                            (previous_pixel[2] + db) & 0xFF,
                            previous_pixel[3],
                        ]
                    case _ if (byte & 0xC0) == self.QOI_OP_RUN:
                        run = byte & 0x3F
                        pixels.append(previous_pixel)
                        continue
                    case _:
                        raise ValueError(f"Invalid QOI byte: {byte:02x}")

                pixels.append(pixel)
                previous_pixel = pixel
                index_pos = (
                    pixel[0] * 3 + pixel[1] * 5 + pixel[2] * 7 + pixel[3] * 11
                ) % 64
                index[index_pos] = pixel
        return pixels

    def decoder(self, data, headers):
        pixels = self.all_pixels(data, headers)
        pixels = [tuple(pixel) for pixel in pixels]
        return pixels
