import discord
from discord import app_commands
from discord.ext import commands
import requests

# Initialize the bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

# Function to fetch data from DexScreener API
def fetch_dexscreener_data(contract_address):
    url = f"https://api.dexscreener.com/latest/dex/tokens/{contract_address}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

# Slash command definition
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Slash commands synced: {len(synced)}")
    except Exception as e:
        print(f"Error syncing commands: {e}")

@bot.tree.command(name="contract", description="Fetch live info for a DexScreener token")
async def contract(interaction: discord.Interaction, contract_address: str):
    await interaction.response.defer()  # Indicate the bot is working on the response
    data = fetch_dexscreener_data(contract_address)
    if not data or "pairs" not in data:
        await interaction.followup.send("Unable to fetch data. Please check the contract address.")
        return

    # Extract the first pair for simplicity
    pair_data = data["pairs"][0]
    token_name = pair_data["baseToken"]["name"]
    token_symbol = pair_data["baseToken"]["symbol"]
    token_price_usd = pair_data["priceUsd"]
    token_price_native = pair_data["priceNative"]
    market_cap = pair_data.get("marketCap", "N/A")
    volume_24h = pair_data["volume"].get("h24", "N/A")
    buys_24h = pair_data["txns"]["h24"].get("buys", "N/A")
    sells_24h = pair_data["txns"]["h24"].get("sells", "N/A")
    liquidity_usd = pair_data["liquidity"].get("usd", "N/A")
    fdv = pair_data.get("fdv", "N/A")
    dex_url = pair_data["url"]

    # Create the embed
    embed = discord.Embed(
        title=f"{token_name} ({token_symbol})",
        url=dex_url,
        color=discord.Color.blue()
    )
    embed.add_field(name="**Price (USD)**", value=f"${float(token_price_usd):,.6f}", inline=True)
    embed.add_field(name="**Price (Native)**", value=f"{float(token_price_native):,.6f}", inline=True)
    embed.add_field(name="**Market Cap**", value=f"${int(market_cap):,}" if market_cap != "N/A" else "N/A", inline=True)
    embed.add_field(name="**Volume (24H)**", value=f"${float(volume_24h):,.2f}", inline=True)
    embed.add_field(name="**Buys (24H)**", value=f"{buys_24h}", inline=True)
    embed.add_field(name="**Sells (24H)**", value=f"{sells_24h}", inline=True)
    embed.add_field(name="**Liquidity (USD)**", value=f"${float(liquidity_usd):,.2f}" if liquidity_usd != "N/A" else "N/A", inline=True)
    embed.add_field(name="**Fully Diluted Valuation (FDV)**", value=f"${int(fdv):,}" if fdv != "N/A" else "N/A", inline=True)
    embed.add_field(name="**Dex URL**", value=f"[View on DexScreener]({dex_url})", inline=False)

    # Add footer and branding
    embed.set_footer(text="Powered by DexyDex - Will you Ape in?")

    # Optionally include token image if available
    if "info" in pair_data and "imageUrl" in pair_data["info"]:
        embed.set_thumbnail(url=pair_data["info"]["imageUrl"])

    await interaction.followup.send(embed=embed)

# Run the bot
import os
bot.run(os.getenv("DISCORD_BOT_TOKEN"))

