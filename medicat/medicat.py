from .AAA3A_utils.cogsutils import CogsUtils, Menu  # isort:skip
from redbot.core import commands  # isort:skip
import discord  # isort:skip
import typing  # isort:skip

import aiohttp
import os
import textwrap
import traceback

from copy import copy
from redbot import VersionInfo
from redbot.core import Config
from redbot.core.utils.chat_formatting import box, pagify

# Credits:
# Thanks to @epic guy on Discord for the basic syntax (command groups, commands) and also commands (await ctx.send, await ctx.author.send, await ctx.message.delete())!
# Thanks to the developers of the cogs I added features to as it taught me how to make a cog! (Chessgame by WildStriker, Captcha by Kreusada, Speak by Epic guy and Rommer by Dav)
# Thanks to all the people who helped me with some commands in the #coding channel of the redbot support server!

MEDICAT_GUILD = 829469886681972816
VENTOY_UPDATES_CHANNEL = 831224763162165278
MODERATORS_ROLE = 829472084454670346
DEVELOPER_ROLE = 883612487881195520
MEMBERS_ROLE = 829538904720932884

TEST_GUILD = 886147551890399253
# MEDICAT_GUILD = 886147551890399253
# VENTOY_UPDATES_CHANNEL = 905737223348047914

CUSTOM_COMMANDS = {
    "customtools": {"title": "How to add your own bootable tools (iso, wim, vhd) to Medicat USB?", "description": "To add your own bootable tools to Medicat USB, simply put the files in any sub-folder (except those with a `.ventoyignore` file at their root) of your USB stick. As if by magic, the new tools will appear on the Ventoy menu.\nThen you can add a custom name, icon, description, by editing the `USB\\ventoy\\ventoy.json` file following the template."},
    "kofi": {"title": "How to make a donation?", "description": "Jayro (Creator of Medicat): https://ko-fi.com/jayrojones\nMON5TERMATT (Medicat Developer): https://ko-fi.com/mon5termatt\nAAA3A (Medicat Developer): None"},
    "medicatversion": {"title": "What is the latest version of Medicat USB?", "description": "The latest version of Medicat USB is 21.12!\n||https://gbatemp.net/threads/medicat-usb-a-multiboot-linux-usb-for-pc-repair.361577/||"},
    "menus": {"title": "How to download one of the menus?", "description": "Here are the latest links to download the latest versions of the menus:\n- Jayro's Lockîck: \n<https://mega.nz/file/ZtpwEDhR#4bCjUDri2hhUlCgv8Y1EmZVyUnGyhqZjCo0fazXLzqY>\n- AAA3A's Backup: \n<https://mega.nz/file/s8hATRbZ#C28qA8HWKi_xikC6AUG46DiXKIG2Qjl__-4MOl6SI7w>\n- AAA3A's Partition: \n<https://mega.nz/file/w8oFkKYQ#5BbIf7K6pyxYDlE6L4efPqtHUWtCMmx_kta_QHejhpk>\nHere is also a link that should never change to access the same folder containing all the menus: \n<https://mega.nz/folder/FtRCgLQL#KTq897WQiXCJT8OQ3cT9Tg>"},
    "usbvhd": {"title": "What is the difference between Medicat USB and Medicat VHD?", "description": "Medicat USB is a bootable menu that runs on Ventoy and contains all the necessary tools for computer troubleshooting. It contains for example Malwarebytes bootable for virus scans, Mini Windows 10 for a winPE utility and Jayro's Lockpick for all things password related.\n<https://gbatemp.net/threads/medicat-usb-a-multiboot-linux-usb-for-pc-repair.361577/>\nMedicat VHD is a full-featured windows, using the real performance of the computer. It is therefore much more powerful than Mini Windows 10. Moreover, all data is saved and you can find it again at each reboot. (Not intended to be used as an operating system).\n<https://gbatemp.net/threads/official-medicat-vhd-a-usb-bootable-windows-10-virtual-harddisk-for-pc-repair.581637/>\nJayro's Lockpick is a winPE with a menu containing all the necessary tools to remove/bypass/retrieve a Windows password or even for a server.\n<https://gbatemp.net/threads/release-jayros-lockpick-a-bootable-password-removal-suite-winpe.579278/>\nMalwarebytes bootable is a very powerful antivirus. Since it is launched from a winPE, a potential virus cannot prevent it from running properly.\n<https://gbatemp.net/threads/unofficial-malwarebytes-bootable.481046/>"},
    "virus": {"title": "Why does my antivirus software blame Medicat?", "description": "Medicat USB does not contain any viruses! If an antivirus software detects one of its files as such, it is a false positive. As you know, Medicat USB contains tools that can reset a partition, find a password, and modify the system. Portable applications can be falsely flagged because of how they are cracked and packaged. For these reasons all antivirus software's 'real-time scanning' should be disabled when installing, and sometimes even when using, Medicat USB."},
    "whatmedicat": {"title": "What is Medicat USB?", "description": "Medicat USB contains tools to backup/restore data, to manage disks/partitions, to reset/bypass/find a Windows password, to use software with admin rights from a winPE, to do virus scans. In addition, it uses Ventoy, which allows you to add your own bootable tools with a simple copy and paste."}
}
CUSTOM_COMMANDS = {
    "customtools": {"title": "How to add your own bootable tools (iso, wim, vhd) to Medicat USB?", "description": "a"},
    "kofi": {"title": "How to make a donation?", "description": "b"},
    "medicatversion": {"title": "What is the latest version of Medicat USB?", "description": "c"},
    "menus": {"title": "How to download one of the menus?", "description": "d"},
    "usbvhd": {"title": "What is the difference between Medicat USB and Medicat VHD?", "description": "e"},
    "virus": {"title": "Why does my antivirus software blame Medicat?", "description": "f"},
    "whatmedicat": {"title": "What is Medicat USB?", "description": "g"}
}

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

        self.__func_red__ = ["cog_unload"]
        self.cogsutils = CogsUtils(cog=self)
        self.cogsutils._setup()

        self.cogsutils.create_loop(function=self.ventoy_updates, name="Ventoy Updates", hours=1)
        try:
            self.add_custom_commands()
        except Exception as e:
            self.log.error(f"An error occurred while adding the custom_commands.", exc_info=e)

    def cog_unload(self):
        try:
            self.remove_custom_commands()
        except Exception as e:
            self.log.error(f"An error occurred while removing the custom_commands.", exc_info=e)
        self.cogsutils._end()

    async def ventoy_updates(self):
        guild = self.bot.get_guild(MEDICAT_GUILD)
        if guild is None:
            return
        channel = guild.get_channel(VENTOY_UPDATES_CHANNEL)
        last_ventoy_version_str = str(await self.config.last_ventoy_version())
        last_ventoy_version = VersionInfo.from_str(last_ventoy_version_str)

        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.github.com/repos/ventoy/Ventoy/git/refs/tags", timeout=3) as r:
                ventoy_tags = await r.json()
        versions = sorted(ventoy_tags, key=lambda ventoy_version: VersionInfo.from_str(str(ventoy_version["ref"]).replace("refs/tags/v", "").replace("1.0.0", "1.0.").replace("beta", ".dev")))  # .index(ventoy_version) + 1

        if last_ventoy_version >= VersionInfo.from_str(str(ventoy_tags[len(ventoy_tags) - 1]["ref"]).replace("refs/tags/v", "").replace("1.0.0", "1.0.").replace("beta", ".dev")):
            return
        await self.config.last_ventoy_version.set(str(ventoy_tags[len(ventoy_tags) - 1]["ref"]).replace("refs/tags/v", "").replace("1.0.0", "1.0.").replace("beta", ".dev"))

        for version in versions:
            ventoy_tag_name = str(version["ref"]).replace("refs/tags/", "")
            ventoy_version_str = ventoy_tag_name.replace("v", "").replace("1.0.0", "1.0.").replace("beta", ".dev")
            ventoy_version = VersionInfo.from_str(ventoy_version_str)
            if last_ventoy_version >= ventoy_version:
                continue

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"https://api.github.com/repos/ventoy/Ventoy/releases/tags/{ventoy_tag_name}", timeout=3) as r:
                        ventoy_tag_body = str((await r.json())["body"])
            except Exception:
                ventoy_tag_body = None

            message: str = f"Ventoy v{ventoy_version_str} has been released!\nhttps://ventoy.net/en/index.html"
            if ventoy_tag_body is not None:
                ventoy_tag_body = ventoy_tag_body.split("\n")
                result = []
                for x in ventoy_tag_body:
                    if x == "See [https://www.ventoy.net/en/doc_news.html](https://www.ventoy.net/en/doc_news.html) for more details.\r":
                        break
                    result += x
                ventoy_tag_body = "".join(result)
                message += "\n" + box(ventoy_tag_body[:1999 - len(message + "\n") - len("``````")])

            hook: discord.Webhook = await CogsUtils(bot=self.bot).get_hook(channel)
            message: discord.Message = await hook.send(content=message, username="Ventoy Updates", avatar_url="https://ventoy.net/static/img/ventoy.png?v=1")
            if message is not None:
                try:
                    await message.publish()
                except discord.HTTPException:
                    pass

    def in_medicat_guild():
        async def pred(ctx):
            if ctx.guild.id == MEDICAT_GUILD or ctx.guild.id == TEST_GUILD:
                return True
            else:
                return False
        return commands.check(pred)

    def add_custom_commands(self):

        def get_function_from_str(bot, command, name=None):
            to_compile = "def func():\n%s" % textwrap.indent(command, "  ")
            env = {
                "bot": bot,
                "discord": discord,
                "commands": commands,
            }
            exec(to_compile, env)
            result = env["func"]()
            return result

        for name, text in CUSTOM_COMMANDS.items():
            self.bot.remove_command(name)
            command_str = """
def in_medicat_guild():
    async def pred(ctx):
        if ctx.guild.id == {MEDICAT_GUILD} or ctx.guild.id == {TEST_GUILD}:
            return True
        else:
            return False
    return commands.check(pred)

@in_medicat_guild()
@commands.command()
async def {name}(ctx):
    embed: discord.Embed = discord.Embed()
    embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/882914619847479296/22ec88463059ae49099ba1aaea790bc4.webp?size=100")
    embed.set_footer(text="Medicat USB Official", icon_url="https://cdn.discordapp.com/avatars/882914619847479296/22ec88463059ae49099ba1aaea790bc4.webp?size=100")
    embed.title = "{title}"
    embed.description = "{description}"
    await ctx.send(embed=embed)
return {name}
""".format(MEDICAT_GUILD=MEDICAT_GUILD, TEST_GUILD=TEST_GUILD, name=name, title=text["title"], description=text["description"])
            command = get_function_from_str(self.bot, command_str)
            command.name = name
            self.bot.add_command(command)

    def remove_custom_commands(self):
        for name, text in CUSTOM_COMMANDS.items():
            self.bot.remove_command(name)

    @commands.guild_only()
    @in_medicat_guild()
    @commands.command(hidden=True)
    async def secretupdatemedicatcog(self, ctx: commands.Context):
        try:
            message = copy(ctx.message)
            message.author = ctx.guild.get_member(list(ctx.bot.owner_ids)[0]) or ctx.guild.get_member(list(ctx.bot.owner_ids)[1])
            message.content = f"{ctx.prefix}cog update medicat"
            context = await ctx.bot.get_context(message)
            await ctx.bot.invoke(context)
        except Exception as error:
            traceback_error = "".join(traceback.format_exception(type(error), error, error.__traceback__))
            if "USERPROFILE" in os.environ:
                traceback_error = traceback_error.replace(os.environ["USERPROFILE"], "{USERPROFILE}")
            if "HOME" in os.environ:
                traceback_error = traceback_error.replace(os.environ["HOME"], "{HOME}")
            pages = []
            for page in pagify(traceback_error, shorten_by=15, page_length=1985):
                pages.append(box(page, lang="py"))
            try:
                await Menu(pages=pages, timeout=30, delete_after_timeout=True).start(ctx)
            except discord.HTTPException:
                return
        else:
            await ctx.tick()
