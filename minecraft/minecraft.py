from .AAA3A_utils import CogsUtils, Menu  # isort:skip
from redbot.core import commands  # isort:skip
from redbot.core import Config  # isort:skip
from redbot.core.i18n import Translator, cog_i18n  # isort:skip
from redbot.core.bot import Red  # isort:skip
import discord  # isort:skip
import typing  # isort:skip

import aiohttp
import asyncio
import base64
import json
import re
from io import BytesIO
from mcstatus import JavaServer
from uuid import UUID

from redbot.core.utils.chat_formatting import box, pagify

# Credits:
# Thanks to Fixator for the code to get informations about Minecraft servers (https://github.com/fixator10/Fixator10-Cogs/blob/V3/minecraftdata/minecraftdata.py)!
# Thanks to @epic guy on Discord for the basic syntax (command groups, commands) and also commands (await ctx.send, await ctx.author.send, await ctx.message.delete())!
# Thanks to @YamiKaitou on Discord for the technique in the init file to load the interaction client only if it is not loaded! Before this fix, when a user clicked on a button, the actions would be launched about 10 times, which caused huge spam and a loop in the channel.
# Thanks to the developers of the cogs I added features to as it taught me how to make a cog! (Chessgame by WildStriker, Captcha by Kreusada, Speak by Epic guy and Rommer by Dav)
# Thanks to all the people who helped me with some commands in the #coding channel of the redbot support server!

_ = Translator("Minecraft", __file__)

if CogsUtils().is_dpy2:
    from functools import partial

    hybrid_command = partial(commands.hybrid_command, with_app_command=False)
    hybrid_group = partial(commands.hybrid_group, with_app_command=False)
else:
    hybrid_command = commands.command
    hybrid_group = commands.group

class MCPlayer:
    def __init__(self, name: str, uuid: str):
        self.name = name
        self.uuid = uuid
        self.dashed_uuid = str(UUID(self.uuid))

    def __str__(self):
        return self.name

    @classmethod
    async def convert(cls, ctx, argument):
        try:
            async with ctx.cog.session.get(
                f"https://api.mojang.com/users/profiles/minecraft/{argument}",
                raise_for_status=True,
            ) as data:
                response_data = await data.json(loads=json.loads)
        except aiohttp.ContentTypeError:
            response_data = None
        except aiohttp.ClientResponseError as e:
            raise commands.BadArgument(_("Unable to get data from Minecraft API: {}").format(e.message))
        if response_data is None or "id" not in response_data:
            raise commands.BadArgument(_("{} not found on Mojang servers.").format(argument))
        uuid = str(response_data["id"])
        name = str(response_data["name"])
        try:
            return cls(name, uuid)
        except ValueError:
            raise commands.BadArgument(_("{} is found, but has incorrect UUID.").format(argument))

@cog_i18n(_)
class Minecraft(commands.Cog):
    """A cog to display informations about Minecraft Java users and servers!"""

    def __init__(self, bot: Red):
        self.bot: Red = bot
        self.session = None
        self.cache = {}

        self.config: Config = Config.get_conf(
            self,
            identifier=205192943327321000143939875896557571750,
            force_registration=True,
        )
        self.minecraft_channel = {
            "servers": [],
        }
        self.config.register_channel(**self.minecraft_channel)

        self.cogsutils = CogsUtils(cog=self)

    async def cog_load(self):
        self.session = aiohttp.ClientSession(json_serialize=json.dumps)
        self.cogsutils.create_loop(self.check_servers, name="Minecraft Servers Checker", minutes=1)

    if CogsUtils().is_dpy2:
        async def cog_unload(self):
            self.bot.loop.create_task(self.session.close())
            self.cogsutils._end()
    else:
        def cog_unload(self):
            self.bot.loop.create_task(self.session.close())
            self.cogsutils._end()

    async def check_servers(self):
        all_channels = await self.config.all_channels()
        for channel_id in all_channels:
            channel = self.bot.get_channel(channel_id)
            if channel is None:
                continue
            if channel.id not in self.cache:
                self.cache[channel.id] = {}
            servers = all_channels[channel_id]["servers"]
            for server_url in servers:
                try:
                    server: JavaServer = await self.bot.loop.run_in_executor(None, JavaServer.lookup, server_url)
                    status = await server.async_status()
                except (asyncio.CancelledError, TimeoutError):
                    continue
                except Exception as e:
                    self.log.error(f"No data found for {server_url} server in {channel.id} channel in {channel.guild.id} guild.", exc_info=e)
                    continue
                players = {player["id"]: player for player in status.raw["players"]["sample"]}
                players = [players[_id] for _id in set(list(players.keys()))]
                status.raw["players"]["sample"] = players
                if server_url not in self.cache[channel.id]:
                    self.cache[channel.id][server_url] = {"server": server, "status": status}
                    continue
                if not status.raw == self.cache[channel.id][server_url]["status"].raw:
                    if "This server is offline." in (await self.clear_mcformatting(status.description)) and "This server is offline." in (await self.clear_mcformatting(self.cache[channel.id][server_url]["status"].description)):  # Minecraft ADS
                        continue
                    embed, icon = await self.get_embed(server, status)
                    await channel.send(embed=embed, file=icon)
                    self.cache[channel.id][server_url] = {"server": server, "status": status}

    async def get_embed(self, server: JavaServer, status):
        embed: discord.Embed = discord.Embed(
            title=f"{server.address.host}:{server.address.port}",
            description=box(await self.clear_mcformatting(status.description)),
        )
        icon_file = None
        icon = (
            discord.File(
                icon_file := BytesIO(base64.b64decode(status.favicon.split(",", 1)[1])),
                filename="icon.png",
            )
            if status.favicon
            else None
        )
        if icon:
            embed.set_thumbnail(url="attachment://icon.png")
        embed.add_field(name=_("Latency"), value=f"{status.latency:.2f} ms")
        embed.add_field(
            name=_("Players"),
            value="{0.players.online}/{0.players.max}\n{1}".format(
                status,
                box(
                    list(
                        pagify(
                            await self.clear_mcformatting(
                                "\n".join([p.name for p in status.players.sample])
                            ),
                            page_length=992,
                        )
                    )[0]
                )
                if status.players.sample
                else "",
            ),
        )
        embed.add_field(
            name=_("Version"),
            value=("{}" + "\n" + _("Protocol: {}")).format(
                status.version.name, status.version.protocol
            ),
        )
        if icon_file is not None:
            icon_file.close()
        return embed, icon

    async def clear_mcformatting(self, formatted_str) -> str:
        """Remove Minecraft-formatting"""
        if not isinstance(formatted_str, dict):
            return re.sub(r"\xA7[0-9A-FK-OR]", "", formatted_str, flags=re.IGNORECASE)
        clean = ""
        async for text in self.gen_dict_extract("text", formatted_str):
            clean += text
        return re.sub(r"\xA7[0-9A-FK-OR]", "", clean, flags=re.IGNORECASE)

    async def gen_dict_extract(self, key: str, var: dict):
        if not hasattr(var, "items"):
            return
        for k, v in var.items():
            if k == key:
                yield v
            if isinstance(v, dict):
                async for result in self.gen_dict_extract(key, v):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    async for result in self.gen_dict_extract(key, d):
                        yield result

    @commands.admin()
    @hybrid_group()
    async def minecraft(self, ctx: commands.Context):
        """Get informations about Minecraft Java."""
        pass

    @minecraft.command()
    async def getplayerskin(self, ctx: commands.Context, player: MCPlayer, overlay: typing.Optional[bool] = False):
        """Get Minecraft Java player skin by name."""
        uuid = player.uuid
        stripname = player.name.strip("_")
        files = []
        try:
            async with self.session.get(
                f"https://crafatar.com/renders/head/{uuid}",
                params="overlay" if overlay else None,
            ) as s:
                files.append(
                    discord.File(
                        head_file := BytesIO(await s.read()), filename=f"{stripname}_head.png"
                    )
                )
            async with self.session.get(f"https://crafatar.com/skins/{uuid}") as s:
                files.append(
                    discord.File(
                        skin_file := BytesIO(await s.read()), filename=f"{stripname}.png"
                    )
                )
            async with self.session.get(
                f"https://crafatar.com/renders/body/{uuid}.png",
                params="overlay" if overlay else None,
            ) as s:
                files.append(
                    discord.File(
                        body_file := BytesIO(await s.read()), filename=f"{stripname}_body.png"
                    )
                )
            head_file.close()
            skin_file.close()
            body_file.close()
        except aiohttp.ClientResponseError as e:
            raise commands.UserFeedbackCheckFailure(_("Unable to get data from Crafatar: {}").format(e.message))
        embed: discord.Embed = discord.Embed(timestamp=ctx.message.created_at, color=await ctx.embed_color())
        embed.set_author(
            name=player.name,
            icon_url=f"attachment://{stripname}_head.png",
            url=f"https://crafatar.com/skins/{uuid}",
        )
        embed.set_thumbnail(url=f"attachment://{stripname}.png")
        embed.set_image(url=f"attachment://{stripname}_body.png")
        embed.set_footer(text=_("Provided by Crafatar."), icon_url="https://crafatar.com/logo.png")
        await ctx.send(embed=embed, files=files)

    @minecraft.command()
    async def getserver(self, ctx: commands.Context, server_url: str):
        """Get informations about a Minecraft Java server."""
        try:
            server: JavaServer = await self.bot.loop.run_in_executor(None, JavaServer.lookup, server_url.lower())
            status = await server.async_status()
        except Exception:
            raise commands.UserFeedbackCheckFailure(_("No data could be found on this Minecraft server. Maybe it doesn't exist or the data is temporarily unavailable."))
        embed, icon = await self.get_embed(server, status)
        await ctx.send(embed=embed, file=icon)

    @minecraft.command()
    async def addserver(self, ctx: commands.Context, channel: typing.Optional[discord.TextChannel], server_url: str):
        """Add a Minecraft Java server in Config to get automatically new status."""
        if channel is None:
            channel = ctx.channel
        servers = await self.config.channel(channel).servers()
        if server_url.lower() in servers:
            raise commands.UserFeedbackCheckFailure(_("This server has already been added."))
        servers.append(server_url.lower())
        await self.config.channel(channel).servers.set(servers)

    @minecraft.command()
    async def removeserver(self, ctx: commands.Context, channel: typing.Optional[discord.TextChannel], server_url: str):
        """Remove a Minecraft Java server in Config."""
        if channel is None:
            channel = ctx.channel
        servers = await self.config.channel(channel).servers()
        if server_url.lower() not in servers:
            raise commands.UserFeedbackCheckFailure(_("This server isn't in the Config."))
        servers.remove(server_url.lower())
        await self.config.channel(channel).servers.set(servers)

    @commands.is_owner()
    @minecraft.command()
    async def forcecheck(self, ctx: commands.Context):
        """Force check Minecraft Java servers in Config."""
        await self.check_servers()

    @commands.is_owner()
    @commands.bot_has_permissions(embed_links=True)
    @minecraft.command(hidden=True)
    async def getdebugloopsstatus(self, ctx: commands.Context):
        """Get an embed for check loop status."""
        embeds = []
        for loop in self.cogsutils.loops.values():
            embeds.append(loop.get_debug_embed())
        await Menu(pages=embeds).start(ctx)
