from .models import Recipient


def get_recipient_url(recipient):
    if hasattr(recipient, "get_absolute_url"):
        return recipient.get_absolute_url()
    recipient = Recipient(**recipient.dict())
    return recipient.get_absolute_url()
