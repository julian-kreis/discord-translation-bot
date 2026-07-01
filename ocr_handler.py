import aiohttp
import asyncio
import io
import os
from PIL import Image

OCR_SPACE_API_KEY = os.getenv("OCR_SPACE_API_KEY")
OCR_SPACE_URL = "https://api.ocr.space/parse/image"

MAX_UPLOAD_SIZE = 1 * 1024 * 1024  # 1MB limit


def message_has_image(message):
    if not message or not message.attachments:
        return False

    return any(
        att.content_type and att.content_type.startswith("image")
        or att.filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
        for att in message.attachments
    )


async def extract_image_text(message):
    """
    Extracts text using OCR.space API.
    Applies compression to respect 1MB upload limit.
    Returns: "[ text ]"
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

                # compress if too large (IMPORTANT for 1MB limit)
                img_bytes = await ensure_under_1mb(img_bytes)

                text = await run_ocr_space(session, img_bytes, att.filename)

                if text:
                    results.append(text)

            except Exception:
                continue

    if not results:
        return None

    return "[" + "\n".join(results).strip() + "]"


async def ensure_under_1mb(img_bytes: bytes):
    """
    Compress image until under 1MB limit.
    """

    if len(img_bytes) <= MAX_UPLOAD_SIZE:
        return img_bytes

    def _compress():
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

        quality = 85
        buffer = io.BytesIO()

        while True:
            buffer.seek(0)
            buffer.truncate()

            img.save(buffer, format="JPEG", quality=quality, optimize=True)
            data = buffer.getvalue()

            if len(data) <= MAX_UPLOAD_SIZE or quality <= 30:
                return data

            quality -= 10

    return await asyncio.to_thread(_compress)


async def run_ocr_space(session, img_bytes: bytes, filename: str):
    """
    Calls OCR.space API
    """

    try:
        data = aiohttp.FormData()
        data.add_field("apikey", OCR_SPACE_API_KEY)
        data.add_field("language", "eng")
        data.add_field("isOverlayRequired", "false")
        data.add_field("file", img_bytes, filename=filename or "image.jpg")

        async with session.post(OCR_SPACE_URL, data=data, timeout=30) as resp:
            if resp.status != 200:
                return None

            result = await resp.json()

            parsed = result.get("ParsedResults")
            if not parsed:
                return None

            return parsed[0].get("ParsedText", "").strip() or None

    except Exception:
        return None