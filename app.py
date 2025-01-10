from flask import Flask, render_template, request
from playwright.sync_api import Playwright, sync_playwright
from bs4 import BeautifulSoup
import sqlite3
import os
import re
import time

app = Flask(__name__)

# Create or connect to the database
def create_database(db_name="lyrics.db"):
    if not os.path.exists(db_name):
        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE Artists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                )
            """)
            cursor.execute("""
                CREATE TABLE Songs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    artist_id INTEGER NOT NULL,
                    lyrics TEXT NOT NULL,
                    FOREIGN KEY (artist_id) REFERENCES Artists (id)
                )
            """)
            conn.commit()
            print(f"Database '{db_name}' created successfully.")
        except sqlite3.Error as e:
            print(f"Error creating database: {e}")
        finally:
            conn.close()
    else:
        print(f"Database '{db_name}' already exists.")

# Insert lyrics into the database


#START PASTING
#PLEASE PASTE HERE YVAN 
#ABEG
#END OF PASTING

# Search for lyrics online
def search_lyrics(playwright: Playwright, artist_name: str, song_title: str):
    base_url = "https://genius.com"
    browser = playwright.chromium.launch(channel="msedge", headless=False)
    context = browser.new_context()
    page = context.new_page()

    try:
        search_query = f"{artist_name} {song_title}".replace(' ', '+')
        search_url = f"{base_url}/search?q={search_query}"
        page.goto(search_url, timeout=0)

        page.wait_for_selector('.column_layout-column_span.column_layout-column_span--primary', timeout=60000)
        top_result = page.query_selector('.column_layout-column_span.column_layout-column_span--primary > div:first-child a')

        if top_result:
            top_result.click()
            time.sleep(2)
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')
            lyrics_containers = soup.select('.Lyrics-sc-1bcc94c6-1.bzTABU')

            lyrics_list = [container.get_text(separator="\n").strip() for container in lyrics_containers if container]
            lyrics = "\n\n".join(lyrics_list)

            if lyrics:
                insert_lyrics("lyrics.db", artist_name, song_title, lyrics)
                return lyrics
        else:
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    finally:
        context.close()
        browser.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    lyrics = None
    message = None
    if request.method == 'POST':
        artist = request.form['artist']
        song = request.form['song']
        lyrics = fetch_lyrics("lyrics.db", artist, song)

        if not lyrics:
            with sync_playwright() as playwright:
                lyrics = search_lyrics(playwright, artist_name=artist, song_title=song)
            if lyrics:
                message = f"Lyrics for '{artist} - {song}' have been fetched and saved!"
            else:
                message = f"Lyrics for '{artist} - {song}' could not be found."

    return render_template('index.html', lyrics=lyrics, message=message)

if __name__ == "__main__":
    create_database()
    app.run(debug=True)
