"""Media reads.

TODO(meta): Confirm the field list ``id,caption,media_type,media_product_type,permalink``
for your login type. Some fields require extra permissions.
"""

MEDIA_FIELDS = "id,caption,media_type,media_product_type,permalink"


def media_path(media_id: str) -> str:
    return media_id
