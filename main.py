import sys
from PIL import Image
from pathlib import Path
from encoder import QoiEncoder
from decoder import QoiDecoder

input_filename = sys.argv[1]
qoi_filename = Path(input_filename).name + ".qoi"
png_filename = Path(input_filename).name + ".png"

# -------------------- Encoding part --------------------

img = Image.open(input_filename)

width, height = img.size
channels = len(img.getbands())
colorspace = 0 
pixels = list(img.getdata())
encoder = QoiEncoder()

output = encoder.encode(pixels, width, height, channels, colorspace)

with open(qoi_filename, "wb") as qoi:
    qoi.write(output)

# -------------------- Decoding part --------------------

with open(qoi_filename, "rb") as qoi_file:
    qoi_data = qoi_file.read()

decoder = QoiDecoder()
headers = decoder.headers(qoi_data)

img = Image.new("RGBA" if headers.channels == 4 else "RGB", (headers.width, headers.height))
img.putdata(decoder.decoder(qoi_data, headers))
img.save(png_filename)