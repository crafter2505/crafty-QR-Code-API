import qrcode
from io import BytesIO
import base64

def generate_QR_code(data: str, size: int = 10) -> str:
    """Generate QR code and return as base64 image."""
    qr = qrcode.QRCode(
        version=1,
        box_size=size,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return img_str