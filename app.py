from __future__ import annotations

import json
import re
from pathlib import Path
from uuid import uuid4

from flask import Flask, abort, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "game.json"
LOADOUT_DIR = BASE_DIR / "data" / "loadouts"
ACTIVE_LOADOUT_FILE = BASE_DIR / "data" / "active_loadout.txt"
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
ALLOWED_AUDIO = {"mp3", "wav", "ogg", "m4a", "aac", "flac"}
ALLOWED_IMAGES = {"png", "jpg", "jpeg", "gif", "webp"}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024


def normalize_game(game: dict) -> dict:
    game.setdefault("title", "AMQ Team Deathmatch")
    game.setdefault("teams", [])
    while len(game["teams"]) < 2:
        team_number = len(game["teams"]) + 1
        game["teams"].append({"name": f"Team {team_number}", "score": 0})
    for team_number, team in enumerate(game["teams"][:2], start=1):
        team.setdefault("name", f"Team {team_number}")
        team.setdefault("score", 0)

    game.setdefault("categories", [])
    while len(game["categories"]) < 12:
        game["categories"].append({"id": len(game["categories"]) + 1})

    for category_number, category in enumerate(game["categories"], start=1):
        category.setdefault("id", category_number)
        category.setdefault("name", f"Category {category_number}")
        category.setdefault("picked", False)
        category.setdefault("explanation", "")
        category.setdefault("image_url", "")
        category.setdefault("scores", [0, 0])
        category.setdefault("songs", [])
        while len(category["songs"]) < 5:
            category["songs"].append({})
        for song in category["songs"]:
            song.setdefault("audio_url", "")
            song.setdefault("anime", "")
            song.setdefault("song", "")
            song.setdefault("artist", "")
            song.setdefault("sample_mode", "fixed")
            song.setdefault("sample_start", 0)
            song.setdefault("sample_end", song["sample_start"] + 20)

    final_showdown = game.setdefault("final_showdown", {})
    final_showdown.setdefault("theme", "")
    final_showdown.setdefault("songs", [])
    while len(final_showdown["songs"]) < 5:
        final_showdown["songs"].append({})
    for song in final_showdown["songs"]:
        song.setdefault("audio_url", "")
        song.setdefault("anime", "")
        song.setdefault("song", "")
        song.setdefault("artist", "")
        song.setdefault("sample_mode", "fixed")
        song.setdefault("sample_start", 0)
        song.setdefault("sample_end", song["sample_start"] + 20)
    return game


def write_json(path: Path, game: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as file:
        json.dump(game, file, indent=2, ensure_ascii=False)
    temporary.replace(path)


def ensure_loadout_storage() -> None:
    LOADOUT_DIR.mkdir(parents=True, exist_ok=True)
    loadout_files = sorted(LOADOUT_DIR.glob("*.json"))
    if not loadout_files:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            legacy_game = normalize_game(json.load(file))
        first_path = LOADOUT_DIR / "original-game.json"
        write_json(first_path, legacy_game)
        loadout_files = [first_path]
    active_key = ACTIVE_LOADOUT_FILE.read_text(encoding="utf-8").strip() if ACTIVE_LOADOUT_FILE.exists() else ""
    if not active_key or not (LOADOUT_DIR / f"{active_key}.json").is_file():
        ACTIVE_LOADOUT_FILE.write_text(loadout_files[0].stem, encoding="utf-8")


def active_loadout_key() -> str:
    ensure_loadout_storage()
    return ACTIVE_LOADOUT_FILE.read_text(encoding="utf-8").strip()


def loadout_path(key: str) -> Path:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", key):
        abort(404)
    path = LOADOUT_DIR / f"{key}.json"
    if not path.is_file():
        abort(404)
    return path


def load_game() -> dict:
    with loadout_path(active_loadout_key()).open("r", encoding="utf-8") as file:
        return normalize_game(json.load(file))


def save_game(game: dict) -> None:
    write_json(loadout_path(active_loadout_key()), game)


def list_loadouts() -> list[dict]:
    ensure_loadout_storage()
    active = active_loadout_key()
    loadouts = []
    for path in sorted(LOADOUT_DIR.glob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as file:
                game = normalize_game(json.load(file))
            loadouts.append({"key": path.stem, "title": game.get("title", path.stem), "active": path.stem == active})
        except (json.JSONDecodeError, OSError):
            continue
    return loadouts


def reset_play_state(game: dict) -> None:
    for category in game["categories"]:
        category["picked"] = False
        category["scores"] = [0, 0]
    for team in game["teams"]:
        team["score"] = 0


def unique_loadout_key(title: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60] or "new-loadout"
    candidate = base
    number = 2
    while (LOADOUT_DIR / f"{candidate}.json").exists():
        candidate = f"{base}-{number}"
        number += 1
    return candidate


@app.context_processor
def loadout_context():
    return {"active_loadout_key": active_loadout_key()}


@app.get("/loadouts")
def loadouts():
    return render_template("loadouts.html", game=load_game(), loadouts=list_loadouts(), mode="loadouts")


@app.post("/loadouts/create")
def create_loadout():
    title = request.form.get("title", "").strip() or "New Game"
    game = json.loads(json.dumps(load_game()))
    game["title"] = title
    reset_play_state(game)
    key = unique_loadout_key(title)
    write_json(LOADOUT_DIR / f"{key}.json", game)
    ACTIVE_LOADOUT_FILE.write_text(key, encoding="utf-8")
    return redirect(url_for("edit_board"))


@app.post("/loadouts/<key>/activate")
def activate_loadout(key: str):
    loadout_path(key)
    ACTIVE_LOADOUT_FILE.write_text(key, encoding="utf-8")
    return redirect(url_for("board"))


@app.post("/loadouts/<key>/duplicate")
def duplicate_loadout(key: str):
    with loadout_path(key).open("r", encoding="utf-8") as file:
        game = normalize_game(json.load(file))
    game["title"] = f"{game['title']} Copy"
    reset_play_state(game)
    new_key = unique_loadout_key(game["title"])
    write_json(LOADOUT_DIR / f"{new_key}.json", game)
    ACTIVE_LOADOUT_FILE.write_text(new_key, encoding="utf-8")
    return redirect(url_for("edit_board"))


@app.post("/loadouts/<key>/delete")
def delete_loadout(key: str):
    path = loadout_path(key)
    remaining = [item for item in LOADOUT_DIR.glob("*.json") if item != path]
    if not remaining:
        abort(400, description="At least one loadout must remain")
    was_active = key == active_loadout_key()
    path.unlink()
    if was_active:
        ACTIVE_LOADOUT_FILE.write_text(sorted(remaining)[0].stem, encoding="utf-8")
    return redirect(url_for("loadouts"))


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


@app.get("/final-showdown")
def final_showdown():
    return render_template("final_showdown.html", game=load_game(), mode="play")


@app.post("/final-showdown/score/<int:team_index>/<action>")
def change_final_showdown_score(team_index: int, action: str):
    changes = {"decrease": -1, "increase": 1}
    if team_index not in (0, 1) or action not in changes:
        abort(400)
    game = load_game()
    game["teams"][team_index]["score"] = max(0, game["teams"][team_index]["score"] + changes[action])
    save_game(game)
    return redirect(url_for("final_showdown"))


@app.post("/score/<int:team_index>/<action>")
def change_score(team_index: int, action: str):
    changes = {"decrease": -1, "increase": 1}
    if team_index not in (0, 1) or action not in changes:
        abort(400)
    game = load_game()
    game["teams"][team_index]["score"] = max(0, game["teams"][team_index]["score"] + changes[action])
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
    reset_play_state(game)
    save_game(game)
    return redirect(url_for("board"))


@app.get("/edit")
def edit_board():
    return render_template("edit.html", game=load_game(), mode="edit")


@app.route("/edit/final-showdown", methods=["GET", "POST"])
def edit_final_showdown():
    game = load_game()
    showdown = game["final_showdown"]
    if request.method == "POST":
        showdown["theme"] = request.form.get("theme", "").strip()
        for index, song in enumerate(showdown["songs"]):
            audio_upload = save_upload(request.files.get(f"audio_upload_{index}"), "audio", ALLOWED_AUDIO)
            song["audio_url"] = audio_upload or request.form.get(f"audio_url_{index}", "").strip()
            for field in ("anime", "song", "artist"):
                song[field] = request.form.get(f"{field}_{index}", "").strip()
            song["sample_mode"] = "random" if request.form.get(f"random_sample_{index}") else "fixed"
            try:
                song["sample_start"] = max(0, float(request.form.get(f"sample_start_{index}", 0)))
            except ValueError:
                song["sample_start"] = 0
            try:
                song["sample_end"] = max(0, float(request.form.get(f"sample_end_{index}", song["sample_start"] + 20)))
            except ValueError:
                song["sample_end"] = song["sample_start"] + 20
            if song["sample_end"] <= song["sample_start"]:
                song["sample_end"] = song["sample_start"] + 20
        save_game(game)
        return redirect(url_for("edit_final_showdown"))
    return render_template("final_showdown_edit.html", game=game, mode="edit")


@app.post("/edit/categories/swap")
def swap_categories():
    try:
        first_id = int(request.form.get("first_category", ""))
        second_id = int(request.form.get("second_category", ""))
    except ValueError:
        abort(400)
    if first_id == second_id:
        return redirect(url_for("edit_board"))
    game = load_game()
    first = get_category(game, first_id)
    second = get_category(game, second_id)
    editable_fields = ("name", "explanation", "image_url", "songs")
    first_content = {field: first[field] for field in editable_fields}
    second_content = {field: second[field] for field in editable_fields}
    for field in editable_fields:
        first[field] = second_content[field]
        second[field] = first_content[field]
    save_game(game)
    return redirect(url_for("edit_board"))


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
            try:
                song["sample_end"] = max(0, float(request.form.get(f"sample_end_{index}", song["sample_start"] + 20)))
            except ValueError:
                song["sample_end"] = song["sample_start"] + 20
            if song["sample_end"] <= song["sample_start"]:
                song["sample_end"] = song["sample_start"] + 20
        save_game(game)
        return redirect(url_for("edit_category", category_id=category_id))
    return render_template("category_edit.html", game=game, category=category, mode="edit")


if __name__ == "__main__":
    app.run(debug=False)
