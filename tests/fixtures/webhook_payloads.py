"""Sample webhook bodies used by tests and local mock runs."""

SIMPLIFIED_GUIDE_COMMENT = {
    "comment_id": "comment_123",
    "media_id": "media_123",
    "instagram_user_id": "user_456",
    "username": "testuser",
    "text": "GUIDE",
}

OFFICIAL_COMMENT = {
    "object": "instagram",
    "entry": [
        {
            "id": "<YOUR_APP_USERS_INSTAGRAM_ACCOUNT_ID>",
            "time": 1710000000,
            "field": "comments",
            "value": {
                "id": "17800000000000000",
                "text": "guide",
                "from": {"id": "17811111111111111", "username": "commenter"},
                "media": {"id": "17822222222222222", "media_product_type": "FEED"},
            },
        }
    ],
}
