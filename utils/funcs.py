import discord
import json
import random


def check_status(status: str, member: discord.Member) -> bool:
    with open(f"json/{status}.json") as file:
        server_users = json.load(file)

    if str(member.guild.id) in server_users.keys():
        if member.id in server_users[str(member.guild.id)]:
            return True
    return False


def get_random_color():
    def r(): return random.randint(0, 255)
    return (r(), r(), r())
