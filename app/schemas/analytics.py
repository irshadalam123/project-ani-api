"""Analytics response schemas."""

from pydantic import BaseModel


class AnalyticsOverviewData(BaseModel):
    comments_received: int
    comments_matched: int
    automations_triggered: int
    public_replies_sent: int
    private_replies_sent: int
    messages_sent: int
    failed_messages: int
    link_clicks: int
    leads: int


class AnalyticsOverviewResponse(BaseModel):
    success: bool = True
    data: AnalyticsOverviewData
