import discord as dc
import requests
import json
import random
import pymongo
import os
import operator
from keep_alive import keep_alive
import time
dbClient = pymongo.MongoClient(os.getenv('DB'), 27017)
db = dbClient.discord

#global vars
client = dc.Client()
problems = {}
dump = []
flag = 0
TOKEN = os.environ["KEY"]


def preCompute():
    global flag
    url = 'https://codeforces.com/api/problemset.problems'
    reqs = requests.get(url)
    data = json.loads(reqs.text)
    for line in data['result']['problems']:
        try:
            dump.append(int(line['rating']))
            flag = 1
            problems[int(line['rating'])].append(line)
        except:
            if (flag):
                problems[int(line['rating'])] = [line]
            else:
                dump.append(line['contestId'])
        flag = 0
    return


def getRating(user: str) -> str:
    url = 'https://codeforces.com/api/user.rating?handle=' + user
    response = requests.get(url)
    data = json.loads(response.text)
    return str(data['result'][-1])


def showLeaderBoard(server: str):
    allValues = db.Handles.find({"server": server})
    users = []
    msgStr = ''
    for i in allValues:
        print(i)
        for j in i['users']:
            try:
                time.sleep(0.5)
                key = eval(getRating(j[0:100]))
                # print(type(eval(key)))
                users.append((key['handle'], key['newRating'],
                              key['newRating'] - key['oldRating']))
            except:
                msgStr += "Error Occured while getting the rating of " + str(
                    j) + '\n'
                continue
    sortedUsers = sorted(users, key=operator.itemgetter(1))
    print(sortedUsers)
    row = "{name1:^20}|{name2:^20}|{name3:^20}".format
    msgStr += '\n\n'
    msgStr = row(name1="Handles", name2="CurrentRating",
                 name3="Changes") + '\n\n'
    for i in reversed(sortedUsers):
        msgStr += row(name1=i[0], name2=i[1], name3=i[2]) + '\n'
    return "```" + msgStr + "```"


def setHandle(server: str, handle: str):
    handleObj = getRating(handle)
    print(handleObj)
    try:
        data = db.Handles.find({"server": server}).next()
        if (handle in data['users']):
            return "Handle Already in the Server"
        db.Handles.find_one_and_update({"server": server},
                                       {"$push": {
                                           "users": handle
                                       }})
    except:
        db.Handles.insert_one({"server": server, "users": [handle]})
    return "Handle Added Successfully of " + handle
    return


def getQuestion(rating, author):
    try:
        poolOfProblems = problems[rating]
        problem = poolOfProblems[random.randint(0, len(poolOfProblems) - 1)]
        msgstr = 'Try to solve this ' + str(rating) + ' rated problem ' + str(
            author) + '\n'
        msgstr += "https://codeforces.com/problemset/problem/" + str(
            problem["contestId"]) + "/" + str(problem["index"])

        return msgstr
    except Exception as e:
        return e
    return


@client.event
async def on_ready():
    print(client.guilds)
    preCompute()
    print('A user has logged in as %s' % (client.user))


@client.event
async def on_message(message):
    if (message.author == client.user):
        return

    if (message.content == '*'):
        await message.channel.send(
            '[ping here](https://CFbot2.harshbhagat1.repl.co)')

    if (message.content.startswith(('* set'))):
        try:
            Handle = message.content.split()[2]
            server = str(message.guild)
            await message.channel.send(setHandle(server, Handle))
        except:
            await message.channel.send(
                'Please try again using * set <HandleName>')

    if (message.content.startswith(('* gimme'))):
        try:
            rating = message.content.split()[2]
            await message.channel.send(getQuestion(int(rating),
                                                   message.author))
        except:
            await message.channel.send(
                'Please try again using * gimme <Rating>')

    if (message.content.startswith(('* list'))):
        try:
            server = str(message.guild)
            await message.channel.send(showLeaderBoard(server))
        except:
            await message.channel.send(
                'Please try again using * set <HandleName>')


#addressing the bot

keep_alive()
try:
    client.run(TOKEN)
except:
    print("\n\n\nBLOCKED BY RATE LIMITS\nRESTARTING NOW\n\n\n")
    os.system('kill 1')
