from django.contrib import admin

from .models import Mailbox, EmailMessage, Attachment

admin.site.register(Mailbox)
admin.site.register(EmailMessage)
admin.site.register(Attachment)
