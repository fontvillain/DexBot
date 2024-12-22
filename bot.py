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

# Function to fetch Bullx Neo coin data
def fetch_bullxneo_data(contract_address):
    try:
        url = f"https://neo.bullx.io/api/coins/{contract_address}"  # Example endpoint
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching data from Bullx Neo: {e}")
    return None

# Function to fetch Bullx Neo chart URL
def fetch_bullxneo_chart_url(contract_address):
    chain_id = "1399811149"  # Example chainId
    return f"https://neo.bullx.io/terminal?chainId={chain_id}&address={contract_address}"

# Button View for Refresh and Open in Bullx Neo
class RefreshButton(discord.ui.View):
    def __init__(self, contract_address, chart_url, source="DexScreener"):
        super().__init__(timeout=None)
        self.contract_address = contract_address
        self.source = source

        # Add a "Open in Bullx Neo" button with the fetched chart URL
        if chart_url:
            self.add_item(discord.ui.Button(label="Open in Bullx Neo", style=discord.ButtonStyle.link, url=chart_url))

    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.green)
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Fetch the latest data from the source
        if self.source == "DexScreener":
            data = fetch_dexscreener_data(self.contract_address)
        else:
            data = fetch_bullxneo_data(self.contract_address)

        if not data:
            await interaction.response.send_message(
                f"Unable to fetch updated data from {self.source}. Please try again later.", ephemeral=True
            )
            return

        # Process data and build embed
        if self.source == "DexScreener":
            pair_data = data["pairs"][0]
            token_name = pair_data["baseToken"]["name"]
            token_symbol = pair_data["baseToken"]["symbol"]
            dex_url = pair_data["url"]

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
        else:  # Bullx Neo
            token_name = data.get("name", "Unknown")
            token_symbol = data.get("symbol", "Unknown")
            embed = discord.Embed(
                title=f"{token_name} ({token_symbol})",
                color=discord.Color.purple(),
            )
            embed.add_field(name="**Price (USD)**", value=data.get("price_usd", "N/A"), inline=True)
            embed.add_field(name="**Market Cap**", value=data.get("market_cap", "N/A"), inline=True)

        embed.set_footer(text=f"Powered by {self.source} - Will you Ape in?")
        await interaction.response.edit_message(embed=embed, view=self)

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

        # Attempt to fetch from DexScreener
        data = fetch_dexscreener_data(contract_address)
        source = "DexScreener"
        if not data or "pairs" not in data:
            # If not found on DexScreener, check Bullx Neo
            data = fetch_bullxneo_data(contract_address)
            source = "Bullx Neo"

        if not data:
            await message.channel.send("Unable to fetch data. Please check the contract address.")
            return

        # Fetch the Bullx Neo chart URL
        chart_url = fetch_bullxneo_chart_url(contract_address)

        # Create the embed
        if source == "DexScreener":
            pair_data = data["pairs"][0]
            token_name = pair_data["baseToken"]["name"]
            token_symbol = pair_data["baseToken"]["symbol"]
            dex_url = pair_data["url"]

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
        else:  # Bullx Neo
            token_name = data.get("name", "Unknown")
            token_symbol = data.get("symbol", "Unknown")
            embed = discord.Embed(
                title=f"{token_name} ({token_symbol})",
                color=discord.Color.purple(),
            )
            embed.add_field(name="**Price (USD)**", value=data.get("price_usd", "N/A"), inline=True)
            embed.add_field(name="**Market Cap**", value=data.get("market_cap", "N/A"), inline=True)

        embed.set_footer(text=f"Powered by {source} - Will you Ape in?")

        # Add buttons for refresh and open in Bullx Neo
        view = RefreshButton(contract_address=contract_address, chart_url=chart_url, source=source)
        await message.channel.send(embed=embed, view=view)

    # Ensure bot processes commands if message is also a command
    await bot.process_commands(message)

# Run the bot
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
