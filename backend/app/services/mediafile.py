"""Figure out what a phone actually sent us and make it displayable everywhere.

Phones are unreliable about this: some Android browsers send no content type
(or application/octet-stream), iPhones and Samsungs can send HEIC photos that
desktop Chrome can't show, and filenames are often 'image.jpg' for anything.
So: trust the bytes first, then the extension, then the browser's header.
"""
import io
import mimetypes
from typing import BinaryIO

# (ext, content type, media type)
JPEG = ("jpg", "image/jpeg", "image")

_VIDEO_BRANDS = {b"qt  ": ("mov", "video/quicktime"), b"3gp4": ("3gp", "video/3gpp"),
                 b"3gp5": ("3gp", "video/3gpp"), b"3g2a": ("3g2", "video/3gpp2")}
_HEIF_BRANDS = {b"heic", b"heix", b"hevc", b"hevx", b"heim", b"heis", b"mif1", b"msf1", b"avif"}

_EXT = {
    "jpg": JPEG, "jpeg": JPEG, "png": ("png", "image/png", "image"),
    "gif": ("gif", "image/gif", "image"), "webp": ("webp", "image/webp", "image"),
    "heic": ("heic", "image/heic", "image"), "heif": ("heif", "image/heif", "image"),
    "avif": ("avif", "image/avif", "image"),
    "mp4": ("mp4", "video/mp4", "video"), "m4v": ("m4v", "video/mp4", "video"),
    "mov": ("mov", "video/quicktime", "video"), "webm": ("webm", "video/webm", "video"),
    "3gp": ("3gp", "video/3gpp", "video"), "mkv": ("mkv", "video/x-matroska", "video"),
}


def sniff(head: bytes) -> tuple[str, str, str] | None:
    if head[:3] == b"\xff\xd8\xff":
        return JPEG
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return _EXT["png"]
    if head[:6] in (b"GIF87a", b"GIF89a"):
        return _EXT["gif"]
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return _EXT["webp"]
    if head[:4] == b"\x1aE\xdf\xa3":
        return _EXT["webm"]
    if head[4:8] == b"ftyp":
        brand = head[8:12]
        if brand in _HEIF_BRANDS:
            return _EXT["avif"] if brand == b"avif" else _EXT["heic"]
        if brand in _VIDEO_BRANDS:
            ext, ct = _VIDEO_BRANDS[brand]
            return (ext, ct, "video")
        return _EXT["mp4"]   # isom, mp41, mp42, M4V, iso*, dash...
    return None


def detect(head: bytes, filename: str | None, content_type: str | None) -> tuple[str, str, str] | None:
    found = sniff(head)
    if found:
        return found
    ext = (filename or "").rsplit(".", 1)[-1].lower() if "." in (filename or "") else ""
    if ext in _EXT:
        return _EXT[ext]
    ct = (content_type or "").split(";")[0].strip().lower()
    if ct.startswith(("image/", "video/")):
        guessed = (mimetypes.guess_extension(ct) or ".bin").lstrip(".")
        return (guessed, ct, ct.split("/")[0])
    return None


LOGO_TYPES = {"png", "jpg", "webp", "gif"}


def detect_logo(head: bytes, filename: str | None) -> tuple[str, str] | None:
    """Logos may also be SVG. They're only ever shown via <img>, where scripts
    inside an SVG don't run, and they're served from the storage domain."""
    text = head.lstrip()[:200].lower()
    if text.startswith(b"<svg") or (text.startswith(b"<?xml") and b"<svg" in head.lower()):
        return ("svg", "image/svg+xml")
    found = sniff(head)
    if found and found[0] in LOGO_TYPES:
        return found[0], found[1]
    return None


def heic_to_jpeg(src: BinaryIO) -> BinaryIO:
    """HEIC/HEIF -> JPEG so every browser (and the TV) can show it."""
    import pillow_heif
    from PIL import Image, ImageOps
    pillow_heif.register_heif_opener()
    src.seek(0)
    img = ImageOps.exif_transpose(Image.open(src))
    out = io.BytesIO()
    img.convert("RGB").save(out, "JPEG", quality=88)
    out.seek(0)
    return out
