import discord
from discord.ext import commands
from discord import app_commands

# Set up intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Create bot
bot = commands.Bot(command_prefix="?", intents=intents)

@bot.hybrid_command(name="test", description="Test command")
async def test_cmd(ctx):
    await ctx.send("Test command works!")

@bot.hybrid_command(name="quests", description="View your current daily and weekly quests")
async def quests_cmd(ctx):
    await ctx.send("Quests command works!")

@bot.hybrid_command(name="quest", description="Generate a new daily or weekly quest")
async def quest_cmd(ctx, quest_type: str):
    await ctx.send(f"Quest command works with type: {quest_type}")

@bot.hybrid_command(name="claim_quest", description="Claim reward from a completed quest")
async def claim_quest_cmd(ctx, quest_type: str):
    await ctx.send(f"Claim quest command works with type: {quest_type}")

if __name__ == "__main__":
    print("Testing bot command registration...")
    try:
        # This should not raise an error
        print("✅ All commands registered successfully")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("Bot test complete!")

