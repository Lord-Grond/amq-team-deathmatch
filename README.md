# Chungus AMQ Team Deathmatch

A small Flask app that replaces the PowerPoint game board.

## Run it

```powershell
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

## How it works

- The main page is the playing board.
- Each category has an introduction slide followed by ten slides: five music slides alternating with five answer slides.
- Returning from the last answer marks the category red.
- The board has two score counters with plus and minus controls.
- Edit mode changes the game title, team names, category names, introduction text/image, uploaded or linked audio, sample timing, and answer text.
- Music can use a chosen 20-second starting point or a new random 20-second sample each time.
- Each category keeps a separate two-team score with +1 and +0.5 controls.
- Game data is saved in `data/game.json`.

For local audio, place files under `static/audio/` and enter paths such as `/static/audio/my-song.mp3` in edit mode.
