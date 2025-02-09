import asyncio
from discord.ext import commands
import aiohttp
import pymongo
import os
from dotenv import load_dotenv

load_dotenv()

mongo = pymongo.MongoClient(os.getenv("MONGO_URI"))
db = mongo["erlc_checker"]
class ServerLinkNotFound(commands.CheckFailure):
    pass

class ResponseFailed(Exception):
    detail: str | None
    code: int | None
    data: str

    def __init__(self, data: str, detail: str | None = None, code: int | None = None, *args, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self) -> str:
        return f"ResponseFailed(data={self.data}, detail={self.detail}, code={self.code})"

class ServerStatus():
    Name: str | None = None
    OwnerId: int | None = None
    CoOwnerIds: list[int] | None = None
    CurrentPlayers: int | None = None
    MaxPlayers: int | None = None
    JoinKey: str | None = None
    AccVerifiedReq: str = ""
    TeamBalance: bool = False

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
class ServerPlayers():
    Player: str | None
    Permission: str
    Callsign: str | None
    Team: str | None

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class ServerJoinLogs():
    Join: bool
    Timestamp: int
    Player: str | None

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class ServerQueue():
    total_players: int

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class ServerKillLogs():
    killed: str | None
    timestamp: int
    killer: str | None

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class ServerCommandLogs():
    player: str | None
    timestamp: int
    command: str | None


class ServerModCalls():
    caller: str | None
    moderator: str | None
    timestamp: int

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class ServerBans():
    player_id: int

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class ServerVehicles():
    texture: str | None
    name: str | None
    owner: str | None

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class ServerCommand():
    command: str | None

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class PRC_API_Client:
    def __init__(self, bot, base_url: str, api_key: str):
        self.bot = bot
        self.base_url = base_url
        self.api_key = api_key
        self.session = aiohttp.ClientSession()

    async def close(self):
        await self.session.close()

    async def fetch_server_key(self, server_id: int):
        server_key = await self.bot.settings.db.find_one({"guild_id": str(server_id)})

        if not server_key:
            print(f"Server key not found for {server_id}")
            return None
        
        print(f"Fetching server key for {server_id}: {"Found" if server_key else "Not Found"}")
        return server_key

    async def _send_request(self, method: str, endpoint: str, server_id: int, **kwargs):
        server_key = await self.fetch_server_key(server_id)
        if not server_key or "api_key" not in server_key:
            print(f"Skipping {server_id} due to missing server key")
        async with self.session.request(method, f"{self.base_url}/{endpoint}", headers={
            "Server-Key": server_key['api_key']
            }, **kwargs) as resp:
            data = await resp.json()
            if resp.status == 200:
                return data
            elif resp.status == 429:
                print(f"Rate limited on {server_id}")
            elif resp.status == 400:
                print(f"Bad request on {server_id}")
            elif resp.status == 403:
                print(f"Unauthorized on {server_id}")
            elif resp.status == 422:
                print(f"Unprocessable entity on {server_id}")
            elif resp.status == 500:
                print(f"Internal server error on {server_id}")
            else:
                print(f"Error Details: {data.get('detail')}")
            
    async def _send_test_request(self, api_key: str):
        async with self.session.request("GET", f"{self.base_url}/server", headers={"Server-Key": api_key}) as resp:
            if resp.status == 200:
                return True
            return False

    async def _fetch_server_status(self, server_id: int):
        return ServerStatus(**await self._send_request("GET", "server", server_id))

    async def _fetch_server_players(self, server_id: int):
        return [ServerPlayers(**x) for x in await self._send_request("GET", "server/players", server_id)]

    async def _fetch_server_join_logs(self, server_id: int):
        return [ServerJoinLogs(**x) for x in await self._send_request("GET", "server/joinlogs", server_id)]

    async def _fetch_server_queue(self, server_id: int):
        return ServerQueue(**await self._send_request("GET", "server/queue", server_id))
    
    async def _fetch_server_killlogs(self, server_id: int):
        return [ServerKillLogs(**x) for x in await self._send_request("GET", "server/killlogs", server_id)]

    async def _fetch_server_commandlogs(self, server_id: int):
        return ServerCommandLogs(**await self._send_request("GET", "server/commandlogs", server_id))

    async def _fetch_server_modcalls(self, server_id: int):
        return [ServerModCalls(**x) for x in await self._send_request("GET", "server/modcalls", server_id)]

    async def _fetch_server_bans(self, server_id: int):
        return [ServerBans(**x) for x in await self._send_request("GET", "server/bans", server_id)]

    async def _fetch_server_vehicles(self, server_id: int):
        return [ServerVehicles(**x) for x in await self._send_request("GET", "server/vehicles", server_id)]
    
    async def _send_command(self, server_id: int, command: str):
        return await self._send_request("POST", "server/command", server_id, json={"command": command})
    
    async def _send_message_command(self, server_id:int, command:str):
        return await self._send_request("POST", "server/command", server_id, json={"command": ":m"+command})
    
    async def _send_hint_command(self, server_id:int, command: str):
        return await self._send_request("POST", "server/command", server_id, json={"command": ":h"+command})