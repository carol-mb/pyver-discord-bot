import discord
from discord.ext import commands, tasks
from discord.utils import get

from utils.db_conn import query_select, query_update
#import utils.utils_func
from utils.funcs import check_status
#import utils.errors

from utils.funcs import check_status, get_random_color

import json
import datetime


class Voice(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("Voice cog s-a incarcat cu succes.")

        infos = query_select("select * from `voice_roles`")

        roles = dict()

        for info in infos:
            if str(info[0]) not in roles.keys():
                roles[str(info[0])] = list()
            roles[str(info[0])].append({
                "role_id": info[1],
                "time_connected": info[2]
            })

        with open("json/voiceroles.json", "w") as file:
            json.dump(roles, file, indent=2)

        self.collect.start()
        self.save_data.start()
        self.auto_roles.start()
        print(
            f'VoiceRoles s-a pornit cu succes la {datetime.datetime.utcnow().strftime("%H:%M:%S")}!')
    # =========================================================================
    #
    #
    #
    # =========================================================================
    # Adauga un rol sa fie acordat automat

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def addvoicerole(self, ctx, role: discord.Role, time_connected=0):
        """
        Adaugă un rol care se va acorda automat după ce un membru stă conectat pe camerele de voce.
        """
        await ctx.message.delete()

        with open("json/voiceroles.json", "r") as file:
            result = json.load(file)

        if str(ctx.guild.id) not in result.keys():
            result[str(ctx.guild.id)] = list()

        for role_dict in result[str(ctx.guild.id)]:
            if role_dict["role_id"] == role.id:
                role_dict["time_connected"] = time_connected
                query_update(
                    f'update `voice_roles` set `time_connected`={time_connected} where `guild_id`={ctx.guild.id} and `role_id`={role.id}')
                break
        else:
            result[str(ctx.guild.id)].append(
                {"role_id": role.id, "time_connected": time_connected})
            query_update(
                f'insert into `voice_roles`(`guild_id`, `role_id`, `time_connected`) values({ctx.guild.id}, {role.id}, {time_connected})')

        with open("json/voiceroles.json", "w") as file:
            json.dump(result, file, indent=2)

        embed = discord.Embed(title="Rolul automat a fost adăugat (voce)",
                              color=discord.Color.from_rgb(*get_random_color()))

        embed.description = f"{role.mention} va fi dat automat după {time_connected}\
                                {'minut' if time_connected == 1 else 'minute'}\
                                după ce membrul stă conectat pe canalele de voce."
        await ctx.send(embed=embed)
    # =========================================================================
    #
    #
    #
    # =========================================================================
    # Sterge un rol care era acordat automat

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def removevoicerole(self, ctx, role: discord.Role):
        """
        Șterge un rol care era setat să se acorde automat (voce).
        """
        await self.message.delete()

        with open("json/voiceroles.json", "r") as file:
            result = json.load(file)

        # verifica daca rolul a fost setat sa se acorde automat
        if str(ctx.guild.id) in result.keys() and result[str(ctx.guild.id)]:

            for role in result[str(ctx.guild.id)]:

                if role["role_id"] == role.id:
                    result[str(ctx.guild.id)].remove(role)
                    embed = discord.Embed(title="Rolul automat a fost șters (voce)",
                                          color=discord.Color.from_rgb(
                                              *get_random_color()),
                                          description=f"{role.mention} nu va mai fi acordat automat.")
                    await ctx.send(embed=embed)

                    with open("json/voiceroles.json", "w") as file:
                        json.dump(result, file, indent=2)

                    query_update(
                        f'delete from `voice_roles` where `guild_id`={ctx.guild.id} and `role_id`={role.id}')

                    break
            else:
                await ctx.send("Acest rol nu era acordat automat (voce).")
        else:
            await ctx.send("Acest rol nu era acordat automat (voce).")
    # =========================================================================
    #
    #
    #
    # =========================================================================
    # comanda de vazut cate minute a stat un membru pe voce in ultimele x zile
    @commands.command(aliases=["mvoice"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def voicestats(self, ctx, member : discord.Member, days=14):
        await ctx.message.delete()
        dt = datetime.datetime.now() - datetime.timedelta(days=days)
        time = sum(info[0] for info in query_select(f"select `time_connected` from `voice_activity` where `datetime`>='{dt}' and `guild_id`={ctx.guild.id} and `member_id`={member.id}"))
        
        await ctx.send(f"{member} a stat {time} minute ({int(time/60)} {'ora' if int(time/60) == 1 else 'ore'}) in {'ultima zi' if days == 1  else 'ultimele ' + str(days) + ' zile'} pe canalele de voce!"
                       if time else
                       f"{member} nu a stat deloc pe canalele de voce in {'ultima zi' if days == 1 else 'ultimele ' + str(days) + ' zile'} pe canalele de voce!")
    # =========================================================================
    #
    #
    #
    # =========================================================================
    # Loop-ul care ia info cine e conectat pe canalele de voce
    @tasks.loop(minutes=1)
    async def collect(self):
        with open("json/voicetime.json", "r") as file:
            states = json.load(file)

        for guild in self.client.guilds:
            if str(guild.id) not in states.keys():
                states[str(guild.id)] = dict()

            for voice_channel in guild.voice_channels:
                for member_id in voice_channel.voice_states.keys():
                    member_voice_state = voice_channel.voice_states[member_id]

                    # daca nu e afk sau are mute sau deafen
                    if not (member_voice_state.afk
                            or member_voice_state.mute
                            or member_voice_state.self_mute
                            or member_voice_state.deaf
                            or member_voice_state.self_deaf
                            or member_voice_state.suppress):
                        if str(member_id) not in states[str(guild.id)].keys():
                            states[str(guild.id)][str(member_id)] = 0
                        states[str(guild.id)][str(member_id)] += 1

        with open("json/voicetime.json", "w") as file:
            json.dump(states, file, indent=2)
    # =========================================================================
    #
    #
    #
    # =========================================================================
    # Loop-ul care salveaza informatiile din json in baza de date

    @tasks.loop(hours=1)
    async def save_data(self):
        with open("json/voicetime.json", "r") as file:
            states = json.load(file)

        for guild in self.client.guilds:
            if str(guild.id) in states.keys():
                for member_id in states[str(guild.id)].keys():
                    query_update(f"insert into `voice_activity`(`guild_id`, `member_id`, `time_connected`) \
                                   values ({guild.id}, {int(member_id)}, {states[str(guild.id)][member_id]})")
            del states[str(guild.id)]

        with open("json/voicetime.json", "w") as file:
            json.dump(states, file, indent=2)
    # =========================================================================
    #
    #
    #
    # =========================================================================
    # Loop-ul care da automat

    @tasks.loop(hours=1)
    async def auto_roles(self):
        dt = datetime.datetime.now() - datetime.timedelta(days=14)
        infos = query_select(
            f"select * from `voice_activity` where `datetime`>='{dt}'")

        states = dict()
        for info in infos:
            # daca serverul a fost salvat local
            if str(info[0]) not in states.keys():
                states[str(info[0])] = dict()
            # daca membrul a fost salvat local in serverul din care face parte
            if str(info[1]) not in states[str(info[0])].keys():
                states[str(info[0])][str(info[1])] = 0
            # i se aduna toate minutele salvate in baza de date
            states[str(info[0])][str(info[1])] += info[2]

        with open("json/voiceroles.json") as file:
            result = json.load(file)

        for guild in self.client.guilds:

            if str(guild.id) in result.keys() and result[str(guild.id)]:
                for member in guild.members:
                    if not check_status("immunity", member) and not check_status("banned", member):

                        for role_dict in result[str(guild.id)]:
                            role_obj = guild.get_role(role_dict["role_id"])
                            if states and str(member.id) in states[str(guild.id)].keys() and states[str(guild.id)][str(member.id)] >= role_dict["time_connected"]:
                                if role_obj not in member.roles:
                                    await member.add_roles(role_obj,
                                                           reason=f'[ROL VOCE] Are {states[str(guild.id)][str(member.id)]}\
                                                                    {"minut" if states[str(guild.id)][str(member.id)] == 1 else "minute"}\
                                                                    pe canalele de voce în ultimele 14 zile')
                            else:
                                if role_obj in member.roles:
                                    await member.remove_roles(role_obj,
                                                              reason='[ROL VOCE] Nu are suficiente minute pe canalele de voce în ultimele 14 zile pentru acest rol')


def setup(client):
    client.add_cog(Voice(client))
