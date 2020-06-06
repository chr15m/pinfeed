from flask import Flask, request, jsonify
from time import time
from os import environ, makedirs
from os.path import getmtime, join, isfile, isdir
from urllib.parse import urlencode
from json import dumps, loads
import re

from ntpl import render, slurp, replace, attr
from feedparser import parse

CACHE_SECONDS = int(environ.get("CACHE_SECONDS", 300))

re_img = re.compile('<img.*?src="(.*?)"', re.IGNORECASE | re.MULTILINE)

app = Flask(__name__)

t = slurp("index.html")

@app.route('/')
def index():
    content = [
        ["h1", "PinFeed"],
        ["h3", "Full-screen Pinterest image feed."],
        ["div", {"class": "formset"},
         ["input", {"id": "user", "placeholder": "user"}],
         ["input", {"id": "board", "placeholder": "board"}],
         ["button", {"onclick": "go()"}, "go"]],
        ["a", {"href": "chrismgamedraw"}, "e.g. chrismgamedraw"],
        ["p", "I use Pinterest for referencing art during drawing practice. " +
            "I found it hard to access the full resolution images through the Pinterest interface, " +
            "so I made this app to browse and view collections at full resolution."],]
    t1 = t
    #t1 = attr(t, "section#main", "id", "readme")
    return replace(t1, "section", render(content))

@app.route('/<path:board>')
def view(board):
    if "." in board:
        return http404()
    slashes = board.count("/")
    if slashes > 1:
        return http404()
    elif slashes == 0:
        board = board + "/feed"
    feed = getboard(board)
    if not feed:
        return http404()
    meta = feed.get("feed")
    result = [
        ["a", {"href": "/", "id": "home"}, "pinfeed"],
        ["h3", ["a", {"href": meta.get("link")}, board.split("/")[0] + " / " + meta.get("title")]],
        #["h4", meta.get("updated")],
    ]
    for e in feed.get("entries"):
        entry = str(e.get("summary"))
        img = re_img.search(str(entry))
        if img:
            src = img.groups()[0]
            big = src.replace("/236x/", "/1200x/")
            src = src.replace("/236x/", "/564x/")
            result.append(["div", {"class": "entry"},
                ["a", {"href": big},
                    ["img", {"src": src}]],
                ["h4",
                    ["a", {"href": e.get("link")}, e.get("published")]]])
    # result = ["pre", dumps(feed, indent=2)]
    t1 = replace(t, "section#main", render(result))
    return replace(t1, "title", "PinFeed: " + meta.get("title"))

def getboard(board):
    filename = join("cached", board.replace("/", ".") + ".json")
    if isfile(filename) and getmtime(filename) > time() - CACHE_SECONDS:
        with open(filename) as f:
            return loads(f.read())
    else:
        feed = parse("https://www.pinterest.com/" + board + ".rss")
        if feed.get("bozo_exception"):
            return None
        if not isdir("cached"):
            makedirs("cached")
        with open(filename, "w") as f:
            f.write(dumps(feed))
        return feed

def http404(message="404 Not found: Invalid board."):
    return replace(t, "section#main", render(["p", message])), 404
