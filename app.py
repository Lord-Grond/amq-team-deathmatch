from __future__ import annotations

import json
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, url_for


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "game.json"

app = Flask(__name__)


def load_game() -> dict:
    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


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
    if slide_number < 1 or slide_number > 10:
        abort(404)
    game = load_game()
    category = get_category(game, category_id)
    song_index = (slide_number - 1) // 2
    slide_type = "music" if slide_number % 2 else "answer"
    return render_template(
        "slide.html",
        game=game,
        category=category,
        song=category["songs"][song_index],
        song_number=song_index + 1,
        slide_number=slide_number,
        slide_type=slide_type,
        mode="play",
    )


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
        for index, song in enumerate(category["songs"]):
            for field in ("audio_url", "anime", "song", "artist"):
                song[field] = request.form.get(f"{field}_{index}", "").strip()
        save_game(game)
        return redirect(url_for("edit_category", category_id=category_id))
    return render_template("category_edit.html", game=game, category=category, mode="edit")


if __name__ == "__main__":
    app.run(debug=False)
