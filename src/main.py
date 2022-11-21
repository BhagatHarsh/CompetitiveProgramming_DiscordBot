import discord as dc
import requests
import json
import random
import pymongo
import os
import operator
# from keep_alive import keep_alive
import time
# from dotenv import load_dotenv
# load_dotenv()  # take environment variables from .env.

dbClient = pymongo.MongoClient(os.getenv('DB'), 27017)
db = dbClient.discord

#global vars
client = dc.Client(intents=dc.Intents.default())
problems = {}
minQuery = 10000
maxQuery = -1
QueryList = set()
dump = []
flag = 0
TOKEN = os.environ["KEY"]


def preCompute():
    global minQuery, maxQuery
    print("Getting the questions ready")
    global flag
    url = 'https://codeforces.com/api/problemset.problems'
    reqs = requests.get(url)
    data = json.loads(reqs.text)
    for line in data['result']['problems']:
        try:
            dump.append(int(line['rating']))
            flag = 1
            minQuery = min(minQuery, int(line['rating']))
            maxQuery = max(maxQuery, int(line['rating']))
            QueryList.add(int(line['rating']))
            problems[int(line['rating'])].append(line)
        except:
            if (flag):
                problems[int(line['rating'])] = [line]
            else:
                dump.append(line['contestId'])
        flag = 0
    return minQuery, maxQuery


# minQuery, maxQuery = preCompute()


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
                users.append(
                    (key['handle'], key['newRating'],
                     '(' + str(key['newRating'] - key['oldRating']) + ')'))
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


def journey(user: str):
    msgStr = ''
    url = 'https://codeforces.com/api/user.rating?handle=' + user
    response = requests.get(url)
    data = json.loads(response.text)
    if (data['status'] == 'OK'):
        row = "{name1:>20}  {name2:>20}  {name3:>20}".format
        result = data['result']
        msgStr = row(name1="Contests", name2="Rank", name3="Rating") + '\n\n'
        for i in reversed(result):
            if (len(msgStr) > 1800):
                break

            try:
                strippedContestName = i['contestName'][i['contestName'].find(
                    'Codeforces'):i['contestName'].find('(')]
            except:
                strippedContestName = i['contestName']
            msgStr += row(
                name1=strippedContestName,
                name2=i['rank'],
                name3=(str(i['newRating']) + ' (' +
                       str(int(i['newRating']) - int(i['oldRating'])) +
                       ')')) + '\n'

    else:
        msgStr = 'No data Found!!'
    return '```' + msgStr + '```'


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
    poolOfProblems = problems[rating]
    problem = poolOfProblems[random.randint(0, len(poolOfProblems) - 1)]
    msgstr = 'Try to solve this ' + str(rating) + ' rated problem ' + str(
        author) + '\n'
    msgstr += "https://codeforces.com/problemset/problem/" + str(
        problem["contestId"]) + "/" + str(problem["index"])

    return msgstr


@client.event
async def on_ready():
    print(client.guilds)
    preCompute()
    print('A user has logged in as %s' % (client.user))


@client.event
async def on_message(message):
    if (message.author == client.user):
        return

    if (message.content == '* help'):
        msgStr = """
        ```
"* set <handle>" to add your code forces handle to the database. 
For example "* set Tourist".

"* gimme <rating> to get a codeforces random question of <rating> level. 
For example "* gimme 1200".

"* ratings" to get a list of all problem ratings you can gimme for.

"* list" to list all the ratings of the registered handles in the database.

"* journey <handle>" to see all the recent activity of the user <handle> on codeforces.```
        """
        await message.channel.send(msgStr)

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
                'Please try again using * gimme <Rating> where rating name is between %s and %s'
                % (str(minQuery), str(maxQuery)))

    if (message.content.startswith(('* ratings'))):
        try:
            msgStr = "The question ratings present are: \n" + (' '.join(
                [str(rating) for rating in sorted(QueryList)]))
            await message.channel.send("```\n" + msgStr + '```')
        except Exception as e:
            await message.channel.send(
                'Please try again using * ratings error occured %s' % (str(e)))

    if (message.content.startswith(('* list'))):
        try:
            server = str(message.guild)
            await message.channel.send(showLeaderBoard(server))
        except:
            await message.channel.send(
                'Please try again using * set <HandleName> ')

    if (message.content.startswith(('* journey'))):
        try:
            Handle = message.content.split()[2]
            await message.channel.send(journey(Handle))
        except Exception as e:
            await message.channel.send(str(e))


#addressing the bot
# keep_alive()
client.run(TOKEN)

