from .AAA3A_utils.cogsutils import CogsUtils, Menu  # isort:skip
from redbot.core import commands  # isort:skip
import discord  # isort:skip
import typing  # isort:skip

import aiohttp

from redbot import VersionInfo
from redbot.core import Config

# Credits:
# Thanks to @epic guy on Discord for the basic syntax (command groups, commands) and also commands (await ctx.send, await ctx.author.send, await ctx.message.delete())!
# Thanks to the developers of the cogs I added features to as it taught me how to make a cog! (Chessgame by WildStriker, Captcha by Kreusada, Speak by Epic guy and Rommer by Dav)
# Thanks to all the people who helped me with some commands in the #coding channel of the redbot support server!

MEDICAT_GUILD = 829469886681972816
VENTOY_UPDATES_CHANNEL = 831224763162165278
MODERATORS_ROLE = 829472084454670346
DEVELOPER_ROLE = 883612487881195520
MEMBERS_ROLE = 829538904720932884

MEDICAT_GUILD = 886147551890399253
VENTOY_UPDATES_CHANNEL = 905737223348047914

def _(untranslated: str):
    return untranslated

class Medicat(commands.Cog):
    """This cog will only work on x server and therefore cannot be used by the general public!"""

    def __init__(self, bot):
        self.bot = bot

        self.config: Config = Config.get_conf(
            self,
            identifier=953864285308,
            force_registration=True,
        )
        self.medicat_global = {
            "last_ventoy_version": "1.0.73",
        }
        self.config.register_global(**self.medicat_global)

        self.cogsutils = CogsUtils(cog=self)
        self.cogsutils._setup()
        
        self.cogsutils.create_loop(function=self.ventoy_updates, name="Ventoy Updates", hours=1)

    async def ventoy_updates(self):
        guild = self.bot.get_guild(MEDICAT_GUILD)
        channel = guild.get_channel(VENTOY_UPDATES_CHANNEL)
        last_ventoy_version_str = str(await self.config.last_ventoy_version())
        last_ventoy_version = VersionInfo.from_str(last_ventoy_version_str)

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.github.com/repos/ventoy/Ventoy/git/refs/tags", timeout=3) as r:
                ventoy_tags = await r.json()
        versions = sorted(ventoy_tags, key=lambda ventoy_version: VersionInfo.from_str(str(ventoy_version["ref"]).replace("refs/tags/v", "").replace("1.0.0", "1.0.").replace("beta", ".dev"))).index(ventoy_version) + 1

        if last_ventoy_version >= str(ventoy_tags[len(ventoy_tags) - 1]["ref"].replace("refs/tags/v", "").replace("1.0.0", "1.0.").replace("beta", ".dev")):
            return
        await self.config.last_ventoy_version.set(str(ventoy_tags[len(ventoy_tags) - 1]["ref"]).replace("refs/tags/v", "").replace("1.0.0", "1.0.").replace("beta", ".dev"))

        for version in versions:
            ventoy_version_str = str(version["ref"]).replace("refs/tags/v", "").replace("1.0.0", "1.0.").replace("beta", ".dev")
            ventoy_version = VersionInfo.from_str(ventoy_version_str)
            if last_ventoy_version >= ventoy_version:
                continue
            message: str = f"Ventoy v{ventoy_version_str} has been released!\nhttps://ventoy.net/en/index.html"
            hook: discord.Webhook = await CogsUtils(bot=self.bot).get_hook(channel)
            message: discord.Message = await hook.send(content=message, username="Ventoy Updates", avatar_url="https://ventoy.net/static/img/ventoy.png?v=1")
            try:
                await message.publish()
            except discord.HTTPException:
                pass
