import discord
import typing
from redbot.core import commands, Config
from dislash import ActionRow

# Credits:
# Thanks to @epic guy on Discord for the basic syntax (command groups, commands) and also commands (await ctx.send, await ctx.author.send, await ctx.message.delete())!
# Thanks to the developers of the cogs I added features to as it taught me how to make a cog! (Chessgame by WildStriker, Captcha by Kreusada, Speak by Epic guy and Rommer by Dav)
# Thanks to all the people who helped me with some commands in the #coding channel of the redbot support server!

class roles_button(commands.Cog):
    """A cog to have roles-buttons!"""

    def __init__(self, bot):
        self.bot = bot
        self.config: Config = Config.get_conf(
            self,
            identifier=370638632963,
            force_registration=True,
        )
        self.roles_button_guild = {
            "roles_buttons": {},
        }

        self.config.register_guild(**self.roles_button_guild)

    @commands.Cog.listener()
    async def on_button_click(self, inter):
        if inter.clicked_button.custom_id == "close_ticket_button":
            return
        guild = inter.guild
        channel = inter.channel
        if inter.author is None:
            return
        if inter.guild is None:
            return
        if inter.author.bot:
            return
        if await self.bot.cog_disabled_in_guild(self, guild):
            return
        if not inter.component.custom_id == "roles_buttons":
            return
        config = await self.config.guild(guild).roles_buttons.all()
        if not f"{inter.channel.id}-{inter.message.id}" in config:
            return
        if getattr(inter.component.emoji, "id", None):
            inter.component.emoji = str(inter.component.emoji.id)
        else:
            inter.component.emoji = str(inter.component.emoji).strip("\N{VARIATION SELECTOR-16}")
        if not f"{inter.component.emoji}" in config[f"{inter.channel.id}-{inter.message.id}"]:
            return
        role = inter.guild.get_role(config[f"{inter.channel.id}-{inter.message.id}"][f"{inter.component.emoji}"]["role"])
        if role is None:
            inter.respond("The role I have to put you in no longer exists. Please notify an administrator of this server.")
            return
        if not role in inter.author.roles:
            try:
                await inter.author.add_roles(role, reason=f"Role-button of {inter.message.id} in {channel.id}.")
            except discord.HTTPException:
                await inter.respond(f"I could not add the {role.mention} ({role.id}) role to you. Please notify an administrator of this server.")
                return
            else:
                await inter.respond(f"You now have the role {role.mention} ({role.id}).")
        else:
            try:
                await inter.author.remove_roles(role, reason=f"Role-button of {inter.message.id} in {channel.id}.")
            except discord.HTTPException:
                await inter.respond(f"I could not remove the {role.mention} ({role.id}) role to you. Please notify an administrator of this server.")
                return
            else:
                await inter.respond(f"I did remove the role {role.mention} ({role.id}).")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not message.guild:
            return
        config = await self.config.guild(message.guild).roles_buttons.all()
        if not f"{message.channel.id}-{message.id}" in config:
            return
        del config[f"{message.channel.id}-{message.id}"]
        await self.config.guild(message.guild).roles_buttons.set(config)

    @commands.guild_only()
    @commands.is_owner()
    @commands.group(aliases=["rtc"])
    async def reacttocommand(self, ctx):
        """Group of commands for use ReactToCommand.
        """
        pass

    @reacttocommand.command()
    async def add(self, ctx, message: discord.Message, role: discord.Role, button: typing.Union[discord.Emoji, str], *, text_button: typing.Optional[str]=None):
        """Add a role-button to a message.
        """
        if not message.author == ctx.guild.me:
            await ctx.send("I have to be the author of the message for the role-button to work.")
            return
        permissions = message.channel.permissions_for(ctx.guild.me)
        if not permissions.add_reactions or not permissions.read_message_history or not permissions.read_messages or not permissions.view_channel:
            await ctx.send("I don't have sufficient permissions on the channel where the message you specified is located.\nI need the permissions to see the messages in that channel.")
            return
        config = await self.config.guild(ctx.guild).roles_buttons.all()
        if not f"{message.channel.id}-{message.id}" in config:
            config[f"{message.channel.id}-{message.id}"] = {}
        if len(config[f"{message.channel.id}-{message.id}"]) == 5:
            await ctx.send("I can't do more than 5 role-button for one message.")
            return
        config[f"{message.channel.id}-{message.id}"][f"{button}"]["role"] = role
        config[f"{message.channel.id}-{message.id}"][f"{button}"]["text_button"] = role
        buttons = {"type": 1, "components": []}
        for button in config[f"{message.channel.id}-{message.id}"]:
            buttons["components"].append({"type": 2, "style": 2, "label": config[f"{message.channel.id}-{message.id}"]["text_button"], "emoji": {"name": f"{button}"}, "custom_id": "roles_buttons"})
        await message.edit(components=[ActionRow.from_dict(buttons)])
        await self.config.guild(ctx.guild).roles_buttons.set(config)
        await ctx.tick()

    @reacttocommand.command()
    async def remove(self, ctx, message: discord.Message, button: typing.Union[discord.Emoji, str]):
        """Remove a role-button to a message.
        """
        if not message.author == ctx.guild.me:
            await ctx.send("I have to be the author of the message for the role-button to work.")
            return
        config = await self.config.guild(ctx.guild).roles_buttons.all()
        if not f"{message.channel.id}-{message.id}" in config:
            await ctx.send("No role-button is configured for this message.")
            return
        if not f"{button}" in config[f"{message.channel.id}-{message.id}"]:
            await ctx.send("I wasn't watching for this button on this message.")
            return
        del config[f"{message.channel.id}-{message.id}"][f"{button}"]
        buttons = {"type": 1, "components": []}
        for button in config[f"{message.channel.id}-{message.id}"]:
            buttons["components"].append({"type": 2, "style": 2, "label": config[f"{message.channel.id}-{message.id}"]["text_button"], "emoji": {"name": f"{button}"}, "custom_id": "roles_buttons"})
        await message.edit(components=[ActionRow.from_dict(buttons)])
        if config[f"{message.channel.id}-{message.id}"] == {}:
            del config[f"{message.channel.id}-{message.id}"]
        await self.config.guild(ctx.guild).roles_buttons.set(config)
        await ctx.tick()

    @reacttocommand.command()
    async def clear(self, ctx, message: discord.Message):
        """Clear all roles-buttons to a message.
        """
        if not message.author == ctx.guild.me:
            await ctx.send("I have to be the author of the message for the role-button to work.")
            return
        config = await self.config.guild(ctx.guild).roles_buttons.all()
        if not f"{message.channel.id}-{message.id}" in config:
            await ctx.send("No role-button is configured for this message.")
            return
        try:
            await message.edit(components=[])
        except discord.HTTPException:
            pass
        del config[f"{message.channel.id}-{message.id}"]
        await self.config.guild(ctx.guild).roles_buttons.set(config)
        await ctx.tick()

    @reacttocommand.command(hidden=True)
    async def purge(self, ctx):
        """Clear all roles-buttons to a **guild**.
        """
        await self.config.guild(ctx.guild).roles_buttons.clear()
        await ctx.tick()