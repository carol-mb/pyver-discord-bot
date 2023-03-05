import discord
from discord.ext import commands
from discord.utils import get

import random

import json

#import utils.utils_func
#import utils.errors
from utils.db_conn import query_update, query_select


'''
Verificarea contului
'''

# addverify


class Verify(commands.Cog):
    '''
    Sistemul de verificare cont (anti atacurilor cu boti)
    '''

    def __init__(self, client):
        self.client = client
        self.verify_text = ['{} si-a verificat contul.',
                            '{} nu este robot.',
                            'Cine a spus ca {} nu este real?',
                            'Salutari pentru {}! Este om!',
                            'Good news! {} este om!',
                            '{} este acum un membru verificat!']

    @commands.Cog.listener()
    async def on_ready(self):
        print("Verify cog s-a incarcat cu succes.")

        # ======= INCARCA JSON INFO DESPRE TOATE SERVERELE CU VERIFY
        results = query_select("select * from `verify`")
        all_info = dict()

        for result in results:
            all_info[str(result[0])] = {
                "channel_id": int(result[1]),
                "message_id": int(result[2]),
                "role_id": int(result[3]),
                "emoji": str(result[4])
            }

        with open("json/verify.json", "w") as file:
            json.dump(all_info, file, indent=2)
        # ======================

    # =========================================================================
    # ADD VERIFY
    # SETEAZA O POSTARE DE VERIFICARE CONT

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def addverify(self, ctx, emoji, role: discord.Role):
        '''
        Setezi o cameră de verificare cont. Împotriva atacurilor cu boți.
        Va fi trimis un mesaj la care se va adăuga un react, iar toți cei care vor da react acolo vor primi un grad setat de tine.
        '''
        await ctx.message.delete()

        embed = discord.Embed(
            title="🌜           **Verificare**           🌛",
            color=discord.Color.from_rgb(117, 114, 218),
            description=f"Reacționează {emoji} pentru a avea\nacces la canalele serverului."
        )
        embed.set_footer(text="👇")

        message = await ctx.send(embed=embed)
        await message.add_reaction(emoji)

        # ADAUG / ACTUALIZEZ IN BAZA DE DATE
        result = query_select(
            f"select * from `verify` where `guild_id` = {ctx.guild.id}")

        if result:
            query_update(f"update `verify` set `channel_id`={ctx.channel.id}, `message_id`={message.id}, \
                         `role_id`={role.id}, `emoji`='{emoji}' where `guild_id`={ctx.guild.id}")
        else:
            query_update(f"insert into `verify`(`guild_id`, `channel_id`, `message_id`, `role_id`, `emoji`) \
                         values({ctx.guild.id}, {ctx.channel.id}, {message.id}, {role.id}, '{emoji}')")

        # ADAUG / ACTUALIZEZ FISIERUL JSON
        with open("json/verify.json", "r") as file:
            all_info = json.load(file)

        all_info[str(ctx.guild.id)] = {
            "channel_id": ctx.channel.id,
            "message_id": message.id,
            "role_id": role.id,
            "emoji": emoji
        }

        with open("json/verify.json", "w") as file:
            json.dump(all_info, file, indent=2)
    # =========================================================================
    #
    #
    #
    # =========================================================================
    # EVENT CARE SE ACTIVEAZA CAND SE DA REACT LA O POSTARE

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # ia info din json despre mesajul la care trebuie react pentru verify
        with open("json/verify.json", "r") as file:
            all_info = json.load(file)
            if str(payload.guild_id) in all_info.keys():
                all_info = all_info[str(payload.guild_id)]
            else:
                return

        # verifica daca react-ul este la postarea specifica pentru verify
        if payload.channel_id == all_info["channel_id"] \
                and payload.message_id == all_info["message_id"] \
                and str(payload.emoji) == all_info["emoji"]:

            # se obtine obiectul serverului
            guild = discord.utils.find(
                lambda g: g.id == payload.guild_id, self.client.guilds)

            # se obtine obiectul membrului care a dat react
            member = discord.utils.find(
                lambda m: m.id == payload.user_id, guild.members)

            # se obtine rolul care trebuie dat
            role = discord.utils.get(
                guild.roles, id=all_info["role_id"])

            # se adauga rolul
            await member.add_roles(role)

            await member.edit(nick=member.name + " ♣")
    # =========================================================================


def setup(client):
    client.add_cog(Verify(client))
