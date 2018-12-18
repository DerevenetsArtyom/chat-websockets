import aiohttp_jinja2
from aiohttp import web, WSMsgType
from aiohttp_session import get_session

from .models import Message
from ..auth.models import User


class ChatList(web.View):

    @aiohttp_jinja2.template('chat/index.html')
    async def get(self):
        message = Message(self.request.db)
        messages = await message.get_messages()
        return {'messages': messages}


class WebSocket(web.View):
    async def get(self):
        ws = web.WebSocketResponse()
        await ws.prepare(self.request)

        session = await get_session(self.request)
        user = User(self.request.db, {'id': session.get('user_id')})
        login = await user.get_login()

        for _ws in self.request.app['websockets']:
            _ws.send_str('%s joined' % login)
        self.request.app['websockets'].append(ws)

        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                if msg.data == 'close':
                    await ws.close()
                else:
                    message = Message(self.request.db)
                    result = await message.save(user=login, text=msg.data)
                    print('result', result)
                    for _ws in self.request.app['websockets']:
                        await _ws.send_str('(%s) %s' % (login, msg.data))
            elif msg.type == WSMsgType.ERROR:
                print('ws connection closed with exception %s' % ws.exception())

        self.request.app['websockets'].remove(ws)
        for _ws in self.request.app['websockets']:
            await _ws.send_str('%s disconected' % login)
        print('websocket connection closed')

        return ws
