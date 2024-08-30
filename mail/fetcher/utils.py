import chardet
import email.message
import uuid
import logging

from bs4 import BeautifulSoup
from datetime import datetime
from django.core.files.base import ContentFile
from django.utils.text import get_valid_filename
from email.utils import parsedate_to_datetime as parse
from email.header import decode_header
from .models import EmailMessage, Attachment


def parse_date(date: str) -> datetime:
    """Clean up date text by removing garbage"""
    return parse(date.split('\n')[-1].split(';')[-1].strip()) if date else None


def get_sender_address(m: email.message.Message) -> str:
    """Get sender address with displayed name"""
    data = []
    for i in decode_header(m['From']):
        if isinstance(i[0], bytes):
            data.append(i[0].decode(chardet.detect(i[0])['encoding']))
        else:
            data.append(i[0])

    return ''.join(data)


def get_inbox_address(m: email.message.Message) -> str:
    """Get inbox address"""
    data = []
    inbox = m['Delivered-To'] or m['To']
    inbox = inbox.split(',')[-1].strip()
    for i in decode_header():
        if isinstance(i[0], bytes):
            data.append(i[0].decode(chardet.detect(i[0])['encoding']))
        else:
            data.append(i[0])

    return ''.join(data)


def parse_and_save_attachments(uid: str, m: email.message.Message) -> tuple[list, list]:
    """
    Parse and save attachment to db,
    returns file_names and file_uuids lists
    """
    file_names = []
    file_uuids = []
    for part in m.walk():

        content_disposition = str(part.get("Content-Disposition"))

        if "attachment" in content_disposition:
            filename = part.get_filename()
            file_uuid = str(uuid.uuid4())

            if filename:

                filename_decoded = decode_header(filename)[0][0]
                if isinstance(filename_decoded, bytes):
                    filename_decoded = filename_decoded.decode('utf-8')

                filename_decoded = get_valid_filename(filename_decoded)
                file_content = ContentFile(part.get_payload(decode=True),
                                           name=filename_decoded)

                Attachment.objects.create(
                    uuid=file_uuid,
                    email=EmailMessage.objects.get(uid=uid),
                    filename=filename_decoded,
                    file=file_content
                )

                file_names.append(filename_decoded)
                file_uuids.append(file_uuid)

    return file_names, file_uuids


def extract_text_from_email(msg: email.message.Message):
    text = ''
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() in ["text/plain", "text/html"]:
                text = part.get_payload(decode=True).decode('utf-8', errors='ignore')
    else:
        text = msg.get_payload(decode=True).decode('utf-8', errors='ignore')

    text = BeautifulSoup(text, 'html.parser').get_text().strip() or text or msg.as_string()
    text = (text.replace('\r\n', ' ')
            .replace('\t', ' ')
            .replace('⠀', ' ')  # Braille invisible
            .replace('\n', ' '))

    return ' '.join(text.split())


def decode_and_clean_values(data: dict) -> dict:
    """Clean and decode values from a dictionary."""

    for key, value in data.items():
        try:
            decoded_value = decode_header(value)[0][0].decode()
            cleaned_value = (decoded_value.replace('"', '')
                                        .replace("'", '')
                                        .replace('<', '')
                                        .replace('>', '')
                                        .replace('\x00', ''))  # NUL symbol
            data[key] = cleaned_value
            logging.debug(f'Decoded value: {value}')

        except UnicodeDecodeError:
            logging.debug(f'UnicodeDecodeError for value: {value}')
            decoded_value = decode_header(value)[0][0]
            result = chardet.detect(decoded_value)
            encoding = result['encoding']

            try:
                data[key] = decoded_value.decode(encoding)
            except TypeError:
                data[key] = value.replace('\x00', '')

        except Exception:
            logging.debug(f'Exception for value: {value}')
            if isinstance(value, str):
                data[key] = value.replace('\x00', '')
            else:
                data[key] = value

    return data
