import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite as sql

token = 'MTIyMjU0NDYzODU2NTY3OTE1NA.GORpSM.-lRqnDgpl3lukuNkivKB-1Mn_AV-LY2LhB6hgc'

bot = commands.Bot(command_prefix='<>', intents=discord.Intents.all())


@bot.event
async def on_ready():
    print(bot.user)
    async with sql.connect('main.db') as db:
        async with db.cursor() as cur:
            await cur.execute("CREATE TABLE IF NOT EXISTS Ongoing(Current_exchange int not null, Title varchar(100) not null);")
            await cur.execute("SELECT * FROM Ongoing;")
            a = await cur.fetchall()
            if len(a) == 0:
                await cur.execute("INSERT INTO Ongoing VALUES(0, 'NONE');")
        await db.commit()
    try:
        synced = await bot.tree.sync()
        print('bot tree is synced')
    except Exception as e:
        print(e)


@bot.tree.command(name='initiate_exchange', description='Use this command to begin the exchange.')
@commands.has_role("Exchange Master")
@app_commands.describe(title='Enter Title of Exchange',
                       submission_period='How long is the submission period (in days)?',
                       exchange_period="How long is the exchange period (in days)?",
                       password="Enter passkey here")
async def initiate(interaction: discord.Interaction, title: str, submission_period: int, exchange_period: int, password: str):
    async with sql.connect('main.db') as db:
        async with db.cursor() as cur:
            await cur.execute("SELECT * FROM Ongoing;")
            ongoing = await cur.fetchall()
        await db.commit()
    if ongoing[0][0] == 1:
        await interaction.response.send_message("An Exchange in already in progress.", ephemeral=True)
    elif (ongoing[0][0] == 0) and (password == "never_share_this"):
        async with sql.connect('main.db') as db:
            async with db.cursor() as cur:
                await cur.execute("SELECT * FROM Ongoing;")
                ongoing = await cur.fetchall()
                if len(ongoing) != 0:
                    await cur.execute(f'''UPDATE Ongoing SET Current_Exchange=1, Title='{title}' where Current_Exchange=0;''')
                    await db.commit()
                else:
                    await cur.execute(f'''INSERT INTO Ongoing VALUES(1, "{title}");''')
                    await db.commit()
                await cur.execute(f'''CREATE TABLE {title}(Member varchar(100) not null, 
                                    Artist varchar(100) not null, 
                                    Album varchar(100) not null, 
                                    Genre varchar(100) not null, 
                                    Year int not null, 
                                    Country varchar(100) not null, rating varchar(100) not null);''')
                await db.commit()
        await interaction.response.send_message("Exchange has been initiated successfully!", ephemeral=True)
    else:
        await interaction.response.send_message("Fuck off imposter!")


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
            if ongoing[0][0] == 1:
                await cur.execute(f'''SELECT * FROM {ongoing[0][1]} where Member='{interaction.user}';''')
                a = await cur.fetchall()
                if len(a) == 0:
                    await cur.execute(f'''INSERT INTO {ongoing[0][1]} VALUES("{interaction.user}", "{artist}", "{album}", "{genre}", {year}, 
                                                "{country}", "{rating}");''')
                    await db.commit()

                    await interaction.response.send_message(
                        f'''You successfully submitted the following entry \n "{artist} - {album} 
                        ({genre}, {country}, {year}) [{rating}]".''', ephemeral=True)
                    role = discord.utils.get(interaction.guild.roles, name="Album Exchanger")
                    await interaction.user.add_roles(role)
                else:
                    await interaction.response.send_message("You have already submitted one entry. Fuck off.",
                                                            ephemeral=True)
            else:
                await interaction.response.send_message(
                    "Please wait for an Exchange to be initiated by the moderators.", ephemeral=True)

bot.run(token)