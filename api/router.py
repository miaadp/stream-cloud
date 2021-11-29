from aiohttp import web
import re

class Router:
    RANGE_REGEX = re.compile(r"bytes=([0-9]+)-")
    BLOCK_SIZE = 1048576
    ext_attachment = [".mp4", ]

    async def hello(self, request):
        return web.Response(text='<h1>Hello babe!</h1>', content_type='text/html')

    async def Fav(self, request):
        return web.Response(text='favicon not found')

    async def Player(self, request):
        id_hex = request.match_info.get("id")
        try:
            id = int(id_hex, 16)
        except ValueError:
            return web.Response(text='Insert hex number')

        message = await self.client.get_messages(self.CHANNEL, ids=id)
        if not message or not message.file:
            return web.Response(text='id not found or its not file message')

        file_ext = message.file.ext
        if file_ext in [".mp4", ".mpv", ".mkv"]:
            link = f"{self.DOMAIN}/{id_hex}"
            name = self.CHANNEL_USERNAME
            return web.Response(text='<!DOCTYPE html><html lang=fa dir=rtl><head><meta charset=UTF-8><meta http-equiv=X-UA-Compatible content="IE=edge"><meta name=viewport content="width=device-width, initial-scale=1.0"><title>' + name + ' player</title><link rel=stylesheet href=https://miaadp.github.io/stream-cloud/style.css></head><body><div class=container-fluid><div class="container justify-content-center"><div class="mt-5 d-flex justify-content-center"><div class="row shadow p-3 mt-5 rounded justify-content-center"><div class="mb-3 d-flex justify-content-center"><video id=my-video class="video-js vjs-theme-forest" controls preload=metadata width=320 height=200 data-setup={}><source src="' + link + '" type=video/mp4></video></div><div class="mt-3 row"><div class="d-flex justify-content-center"><div class=mb-3><label for=formFile class="form-label text-white">بخش افزودن زیرنویس|Add subtitle</label><input class="form-control form-control-sm" type=file id=formFile name=fileItem accept=.srt,.vtt value=hiasfsa.srt><div class="mt-1 justify-content-center"><button class="btn btn-outline-light" type=button onclick=addSub()>آپلود|Upload</button></div></div></div></div></div></div></div></div><footer class="mt-3 text-white fixed-bottom" style=background-color:#000013><div class=container><div class=row><div class="mt-3 mt-2 d-flex justify-content-center"><p style=text-align:left;font-size:12px>Design by ' + name + '</p></div><div class="d-flex justify-content-center"><p style=text-align:left;font-size:10px>All Rights Reserved. &copy 2021</p></div></div></div></footer></body><script src=https://miaadp.github.io/stream-cloud/js.js></script></html>',content_type='text/html')
        else:
            return web.Response(text='message format is not mp4 or mkv , message format is ' + file_ext)

    async def Downloader(self, request):
        id_hex = request.match_info.get("id")

        try:
            id = int(id_hex, 16)
        except ValueError:
            return web.Response(text='Insert hex number')

        message = await self.client.get_messages(self.CHANNEL, ids=id)
        if not message or not message.file:
            return web.Response(text='id not found or its not file message')

        offset = request.headers.get("Range", 0)
        if not isinstance(offset, int):
            matches = self.RANGE_REGEX.search(offset)
            if matches is None:
                return web.Response(text='xxxxxxxxxxxxxxxx1xxxxxxxxxxxxxxxxxxxxxxxx')
            offset = matches.group(1)
            if not offset.isdigit():
                return web.Response(text='xxxxxxxxxxxxxxxx2xxxxxxxxxxxxxxxxxxxxxxxx')
            offset = int(offset)

        file_size = message.file.size
        file_ext = message.file.ext
        download_skip = (offset // self.BLOCK_SIZE) * self.BLOCK_SIZE
        read_skip = offset - download_skip
        rem_size = file_size-offset

        if download_skip >= file_size:
            return web.Response(text='xxxxxxxxxxxxxxxxxxx3xxxxxxxxxxxxxxxxxxxxx')
        if read_skip > self.BLOCK_SIZE:
            return web.Response(text='xxxxxxxxxxxxxxxxxxx4xxxxxxxxxxxxxxxxxxxxx')

        name = request.match_info.get("name") or self.get_file_name(message)
        resp = web.StreamResponse(
            headers={
                'Content-Type': message.file.mime_type,
                'Accept-Ranges': 'bytes',
                'Content-Range': f'bytes {offset}-{file_size}/{file_size}',
                "Content-Length": str(rem_size),
                "Content-Disposition": f'attachment; filename={name}' if file_ext in self.ext_attachment else f'inline; filename={name}',
            },
            status=206 if offset else 200,
        )
        await resp.prepare(request)

        cls = self.client.iter_download(message.media, offset=download_skip)
        async for part in cls:
            if len(part) < read_skip:
                read_skip -= len(part)
            elif read_skip:
                await resp.write(part[read_skip:])
                read_skip = 0
            else:
                await resp.write(part)
        web.Response(text='xxxxxxxxxxxxxxxxxxx5xxxxxxxxxxxxxxxxxxxxx')
        return resp
