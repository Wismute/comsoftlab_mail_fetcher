import email.message
import imaplib
import email

from mail.settings import IMAP_SERVERS
from . import db_connector


def get_imap_server_by_address(address: str) -> str | None:
    domain_name = address.split('@')[1].split('.')[0]
    return IMAP_SERVERS.get(domain_name)


def get_imap_connection(address: str = None, password: str = None) -> imaplib.IMAP4_SSL:
    if address is None:
        creds = db_connector.get_mailbox_creds()
        address = creds.address
        password = creds.password

    imap_server = get_imap_server_by_address(address)
    imap = imaplib.IMAP4_SSL(imap_server)
    imap.login(address, password)
    imap.select("INBOX")
    return imap


def get_all_uids(imap: imaplib.IMAP4_SSL) -> list[int]:
    _, data = imap.uid('search', 'ALL')
    uid_list = data[0].decode().split()
    return list(map(int, uid_list)) if data[0] else []


def get_email_by_uid(uid: str, imap: imaplib.IMAP4_SSL) -> email.message.Message:
    _, data = imap.uid('fetch', uid, '(RFC822)')
    return email.message_from_bytes(data[0][1]) if data[0] else None
