from PIL import Image, ImageDraw, ImageFont
import qrcode
from io import BytesIO


class QRCodeService:

    @staticmethod
    def generate_qr_with_label(data: str, label: str) -> BytesIO:
        # Generate QR code
        qr_img = qrcode.make(data).convert("RGB")
        # Font setup
        try:
            font = ImageFont.truetype("arial.ttf", 18)  
        except IOError:
            font = ImageFont.load_default()

        # Create a new image with space for text
        text_height = 40
        new_img = Image.new("RGB", (qr_img.width, qr_img.height + text_height), "white")
        new_img.paste(qr_img, (0, 0))

        # Draw text
        draw = ImageDraw.Draw(new_img)
        text_width = draw.textlength(label, font=font)
        text_x = (qr_img.width - text_width) // 2
        draw.text((text_x, qr_img.height + 10), label, font=font, fill="black")

        # Save to buffer
        output = BytesIO()
        new_img.save(output, format="PNG")
        output.seek(0)
        
        return output



