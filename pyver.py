import discord
from discord.ext import commands, tasks
import logging

from pretty_help import PrettyHelp

import json

from utils.db_conn import query_update

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(
    filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


def get_prefix(client, message):
    if message.guild:
        with open("json/prefixes.json", "r") as file:
            prefixes = json.load(file)
            return prefixes[str(message.guild.id)]
    else:
        return ">"


intents = discord.Intents.all()


class MyClient(commands.Bot):
    # =========================================================================
    # ON READY (cand porneste botul)
    async def on_ready(self):

        print('Logged on as {0}!'.format(self.user))
    # =========================================================================

    # =========================================================================
    # ON MESSAGE (cand se trimite un mesaj pe chat)
    async def on_message(self, message):
        #print('Message from {0.author}: {0.content}'.format(message))
        await self.process_commands(message)
    # =========================================================================

    # =========================================================================
    # ON GUILD JOIN (cand intra botul pe un server)
    async def on_guild_join(self, guild):
        with open("json/prefixes.json", "r") as file:
            prefixes = json.load(file)

        prefixes[str(guild.id)] = ">"

        with open("json/prefixes.json", "w") as file:
            json.dump(prefixes, file, indent=2)

        # cand intra prima data pe server creaza camp in baza de date
        try:
            query_update(
                f'insert into `serverconfigs`(`guild_id`) values ({guild.id})')
        except:
            pass

        #query_update(f'insert into `serverconfigs`(`guildID`) values ({guild.id})')
    # =========================================================================

    # =========================================================================
    # ON GUILD REMOVE (cand iese botul de pe un server)
    async def on_guild_remove(self, guild):
        with open("json/prefixes.json", "r") as file:
            prefixes = json.load(file)

        del prefixes[str(guild.id)]
        with open("json/prefixes.json", "w") as file:
            json.dump(prefixes, file, indent=2)

        #query_update(f'delete from `serverconfigs` where `guildID` = {guild.id}')
    # =========================================================================

    # =========================================================================
    # ON COMMAND ERROR (cand se intampla vreo eroare cand cineva da o comanda)
    async def on_command_error(self, ctx, error):
        embed = discord.Embed(
            title='Eroare',
            color=discord.Color.dark_red()
        )

        # cand lipseste un argument
        if isinstance(error, commands.MissingRequiredArgument):
            embed.description = 'Comanda nu este completa. Foloseste >help'
            await ctx.send(embed=embed)

        # cand sunt prea multe argumente
        elif isinstance(error, commands.TooManyArguments):
            embed.description = 'Ai folosit prea multe argumente. Foloseste >help'
            await ctx.send(embed=embed)

        # cand foloseste cine nu trebuie comanda (owner only)
        elif isinstance(error, commands.NotOwner):
            embed.description = 'Hahah, you impostor.\nNu mai folosi niciodata aceasta comanda!'
            await ctx.send(embed=embed)

        # cand botul nu are acces sa faca anumite lucruri
        elif isinstance(error, commands.BotMissingPermissions):
            embed.description = 'Imi pare rau! N-am permisiune sa folosesc aceasta comanda, da-mi permisiuni ca sa te pot ajuta!'
            await ctx.send(embed=embed)

        # orice altceva
        else:
            embed.description = str(error)
            await ctx.send(embed=embed)
    # =========================================================================


client = MyClient(intents=intents, command_prefix=get_prefix,
                  help_command=PrettyHelp(), guild_subscriptions=True)


# incarca toate cogs
with open("cogs.txt") as cogs:
    for cog in cogs:
        client.load_extension(f'cogs.{cog.strip()}')

client.run('SECRET')
