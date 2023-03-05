import discord
from discord.ext import commands
from discord.utils import get

from utils.db_conn import query_select, query_update
#import utils.utils_func
from utils.funcs import check_status
#import utils.errors

import json

# verimmunity
# immunity
# immunitylist


class Immunity(commands.Cog):
    '''
    Sistem de imunitate. Cei imuni de pe server nu vor fi afectați de bot (nu vor mai primi grade etc)
    '''

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("Immunity cog s-a incarcat cu succes.")

        # salveaza local in json membrii cu imunitate
        infos = query_select('select * from `immunity`')

        immune_users = dict()

        for info in infos:
            if str(info[0]) not in immune_users.keys():
                immune_users[str(info[0])] = list()
            immune_users[str(info[0])].append(info[1])

        with open("json/immunity.json", "w") as file:
            json.dump(immune_users, file, indent=2)

    #
    #
    #
    # =========================================================================
    # Verifica daca un membru are imunitate
    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def verimmunity(self, ctx, member: discord.Member):
        '''
        Verifici imunitatea unui membru (dacă are sau nu)
        '''
        await ctx.message.delete()

        embed = discord.Embed(
            title=f'👁️‍🗨️ Este {member} imun?',
            description=f'👉 {"Da, este" if check_status("immunity", member) else "Nu, nu este"} 👀 ',
            color=discord.Color.from_rgb(117, 114, 218)
        )
        await ctx.send(embed=embed)
    # =========================================================================
    #
    #
    #
    # =========================================================================
    # Adauga sau scoate imunitatea unui membru

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def immunity(self, ctx, action, member: discord.Member):
        '''
        Comanda cu care adaugi sau scoți imunitate pentru un membru
        immunity add - Adaugi imunitate unui membru
        immunity remove - Ștergi imunitatea unui membru
        '''
        await ctx.message.delete()

        with open("json/immunity.json", "r") as file:
            result = json.load(file)

        if action == "add":
            if str(member.guild.id) not in result.keys():
                result[str(member.guild.id)] = [member.id]
                await ctx.send(f'{member.mention} a fost adăugat pe lista de imunitate.')
                query_update(
                    f'insert into `immunity`(`guild_id`, `member_id`) values ({ctx.guild.id}, {member.id})')

            elif member.id not in result[str(member.guild.id)]:
                result[str(member.guild.id)].append(member.id)
                await ctx.send(f'{member.mention} a fost adăugat pe lista de imunitate.')
                query_update(
                    f'insert into `immunity`(`guild_id`, `member_id`) values ({ctx.guild.id}, {member.id})')
            else:
                await ctx.send(f'{member.mention} este deja pe lista de imunitate.')

        elif action == "remove":
            if str(member.guild.id) not in result.keys():
                await ctx.send(f'{member.mention} nu este imun.')
            elif member.id in result[str(member.guild.id)]:
                result[str(member.guild.id)].remove(member.id)
                await ctx.send(f'{member.mention} a fost șters de pe lista de imunitate.')
                query_update(
                    f'delete from `immunity` where `guild_id`={ctx.guild.id} and `member_id`={member.id}')
            else:
                await ctx.send(f'{member.mention} nu este imun.')

        else:
            await ctx.send("Folosește 'add' sau 'remove'. Alte valori nu funcționează.")

        with open("json/immunity.json", "w") as file:
            json.dump(result, file, indent=2)
    # =========================================================================
    #
    #
    #
    # =========================================================================
    # Arata o lista cu toti membrii cu imunitate de pe server

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def immunitylist(self, ctx):
        '''
        Afișează o listă cu toți cei imuni de pe server.
        '''
        # da load la fisierul json
        with open("json/immunity.json", "r") as file:
            result = json.load(file)

        # daca exista membri incarcati pentru acel server, se pastreaza in memorie doar membri acelui server
        if str(ctx.guild.id) in result.keys():
            result = result[str(ctx.guild.id)]
        else:
            return

        # list comprehension in care se da get la fiecare membru pentru a-i da mention in embed
        members = [(await ctx.guild.fetch_member(id)).mention for id in result]

        if members:
            string = ','.join(members)
        else:
            string = "Nu există!"

        embed = discord.Embed(
            title="🤠 Membrii cu imunitate",
            description=string,
            color=discord.Color.from_rgb(117, 114, 218)
        )

        await ctx.send(embed=embed)
    # =========================================================================


def setup(client):
    client.add_cog(Immunity(client))
