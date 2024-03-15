# should download model locally
import easyocr
reader = easyocr.Reader(['en'], gpu=True)
result = reader.readtext('./pdf.png', paragraph=True, height_ths=5, width_ths=0.8)
print(result)