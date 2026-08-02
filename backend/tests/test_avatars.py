from io import BytesIO

import pytest
from PIL import Image

from backend.app.avatars import (
    AVATAR_EDGE_PIXELS,
    MAX_AVATAR_UPLOAD_BYTES,
    AvatarValidationError,
    process_avatar_upload,
)


def test_avatar_upload_is_center_cropped_and_normalized_to_webp() -> None:
    source = BytesIO()
    Image.new("RGBA", (900, 500), (219, 171, 84, 170)).save(
        source,
        format="PNG",
    )

    payload, mime_type = process_avatar_upload(source.getvalue())

    assert mime_type == "image/webp"
    with Image.open(BytesIO(payload)) as avatar:
        assert avatar.format == "WEBP"
        assert avatar.size == (AVATAR_EDGE_PIXELS, AVATAR_EDGE_PIXELS)
        assert avatar.mode == "RGB"


@pytest.mark.parametrize(
    ("payload", "reason"),
    [
        (b"", "empty"),
        (b"not-an-image", "invalid_image"),
        (b"x" * (MAX_AVATAR_UPLOAD_BYTES + 1), "too_large"),
    ],
)
def test_avatar_upload_rejects_invalid_payloads(
    payload: bytes,
    reason: str,
) -> None:
    with pytest.raises(AvatarValidationError) as captured:
        process_avatar_upload(payload)

    assert captured.value.reason == reason
