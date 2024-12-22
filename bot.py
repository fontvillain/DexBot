import os
import re
import requests
import discord
from discord.ext import commands

# Initialize the bot with intents
intents = discord.Intents.default()
intents.messages = True  # Enable message intents
intents.message_content = True  # Required to read message content
bot = commands.Bot(command_prefix="/", intents=intents)

# Function to fetch data from DexScreener API
def fetch_dexscreener_data(contract_address):
    url = f"https://api.dexscreener.com/latest/dex/tokens/{contract_address}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

# Button View for Refresh and Open in Bullx Neo
class RefreshButton(discord.ui.View):
    def __init__(self, contract_address, bullx_neo_base_url="https://bullxneo.com/"):
        super().__init__(timeout=None)
        self.contract_address = contract_address
        self.bullx_neo_base_url = bullx_neo_base_url

    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.green)
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Fetch the latest data
        data = fetch_dexscreener_data(self.contract_address)
        if not data or "pairs" not in data:
            await interaction.response.send_message(
                "Unable to fetch updated data. Please try again later.", ephemeral=True
            )
            return

        pair_data = data["pairs"][0]
        token_name = pair_data["baseToken"]["name"]
        token_symbol = pair_data["baseToken"]["symbol"]
        dex_url = pair_data["url"]

        # Build the updated embed
        embed = discord.Embed(
            title=f"{token_name} ({token_symbol})",
            url=dex_url,
            color=discord.Color.blue(),
        )
        embed.add_field(name="**Price (USD)**", value=f"${float(pair_data['priceUsd']):,.6f}", inline=True)
        embed.add_field(name="**Price (Native)**", value=f"{float(pair_data['priceNative']):,.6f}", inline=True)
        embed.add_field(
            name="**Market Cap**",
            value=f"${int(pair_data.get('marketCap', 0)):,}" if pair_data.get("marketCap") else "N/A",
            inline=True,
        )
        embed.add_field(
            name="**Volume (24H)**",
            value=f"${float(pair_data['volume'].get('h24', 0)):,}" if pair_data["volume"].get("h24") else "N/A",
            inline=True,
        )
        embed.add_field(name="**Buys (24H)**", value=f"{pair_data['txns']['h24'].get('buys', 'N/A')}", inline=True)
        embed.add_field(name="**Sells (24H)**", value=f"{pair_data['txns']['h24'].get('sells', 'N/A')}", inline=True)
        embed.add_field(
            name="**Liquidity (USD)**",
            value=f"${float(pair_data['liquidity'].get('usd', 0)):,}" if pair_data["liquidity"].get("usd") else "N/A",
            inline=True,
        )
        embed.add_field(
            name="**Fully Diluted Valuation (FDV)**",
            value=f"${int(pair_data.get('fdv', 0)):,}" if pair_data.get("fdv") else "N/A",
            inline=True,
        )
        embed.set_footer(text="Powered by DexyDex - Will you Ape in?")

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Open in Bullx Neo", style=discord.ButtonStyle.link, url="")
    async def open_in_bullxneo(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.url = f"{self.bullx_neo_base_url}{self.contract_address}"
        # No further interaction handling is needed for link buttons.

# Event to detect messages with contract addresses
@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Ignore messages from bots

    # Regex patterns to match contract addresses
    eth_contract_pattern = r"0x[a-fA-F0-9]{40}"  # Ethereum contract
    sol_contract_pattern = r"[1-9A-HJ-NP-Za-km-z]{32,44}"  # Solana Base58 address

    # Check for Ethereum or Solana contract addresses
    eth_match = re.search(eth_contract_pattern, message.content)
    sol_match = re.search(sol_contract_pattern, message.content)

    contract_address = eth_match.group(0) if eth_match else sol_match.group(0) if sol_match else None

    if contract_address:
        await message.channel.send(f"Detected contract address: `{contract_address}`. Fetching data...")

        # Fetch DexScreener data
        data = fetch_dexscreener_data(contract_address)
        if not data or "pairs" not in data:
            await message.channel.send("Unable to fetch data. Please check the contract address.")
            return

        pair_data = data["pairs"][0]
        token_name = pair_data["baseToken"]["name"]
        token_symbol = pair_data["baseToken"]["symbol"]
        dex_url = pair_data["url"]

        # Create the embed
        embed = discord.Embed(
            title=f"{token_name} ({token_symbol})",
            url=dex_url,
            color=discord.Color.blue(),
        )
        embed.add_field(name="**Price (USD)**", value=f"${float(pair_data['priceUsd']):,.6f}", inline=True)
        embed.add_field(name="**Price (Native)**", value=f"{float(pair_data['priceNative']):,.6f}", inline=True)
        embed.add_field(
            name="**Market Cap**",
            value=f"${int(pair_data.get('marketCap', 0)):,}" if pair_data.get("marketCap") else "N/A",
            inline=True,
        )
        embed.add_field(
            name="**Volume (24H)**",
            value=f"${float(pair_data['volume'].get('h24', 0)):,}" if pair_data["volume"].get("h24") else "N/A",
            inline=True,
        )
        embed.add_field(name="**Buys (24H)**", value=f"{pair_data['txns']['h24'].get('buys', 'N/A')}", inline=True)
        embed.add_field(name="**Sells (24H)**", value=f"{pair_data['txns']['h24'].get('sells', 'N/A')}", inline=True)
        embed.add_field(
            name="**Liquidity (USD)**",
            value=f"${float(pair_data['liquidity'].get('usd', 0)):,}" if pair_data["liquidity"].get("usd") else "N/A",
            inline=True,
        )
        embed.add_field(
            name="**Fully Diluted Valuation (FDV)**",
            value=f"${int(pair_data.get('fdv', 0)):,}" if pair_data.get("fdv") else "N/A",
            inline=True,
        )
        embed.set_footer(text="Powered by DexyDex - Will you Ape in?")

        # Add buttons for refresh and open in Bullx Neo
        view = RefreshButton(contract_address=contract_address)
        await message.channel.send(embed=embed, view=view)

    # Ensure bot processes commands if message is also a command
    await bot.process_commands(message)

# Run the bot
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
