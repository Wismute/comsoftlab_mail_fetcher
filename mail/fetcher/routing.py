from django.urls import path

from . import consumers

ws_urlpatterns = [
    path(r"ws/data/", consumers.WsConsumer.as_asgi()),
]
