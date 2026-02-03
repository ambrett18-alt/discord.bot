import discord
from discord.ext import commands
from discord.ui import Button, View
import json
import os

# ---------- CONFIG ----------
TOKEN = "MTQ2NzgxNzg2MDkzOTM4Mjk4MQ.Gvawob.aRVllI4KWRN7I6ig8X0SLfSFhrZYawPZfEjdsQ"
GUILD_ID = 1465985398156165279  # replace with your server ID
WELCOME_CHANNEL_ID = 1465986351269675130  # replace with your welcome channel ID
TICKET_CATEGORY_ID = 1465985576372011193  # replace with your ticket category ID
TICKET_PANEL_CHANNEL_ID = 1465987550089842709  # replace with your channel ID for the ticket panel
# ----------------------------

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- LEVEL SYSTEM ----------
if os.path.exists("levels.json"):
    with open("levels.json") as f:
        levels = json.load(f)
else:
    levels = {}

def save_levels():
    with open("levels.json", "w") as f:
        json.dump(levels, f)

# ---------- EVENTS ----------
@bot.event
async def on_ready():
    print(f"{bot.user} is online!")

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        await channel.send(f"Welcome to the server, {member.mention}! 🎉")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # LEVELING SYSTEM
    user_id = str(message.author.id)
    if user_id not in levels:
        levels[user_id] = {"xp": 0, "level": 1}
    
    levels[user_id]["xp"] += 10  # 10 XP per message
    xp = levels[user_id]["xp"]
    lvl = levels[user_id]["level"]
    
    if xp >= lvl * 100:  # Level up
        levels[user_id]["level"] += 1
        await message.channel.send(f"{message.author.mention} has leveled up to level {levels[user_id]['level']}! 🎉")
    
    save_levels()
    await bot.process_commands(message)

# ---------- TICKET SYSTEM ----------
@bot.command()
async def ticket(ctx, *, reason="No reason provided"):
    # Safe category fetching
    category = None
    for cat in ctx.guild.categories:
        if cat.id == TICKET_CATEGORY_ID:
            category = cat
            break
    
    if category is None:
        await ctx.send("Ticket category not found! Make sure the bot has permission to view it and the ID is correct.")
        return

    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }

    safe_name = "".join(c for c in ctx.author.name if c.isalnum())
    ticket_channel = await ctx.guild.create_text_channel(
        name=f"ticket-{safe_name}",
        category=category,
        overwrites=overwrites
    )

    await ticket_channel.send(f"{ctx.author.mention}, your ticket is created! Reason: {reason}")

@bot.command()
async def close(ctx):
    if ctx.channel.name.startswith("ticket-"):
        await ctx.channel.delete()
    else:
        await ctx.send("You can only close ticket channels.")

@bot.command()
async def say(ctx, *, message):
    """Bot repeats whatever you type after !say"""
    await ctx.send(message)

# ---------- TICKET PANEL WITH BUTTON ----------
class TicketButton(View):
    def __init__(self):
        super().__init__(timeout=None)  # keeps button persistent

    @discord.ui.button(label="Open Ticket", style=discord.ButtonStyle.blurple)
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Defer the interaction immediately to prevent "This interaction failed"
        await interaction.response.defer(ephemeral=True)

        # Safe category fetching
        category = None
        for cat in interaction.guild.categories:
            if cat.id == TICKET_CATEGORY_ID:
                category = cat
                break

        if category is None:
            await interaction.followup.send(
                "Ticket category not found! Contact an admin.", ephemeral=True
            )
            return

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        safe_name = "".join(c for c in interaction.user.name if c.isalnum())
        ticket_channel = await interaction.guild.create_text_channel(
            name=f"ticket-{safe_name}",
            category=category,
            overwrites=overwrites
        )

        await ticket_channel.send(f"{interaction.user.mention}, your ticket is created!")
        await interaction.followup.send("Ticket created! ✅", ephemeral=True)

@bot.command()
async def ticket_panel(ctx=None):
    """Sends a ticket panel in the designated panel channel"""
    panel_channel = bot.get_channel(TICKET_PANEL_CHANNEL_ID)
    if not panel_channel:
        print("Ticket panel channel not found!")
        if ctx:
            await ctx.send("Ticket panel channel not found!", delete_after=5)
        return

    view = TicketButton()
    await panel_channel.send("Click the button below to open a ticket!", view=view)
    if ctx:
        await ctx.send("Ticket panel sent! ✅", delete_after=5)

# ---------- RUN BOT ----------
bot.run(TOKEN)
