import email.message

from .models import Mailbox, EmailMessage
from .utils import parse_date, get_sender_address
from .utils import decode_and_clean_values, extract_text_from_email
from .utils import parse_and_save_attachments


def get_last_fetched_email() -> EmailMessage | None:
    """Get last (newest) email message saved
    for currently set address in db, returns model"""
    mailbox = Mailbox.objects.first()
    return EmailMessage.objects.filter(from_inbox_address=mailbox).last()


def get_mailbox_creds() -> Mailbox | None:
    """Get first mailbox, returns model"""
    return Mailbox.objects.first()


def save_email(uid: str, m: email.message.Message) -> dict:
    """Parse email message data and add it to db, then return dict of it"""

    defaults = decode_and_clean_values({
        'sender_address': get_sender_address(m),
        'subject': m['Subject'],
        'date_sent': parse_date(m['Date']),
        'date_received': parse_date(m['Received']),
        'body': extract_text_from_email(m)
    })

    defaults['from_inbox_address'] = get_mailbox_creds()

    EmailMessage.objects.update_or_create(
        uid=uid,
        defaults=defaults
    )

    file_names, file_uuids = parse_and_save_attachments(uid, m)
    defaults['attachments_names'] = ', '.join(file_names)
    defaults['attachments_ids'] = ', '.join(file_uuids)
    EmailMessage.objects.filter(uid=uid).update(**defaults)

    defaults['uid'] = uid
    defaults['from_inbox_address'] = get_mailbox_creds().address
    defaults['date_sent'] = str(defaults['date_sent'])
    defaults['date_received'] = str(defaults['date_received'])

    return defaults
