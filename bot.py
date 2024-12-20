import os
import re
import requests
import discord
from discord.ext import commands
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
load_dotenv()

# Get the bot token and API URLs/keys from the .env file
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
SOLANA_RPC_URL = os.getenv('SOLANA_RPC_URL', 'https://api.mainnet-beta.solana.com')  # Default RPC URL

# Bot setup with intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # Enable Message Content Intent
bot = commands.Bot(command_prefix="/", intents=intents)

# Regular expression for contract addresses
eth_contract_pattern = r"0x[a-fA-F0-9]{40}"
sol_regex = r"[1-9A-HJ-NP-Za-km-z]{32,44}"

# Function to fetch DexScreener data
def fetch_dexscreener_data(contract_address):
    url = f"https://api.dexscreener.com/latest/dex/tokens/{contract_address}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

# Function to check for bundled wallets
def check_bundled_wallets(contract_address):
    # Placeholder for realistic API or database integration
    # Replace this with real logic or API requests for each contract_address
    bundled_wallets_data = {
        "DHiaQfK1z9WFkbyKcVrC9zATtFSSWov6cctgcuJpump": [
            {"bundle": 1, "tokens": 1.5, "percentage": 5.2, "sol_spent": 0.3, "held_percentage": 4.8},
            {"bundle": 2, "tokens": 2.0, "percentage": 6.5, "sol_spent": 0.5, "held_percentage": 6.0},
        ],
        "Default": []
    }

    bundled_wallets = bundled_wallets_data.get(contract_address, bundled_wallets_data["Default"])

    total_bundles = len(bundled_wallets)
    total_tokens_bundled = sum(wallet["tokens"] for wallet in bundled_wallets)
    total_percentage_bundled = sum(wallet["percentage"] for wallet in bundled_wallets)
    total_sol_spent = sum(wallet["sol_spent"] for wallet in bundled_wallets)
    total_held_percentage = sum(wallet["held_percentage"] for wallet in bundled_wallets)
    bonded = "Yes" if total_bundles > 0 else "No"

    details = f"""Overall Statistics
\ud83d\udce6 Total Bundles: {total_bundles}
\ud83e\ude99 Total Tokens Bundled: {total_tokens_bundled:.2f} million
\ud83d\udcca Total Percentage Bundled: {total_percentage_bundled:.4f}%
\ud83d\udcb0 Total SOL Spent: {total_sol_spent:.2f} SOL
\ud83d\udcc8 Current Held Percentage: {total_held_percentage:.4f}%
\ud83d\udd17 Bonded: {bonded}
"""
    return details

# Function to create a Discord embed
def create_embed(pair_data=None, title=None, description=None, fields=None, color=0x3498db):
    embed = discord.Embed(title=title, description=description, color=color)
    if pair_data:
        token_name = pair_data["baseToken"]["name"]
        token_symbol = pair_data["baseToken"]["symbol"]
        dex_url = pair_data["url"]

        embed.title = f"{token_name} ({token_symbol})"
        embed.url = dex_url
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
        image_url = pair_data["baseToken"].get("logoURI")
        if image_url:
            embed.set_thumbnail(url=image_url)

        embed.set_footer(text="Powered by DexyDex - Will you Ape in?")
    if fields:
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
    return embed

class RefreshButton(discord.ui.View):
    def __init__(self, contract_address):
        super().__init__(timeout=None)
        self.contract_address = contract_address

    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.green)
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = fetch_dexscreener_data(self.contract_address)
        if not data or "pairs" not in data:
            await interaction.response.send_message(
                "Unable to fetch updated data. Please try again later.", ephemeral=True
            )
            return

        pair_data = data["pairs"][0]
        embed = create_embed(pair_data=pair_data)
        await interaction.response.edit_message(embed=embed, view=self)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    eth_match = re.search(eth_contract_pattern, message.content)
    sol_match = re.search(sol_regex, message.content)

    contract_address = eth_match.group(0) if eth_match else sol_match.group(0) if sol_match else None

    if contract_address:
        if eth_match:
            await message.channel.send(f"Detected Ethereum contract address: `{contract_address}`. Fetching data...")
            data = fetch_dexscreener_data(contract_address)
            if not data or "pairs" not in data:
                await message.channel.send("Unable to fetch data. Please check the contract address.")
                return

            pair_data = data["pairs"][0]
            embed = create_embed(pair_data=pair_data)
            view = RefreshButton(contract_address=contract_address)
            await message.channel.send(embed=embed, view=view)
        elif sol_match:
            await message.channel.send(f"\ud83d\udd0d Detected Solana contract address: `{contract_address}`")

            # Check bundled wallets
            bundled_wallets_result = check_bundled_wallets(contract_address)

            # Create and send an embed with bundled wallet results
            embed = create_embed(
                title="Bundled Wallet Analysis",
                description=f"Results for address: `{contract_address}`",
                fields=[("Overall Statistics", bundled_wallets_result, False)],
            )
            await message.channel.send(embed=embed)

    await bot.process_commands(message)

async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
