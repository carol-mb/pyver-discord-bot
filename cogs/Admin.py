import discord
from discord.ext import commands
from discord.utils import get

import json

from utils.db_conn import query_update, query_select
from utils.funcs import check_status
#import utils.errors

#import asyncio


# clear
# prefix
# banrole
# ban
# unban
# banlist
class Admin(commands.Cog):
    '''
    Comenzi de admin
    '''

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("Admin cog s-a incarcat cu succes.")

        # ======== INCARCA PREFIXURILE
        infos = query_select(
            'select `guild_id`, `bot_prefix` from `serverconfigs`')
        prefixes = dict()
        for info in infos:
            prefixes[str(info[0])] = info[1]

        with open("json/prefixes.json", "w") as file:
            json.dump(prefixes, file, indent=2)
        # =============================
        #
        # ======== INCARCA MEMBRI BANATI
        infos = query_select(
            f'select `guild_id`, `member_id` from `bannedmembers`')

        banned = dict()

        for info in infos:
            if str(info[0]) not in banned.keys():
                banned[str(info[0])] = list()
            banned[str(info[0])].append(info[1])

        with open("json/banned.json", "w") as file:
            json.dump(banned, file, indent=2)
        # =============================

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # ====== Da gradul de banat inapoi
        with open("json/banned.json", "r") as file:
            banned_members = json.load(file)

        ban_role_id = query_select(
            f'select `ban_role_id` from `serverconfigs` where `guild_id`={member.guild.id}')[0][0]
        ban_role = discord.utils.get(member.guild.roles, id=ban_role_id)

        if str(member.guild.id) in banned_members.keys() and member.id in banned_members[str(member.guild.id)]:
            await member.add_roles(ban_role, reason="avea ban cand a iesit de pe server")

    #
    #
    #
    # =========================================================================
    # COMANDA DE STERS MESAJE DIN CHAT

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount=5):
        '''
        Comandă de șters mesaje din chat. Dacă nu precizezi cât să șteargă, o să șteargă 5.
        '''
        if type(ctx.author) != discord.User:
            await ctx.message.delete()
            await ctx.channel.purge(limit=amount)
    # =========================================================================
    #
    #
    #
    # =========================================================================
    # COMANDA DE SCHIMBARE PREFIX

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def prefix(self, ctx, args=None):
        '''
        Comandă cu care setezi prefix-ul pe care să-l foloseasca botul. Dacă nu precizezi un nou prefix, îl va arăta pe cel deja existent.
        '''
        # deschide json cu prefixurile
        with open("json/prefixes.json", "r") as file:
            prefixes = json.load(file)

        # cand nu e introdus niciun prefix, il afiseaza pe cel deja existent
        if not args:
            await ctx.send(f"Prefixul botului este **{prefixes[str(ctx.guild.id)]}**")

        # cand este introdus ul alt prefix este modificat cel vechi
        elif len(args) <= 5:

            prefixes[str(ctx.guild.id)] = args

            with open("json/prefixes.json", "w") as file:
                json.dump(prefixes, file, indent=2)

            embed = discord.Embed(
                title="Prefixul a fost schimbat cu succes",
                color=discord.Color.green(),
                description=f"De acum vei putea folosi **pyver** folosind prefixul **{args}**"
            )
            await ctx.send(embed=embed)

            query_update(
                f'update `serverconfigs` set `prefix`="{args}" where `guild_id`={ctx.guild.id}')
        else:
            await ctx.send('Prefixul trebuie sa aibă 5 caractere sau mai puțin.')
    # =========================================================================
    #
    #
    #
    # =========================================================================
    # COMANDA DE SETAT ROL PENTRU BAN

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def banrole(self, ctx, role: discord.Role = None):
        """
        Setezi rolul pe care un membru il va primi daca ii vei da ban prin intermediul comenzii din bot.
        Daca nu introduci niciun rol cel deja existent se va sterge.
        """
        await ctx.message.delete()
        if role:
            query_update(
                f'update `serverconfigs` set `ban_role_id`={role.id} where `guild_id`={ctx.guild.id}')
        else:
            query_update(
                f'update `serverconfigs` set `ban_role_id`=NULL where `guild_id`={ctx.guild.id}')
    # =========================================================================
    #
    #
    #
    # =========================================================================
    # COMANDA DE DAT BAN

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="niciun motiv"):
        """
        Dai ban unui membru. Nu-l scoate de pe server, doar îi scoate toate gradele si ii da gradul setat cu comanda banrole.
        Daca nu a fost setat niciun grad de ban cu banrole, atunci va fi scos de pe server.
        """
        if not check_status("immunity", member):
            # se obtine rolul de ban
            ban_role_id = query_select(
                f'select `ban_role_id` from `serverconfigs` where `guild_id`={ctx.guild.id}')[0][0]
            ban_role = discord.utils.get(ctx.guild.roles, id=ban_role_id)

            with open("json/banned.json", "r") as file:
                banned_members = json.load(file)

            if str(ctx.guild.id) in banned_members.keys() and member.id in banned_members[str(ctx.guild.id)]:
                already_banned = True
            else:
                already_banned = False

            if ban_role and not already_banned:
                # salveaza rolurile pe care le avea inainte sa ia ban
                # folositor in cazul in care ia unban pentru ca le va primi inapoi
                query_update(
                    f'delete from `bannedbackuproles` where `guild_id`={ctx.guild.id} and `member_id`={member.id}')
                for role in member.roles[1:]:
                    query_update(f'insert into `bannedbackuproles`(`guild_id`, `member_id`, `role_id`) \
                                values ({ctx.guild.id}, {member.id}, {role.id})')
                    await member.remove_roles(role, reason="banned")

                await member.add_roles(ban_role, reason=reason)

                # se adauga in baza de date
                query_update(f'insert into `bannedmembers`(`guild_id`, `member_id`, `reason`) \
                                values ({ctx.guild.id}, {member.id}, "{reason}")')

                # ======= Scriere in fisier json a membrilor banati

                if str(ctx.guild.id) not in banned_members.keys():
                    banned_members[str(ctx.guild.id)] = list()

                banned_members[str(ctx.guild.id)].append(member.id)

                with open("json/banned.json", "w") as file:
                    json.dump(banned_members, file, indent=2)
                # ===========================
            # daca nu exista un rol de ban setat ii da direct ban de pe server
            else:
                await member.ban(reason=reason)

            embed = discord.Embed(
                title=f"❌ Ai primit ban pe serverul *{ctx.guild.name}* de la *{ctx.author}* ❌",
                description=f"👉 Motivul: **{reason}**\n❗ Daca vrei unban creaza o cerere de unban pe acel server.\n❗ Daca iesi de pe server si intri din nou tot va ramane banul.",
                color=discord.Color.from_rgb(117, 114, 218)
            )
            await member.send(embed=embed)
        else:
            await ctx.send("Acest membru este imun, nu poți să-i dai ban.")
    # =========================================================================
    #
    #
    #
    # =========================================================================
    # COMANDA DE DAT UNBAN

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, member: discord.Member, *, reason="niciun motiv"):
        """
        Dai unban unui membru. Acesta va primi gradele pe care le-a avut inainte de ban.
        """

        # se obtine rolul de ban
        ban_role_id = query_select(
            f'select `ban_role_id` from `serverconfigs` where `guild_id`={ctx.guild.id}')[0][0]
        ban_role = discord.utils.get(ctx.guild.roles, id=ban_role_id)

        with open("json/banned.json", "r") as file:
            banned_members = json.load(file)

        if str(ctx.guild.id) in banned_members.keys() and member.id in banned_members[str(ctx.guild.id)]:
            already_banned = True
        else:
            already_banned = False

        if ban_role and already_banned:
            await member.remove_roles(ban_role, reason=reason)

            # se obtin rolurile pe care le avea inainte si i le da
            roles = query_select(
                f'select `role_id` from `bannedbackuproles` where `guild_id`={ctx.guild.id} and `member_id`={member.id}')
            for role in roles:
                await member.add_roles(discord.utils.get(ctx.guild.roles, id=role[0]), reason="unbanned")

            query_update(
                f'delete from `bannedbackuproles` where `guild_id`={ctx.guild.id} and `member_id`={member.id}')
            query_update(
                f'delete from `bannedmembers` where `guild_id`={ctx.guild.id} and `member_id`={member.id}')

            # ======= Scriere in fisier json a membrilor banati

            if str(ctx.guild.id) not in banned_members.keys():
                banned_members[str(ctx.guild.id)] = list()

            banned_members[str(ctx.guild.id)].remove(member.id)

            with open("json/banned.json", "w") as file:
                json.dump(banned_members, file, indent=2)
            # ===========================

        embed = discord.Embed(
            title=f"✌ Ai primit unban pe serverul *{ctx.guild.name}* de la *{ctx.author}* ✌",
            description=f"👉 Motiv: **{reason}**\n❗ Ai primit inapoi toate gradele pe care le aveai inainte de ban.",
            color=discord.Color.from_rgb(117, 114, 218)
        )
        await member.send(embed=embed)
    # =========================================================================
    #
    #
    #
    # =========================================================================
    # Arata o lista cu toti membrii cu ban de pe server

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def banlist(self, ctx):
        '''
        Afișează o listă cu toți cei banati de pe server.
        '''
        # da load la fisierul json
        with open("json/banned.json", "r") as file:
            result = json.load(file)

        # daca exista membri incarcati pentru acel server, se pastreaza in memorie doar membri acelui server
        if str(ctx.guild.id) in result.keys():
            result = result[str(ctx.guild.id)]
        else:
            return

        if result:
            banned = []
            for id in result:
                name = str(await self.client.fetch_user(id))
                reason = query_select(f'select `reason` from `bannedmembers` where `guild_id`={ctx.guild.id} and `member_id`={id}')[0][0]
                banned.append(f'{name} - {reason}')
            string = '\n'.join(banned)
        else:
            string = "Nu există!"

        embed = discord.Embed(
            title="🤠 Membrii banati",
            description=string,
            color=discord.Color.from_rgb(117, 114, 218)
        )
        await ctx.send(embed=embed)
    # =========================================================================


def setup(client):
    client.add_cog(Admin(client))
