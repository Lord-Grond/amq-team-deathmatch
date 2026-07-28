from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from flask import Flask, abort, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "game.json"
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
ALLOWED_AUDIO = {"mp3", "wav", "ogg", "m4a", "aac", "flac"}
ALLOWED_IMAGES = {"png", "jpg", "jpeg", "gif", "webp"}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024


def load_game() -> dict:
    with DATA_FILE.open("r", encoding="utf-8") as file:
        game = json.load(file)
    for category in game["categories"]:
        category.setdefault("explanation", "Add a short explanation for this category in edit mode.")
        category.setdefault("image_url", "")
        category.setdefault("scores", [0, 0])
        for song in category["songs"]:
            song.setdefault("sample_mode", "fixed")
            song.setdefault("sample_start", 0)
    return game


def save_game(game: dict) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = DATA_FILE.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as file:
        json.dump(game, file, indent=2, ensure_ascii=False)
    temporary.replace(DATA_FILE)


def get_category(game: dict, category_id: int) -> dict:
    category = next((item for item in game["categories"] if item["id"] == category_id), None)
    if category is None:
        abort(404)
    return category


def save_upload(file, folder: str, allowed_extensions: set[str]) -> str | None:
    if not file or not file.filename:
        return None
    filename = secure_filename(file.filename)
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in allowed_extensions:
        abort(400, description=f"Unsupported .{extension} file")
    destination = UPLOAD_DIR / folder
    destination.mkdir(parents=True, exist_ok=True)
    saved_name = f"{uuid4().hex}-{filename}"
    file.save(destination / saved_name)
    return url_for("static", filename=f"uploads/{folder}/{saved_name}")


@app.get("/")
def board():
    return render_template("board.html", game=load_game(), mode="play")


@app.post("/score/<int:team_index>/<int:change>")
def change_score(team_index: int, change: int):
    if team_index not in (0, 1) or change not in (-1, 1):
        abort(400)
    game = load_game()
    game["teams"][team_index]["score"] = max(0, game["teams"][team_index]["score"] + change)
    save_game(game)
    return redirect(url_for("board"))


@app.get("/category/<int:category_id>/<int:slide_number>")
def category_slide(category_id: int, slide_number: int):
    if slide_number < 1 or slide_number > 11:
        abort(404)
    game = load_game()
    category = get_category(game, category_id)
    if slide_number == 1:
        song_index = None
        slide_type = "intro"
        song = None
    else:
        song_index = (slide_number - 2) // 2
        slide_type = "music" if slide_number % 2 == 0 else "answer"
        song = category["songs"][song_index]
    return render_template(
        "slide.html",
        game=game,
        category=category,
        song=song,
        song_number=song_index + 1 if song_index is not None else None,
        slide_number=slide_number,
        slide_type=slide_type,
        mode="play",
    )


@app.post("/category/<int:category_id>/score/<int:team_index>/<change>")
def change_category_score(category_id: int, team_index: int, change: str):
    changes = {"1": 1, "0.5": 0.5}
    if team_index not in (0, 1) or change not in changes:
        abort(400)
    game = load_game()
    category = get_category(game, category_id)
    category["scores"][team_index] += changes[change]
    save_game(game)
    slide_number = request.form.get("slide_number", "1")
    return redirect(url_for("category_slide", category_id=category_id, slide_number=slide_number))


@app.post("/category/<int:category_id>/complete")
def complete_category(category_id: int):
    game = load_game()
    category = get_category(game, category_id)
    category["picked"] = True
    save_game(game)
    return redirect(url_for("board"))


@app.post("/reset-board")
def reset_board():
    game = load_game()
    for category in game["categories"]:
        category["picked"] = False
        category["scores"] = [0, 0]
    for team in game["teams"]:
        team["score"] = 0
    save_game(game)
    return redirect(url_for("board"))


@app.get("/edit")
def edit_board():
    return render_template("edit.html", game=load_game(), mode="edit")


@app.post("/edit/board")
def update_board():
    game = load_game()
    game["title"] = request.form.get("title", "").strip() or game["title"]
    for index, team in enumerate(game["teams"]):
        team["name"] = request.form.get(f"team_{index}", "").strip() or team["name"]
    for category in game["categories"]:
        name = request.form.get(f"category_{category['id']}", "").strip()
        if name:
            category["name"] = name
    save_game(game)
    return redirect(url_for("edit_board"))


@app.route("/edit/category/<int:category_id>", methods=["GET", "POST"])
def edit_category(category_id: int):
    game = load_game()
    category = get_category(game, category_id)
    if request.method == "POST":
        category["name"] = request.form.get("name", "").strip() or category["name"]
        category["explanation"] = request.form.get("explanation", "").strip()
        image_upload = save_upload(request.files.get("image_upload"), "images", ALLOWED_IMAGES)
        category["image_url"] = image_upload or request.form.get("image_url", "").strip()
        for index, song in enumerate(category["songs"]):
            audio_upload = save_upload(request.files.get(f"audio_upload_{index}"), "audio", ALLOWED_AUDIO)
            song["audio_url"] = audio_upload or request.form.get(f"audio_url_{index}", "").strip()
            for field in ("anime", "song", "artist"):
                song[field] = request.form.get(f"{field}_{index}", "").strip()
            song["sample_mode"] = "random" if request.form.get(f"random_sample_{index}") else "fixed"
            try:
                song["sample_start"] = max(0, float(request.form.get(f"sample_start_{index}", 0)))
            except ValueError:
                song["sample_start"] = 0
        save_game(game)
        return redirect(url_for("edit_category", category_id=category_id))
    return render_template("category_edit.html", game=game, category=category, mode="edit")


if __name__ == "__main__":
    app.run(debug=False)
