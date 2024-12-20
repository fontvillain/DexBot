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

# Function to fetch data from PumpFun API
def fetch_pumpfun_data(coin_name):
    url = f"https://api.pumpfun.com/coins/{coin_name}"  # Replace with the actual PumpFun API URL
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

# Function to fetch bundled wallet data
def fetch_bundled_wallet_data(wallet_address):
    url = f"https://api.bundledwallet.com/wallets/{wallet_address}"  # Replace with the actual Bundled Wallet API URL
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

# Button View for Refresh
class RefreshButton(discord.ui.View):
    def __init__(self, contract_address=None, coin_name=None, wallet_address=None):
        super().__init__(timeout=None)
        self.contract_address = contract_address
        self.coin_name = coin_name
        self.wallet_address = wallet_address

    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.green)
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.coin_name:
            data = fetch_pumpfun_data(self.coin_name)
            if not data:
                await interaction.response.send_message(
                    "Unable to fetch updated data. Please try again later.", ephemeral=True
                )
                return

            # Build the updated embed for PumpFun
            embed = discord.Embed(
                title=f"{data['name']} ({data['symbol']})",
                url=data['website'],
                color=discord.Color.orange(),
            )
            embed.add_field(name="**Price (USD)**", value=f"${data['price_usd']:.6f}", inline=True)
            embed.add_field(name="**Market Cap**", value=f"${data['market_cap']:,}", inline=True)
            embed.add_field(name="**Volume (24H)**", value=f"${data['volume_24h']:,}", inline=True)
            embed.set_footer(text="Powered by PumpFun")

            await interaction.response.edit_message(embed=embed, view=self)
            return

        if self.wallet_address:
            data = fetch_bundled_wallet_data(self.wallet_address)
            if not data:
                await interaction.response.send_message(
                    "Unable to fetch updated wallet data. Please try again later.", ephemeral=True
                )
                return

            # Build the updated embed for bundled wallet data
            embed = discord.Embed(
                title="Bundled Wallet Statistics",
                color=discord.Color.purple(),
            )
            embed.add_field(name="**📦 Total Bundles**", value=f"{data['total_bundles']}", inline=True)
            embed.add_field(name="**🪙 Total Tokens Bundled**", value=f"{data['total_tokens_bundled']} million", inline=True)
            embed.add_field(name="**📊 Total Percentage Bundled**", value=f"{data['total_percentage_bundled']}%", inline=True)
            embed.add_field(name="**💰 Total SOL Spent**", value=f"{data['total_sol_spent']} SOL", inline=True)
            embed.add_field(name="**📈 Current Held Percentage**", value=f"{data['current_held_percentage']}%", inline=True)
            embed.add_field(name="**🔗 Bonded**", value=f"{'Yes' if data['bonded'] else 'No'}", inline=True)
            embed.set_footer(text="Powered by Bundled Wallet API")

            await interaction.response.edit_message(embed=embed, view=self)
            return

        # Fetch the latest data from DexScreener
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

# Event to detect messages with contract addresses, coin names, or wallet addresses
@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Ignore messages from bots

    # Regex patterns to match contract addresses and wallet addresses
    eth_contract_pattern = r"0x[a-fA-F0-9]{40}"  # Ethereum contract
    sol_contract_pattern = r"[1-9A-HJ-NP-Za-km-z]{32,44}"  # Solana Base58 address
    wallet_address_pattern = r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b"  # Example wallet address pattern

    # Check for Ethereum, Solana contract addresses, or wallet addresses
    eth_match = re.search(eth_contract_pattern, message.content)
    sol_match = re.search(sol_contract_pattern, message.content)
    wallet_match = re.search(wallet_address_pattern, message.content)

    # Check for PumpFun coin names (example pattern, update as needed)
    pumpfun_coin_pattern = r"\b[A-Za-z]{2,10}\b"
    pumpfun_match = re.search(pumpfun_coin_pattern, message.content)

    if pumpfun_match:
        coin_name = pumpfun_match.group(0)
        await message.channel.send(f"Detected PumpFun coin: `{coin_name}`. Fetching data...")

        # Fetch PumpFun data
        data = fetch_pumpfun_data(coin_name)
        if not data:
            await message.channel.send("Unable to fetch data. Please check the coin name.")
            return

        # Create the embed
        embed = discord.Embed(
            title=f"{data['name']} ({data['symbol']})",
            url=data['website'],
            color=discord.Color.orange(),
        )
        embed.add_field(name="**Price (USD)**", value=f"${data['price_usd']:.6f}", inline=True)
        embed.add_field(name="**Market Cap**", value=f"${data['market_cap']:,}", inline=True)
        embed.add_field(name="**Volume (24H)**", value=f"${data['volume_24h']:,}", inline=True)
        embed.set_footer(text="Powered by PumpFun")

        # Add a refresh button
        view = RefreshButton(contract_address=None, coin_name=coin_name)
        await message.channel.send(embed=embed, view=view)
        return

    if wallet_match:
        wallet_address = wallet_match.group(0)
        await message.channel.send(f"Detected wallet address: `{wallet_address}`. Fetching data...")

        # Fetch bundled wallet data
        data = fetch_bundled_wallet_data(wallet_address)
        if not data:
            await message.channel.send("Unable to fetch wallet data. Please check the wallet address.")
            return

        # Create the embed
        embed = discord.Embed(
            title="Bundled Wallet Statistics",
            color=discord.Color.purple(),
        )
        embed.add_field(name="**📦 Total Bundles**", value=f"{data['total_bundles']}", inline=True)
        embed.add_field(name="**🪙 Total Tokens Bundled**", value=f"{data['total_tokens_bundled']} million", inline=True)
        embed.add_field(name="**📊 Total Percentage Bundled**", value=f"{data['total_percentage_bundled']}%", inline=True)
        embed.add_field(name="**💰 Total SOL Spent**", value=f"{data['total_sol_spent']} SOL", inline=True)
        embed.add_field(name="**📈 Current Held Percentage**", value=f"{data['current_held_percentage']}%", inline=True)
        embed.add_field(name="**🔗 Bonded**", value=f"{'Yes' if data['bonded'] else 'No'}", inline=True)
        embed.set_footer(text="Powered by Bundled Wallet API")

        # Add a refresh button
        view = RefreshButton(wallet_address=wallet_address)
        await message.channel.send(embed=embed, view=view)
        return

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

        # Add a refresh button
        view = RefreshButton(contract_address=contract_address)
        await message.channel.send(embed=embed, view=view)

    # Ensure bot processes commands if message is also a command
    await bot.process_commands(message)

# Run the bot
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
