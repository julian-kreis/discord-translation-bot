import aiohttp
import numpy as np
import cv2
import easyocr
import asyncio

# Initialize once (important for performance)
# You can add languages as needed
reader = easyocr.Reader(['en'], gpu=False)


def message_has_image(message):
    if not message or not message.attachments:
        return False

    for att in message.attachments:
        if att.content_type and att.content_type.startswith("image"):
            return True

        if att.filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
            return True

    return False


async def extract_image_text(message):
    """
    Downloads Discord images and extracts text using EasyOCR.
    Returns: "[ extracted text ]" or None
    """

    if not message.attachments:
        return None

    results = []

    async with aiohttp.ClientSession() as session:
        for att in message.attachments:

            if att.content_type and not att.content_type.startswith("image"):
                continue

            try:
                async with session.get(att.url) as resp:
                    if resp.status != 200:
                        continue
                    img_bytes = await resp.read()

                text = await run_ocr(img_bytes)

                if text:
                    results.append(text)

            except Exception:
                continue

    if not results:
        return None

    return "[" + "\n".join(results).strip() + "]"


async def run_ocr(image_bytes: bytes):
    """
    Runs EasyOCR in a thread to avoid blocking event loop.
    """

    def _ocr():
        # Convert bytes -> OpenCV image
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return ""

        # EasyOCR returns list of (bbox, text, confidence)
        results = reader.readtext(img)

        # join detected text in reading order
        return " ".join([text for _, text, _ in results]).strip()

    try:
        text = await asyncio.to_thread(_ocr)
        return text if text else None
    except Exception:
        return None