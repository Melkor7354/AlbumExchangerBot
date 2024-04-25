# AlbumExchangerBot
The Exchanger bot has been created for the purpose of automating the weekly album exchange event in the MetalMemes discord server.

The bot uses SQLite as a database and uses the standard Discord.py library to create the bot.

# Main Functions
## Shuffle
```python
def shuffle(data) -> list:
    def create_reference(dat):
        submissions = {}
        member_list = []
        album_list = []
        for submission in dat:
            album = f"{submission[1]} - {submission[2]} ({submission[3]}, {submission[4]}, {submission[5]}) [{submission[6]}]"
            submissions[submission[0]] = album
            member_list.append(submission[0])
            album_list.append(album)
        return submissions, member_list, album_list
    reference, members, albums = create_reference(data)
    shuffled = []
    def get(reference, member, albums):
        album = random.choice(albums)
        if album == reference[member]:
            get(reference=reference, member=member, albums=albums)
        else:
            return album

    for member in members:
        album = get(reference=reference, member=member, albums=albums)
        shuffled.append((member, album))
        albums.remove(album)
    return shuffled
```
Assigns unique random albums to each submitter. Creates a reference to avoid giving a user's album back to them using the get function (recursive logic). Returns a shuffled list.
## Create Messages and Unix Time
```python
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
```
Creates starting messages to be sent by the bot once the exchange has begun. Returns a list of messages to be sent to desired channel.
