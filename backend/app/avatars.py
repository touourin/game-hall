from __future__ import annotations

import warnings
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError


MAX_AVATAR_UPLOAD_BYTES = 8 * 1024 * 1024
MAX_AVATAR_PIXELS = 25_000_000
AVATAR_EDGE_PIXELS = 512
ACCEPTED_AVATAR_FORMATS = {"GIF", "JPEG", "PNG", "WEBP"}


class AvatarValidationError(ValueError):
    def __init__(self, message: str, *, reason: str) -> None:
        super().__init__(message)
        self.reason = reason


def process_avatar_upload(payload: bytes) -> tuple[bytes, str]:
    if not payload:
        raise AvatarValidationError("请选择头像图片", reason="empty")
    if len(payload) > MAX_AVATAR_UPLOAD_BYTES:
        raise AvatarValidationError(
            "头像图片不能超过 8 MB",
            reason="too_large",
        )

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(payload)) as source:
                if source.width * source.height > MAX_AVATAR_PIXELS:
                    raise AvatarValidationError(
                        "图片分辨率过大，请缩小后重试",
                        reason="pixel_limit",
                    )
                if source.format not in ACCEPTED_AVATAR_FORMATS:
                    raise AvatarValidationError(
                        "仅支持 JPEG、PNG、WebP 或 GIF 图片",
                        reason="unsupported_format",
                    )
                try:
                    source.seek(0)
                    upright = ImageOps.exif_transpose(source)
                    if upright.mode in {"RGBA", "LA"}:
                        rgba = upright.convert("RGBA")
                        background = Image.new("RGBA", rgba.size, "#0b2625")
                        background.alpha_composite(rgba)
                        prepared = background.convert("RGB")
                    else:
                        prepared = upright.convert("RGB")
                    square = ImageOps.fit(
                        prepared,
                        (AVATAR_EDGE_PIXELS, AVATAR_EDGE_PIXELS),
                        method=Image.Resampling.LANCZOS,
                        centering=(0.5, 0.5),
                    )
                    output = BytesIO()
                    square.save(
                        output,
                        format="WEBP",
                        quality=86,
                        method=6,
                    )
                finally:
                    if "upright" in locals() and upright is not source:
                        upright.close()
    except AvatarValidationError:
        raise
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as error:
        raise AvatarValidationError(
            "图片分辨率过大，请缩小后重试",
            reason="pixel_limit",
        ) from error
    except (OSError, UnidentifiedImageError, ValueError) as error:
        raise AvatarValidationError(
            "无法识别这张图片，请更换后重试",
            reason="invalid_image",
        ) from error
    return output.getvalue(), "image/webp"
