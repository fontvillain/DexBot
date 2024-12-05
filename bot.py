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

# Button View for Refresh
class RefreshButton(discord.ui.View):
    def __init__(self, contract_address):
        super().__init__(timeout=None)
        self.contract_address = contract_address

    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.green)
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Fetch the latest data
        data = fetch_dexscreener_data(self.contract_address)
        if not data or "pairs" not in data:
            await interaction.response.send_message("Unable to fetch updated data. Please try again later.", ephemeral=True)
            return

        pair_data = data["pairs"][0]
        token_name = pair_data["baseToken"]["name"]
        token_symbol = pair_data["baseToken"]["symbol"]
        dex_url = pair_data["url"]

        # Build the updated embed
        embed = discord.Embed(
            title=f"{token_name} ({token_symbol})",
            url=dex_url,
            color=discord.Color.blue()
        )
        embed.add_field(name="**Price (USD)**", value=f"${float(pair_data['priceUsd']):,.6f}", inline=True)
        embed.add_field(name="**Price (Native)**", value=f"{float(pair_data['priceNative']):,.6f}", inline=True)
        embed.add_field(name="**Market Cap**", value=f"${int(pair_data.get('marketCap', 0)):,}" if pair_data.get('marketCap') else "N/A", inline=True)
        embed.add_field(name="**Volume (24H)**", value=f"${float(pair_data['volume'].get('h24', 0)):,}" if pair_data['volume'].get('h24') else "N/A", inline=True)
        embed.add_field(name="**Buys (24H)**", value=f"{pair_data['txns']['h24'].get('buys', 'N/A')}", inline=True)
        embed.add_field(name="**Sells (24H)**", value=f"{pair_data['txns']['h24'].get('sells', 'N/A')}", inline=True)
        embed.add_field(name="**Liquidity (USD)**", value=f"${float(pair_data['liquidity'].get('usd', 0)):,}" if pair_data['liquidity'].get('usd') else "N/A", inline=True)
        embed.add_field(name="**Fully Diluted Valuation (FDV)**", value=f"${int(pair_data.get('fdv', 0)):,}" if pair_data.get('fdv') else "N/A", inline=True)
        embed.set_footer(text="Powered by DexyDex - Will you Ape in?")

        await interaction.response.edit_message(embed=embed, view=self)

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
    dex_url = pair_data["url"]

    # Create the embed
    embed = discord.Embed(
        title=f"{token_name} ({token_symbol})",
        url=dex_url,
        color=discord.Color.blue()
    )
    embed.add_field(name="**Price (USD)**", value=f"${float(pair_data['priceUsd']):,.6f}", inline=True)
    embed.add_field(name="**Price (Native)**", value=f"{float(pair_data['priceNative']):,.6f}", inline=True)
    embed.add_field(name="**Market Cap**", value=f"${int(pair_data.get('marketCap', 0)):,}" if pair_data.get('marketCap') else "N/A", inline=True)
    embed.add_field(name="**Volume (24H)**", value=f"${float(pair_data['volume'].get('h24', 0)):,}" if pair_data['volume'].get('h24') else "N/A", inline=True)
    embed.add_field(name="**Buys (24H)**", value=f"{pair_data['txns']['h24'].get('buys', 'N/A')}", inline=True)
    embed.add_field(name="**Sells (24H)**", value=f"{pair_data['txns']['h24'].get('sells', 'N/A')}", inline=True)
    embed.add_field(name="**Liquidity (USD)**", value=f"${float(pair_data['liquidity'].get('usd', 0)):,}" if pair_data['liquidity'].get('usd') else "N/A", inline=True)
    embed.add_field(name="**Fully Diluted Valuation (FDV)**", value=f"${int(pair_data.get('fdv', 0)):,}" if pair_data.get('fdv') else "N/A", inline=True)
    embed.set_footer(text="Powered by DexyDex - Will you Ape in?")

    # Add a refresh button
    view = RefreshButton(contract_address=contract_address)
    await interaction.followup.send(embed=embed, view=view)

# Run the bot
import os
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
