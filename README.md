# Orga Bot

A Discord Bot that send files from moodle in a Discord Channel using [python Moodle downloader](https://github.com/C0D3D3V/Moodle-Downloader-2)

## How to use?

0. Führe `pip install -r requirements.txt` aus (für raspberrypi: `sudo apt-get install g++ python3-lxml -y`)
1. Erstelle den Ordner moodle/ und führe die Konfiguration vom Moodle Downloader aus (man kann auch mit `moodle-dl --init -p moodle/` den Befehl außerhalb des Ordners ausführen)
2. Führe den Moodle Downloader einmalig mit `moodle-dl -p moodle/` aus
3. Erstelle die Datei `.env` und füge folgende Werte ein:
    * `GUILD_ID = [ID vom GUILD]`
    * `DISCORD_TOKEN="[DISCORD BOT TOKEN]"`
    * `MOODLE_URL="[URL VOM MOODLE]"`
    * `USE_GOOGLE_DRIVE=[True/False]`
    * `RESTART_TIMER=[True/False]`
4. Erstelle dir eine Google Cloud Projekt in der Google Cloud Console und aktiviere die API Google Drive (**OPTIONAL**, Kann geändert werden durch ändern des Wertes `USE_GOOGLE_DRIVE` in der Datei `.env`)
    * Gehe auf die Webseite und klicke auf "Projekt erstellen" image.png
    * Gebe die Email-Adresse des Google-Accounts, auf welchem die Dateien die größer als 8 MB sind hochgeladen werden sollen, als Apptester an
    * Erstelle nun eine OAuth2 Schlüssel und wähle die Bereiche  `auth/docs`, `auth/drive`, `auth/drive.metadata.readonly`, `auth/docs` aus
    * Lade die Zugriffsdaten als json Datei herunter und ändere den Namen der Datei zu token.json und füge sie in den Root-Ordner des Programms ein
    * Führe das python Progamm quickstart.py mit python quickstart.py aus
    * Es öffnet sich ein Browserfenster. Melde dich nun mit dem Google Account an, dessen Email du zuvor als Apptester eingetragen hast. Als nächstes musst du alle Felder auswählen und auf akzeptieren klicken.

5. Starte den Bot mit python main.py
6. Weise den Moodle-Kursen einen Channel zu indem du in Discord den Befehl /assign #textchannel eingibst. Daraufhin Kannst du über ein Dropdown-Menu auswählen welchen Kurs du den Channel zuweisen möchtest.
7. Stoppe den Discord Bot und lösche alle Ordner und Dateien im Ordner moodle/ außer moodle_state.db und config.json
8. Öffne eine Verbindung mit der Datenbank moodle_state.db und lösche alle Einträge in der Tabelle files mit dem SQL-Befehl: `DELETE FROM files`
9. Starte den Bot neu. Nun sollten alle Dateien aus den Kursen heruntergeladen werden und in die zugewiesenen Channels geschickt. Nun werden Threads zu den einzelnen Themen im Kurs erstellt.

Nun kannst du den Discordbot benutzen um deine Moodle-Dateien an einem Ort zu speichern und mit anderen Leuten zu teilen

## Befehle

### Aktuell existierende Befehle

* /assign #textchannel - Weise ein Textchannel einem Kurs zu

### Zukünftig geplante Befehle

* /pm kurs_name - Erhalte eine Persöhnliche Nachricht falls es neue Dateien für einen Kurs gibt
  * /pm all - Erhalte eine Persöhnliche Nachricht falls es neue Dateien, egal für welchen Kurs, gibt
  * /pm revoke kurs_name - Widerrufe den Erhalt einer Persönlichen Nachricht für einen Kurs

## Bekannte Fehler

* Unter Linux-Betriebssystemen kann das pip-Paket `aiohttp` nicht gebaut werden
* Bei dem wiederholenden Task kommt beim ersten Durchgang die Fehlermeldung `await self.coro(*args, **kwargs)
RuntimeWarning: Enable tracemalloc to get the object allocation traceback`
* Falls mitten in dem Moodle Download das Programm beendet ist muss die Datei `moodle/running.lock` gelöscht werden
