#!/usr/bin/env python
import os
import sys
import random
import sqlite3
import time
import interactions
import asyncio
import requests

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from termcolor import colored

from discord.ext import tasks
from dotenv import load_dotenv
from genericpath import exists
from datetime import datetime
from ics import Calendar, Event
from typing import List, Union

# https://interactionspy.readthedocs.io/en/latest/quickstart.html
from interactions import ActionRow, SelectMenu, SelectOption

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
MOODLE_URL = os.getenv("MOODLE_URL")
USE_GD = os.getenv("USE_GOOGLE_DRIVE")
RESTART_TIMER = os.getenv("RESTART_TIMER")
CALENDAR_URL = os.getenv("CALENDAR_URL")

TEST = False

# Starte den Bot
bot = interactions.Client(token=TOKEN)

# TODO: courses und course_ids in dict umwandeln

courses = []
course_ids = []

channel_dict = {}
con = sqlite3.connect("moodle/moodle_state.db")
cur = con.cursor()


async def getCalendarInformations():
    if CALENDAR_URL:
        c = Calendar(requests.get(CALENDAR_URL).text)
        for ev in c.events:
            # Abgleichen mit der Datenbank
            res = cur.execute(f"SELECT * FROM event WHERE uid='{ev.uid}'")
            fetch = res.fetchone()
            if fetch:
                # TODO: Event ändern falls es Änderungen gibt
                print("")
            else:
                if ev.end.datetime.timestamp() > time.time():
                    print(
                        colored(f"Ein neues Event '{ev.name}' wird erstellt", "yellow")
                    )
                    category = ev.categories.pop()
                    location = "Moodle"
                    if ev.location:
                        location = ev.location

                    event = await createEvent(
                        name=f"{ev.name} - {category}",
                        description=ev.description,
                        location=location,
                        scheduled_start_time=ev.begin.datetime,
                        scheduled_end_time=ev.end.datetime,
                        entitiy_type=interactions.EntityType.EXTERNAL,
                        channel_id=None,
                    )
                    if event:
                        time.sleep(2)
                        print(event)
                        insert = f"INSERT INTO event VALUES('{ev.uid}', '{category}', '{ev.description}', '{ev.begin}', '{ev.end}', '{ev.name}', '{event.get('id')}')"
                        print(insert)
                        req = cur.execute(
                            insert
                        )
                        con.commit ()


# Erstelle ein Event für Abgaben auf moodle


async def createEvent(
    name: str,
    description: str,
    location: str,
    scheduled_start_time: datetime,
    scheduled_end_time: datetime,
    entitiy_type: interactions.EntityType,
    channel_id: interactions.Snowflake,
):

    if scheduled_end_time.timestamp() >= time.time():

        # Korregiere Zeit
        if scheduled_start_time.timestamp() == scheduled_end_time.timestamp():
            scheduled_end_time = scheduled_end_time.replace(
                second=scheduled_end_time.second + 1
            )
        if scheduled_start_time.timestamp() == scheduled_end_time.timestamp():
            print("Fehler")
        apayload = {
            "name": name,
            "description": description,
            "privacy_level": 2,
            "scheduled_start_time": scheduled_start_time.isoformat(),
            "entity_type": entitiy_type.value,
        }

        if entitiy_type == interactions.EntityType.VOICE:
            if channel_id:
                apayload.update("channel_id", channel_id)
        elif entitiy_type == interactions.EntityType.EXTERNAL:
            if location:
                apayload.update({"entity_metadata": {"location": location}})
            if scheduled_end_time:
                apayload.update({"scheduled_end_time": scheduled_end_time.isoformat()})

        print("Payload:", apayload)
        aevent = await bot._http.create_scheduled_event(
            guild_id=GUILD_ID, payload=apayload
        )
        return aevent
    else:
        print(colored("Das Event hat bereits stattgefunden!", "red"))
        return None


# Alle Kurse die keinen Kurs zugewiesen sind werden zugewiesen


async def generateCourseAssosiation():
    res = cur.execute(
        "SELECT course_fullname, course_id FROM files WHERE course_id NOT IN (SELECT DISTINCT course_id FROM course_channel_assignment) GROUP BY course_id"
    )
    for v in res.fetchall():
        courses.append(v[0])
        course_ids.append(v[1])


# Alle Channels bekommen die einem Kurs zugewiesen sind
async def fetchChannels():
    res = cur.execute("SELECT * from course_channel_assignment")
    if res:
        for v in res.fetchall():
            channel = await interactions.get(
                client=bot, obj=interactions.Channel, object_id=v[1]
            )

            if channel:
                channel_dict.update({v[0]: channel})


async def createDatabase():

    db1 = cur.execute(
        "CREATE TABLE IF NOT EXISTS course_channel_assignment(course_id INT, text_channel INT, PRIMARY KEY(course_id, text_channel), FOREIGN KEY(course_id) REFERENCES files(course_id))"
    )
    db2 = cur.execute(
        "CREATE TABLE IF NOT EXISTS thread_channel(thread_id INT, section_id INT, text_channel INT, PRIMARY KEY(thread_id, section_id), FOREIGN KEY(section_id) REFERENCES files(section_id), FOREIGN KEY(text_channel) REFERENCES course_channel_assignment(text_channel))"
    )
    db3 = cur.execute(
        "CREATE TABLE IF NOT EXISTS event(uid VARCHAR(100) PRIMARY KEY, category VARCHAR(100), description TEXT, start DATETIME, end DATETIME, title VARCHAR(255), location VARCHAR(255), event_id INT)"
    )


def _restart():
    sys.stdout.flush()
    os.execl(sys.executable, "python", __file__, *sys.argv[1:])


@bot.event
async def on_ready():
    print(colored(f"{bot.me.name} hat sich mit Discord verbunden!", "green"))
    # bot.change_presence(interactions.ClientPresence(status=interactions.StatusType.IDLE, activities=[interactions.PresenceActivity(name="Organisieren", type=interactions.PresenceActivityType.CUSTOM)]))

    await createDatabase()
    # Schauen, ob eine Verbindung mit der Datenbank aufgebaut werden konnte
    if con:
        await fetchChannels()
        await generateCourseAssosiation()
        await getCalendarInformations()
        # await createEvent(name="Test", description="", location="test", scheduled_start_time=time.time()+3600, scheduled_end_time=time.time()+2*3600, entitiy_type=interactions.EntityType.EXTERNAL, channel_id=None)
        if not TEST:
            try:
                await run_task.start(round(time.time()) + 3600)
            except RuntimeWarning as warning:
                print(colored(f"An error occured: {warning}", "red"))

            if RESTART_TIMER in ["true", "True"]:
                print(colored("Restart-Timer läuft", "green"))

    else:
        print(
            colored("Es konnte keine Verbindung zur Datenbank aufgebaut werden!", "red")
        )
        exit()


@bot.command(
    name="assign",
    description="Assigns a moodle course with a textchannel",
    scope=GUILD_ID,
    options=[
        interactions.Option(
            name="text_channel",
            description="choose textchannel",
            type=interactions.OptionType.CHANNEL,
            required=True,
        ),
    ],
    default_member_permissions=interactions.Permissions.ADMINISTRATOR,
)
async def assign(ctx: interactions.CommandContext, text_channel: interactions.Channel):
    options = []
    options = await generateOptions(text_ids=text_channel.id)
    if options:

        if text_channel.type == interactions.ChannelType.GUILD_TEXT:
            await ctx.send(
                f"Select a course that you like to assign to textchannel <#{text_channel.id}>",
                components=ActionRow.new(
                    SelectMenu(
                        custom_id="assign_selector",
                        options=options,
                    )
                ),
            )
        else:
            await ctx.send("You have to select a textchannel!")
    else:
        await ctx.send("No courses found :frowning:")


@bot.command(
    name="restart",
    description="Restart bot",
    options=[],
    scope=GUILD_ID,
    default_member_permissions=interactions.Permissions.ADMINISTRATOR,
)
async def restart(ctx):
    await ctx.send("Bot wird neugestartet...")

    _restart()


# Optionen für die Auswahl der Kurswahl


async def generateOptions(text_ids: interactions.Snowflake):
    options = []
    p = 0
    for item in courses:
        options.append(
            SelectOption(
                label=f"{item}", value=f"{course_ids[p]};{text_ids};{random.random()}"
            )
        )
        p = p + 1
    return options


@bot.component("assign_selector")
async def modal_response(ctx: interactions.ComponentContext, response):
    if response:
        id = str(response[0]).split(";")[0]
        text = str(response[0]).split(";")[1]
        r = cur.execute(
            f"SELECT COUNT(*) FROM course_channel_assignment WHERE course_id={id}"
        )

        if r.fetchone()[0] == 0:
            res = cur.execute(
                f"INSERT INTO course_channel_assignment VALUES({id}, {text})"
            )
            con.commit()
            r2 = cur.execute(
                f"SELECT COUNT(*) FROM course_channel_assignment WHERE course_id={id}"
            )

            await fetchChannels()
            await generateCourseAssosiation()

            await ctx.send(f"Successfully connected!")
        else:
            await ctx.send(f"You have already connected the course with <#{text}>!")


def generateFilter(filter: List[str]):
    s = ""
    for a in filter:
        s = (
            s
            + f"(content_filename NOT LIKE '%.{a}' AND saved_to NOT LIKE '%.{a}') AND "
        )
    return s


# Upload a file to Google Drive


async def uploadFile(path):
    SCOPES = [
        "https://www.googleapis.com/auth/docs",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/drive.metadata.readonly",
        "/auth/docs",
    ]

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run^
        try:
            with open("token.json", "w") as token:
                token.write(creds.to_json())
        except FileNotFoundError:
            print("Token not found!")
            exit()

    uploadFileList = [path]
    try:
        # create drive api client
        service = build("drive", "v3", credentials=creds)
        for uploadFile in uploadFileList:
            sp = uploadFile.split("\\")
            file_metadata = {"name": sp[-1]}
            media = MediaFileUpload(uploadFile)
            file = (
                service.files()
                .create(body=file_metadata, media_body=media, fields="id")
                .execute()
            )
            # print(F'File ID: {file}')
            file_id = file.get("id")
            ids = []

            def callback(request_id, response, exception):
                if exception:
                    # Handle error
                    print(colored(exception, "red"))
                else:
                    # print(f'Request_Id: {request_id}')
                    # print(F'File Link: https://drive.google.com/uc?export=download&id={file_id}')
                    ids.append(response.get("id"))

            # pylint: disable=maybe-no-member
            batch = service.new_batch_http_request(callback=callback)
            user_permission = {"type": "anyone", "role": "reader"}
            batch.add(
                service.permissions().create(
                    fileId=file_id,
                    body=user_permission,
                )
            )

            batch.execute()

    except HttpError as error:
        print(colored(f"An error occurred: {error}", "red"))
        file = None
        return None

    return f"https://drive.google.com/uc?export=download&id={file_id}"


@tasks.loop(minutes=5)
async def run_task(timer):
    await bot.wait_until_ready()
    guild: interactions.Guild = interactions.get(
        client=bot, obj=interactions.Guild, object_id=1030146188214812783
    )
    if not exists("moodle/"):
        os.mkdir("moodle/")
        print(
            colored(
                "Ordner moodle/ wurde erstellt. Bitte führe die Konfiguration von dem Moodle-Downloader aus",
                "green",
            )
        )
        exit()

    ptime = round(time.time())
    print(colored("Der Moodle-Downloader wird ausgeführt...\n", "yellow"))

    os.system("moodle-dl -p moodle/")

    print(
        "Wähle alle neuen Dateien aus:\n"
        + colored(
            f"SELECT COUNT(*) FROM files WHERE time_stamp > {ptime}",
            "yellow",
            attrs=["bold"],
        )
        + "\n"
    )

    res = cur.execute(f"Select COUNT(*) FROM files WHERE time_stamp >= {ptime}")

    if res:
        rfo = res.fetchone()
        if rfo:
            # Checken ob mehr als 1 neue Datei dabei ist
            if rfo[0] >= 1:
                print("Mehr als 1 neue Datei!")

                ch_con = con.execute(f"SELECT * FROM course_channel_assignment")
                if ch_con:
                    print("Selecting from courses")

                    for ccon in ch_con.fetchall():
                        print(ccon[0])
                        query = (
                            f"SELECT saved_to, content_filesize, course_id, section_name, section_id FROM files WHERE time_stamp >= {ptime} AND "
                            + generateFilter(["php", "html", "css", "md"])
                            + f"course_id={ccon[0]} ORDER BY section_id"
                        )

                        # print(query)
                        res2 = cur.execute(query)

                        files = {}
                        links = []
                        # TODO: Channel auswählen von Thread
                        channel: interactions.Channel = channel_dict.get(ccon[0])
                        if channel:
                            if channel.type in [
                                interactions.ChannelType.GUILD_TEXT,
                                interactions.ChannelType.PUBLIC_THREAD,
                            ]:
                                for re in res2.fetchall():
                                    if re[1] >= 8389000000:
                                        print("File to large")
                                    elif re[1] > 0:
                                        ar = files.get(re[3])
                                        if ar == None:
                                            ar = []

                                        file = interactions.File(re[0])
                                        if (
                                            os.path.getsize(re[0]) / (1024 * 1024)
                                        ) <= 8:
                                            ar.append(file)
                                            files.update({re[3]: ar})
                                        else:
                                            if USE_GD in ["true", "True"]:
                                                url = await uploadFile(re[0])
                                                if url:
                                                    links.append(url)
                                                else:
                                                    print(
                                                        colored(
                                                            "Fehler beim hochladen der Datei zu Google Drive!!!",
                                                            "red",
                                                        )
                                                    )
                                            else:
                                                print(
                                                    colored(
                                                        "Datei wurde nicht hochgeladen da Google Drive deaktiviert wurde!",
                                                        "yellow",
                                                    )
                                                )

                        for key in files:
                            # Test if thread exists
                            req = cur.execute(
                                f"SELECT thread_channel.thread_id FROM thread_channel, files WHERE files.section_name='{key}' and files.course_id='{ccon[0]}' and files.section_id=thread_channel.section_id"
                            )
                            thread_res = req.fetchone()
                            if thread_res:
                                channel = await interactions.get(
                                    client=bot,
                                    obj=interactions.Thread,
                                    object_id=thread_res[0],
                                )
                            if files.get(key):
                                if (
                                    channel.type
                                    != interactions.ChannelType.PUBLIC_THREAD
                                ):

                                    # TODO: Einen Thread erstellen ohne die Dateien in den Textchannel zu senden
                                    try:
                                        msg_txt = f"**Dateien für den Bereich '{key}'** (von {MOODLE_URL}/course/view.php?id={ccon[0]})"
                                        if links:
                                            for link in links:
                                                links.remove(link)
                                                msg_txt = msg_txt + f"\n {link}"

                                        msg: interactions.Message = await channel.send(
                                            msg_txt, files=files.get(key)
                                        )
                                        time.sleep(1)
                                        thread: interactions.Channel = await channel.create_thread(
                                            name=key,
                                            type=interactions.ChannelType.PUBLIC_THREAD,
                                            invitable=True,
                                            message_id=msg.id,
                                            reason=f"Store files of {key}",
                                        )
                                        r = cur.execute(
                                            f"INSERT INTO thread_channel(thread_id, section_id, text_channel) SELECT DISTINCT '{thread.id}', section_id, '{channel.id}' FROM files WHERE section_name='{key}' and course_id='{ccon[0]}'"
                                        )
                                        con.commit()
                                    except:
                                        print("Failed to upload files")
                                else:

                                    try:
                                        thread: interactions.Channel = channel
                                        msg_txt = ""
                                        if links:
                                            for link in links:
                                                links.remove(link)
                                                msg_txt = msg_txt + f"\n {link}"

                                        await thread.send(msg_txt, files=files.get(key))

                                    except:
                                        print("Failed to upload files")

    if round(time.time()) >= timer:
        if RESTART_TIMER in ["True", "true"]:
            print("Neustarten...")
            _restart()


bot.start()
