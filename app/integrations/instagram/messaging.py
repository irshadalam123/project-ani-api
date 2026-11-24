"""Private replies to a commenter.

Documented call: ``POST /<IG_ID>/messages`` with

    {"recipient": {"comment_id": "<COMMENT_ID>"}, "message": {"text": "..."}}

Host ``graph.instagram.com`` for Instagram Login. Authorization uses a Bearer
user token.

TODO(meta): Private replies must be sent within 7 days, and only one private
reply is allowed until the person responds. Live comments can only be replied
to during the broadcast. Confirm the permission set
(``instagram_business_manage_comments`` and, for the messages edge,
``instagram_business_manage_messages``) against the current private-reply guide.
"""


def private_reply_path(instagram_user_id: str) -> str:
    return f"{instagram_user_id}/messages"


def private_reply_body(comment_id: str, text: str) -> dict[str, object]:
    return {
        "recipient": {"comment_id": comment_id},
        "message": {"text": text},
    }
