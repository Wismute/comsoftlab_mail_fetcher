from django.db import models
from django.db.models import UniqueConstraint


class Mailbox(models.Model):
    address = models.CharField(primary_key=True, null=False, max_length=255)
    name = models.CharField(max_length=255)
    password = models.CharField(max_length=255)


class EmailMessage(models.Model):
    email_id = models.BigAutoField(primary_key=True)
    uid = models.IntegerField()
    from_inbox_address = models.ForeignKey(Mailbox, on_delete=models.CASCADE)
    sender_address = models.CharField(max_length=255)
    subject = models.CharField(max_length=255, null=True)
    date_sent = models.DateTimeField(null=True)
    date_received = models.DateTimeField(null=True)
    body = models.TextField(null=True)
    attachments_names = models.TextField(null=True)
    attachments_ids = models.TextField(null=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['uid', 'from_inbox_address'],
                name='uid_mailbox_unique',
            ),
        ]


class Attachment(models.Model):
    uuid = models.UUIDField(primary_key=True)
    email = models.ForeignKey(EmailMessage, related_name='attachments',
                              on_delete=models.CASCADE)
    file = models.FileField(upload_to='attachments/')
    filename = models.CharField(max_length=255)
