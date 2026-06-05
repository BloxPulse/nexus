#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Bot Discord OSINT (Email, Téléphone, Nom, Username, IP, Discord ID)
# À héberger sur Aclcloud (ou tout VPS)
# Prérequis: pip install discord.py requests

import discord
from discord.ext import commands
import requests
import json
import socket
import subprocess
import random
import time

# Configuration
TOKEN = "VOTRE_TOKEN_DISCORD_ICI"  # Remplacez par le token de votre bot
PREFIX = "!"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# ---------- Fonctions OSINT (reprises de nexus.py) ----------
def ip_geolocation(ip=None):
    if not ip:
        try:
            ip = requests.get('https://api.ipify.org').text.strip()
        except:
            return "Impossible de récupérer votre IP"
    try:
        r = requests.get(f'http://ip-api.com/json/{ip}?fields=status,country,regionName,city,lat,lon,isp,org,query', timeout=5)
        data = r.json()
        if data['status'] == 'success':
            return (f"**IP:** {data['query']}\n"
                    f"**Pays:** {data['country']}\n"
                    f"**Région:** {data['regionName']}\n"
                    f"**Ville:** {data['city']}\n"
                    f"**Coordonnées:** {data['lat']}, {data['lon']}\n"
                    f"**FAI:** {data['isp']}")
        else:
            return "Erreur de géolocalisation"
    except:
        return "Erreur requête IP"

def osint_email(email):
    try:
        r = requests.get(f'https://haveibeenpwned.com/api/v3/breachedaccount/{email}', headers={'hibp-api-key': ''}, timeout=10)
        if r.status_code == 200:
            breaches = r.json()
            msg = f"**{len(breaches)} brèche(s) trouvée(s) pour {email}**\n"
            for b in breaches[:10]:
                msg += f"- {b['Name']} ({b['BreachDate']})\n"
            return msg
        elif r.status_code == 404:
            return f"Aucune brèche connue pour {email}"
        else:
            return f"Erreur API (code {r.status_code})"
    except:
        return "Impossible de vérifier haveibeenpwned"

def osint_username(username):
    sites = {
        "Twitter": f"https://twitter.com/{username}",
        "Instagram": f"https://instagram.com/{username}",
        "GitHub": f"https://github.com/{username}",
        "Reddit": f"https://reddit.com/user/{username}",
        "TikTok": f"https://tiktok.com/@{username}",
        "YouTube": f"https://youtube.com/@{username}",
        "Twitch": f"https://twitch.tv/{username}",
        "Pinterest": f"https://pinterest.com/{username}",
        "Snapchat": f"https://snapchat.com/add/{username}",
        "Telegram": f"https://t.me/{username}",
    }
    found = []
    for name, url in sites.items():
        try:
            r = requests.get(url, timeout=3, allow_redirects=True)
            if r.status_code == 200 and ("doesn't exist" not in r.text.lower() and "not found" not in r.text.lower()):
                found.append(f"**{name}:** {url}")
        except:
            pass
        time.sleep(0.2)
    if found:
        return "\n".join(found)
    else:
        return f"Aucun profil trouvé pour @{username}"

def roblox_user_info(user_id):
    try:
        r = requests.get(f'https://users.roblox.com/v1/users/{user_id}')
        if r.status_code == 200:
            data = r.json()
            return (f"**Nom:** {data.get('name')}\n"
                    f"**DisplayName:** {data.get('displayName')}\n"
                    f"**Créé le:** {data.get('created')}")
        else:
            return "Utilisateur Roblox non trouvé"
    except:
        return "Erreur requête Roblox"

def discord_id_info(user_id):
    # Pas d'API publique, on retourne juste une info de base
    return f"L'ID Discord {user_id} ne peut pas être recherché directement via l'API publique. Utilisez un bot avec token pour obtenir des infos."

# ---------- Commandes Discord ----------
@bot.command()
async def ip(ctx, adresse: str = None):
    """Recherche géolocalisation d'une IP (ou votre IP)"""
    await ctx.send(ip_geolocation(adresse))

@bot.command()
async def email(ctx, adresse: str):
    """Vérifie les brèches d'un email (HaveIBeenPwned)"""
    await ctx.send(osint_email(adresse))

@bot.command()
async def username(ctx, pseudo: str):
    """Recherche un username sur les réseaux sociaux"""
    await ctx.send(osint_username(pseudo))

@bot.command()
async def roblox(ctx, user_id: int):
    """Infos sur un utilisateur Roblox"""
    await ctx.send(roblox_user_info(user_id))

@bot.command()
async def discordid(ctx, user_id: int):
    """Infos sur un ID Discord (limité sans token)"""
    await ctx.send(discord_id_info(user_id))

@bot.command()
async def phone(ctx, numero: str):
    """Recherche téléphone (API démo limitée)"""
    try:
        r = requests.get(f'http://apilayer.net/api/validate?access_key=demo&number={numero}')
        if r.status_code == 200:
            data = r.json()
            msg = (f"**Pays:** {data.get('country_name')}\n"
                   f"**Opérateur:** {data.get('carrier')}\n"
                   f"**Localisation:** {data.get('location')}")
            await ctx.send(msg)
        else:
            await ctx.send("API de validation non disponible (clé démo limitée)")
    except:
        await ctx.send("Erreur lors de la recherche téléphonique")

@bot.command()
async def name(ctx, prenom: str, nom: str):
    """Recherche nom/prénom sur réseaux"""
    combos = list(set([
        f"{prenom}{nom}", f"{prenom}.{nom}", f"{prenom}_{nom}", f"{prenom}-{nom}",
        f"{prenom}{nom[0]}", f"{prenom[0]}{nom}", f"{prenom[0]}.{nom}"
    ]))
    sites = ["twitter.com", "instagram.com", "github.com", "reddit.com"]
    found = []
    for combo in combos:
        for site in sites:
            url = f"https://{site}/{combo}"
            try:
                r = requests.get(url, timeout=2)
                if r.status_code == 200 and "not found" not in r.text.lower():
                    found.append(f"**{site}:** {url}")
            except:
                pass
        time.sleep(0.2)
    if found:
        await ctx.send("\n".join(found))
    else:
        await ctx.send(f"Aucun profil trouvé pour {prenom} {nom}")

@bot.event
async def on_ready():
    print(f"Bot connecté en tant que {bot.user}")

if __name__ == "__main__":
    if TOKEN == "MTUxMjMxNTQ4ODQ1NjE1MTE0Mg.GxCJRo.eeJmt9PTphp0QrBE9FrKNlj-9moB2elI4tj1io":
        print("Erreur: remplacez TOKEN par le token de votre bot Discord")
    else:
        bot.run(TOKEN)