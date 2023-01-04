# EVERY FRAME IN ORDER BOT FOR TWITTER
# By Pigeonburger, 2022
# https://github.com/pigeonburger

import os, re, glob, sqlite3 as db

# This is the frame-splitting part (this will probably take a while depending on how fast your computer is)

# Get all the mp4 files in the current folder (change file extension if needed)
eps = glob.glob(f"episodes{os.sep}*.{os.environ.get('FILE_EXTENSION', 'mp4')}")

# Number of frames per second you want the show to be split into
fps = int(os.environ.get("FPS", 1))
captions = os.environ.get("CAPTIONS", "True") == "True"

x_res = int(os.environ.get("X_RES", 1920))
y_res = int(os.environ.get("Y_RES", 1080))

if not os.path.exists("frames"):
    os.mkdir("frames")

# Supports common file season-episode formats e.g. S01E01, 01x01, Season 1 Episode 1 etc.
regx = re.compile(r"(?:.*)(?:s|season|)\s?(\d{1,2})\s?(?:e|x|episode|ep|\n)\s?(\d{1,2})", re.IGNORECASE)

for ep in eps:
    ep_regx = regx.match(ep)

    if ep_regx:
        # Parse to get the video's season and episode numbers
        season, episode = ep_regx.groups()

        # All videos will be stored in a folder called 'frames', inside another folder denoting the season number
        out_path = f'.{os.sep}frames{os.sep}S{season.zfill(2)}'
        if not os.path.isdir(out_path):
            os.mkdir(out_path)

        filters = [
            f"fps={fps}",
            f"scale=(iw*sar)*min({x_res}/(iw*sar)\,{y_res}/ih):ih*min({x_res}/(iw*sar)\,{y_res}/ih)"  # works with 4:3 and 16:9
        ]

        if os.path.splitext(ep)[1] == ".mkv" and captions:
            if os.path.sep == "\\":
                safe_ep = ep.replace("\\", "\\\\")
            else:
                safe_ep = ep
            filters.insert(1, f"subtitles='{safe_ep}'")

        vf_arg = ",".join(filters)

        # The outputted frame files will look like 00x00.jpg, where the number on the left side of the x is the episode number, and the number on the right side is the frame number.
        # Also scale down to 360p to save server space (and Twitter compresses the hell out of uploaded media anyway so no point having HD)
        os.system(f'ffmpeg -i "{ep}" -vf "{vf_arg}" {out_path}{os.sep}{episode}x%d.jpg')


# This half of the script will create the required (SQLite) database entries.

connection = db.connect("framebot.db")
cursor = connection.cursor()

cursor.execute("CREATE TABLE show (ep, frames)")
cursor.execute("CREATE TABLE bot (current_episode, last_frame)")
cursor.execute("INSERT INTO bot(current_episode, last_frame) VALUES (\"01x01\", 0)")
connection.commit()

total_seasons = int(season)

# Store the number of frames per episode in a database so that it can be retrieved faster (rather than counting this every time the bot is run)
for n in range(total_seasons):
    current_season = str(n+1).zfill(2)
    
    total_eps = len(glob.glob(f"./frames/S{current_season}/*x1.jpg"))

    for i in range(total_eps):
        current_ep = str(i + 1).zfill(2)
        frames = glob.glob(f"./frames/S{current_season}/{current_ep}x*.jpg")
        cursor.execute(f"INSERT INTO show (ep, frames) VALUES (\"{current_season}x{current_ep}\", {len(frames)})")
        
connection.commit()

# Congratulations! You're now almost ready to put the bot online!
