import random

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

SENTENCES = [
    "The quick brown fox jumps over the lazy dog while the cat watches from the fence.",
    "Typing fast is a skill that improves with practice and a little bit of patience.",
    "A journey of a thousand miles begins with a single step taken with confidence.",
    "Good code is its own best documentation as it explains itself to the reader.",
    "The sun set behind the mountains and painted the sky in shades of orange and pink.",
    "Simplicity is the ultimate sophistication when it comes to design and engineering.",
    "She sells seashells by the seashore and the shells she sells are surely seashells.",
    "Every great developer you know got there by solving problems they were unqualified to solve.",
]


def rate(wpm) -> float:
    if wpm < 50:
        return "slow"
    if wpm < 100:
        return "progressing"
    if wpm < 200:
        return "good"
    if wpm < 350:
        return "goated"
    if wpm > 900:
    	return "even robots can't do that"

def check(string):
    # Oops chat I might have accidently made it unsolvable. Only one way to find out? Let's see if you are 1337 enough
    string = string.lower()
    disallowed = [".","_","import", "=", ",", "'", '"', "attr", "global", "local", ";", ":", "^", "/", ">", "<", "{", "}", "m", "a", "not", "and", "or", "eval", "exec", "for", "in", "chr", "ord", "hex", "int", "repr", "str", "dir", "set", "len", "SENTENCES", "random", "request", "app", "flask"]
    c = any([x in string for x in disallowed]) 
    non_ascii = any([ord(x) < 32 for x in string]) or any([ord(x) > 126 for x in string])
    return c or non_ascii or len(set(string)) > 18

@app.route("/")
def index():
    return render_template("index.html", sentence=random.choice(SENTENCES))

	
@app.route("/rate")
def rate_wpm():
    try:
        wpm = request.args.get("wpm", "")
    except ValueError:
        return jsonify(error="invalid wpm"), 400
    if check(wpm):
        return "Invalid WPM!"
    return jsonify(verdict=rate(eval(wpm.lower())), wpm=float(wpm))


if __name__ == "__main__":
    app.run('0.0.0.0',debug=True)
