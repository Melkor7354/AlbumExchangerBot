import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiosqlite as sql
import datetime
import time
import random

token = 'MTIyMjU0NDYzODU2NTY3OTE1NA.GORpSM.-lRqnDgpl3lukuNkivKB-1Mn_AV-LY2LhB6hgc'
passkey = "hello"
utc = datetime.timezone.utc
bot = commands.Bot(command_prefix='?', intents=discord.Intents.all())
print(datetime.datetime.utcnow())
daily_announcement_time = datetime.time(hour=12, tzinfo=utc)


@bot.command()
async def text(ctx, arg):
    await ctx.channel.send(arg)
    print(arg)


def shuffle(data) -> list:
    def create_reference(data):
        submissions = {}
        member_list = []
        album_list = []
        for submission in data:
            album = f"{submission[1]} - {submission[2]} ({submission[3]}, {submission[4]}, {submission[5]}) [{submission[6]}]"
            submissions[submission[0]] = album
            member_list.append(submission[0])
            album_list.append(album)
        return submissions, member_list, album_list
    reference, members, albums = create_reference(data)
    shuffled = []
    for member in members:
        album = random.choice(albums)
        while album == reference[member]:
            album = random.choice(albums)
        shuffled.append((member, album))
        albums.remove(album)
    return shuffled


def starting_messages(shuffled) -> list:
    messages = []
    message = ''
    for i in shuffled:
        part = f"<@{i[0]}> - {i[1]} \n"
        if len(message + part) <= 2000:
            message = message + part
        else:
            message.append(messages)
            message = ''
    if len(messages) == 0:
        return [message]
    else:
        messages.append(message)
        return messages


def unix_time(date: datetime.datetime, days: int, hours: int = 0, minutes: int = 0, seconds: int = 0) -> str:
    end_date = date + datetime.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
    date_tuple = (end_date.year, end_date.month, end_date.day, end_date.hour, end_date.minute, end_date.second)
    return f'<t:{int(time.mktime(datetime.datetime(*date_tuple).timetuple()))}>'


@bot.event
async def on_ready():
    print(bot.user)
    async with sql.connect('main.db') as db:
        async with db.cursor() as cur:
            await cur.execute('''CREATE TABLE IF NOT EXISTS Ongoing(Current_exchange int not null, 
            Title varchar(100) not null, Accepting_Entries int not null, Submission_period int not null, 
            Exchange_period int not null);''')
            await cur.execute("SELECT * FROM Ongoing;")
            a = await cur.fetchall()
            if len(a) == 0:
                await cur.execute("INSERT INTO Ongoing VALUES(0, 'NONE', 0, 0, 0);")
        await db.commit()
    try:
        synced = await bot.tree.sync()
        print('bot tree is synced')
        sync = await bot.command()
    except Exception as e:
        print(e)


@tasks.loop(time=daily_announcement_time)  # scheduling task runs daily
async def daily_reminder():
    pass


@bot.event
async def on_message(message: discord.Message) -> None:

    try:
        channel = bot.get_channel(1223193607050362945)
        role = discord.utils.get(message.guild.roles, name="Album Exchanger")
        if message.channel.id == 1223193607050362945 and message.author != bot.user:
            async with sql.connect('main.db') as db:
                async with db.cursor() as cur:
                    await cur.execute("SELECT * FROM Ongoing;")
                    ongoing = await cur.fetchall()
                    await cur.execute(f'''UPDATE {ongoing[0][1]}_shuffled set reviewed=1 where 
                    member="{message.author.id}"''')
                    await db.commit()
            await channel.send(f"Thank you for submitting your review, {message.author}!")
            await message.author.remove_roles(role)
        else:
            pass
    except Exception:
        pass


@bot.tree.command(name='initiate_exchange', description='Use this command to begin the exchange.')
@commands.has_role("Exchange Master")
@app_commands.describe(title='Enter Title of Exchange',
                       submission_period='How long is the submission period (in days)?',
                       exchange_period="How long is the exchange period (in days)?",
                       message="Give a Custom Message.",
                       theme="Give a Theme for the exchange.",
                       password="Enter passkey here",
                       roles="Roles to Tag")
async def initiate(interaction: discord.Interaction, title: str, submission_period: int, exchange_period: int,
                   password: str, message: str = None, theme: str = None, roles: discord.Role = None):
    async with sql.connect('main.db') as db:
        async with db.cursor() as cur:
            await cur.execute("SELECT * FROM Ongoing;")
            ongoing = await cur.fetchall()
        await db.commit()
    if ongoing[0][0] == 1:
        await interaction.response.send_message("An Exchange in already in progress.", ephemeral=True)
    elif (ongoing[0][0] == 0) and (password == passkey):
        async with sql.connect('main.db') as db:
            async with db.cursor() as cur:
                await cur.execute("SELECT * FROM Ongoing;")
                ongoing = await cur.fetchall()
                try:
                    if len(ongoing) != 0:
                        await cur.execute(f'''UPDATE Ongoing SET Current_exchange=1, Title='{title}', 
                        Accepting_Entries=1, Submission_period={submission_period}, Exchange_Period={exchange_period} 
                        where Current_exchange=0;''')
                    else:
                        await cur.execute(f'''INSERT INTO Ongoing VALUES(1, "{title}", 1, {submission_period}, 
                        {exchange_period});''')
                    await cur.execute(f'''CREATE TABLE {title}(Member varchar(100) not null, 
                                                        Artist varchar(100) not null, 
                                                        Album varchar(100) not null, 
                                                        Genre varchar(100) not null, 
                                                        Year int not null, 
                                                        Country varchar(100) not null, Rating varchar(100) not null, 
                                                        Id INTEGER primary key AUTOINCREMENT);''')
                    await db.commit()
                except Exception as e:
                    print(e)
                    await interaction.response.send_message("Exchange with that title already exists. Please try again",
                                                            ephemeral=True)
                    return

        channel = bot.get_channel(1222594360630050857)
        try:
            await channel.send(f'''# Submissions are now open! \n \n 
            ### You have until {unix_time(date=datetime.datetime.now(), days=submission_period)}\n
            ### The albums will be handed out on {unix_time(date=datetime.datetime.now(), days=submission_period)}
            ### After you receive your album, you have until {unix_time(date=datetime.datetime.now(), days=submission_period+exchange_period)} to send in your feedback.
            {roles.mention}.''')
        except Exception:
            await channel.send(f'''# Submissions are now open! \n \n 
            ### You have until {unix_time(date=datetime.datetime.now(), days=submission_period)}\n
            ### The albums will be handed out on {unix_time(date=datetime.datetime.now(), days=submission_period)}
            ### After you receive your album, you have until {unix_time(date=datetime.datetime.now(), days=submission_period+exchange_period)} to send in your feedback. 
            <@&1222628620158369823>''')
        await interaction.response.send_message("Exchange has been initiated successfully!", ephemeral=True)
    else:
        await interaction.response.send_message("Fuck off imposter!", ephemeral=True)


@bot.tree.command(name='enter_exchange', description='Use this command to enter the album exchange!')
@app_commands.describe(artist='Artist/Band Name', album='Name of the Record', genre='Genre', year='Year of release',
                       country='Country', rating='Your rating of the album')
async def enter(interaction: discord.Interaction, artist: str, album: str, genre: str, year: int, country: str,
                rating: str):
    async with sql.connect('main.db') as db:
        async with db.cursor() as cur:
            await cur.execute("SELECT * FROM Ongoing;")
            ongoing = await cur.fetchall()
            await db.commit()
            print(ongoing[0][0])
            if ongoing[0][0] == 1 and ongoing[0][2] == 1:
                await cur.execute(f'''SELECT * FROM {ongoing[0][1]} where Member='{interaction.user.id}';''')
                check_member = await cur.fetchall()
                if len(check_member) == 0:
                    await cur.execute(f'''SELECT * FROM {ongoing[0][1]} where Artist="{artist}" and Album="{album}";''')
                    check_album = await cur.fetchall()
                    if len(check_album) == 0:
                        await cur.execute(f'''INSERT INTO {ongoing[0][1]} (Member, Artist, Album, Genre, Year, Country, 
                        Rating) VALUES("{interaction.user.id}", "{artist}", "{album}", "{genre}", {year}, "{country}", 
                        "{rating}");''')
                        await db.commit()
                        await interaction.response.send_message(f'''You successfully submitted the following entry - \n "{artist} - {album} ({genre}, {country}, {year}) [{rating}]".''', ephemeral=True)
                        role = discord.utils.get(interaction.guild.roles, name="Album Exchanger")
                        await interaction.user.add_roles(role)
                    else:
                        await interaction.response.send_message('''Someone has already submitted the same album. 
                        Please try again with a different record.''', ephemeral=True)
                else:
                    await interaction.response.send_message("You have already submitted one entry. Fuck off.",
                                                            ephemeral=True)
            elif ongoing[0][0] == 1 and ongoing[0][2] == 0:
                interaction.response.send_message("The submissions for the current exchange are closed. ")
            else:
                await interaction.response.send_message(
                    "Please wait for an Exchange to be initiated by the moderators.", ephemeral=True)


@bot.tree.command(name='start_exchange', description='Use this to begin the exchange and assign albums.')
@app_commands.describe(password="Enter Password Here")
async def start(interaction: discord.Interaction, password: str):
    if password == passkey:
        async with sql.connect('main.db') as db:
            async with db.cursor() as cur:
                await cur.execute("SELECT * FROM Ongoing;")
                ongoing = await cur.fetchall()
                await cur.execute(f"SELECT * FROM {ongoing[0][1]}")
                data = await cur.fetchall()
                shuffled = shuffle(data)
                await cur.execute(f'''CREATE TABLE {ongoing[0][1]}_shuffled(member varchar(100) not null, 
                album varchar(100) not null, reviewed int not null);''')
                await db.commit()
                for i in shuffled:
                    await cur.execute(f'''INSERT INTO {ongoing[0][1]}_shuffled VALUES("{i[0]}", "{i[1]}", 0);''')
                await cur.execute(f'UPDATE Ongoing set Accepting_Entries=0 where Current_Exchange=1;')
                await db.commit()
                messages = starting_messages(shuffled=shuffled)
                channel = bot.get_channel(1222594360630050857)
                await channel.send(f"# Exchange has begun! \n\n Be ready with your feedback by {unix_time(date=datetime.datetime.now(), days=ongoing[0][4])}")
                for message in messages:
                    await channel.send(message)
        await interaction.response.send_message("Exchange has started", ephemeral=True)
    else:
        await interaction.response.send_message("Fuck off imposter", ephemeral=True)


@bot.tree.command(name='end_exchange', description='Ends the ongoing exchange.')
@app_commands.describe(password='Enter password here.', roles="Enter role to ping.")
async def end(interaction: discord.Interaction, password: str, roles: discord.Role = None):
    async with sql.connect('main.db') as db:
        async with db.cursor() as cur:
            await cur.execute("SELECT * FROM Ongoing;")
            ongoing = await cur.fetchall()
            if password == passkey:
                if ongoing[0][0] == 1:
                    await cur.execute('UPDATE Ongoing SET Current_exchange=0, Title="NONE" where Current_exchange=1;')
                    await db.commit()
                    await interaction.response.send_message("Exchange ended successfully!", ephemeral=True)
                    channel = bot.get_channel(1222594360630050857)
                    role = discord.utils.get(interaction.guild.roles, name='shitter')
                    await cur.execute(f'''SELECT * FROM {ongoing[0][1]}_shuffled;''')
                    data = await cur.fetchall()
                    good = []
                    shit = []
                    for i in data:
                        if i[2] == 1:
                            good.append(int(i[0]))
                        else:
                            shit.append(int(i[0]))
                    print(good)
                    print(shit)
                    messages = ['Gather around to look at the shitters from this round! \n']
                    message = ''
                    for shitter in shit:
                        member = interaction.guild.get_member(shitter)
                        print(member)
                        await member.add_roles(role)
                        part = f'<@{shitter}> \n'
                        if len(message+part) <= 2000:
                            message += part
                        else:
                            messages.append(message)
                            message = ''
                    messages.append(message)
                    for message in messages:
                        await channel.send(message)
                    try:
                        await channel.send(f"The exchange has ended! Thank you for participating! \n{roles.mention}")
                    except Exception:
                        await channel.send("The exchange has ended! Thank you for participating \n<@&1222628620158369823>")

                else:
                    await interaction.response.send_message("No Exchange ongoing.", ephemeral=True)
            else:
                await interaction.response.send_message('Fuck off imposter', ephemeral=True)


@bot.tree.command(name='review_entries', description='View the current entries and review them')
@app_commands.describe(password='Enter Password')
async def review(interaction: discord.Interaction, password: str):
    if password == passkey:
        async with sql.connect('main.db') as db:
            async with db.cursor() as cur:
                await cur.execute("SELECT * FROM Ongoing;")
                ongoing = await cur.fetchall()
                await cur.execute(f"SELECT * FROM {ongoing[0][1]}")
                data = await cur.fetchall()
                messages = []
                message = ''
                for i in data:
                    part = f"{i[7]} -- <@{i[0]}> : {i[1]} - {i[2]} ({i[3]}, {i[4]}, {i[5]}) [{i[6]}] \n"
                    if len(message + part) <= 2000:
                        message = message + part
                    else:
                        message.append(messages)
                        message = ''
                if len(messages) == 0:
                    messages = [message]
                else:
                    messages.append(message)
                embed = discord.Embed(title="Current Submissions", description="Here is a list of current submissions within this exchange", color=0x00ff00)
                for message in messages:
                    embed.add_field(name='\n', value=message, inline=False)
                await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("Password Invalid", ethereal=True)


@bot.tree.command(name="remove_entries", description="Remove Entries after review")
@app_commands.describe(password="Enter Password", indexes="Enter the index of the entry/ies to be removed. For example, to remove entries 1 and 3, enter 1,3 ")
async def remove(interaction: discord.Interaction, password: str, indexes: str):
    if password == passkey:
        indices = indexes.replace(" ", "").split(",")
        to_delete = []
        try:
            for i in indices:
                to_delete.append(int(i))
        except ValueError:
            interaction.response.send_message(
                "Please enter the required indexes correctly. Ensure that they are valid integers.", ethereal=True)
            return
        try:
            async with sql.connect('main.db') as db:
                async with db.cursor() as cur:
                    await cur.execute("SELECT * FROM Ongoing;")
                    ongoing = await cur.fetchall()
                    for i in indices:
                        await cur.execute(f"DELETE FROM {ongoing[0][1]} WHERE Id={i};")
                    await db.commit()
            await interaction.response.send_message("Entries removed successfully.")
        except Exception as e:
            print(e)
            await interaction.response.send_message("Problem with the indices. Please try again.", ethereal=True)

    else:
        interaction.response.send_message("Invalid Password")


bot.run(token)
