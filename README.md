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
- Each category has its own route with ten slides: five music slides alternating with five answer slides.
- Returning from the last answer marks the category red.
- The board has two score counters with plus and minus controls.
- Edit mode changes the game title, team names, category names, audio paths, and answer text.
- Game data is saved in `data/game.json`.

For local audio, place files under `static/audio/` and enter paths such as `/static/audio/my-song.mp3` in edit mode.
