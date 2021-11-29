import asyncio

from aiohttp import web
import math
import re
from telethon.client.downloads import MAX_CHUNK_SIZE
from config import Config


class Router:
    RANGE_REGEX = re.compile(r"bytes=([0-9]+)-")
    BLOCK_SIZE = MAX_CHUNK_SIZE
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
            link = f"{Config.DOMAIN}/{id_hex}"
            name = Config.CHANNEL_USERNAME
            return web.Response(
                text='<!DOCTYPE html><html lang=fa dir=rtl><head><meta charset=UTF-8><meta http-equiv=X-UA-Compatible content="IE=edge"><meta name=viewport content="width=device-width, initial-scale=1.0"><title>' + name + ' player</title><link rel=stylesheet href=https://miaadp.github.io/stream-cloud/style.css></head><body><div class=container-fluid><div class="container justify-content-center"><div class="mt-5 d-flex justify-content-center"><div class="row shadow p-3 mt-5 rounded justify-content-center"><div class="mb-3 d-flex justify-content-center"><video id=my-video class="video-js vjs-theme-forest" controls preload=metadata width=320 height=200 data-setup={}><source src="' + link + '" type=video/mp4></video></div><div class="mt-3 row"><div class="d-flex justify-content-center"><div class=mb-3><label for=formFile class="form-label text-white">بخش افزودن زیرنویس|Add subtitle</label><input class="form-control form-control-sm" type=file id=formFile name=fileItem accept=.srt,.vtt value=hiasfsa.srt><div class="mt-1 justify-content-center"><button class="btn btn-outline-light" type=button onclick=addSub()>آپلود|Upload</button></div></div></div></div></div></div></div></div><footer class="mt-3 text-white fixed-bottom" style=background-color:#000013><div class=container><div class=row><div class="mt-3 mt-2 d-flex justify-content-center"><p style=text-align:left;font-size:12px>Design by ' + name + '</p></div><div class="d-flex justify-content-center"><p style=text-align:left;font-size:10px>All Rights Reserved. &copy 2021</p></div></div></div></footer></body><script src=https://miaadp.github.io/stream-cloud/js.js></script></html>',
                content_type='text/html')
        else:
            return web.Response(text='message format is not mp4 or mkv , message format is ' + file_ext)

    async def download(self, file, offset, limit):
        part_size = 512 * 1024
        first_part_cut = offset % part_size
        first_part = math.floor(offset / part_size)
        last_part_cut = part_size - (limit % part_size)
        last_part = math.ceil(limit / part_size)
        part = first_part
        try:
            async for chunk in self.client.iter_download(file, offset=first_part * part_size, request_size=part_size):
                if part == first_part:
                    yield chunk[first_part_cut:]
                elif part == last_part:
                    yield chunk[:last_part_cut]
                else:
                    yield chunk
                part += 1
        except (GeneratorExit, StopAsyncIteration, asyncio.CancelledError):
            raise
        except Exception:
            raise

    async def Downloader(self, request):
        id_hex = request.match_info.get("id")

        try:
            id = int(id_hex, 16)
        except ValueError:
            return web.Response(text='Insert hex number')

        message = await self.client.get_messages(self.CHANNEL, ids=id)

        if not message or not message.file:
            return web.Response(text='id not found or its not file message')

        media = message.media
        size = message.file.size
        file_size = size
        file_name = request.match_info.get("name") or self.get_file_name(message)
        mime_type = message.file.mime_type

        try:
            range_header = request.headers.get('Range', 0)
            if range_header:
                range_data = range_header.replace('bytes=', '').split('-')
                from_bytes = int(range_data[0])
                until_bytes = int(range_data[1]) if range_data[1] else file_size - 1
            else:
                from_bytes = request.http_range.start or 0
                until_bytes = request.http_range.stop or file_size - 1

            req_length = until_bytes - from_bytes

            offset = from_bytes or 0
            limit = until_bytes or size
            if (limit > size) or (offset < 0) or (limit < offset):
                raise ValueError("range not in acceptable format")
        except ValueError:
            return web.Response(
                status=416,
                text="416: Range Not Satisfiable",
                headers={
                    "Content-Range": f"bytes */{size}"
                }
            )

        body = self.download(media, offset, limit)

        return_resp = web.Response(
            status=206 if request.http_range.start else 200,
            body=body,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Content-Type": mime_type,
                "Content-Range": f"bytes {offset}-{limit}/{size}",
                "Content-Disposition": f'attachment; filename="{file_name}"',
                "Accept-Ranges": "bytes",
                "Content-Length": f"{limit-offset}"
            }
        )

        if return_resp.status == 200:
            return_resp.headers.add("Content-Length", str(size))

        return return_resp
