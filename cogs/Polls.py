import discord
from discord.ext import commands, tasks
from discord.utils import get, find

from utils.db_conn import query_update, query_select
#import utils.utils_func
#import utils.errors

import asyncio

import json

from datetime import datetime, timedelta


class Polls(commands.Cog):
    '''
    Sistem de sondaje
    '''

    def __init__(self, client):
        self.client = client
    #
    #
    # =========================================================================

    @commands.Cog.listener()
    async def on_ready(self):
        print("Polls cog s-a încărcat cu succes.")

        # Salveaza local in json sondajele care au inceput si trebuie sa se termine
        infos = query_select(
            "select `guild_id`, `id`, `endtime` from `poll_questions` where `status`='started'")
        polls = dict()
        for info in infos:
            if str(info[0]) not in polls.keys():
                polls[str(info[0])] = list()
            polls[str(info[0])].append({
                "q_id": info[1],
                "endtime": str(info[2])
            })

        with open("json/polls.json", "w") as file:
            json.dump(polls, file, indent=2)

        # porneste loop-ul care inchide sondajele
        self.polls_check.start()
    # =========================================================================
    #
    #
    #
    # =========================================================================
    # QPREVIEW VEZI CUM ARATA SONDAJUL INAINTE SA FIE POSTAT

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def qpreview(self, ctx, qID: int):
        '''Previzualizezi cum ar arăta sondajul când l-ai porni.'''
        await ctx.message.delete()
        await ctx.send(embed=Polls.questionPreview(qID, ctx.guild.id))
    # =========================================================================
    #
    #
    #
    # =========================================================================
    # ADDQUESTION ADAUGI O INTREBARE

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def addquestion(self, ctx, *, question):
        '''
        Generezi o întrebare.
        '''
        await ctx.message.delete()

        query_update(
            f'insert into `poll_questions`(`guild_id`, `question`) values ({ctx.guild.id}, "{question}")')

        q_id = query_select(
            f'select `id` from `poll_questions` where `guild_id` = {ctx.guild.id}')

        await ctx.send(embed=Polls.questionPreview(q_id[len(q_id) - 1][0], ctx.guild.id))
    # =========================================================================
    #
    #
    #
    # =========================================================================
    # ADDANSWER ADAUGI UN RASPUNS LA O INTREBARE

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def addanswer(self, ctx, qID: int, emoji, *, answer):
        '''
        Adaugi un răspuns pentru o anumită întrebare.
        '''
        await ctx.message.delete()

        query_update(
            f'insert into `poll_answers`(`q_id`, `guild_id`,`emoji`, `answer`) values ({qID}, {ctx.guild.id}, "{emoji}", "{answer}")')

        await ctx.send(embed=Polls.questionPreview(qID, ctx.guild.id))
    # =========================================================================
    #
    #
    #
    # =========================================================================
    # STARTQUESTION PORNESTI UN SONDAJ

    @commands.command(aliases=['startpoll'])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def startquestion(self, ctx, qID: int, close_time=1):
        '''
        Începi un sondaj. Acesta se va termina după câte ore alegi tu. Dacă nu introduci orele, se va închide automat după 1 oră.
        '''
        await ctx.message.delete()

        # obtinem intrebarea
        question = query_select(
            f'select `question`, `status` from `poll_questions` where `guild_id` = {ctx.guild.id} and `id` = {qID}')[0]

        # daca intrebarea exista si este a acestui server de discord
        if question:
            # daca sondajul nu a inceput il porneste
            if question[1] == "not started":

                # obtine raspunsurile pentru a genera embed-ul
                answers = query_select(
                    f'select `emoji`, `answer` from `poll_answers` where `q_id` = {qID} and `guild_id`={ctx.guild.id}')

                emojis = []
                text = ''

                for answer in answers:
                    text += f'{answer[0]} - {answer[1]}\n'
                    emojis.append(answer[0])

                # asta-i doar pentru afisarea mai frumoasa a intrebarii, sa fie centrat
                bubbles = "▫\t" * (int((54 - len(question[0]))/10)-1)

                question_embed = discord.Embed(
                    title=f"**{bubbles}❓ {question[0]} ❓  {bubbles}**",
                    description="📌 Fiecare emoji corespunde răspunsului din dreptul său!\n\n\n",
                    color=discord.Color.dark_magenta()
                )
                question_embed.add_field(
                    name=f'▫\t▫\t▫\t▫ ⚡ **Răspunsuri** ⚡ ▫\t▫\t▫\t▫', value=text)

                question_embed.set_footer(
                    text="👇 Reacționează cu unul sau mai multe emoji pentru a vota!")

                await ctx.send(f"@everyone, aveți timp {close_time} {'oră' if close_time == 1 else 'ore'} să votați!")
                msg = await ctx.send(embed=question_embed)

                for emoji in emojis:
                    await msg.add_reaction(emoji)

                # actualizeaza in baza de date tot ce mai este nevoie pentru a putea lua mai tarziu
                # raspunsurile, cum ar fi id camerei, id mesajului si schimba statusul in started
                query_update(
                    f'update `poll_questions` set `channel_id` = {ctx.channel.id}, `message_id` = {msg.id}, \
                        `endtime` = "{datetime.now() + timedelta(hours=close_time)}", `status` = "started" \
                        where `guild_id` = {ctx.guild.id} and `id` = {qID}')

                # salveaza local in fisierul json intrebarea pentru ca a pornit
                with open("json/polls.json", "r") as file:
                    polls = json.load(file)

                if str(ctx.guild.id) not in polls.keys():
                    polls[str(ctx.guild.id)] = list()
                polls[str(ctx.guild.id)].append({
                    "q_id": qID,
                    "endtime": (datetime.now() + timedelta(hours=close_time)).strftime("%Y-%m-%d %H:%M:%S")
                })

                with open("json/polls.json", "w") as file:
                    json.dump(polls, file, indent=2)

            # astea 2 sunt cazurile in care intrebarea deja a fost pornita
            elif question[1] == "started":
                await ctx.send(f"❌ Sondajul pentru întrebarea cu ID {qID} (_{question[0]}_) a început deja!")

            elif question[1] == "ended":
                await ctx.send(f"❌ Sondajul pentru întrebarea cu ID {qID} (_{question[0]}_) s-a încheiat deja!")
        else:
            ctx.send(f"❌ Întrebarea cu ID {qID} nu există!")
    # =========================================================================
    #
    #
    #
    # =========================================================================

    @staticmethod
    def questionPreview(qID: int, guild_id: int):
        answers = query_select(
            f'select `emoji`, `answer` from `poll_answers` where `q_id` = {qID} and `guild_id`={guild_id}')
        question = query_select(
            f'select `question` from `poll_questions` where `guild_id` = {guild_id} and `ID` = {qID}')[0][0]

        text = ''

        for answer in answers:
            text += f'{answer[0]} - {answer[1]}\n'

        embed = discord.Embed(
            title=f"❓{question}❓",
            color=discord.Color.dark_magenta()
        )
        embed.set_footer(
            text=f"👉  Vizualizezi intrebarea cu ***ID {qID}***  👈")
        if text != '':
            embed.add_field(name='Răspunsuri', value=text)
        return embed
    # =========================================================================
    #
    #
    #
    # =========================================================================
    # asta-i loop-ul care inchide sondajele si ia raspunsurile din mesaje

    @tasks.loop(minutes=1)
    async def polls_check(self):

        # se foloseste de fisierul local json
        with open("json/polls.json", "r") as file:
            polls = json.load(file)

        # ia fiecare server id in parte din key-le salvate in json
        # verifica fiecare poll inceput daca nu cumva a trecut timpul de inchidere
        for guild_id in polls.keys():
            for poll in polls[guild_id]:
                if(datetime.now() > datetime.strptime(poll["endtime"], "%Y-%m-%d %H:%M:%S")):

                    # daca a trecut timpul, ia celelalte info de care mai e nevoie, gen id camerei, id mesaj etc
                    poll_info = query_select(f"select `channel_id`, `message_id`, `question` from `poll_questions`\
                        where `guild_id`={guild_id} and `id`={poll['q_id']}")[0]

                    # genereaza obiectele necesare pentru a putea lua react-urile de la acel mesaj + camera
                    # ca sa poata trimite rezultatele
                    guild = find(lambda g: g.id == int(guild_id),
                                 self.client.guilds)
                    channel = get(guild.text_channels, id=poll_info[0])
                    message = await channel.fetch_message(poll_info[1])

                    # obtine toate raspunsurile
                    answers = query_select(f"select `emoji`, `answer` from `poll_answers` \
                        where `guild_id`={guild_id} and `q_id`={poll['q_id']}")

                    # generez o lista mai aspectuoasa doar cu informatiile de care am nevoie
                    # verific daca react-ul respectiv reprezinta un vot (adica daca e in baza de date)
                    # un raspuns cu emoji respectiv si salvez totul intr-un tuple (nr voturi, raspuns)
                    votes = list()
                    all_votes = 0
                    for answer in answers:

                        reaction = find(lambda r: str(r.emoji) ==
                                        answer[0], message.reactions)
                        if reaction:
                            all_votes += (reaction.count - 1)
                            votes.append((reaction.count-1, answer[1]))
                    votes.sort(key=lambda x: x[0], reverse=True)

                    # de aici se genereaza embed
                    results_embed = discord.Embed(
                        title=f"👉 Sondajul a luat sfârșit\n\n**❓ {poll_info[2]} ❓**\n\n⚡ Rezultate ⚡",
                        color=discord.Color.green()
                    )

                    for vote in votes:
                        results_embed.add_field(name=f'{vote[1]}  \n',
                                                value=f'{vote[0]} {"vot" if vote[0] == 1 else "voturi"}  - (*{vote[0]/all_votes*100:.2f}%*)',
                                                inline=False)

                    results_embed.set_footer(
                        text=f"Voturi totale: {all_votes}")

                    await channel.send(embed=results_embed)

                    # se actualizeaza baza de date, adica se pune status ended la respectivul sondaj
                    query_update(
                        f"update `poll_questions` set `status`='ended' where `guild_id`={guild.id} and `id`={poll['q_id']}")
                    # se sterge sondajul din json
                    polls[guild_id].remove(poll)

        # se rescrie local fisierul json pentru a se actualiza
        with open("json/polls.json", "w") as file:
            json.dump(polls, file, indent=2)


def setup(client):
    client.add_cog(Polls(client))
