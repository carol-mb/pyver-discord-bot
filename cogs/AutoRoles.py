import discord
from discord.ext import commands, tasks
from discord.utils import get

from datetime import datetime
import json

#import utils.errors
from utils.funcs import check_status, get_random_color
from utils.db_conn import query_select, query_update


class AutoRoles(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("AutoRoles cog s-a încărcat cu succes.")

        infos = query_select(
            "select * from `autoroles`")

        roles = dict()

        for info in infos:
            if str(info[0]) not in roles.keys():
                roles[str(info[0])] = list()
            roles[str(info[0])].append({
                "role_id": info[1],
                "receive_after": info[2],
                "remove_after": info[3]
            })

        with open("json/autoroles.json", "w") as file:
            json.dump(roles, file, indent=2)

        self.auto_roles.start()
        print(
            f'AutoRoles s-a pornit cu succes la {datetime.utcnow().strftime("%H:%M:%S")}!')

    @commands.Cog.listener()
    async def on_member_join(self, member):

        # ii da gradele care trebuie sa se dea cand intra pe server
        # daca nu este imun sau banat
        if not check_status("immunity", member) and not check_status("banned", member):
            join_roles = query_select(
                f'select `role_id` from `autoroles` where `guild_id` = {member.guild.id} and `receive_after` = 0')

            for join_role in join_roles:
                role = member.guild.get_role(join_role[0])
                if role is not None:
                    await member.add_roles(role, reason='rol automat (la intrarea pe server)')
    #
    #
    #
    # =========================================================================
    # Adauga rol automat

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def addautorole(self, ctx, role: discord.Role, receive_days=0, remove_days=0):
        """
        Adaugă un rol care se va acorda automat după un număr setat de zile.
        """
        await ctx.message.delete()

        with open("json/autoroles.json", "r") as file:
            result = json.load(file)

        if str(ctx.guild.id) not in result.keys():
            result[str(ctx.guild.id)] = list()

        for role_dict in result[str(ctx.guild.id)]:
            if role_dict["role_id"] == role.id:
                role_dict["receive_after"] = receive_days
                role_dict["remove_after"] = remove_days
                query_update(
                    f'update `autoroles` set `receive_after`={receive_days}, `remove_after`={remove_days} where `guild_id`={ctx.guild.id} and `role_id`={role.id}')
                break
        else:
            result[str(ctx.guild.id)].append(
                {"role_id": role.id, "receive_after": receive_days, "remove_after": remove_days})
            query_update(
                f'insert into `autoroles`(`guild_id`, `role_id`, `receive_after`, `remove_after`) values({ctx.guild.id}, {role.id}, {receive_days}, {remove_days})')

        with open("json/autoroles.json", "w") as file:
            json.dump(result, file, indent=2)

        embed = discord.Embed(title="Rolul automat a fost adăugat",
                              color=discord.Color.from_rgb(*get_random_color()))

        given = f"după {receive_days} {'zi' if receive_days == 1 else 'zile'} după ce membrul intră pe server" if receive_days else "când membrul intră pe server"
        removed = f"după {remove_days} {'zi' if receive_days == 1 else 'zile'} după ce membrul a primit acest rol" if remove_days else "niciodată"

        embed.description = f"{role.mention} va fi dat automat {given} și va fi șters {removed}."
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
    async def removeautorole(self, ctx, role: discord.Role):
        """
        Șterge un rol care era setat să se acorde automat.
        """
        await self.message.delete()

        with open("json/autoroles.json", "r") as file:
            result = json.load(file)

        # verifica daca rolul a fost setat sa se acorde automat
        if str(ctx.guild.id) in result.keys() and result[str(ctx.guild.id)]:

            for role in result[str(ctx.guild.id)]:

                if role["role_id"] == role.id:
                    result[str(ctx.guild.id)].remove(role)
                    embed = discord.Embed(title="Rolul automat a fost șters",
                                          color=discord.Color.from_rgb(
                                              *get_random_color()),
                                          description=f"{role.mention} nu va mai fi acordat automat.")
                    await ctx.send(embed=embed)

                    with open("json/autoroles.json", "w") as file:
                        json.dump(result, file, indent=2)

                    query_update(
                        f'delete from `autoroles` where `guild_id`={ctx.guild.id} and `role_id`={role.id}')

                    break
            else:
                await ctx.send("Acest rol nu era acordat automat.")
        else:
            await ctx.send("Acest rol nu era acordat automat.")
    # =========================================================================
    #
    #
    #
    # =========================================================================
    # Loop-ul care da automat

    @tasks.loop(hours=1)
    async def auto_roles(self):
        time_now = datetime.utcnow()

        with open("json/autoroles.json") as file:
            result = json.load(file)

        for server in self.client.guilds:

            if str(server.id) in result.keys() and result[str(server.id)]:
                for member in server.members:
                    if not check_status("immunity", member) and not check_status("banned", member):
                        days_on_server = (
                            datetime.utcnow() - member.joined_at).total_seconds() / 60 / 60 / 24

                        for role_dict in result[str(server.id)]:
                            role_obj = server.get_role(role_dict["role_id"])

                            # cand are zilele pentru grad, dar mai putin decat cand trebuie sa i-l stearga
                            if days_on_server >= role_dict["receive_after"] and (days_on_server < role_dict["receive_after"] + role_dict["remove_after"]
                                                                                 or not role_dict["remove_after"]):
                                if role_obj not in member.roles:
                                    await member.add_roles(role_obj,
                                                           reason=f'[ROL AUTOMAT] Are {int(days_on_server)} {"zi" if days_on_server == 1 else "zile"} pe server')

                            # cand are mai mult de cate zile trebuie pentru acest rol
                            elif role_dict["remove_after"]:
                                if role_obj in member.roles:
                                    await member.remove_roles(role_obj,
                                                              reason=f'[ROL AUTOMAT] Are mai mult de {int(days_on_server)} {"zi" if (role_dict["receive_after"] + role_dict["remove_after"]) == 1 else "zile" } pe server')
                            # cand nu are zilele necesare
                            else:
                                if role_obj in member.roles:
                                    await member.remove_roles(role_obj,
                                                              reason='[ROL AUTOMAT] Nu are suficiente zile pe server pentru acest rol')


def setup(client):
    client.add_cog(AutoRoles(client))
