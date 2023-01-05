# EVERY FRAME IN ORDER BOT FOR TWITTER
# By Pigeonburger, 2022
# https://github.com/pigeonburger
import os
import sqlite3 as db
import time

import tweepy

# Put your Twitter API keys and stuff here
CONSUMER_KEY = os.environ["CONSUMER_KEY"]
CONSUMER_SECRET = os.environ["CONSUMER_SECRET"]
ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
ACCESS_TOKEN_SECRET = os.environ["ACCESS_TOKEN_SECRET"]

auth = tweepy.OAuth1UserHandler(
    CONSUMER_KEY,
    CONSUMER_SECRET,
    ACCESS_TOKEN,
    ACCESS_TOKEN_SECRET
)
api = tweepy.API(auth)

# Connect to the SQLite database that was created in setupbot.py
connection = db.connect(os.environ.get("EVERY_FRAME_SQLITE", f".{os.sep}data{os.sep}framebot.db"))
cursor = connection.cursor()

# Find directory
frame_directory = os.environ.get("EVERY_FRAME_DIRECTORY", f".{os.sep}data{os.sep}frames")

# Enter the name of the show you're posting frames for here:
show_name = os.environ.get("SHOW_NAME", "Breaking Bad")

# Put the number of frames the bot should post each time this script is run here.
iters = int(os.environ.get("RUNS_PER_CYCLE", 1))

# The number of seconds to wait between each tweet cluster
wait_time = float(os.environ.get("WAIT_TIME", 120))

try:
    while True:
        for _ in range(iters):
            # Get the current season & episode the bot is currently on.
            current_ep = cursor.execute("SELECT current_episode FROM bot").fetchone()[0]

            # Get season and episode number
            ep_season, ep_num = current_ep.split('x')

            # Get the total frames from that episode.
            total_frames = cursor.execute(f"SELECT frames FROM show WHERE ep = \"{current_ep}\"").fetchone()[0]

            # Get the number of the last frame that was uploaded, then add one to that number to get the number of the next frame to post.
            next_frame = cursor.execute("SELECT last_frame FROM bot").fetchone()[0] + 1

            # If the next_frame number is bigger than the number of total frames in the episode, then the current_episode db value needs to be updated.
            if next_frame > total_frames:
                next_ep = str(int(ep_num) + 1).zfill(2)

                # If another episode in the same season is found, update the database to reflect that.
                if os.path.isfile(os.path.join(frame_directory, f"S{ep_season}/{next_ep}x1.jpg")):
                    cursor.execute(f'UPDATE bot SET current_episode = "{ep_season}x{next_ep}"')
                    cursor.execute(f'UPDATE bot SET last_frame = 0')
                    connection.commit()
                    continue  # var iters does not change, loop again

                # Otherwise, we need to go to a new season.

                else:
                    next_season = str(int(ep_season) + 1).zfill(2)

                    cursor.execute(f'UPDATE bot SET current_episode = "{next_season}x01"')
                    cursor.execute(f'UPDATE bot SET last_frame = 0')
                    connection.commit()
                    continue  # var iters does not change, loop again

                # Need to add a check here to see if the entire series is finished or not....

            # Get the file path for the next frame to upload.
            frame_path = os.path.join(frame_directory, f"S{ep_season}/{ep_num}x{next_frame}.jpg")

            # The message to attach to the tweet
            msg = f"{show_name} - Season {ep_season} Episode {ep_num} - Frame {next_frame} of {total_frames}"

            print(f"Uploading {frame_path} to Twitter...")
            print(msg)

            # Send the Tweet
            api.update_status_with_media(msg, frame_path)

            # Update the database to reflect the most recently uploaded frame.
            cursor.execute(f"UPDATE bot SET last_frame = {next_frame}")
            connection.commit()

            # Wait the specified amount of time before continuing.
        time.sleep(wait_time)
except KeyboardInterrupt:
    print("Exiting...")
    connection.close()
    exit()
