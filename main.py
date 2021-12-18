import api
from aiohttp import web

server = api.Client()

async def main():
    app = web.Application()
    app.add_routes(
        [
            web.get('/', server.hello),
            web.get('/favicon.ico', server.Fav),
            #web.get('/player/{id}', server.Player),
            #web.get('/player/{id}/', server.Player),
            web.get('/{id}', server.Downloader),
            web.get('/{id}/', server.Downloader),
            web.get('/{id}/{name}', server.Downloader),
        ]
    )
    return app

if __name__ == "__main__":
    web.run_app(main())
