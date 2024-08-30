import json
import imaplib
import logging
import socket

from . import db_connector
from . import imap_connector
from asyncio import sleep as a_sleep
from asgiref.sync import sync_to_async as sta
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async as db

fmt = '%(asctime)s - %(name)s: - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=fmt)


class WsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(
            "mail_fetching",
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            "mail_fetching",
            self.channel_name
        )
        await self.close()

    async def receive(self, text_data: str):
        message = json.loads(text_data)['message']
        await self.process_message(message)

    async def process_message(self, message: str):
        """Consumer function with common logic"""

        async def send_msg(self, text: str):
            """Shortcut to send to WS"""
            await self.send(text_data=json.dumps({
                'message': text
            }))

        # Start fetching command
        if message == 'start_fetching':

            await send_msg(self, 'Входим в почту..')

            try:
                imap = await sta(imap_connector.get_imap_connection)()
            except socket.gaierror as e:
                await send_msg(self, f'Вы под VPN?: {e}')
                await a_sleep(10)
                await self.close()
                return

            await send_msg(self, 'Чтение сообщений..')

            last_email = await db(db_connector.get_last_fetched_email)()
            last_email_uid = last_email.uid if last_email else 0
            uids = await sta(imap_connector.get_all_uids)(imap)

            # If there are emails we already fetched,
            # filter to fetch only new ones
            if last_email_uid > 0:
                uids = [uid for uid in uids if uid > last_email_uid]
            await self.fetch_new_messages(uids, imap)

    async def fetch_new_messages(self, uids: list[str],
                                 imap: imaplib.IMAP4_SSL):
        count = 1
        total = len(uids)

        for uid in uids:
            # Check if the WebSocket connection is still active
            if not self.channel_layer:
                logging.info('Channel layer disconnected')
                await self.close()
                break

            try:
                # Fetch and save the message
                logging.debug(f'uid: {uid}')
                email = await sta(imap_connector.get_email_by_uid)(uid, imap)
                saved_email = await db(db_connector.save_email)(uid, email)

                # Send data and progress
                await self.send(text_data=json.dumps({
                    'message': 'Получение сообщений',
                    'email': saved_email,
                    'count': count,
                    'total': total
                }))
            except Exception as e:
                logging.error(f'Exception in fetch_new_messages(): {e}')

            count += 1

        # If no new messages, close connection
        if len(uids) == 0:
            logging.info('No new messages')
            message = 'Нет новых сообщений'
        else:
            logging.info('Finished')
            message = 'Готово'

        await self.send(text_data=json.dumps({
            'message': message
        }))

        imap.close()
        imap.logout()
        await a_sleep(10)
        await self.close()
