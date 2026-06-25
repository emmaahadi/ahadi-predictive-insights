from flask import Flask, request, render_template_string, Response, redirect, url_for, session
from collections import Counter
from itertools import combinations
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

import random
import requests
import csv
import io
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "ahadi_v11_secret_key"

APP_NAME = "Ahadi Predictive Insights v11"

DB_FILE = "ahadi_v11_users.db"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

POWERBALL_API = "https://data.ny.gov/resource/d6yy-54nr.json?$limit=250&$order=draw_date DESC"

JACKPOT = "$327 Million"
CASH_VALUE = "$148 Million"
NEXT_DRAW = "Wed, Jun 24, 2026"
NEXT_DRAW_JS = "2026-06-24T22:59:00"
LAUNCH_DATE = datetime(2026, 6, 25)
FREE_DAYS = 10

LAST_PICKS = []

GAMES = {
    "Powerball": {
        "main_count": 5,
        "main_min": 1,
        "main_max": 69,
        "bonus_name": "Powerball",
        "bonus_min": 1,
        "bonus_max": 26
    },

    "Pick 4": {
        "main_count": 4,
        "main_min": 0,
        "main_max": 9,
        "bonus_name": None,
        "bonus_min": None,
        "bonus_max": None
    },

    "Cash4Life": {
        "main_count": 5,
        "main_min": 1,
        "main_max": 60,
        "bonus_name": "Cash Ball",
        "bonus_min": 1,
        "bonus_max": 4
    }
}

PRIZE_TABLE = [
    ["5 + Powerball", "Grand Prize"],
    ["5", "$1,000,000"],
    ["4 + Powerball", "$50,000"],
    ["4", "$100"],
    ["3 + Powerball", "$100"],
    ["3", "$7"],
    ["2 + Powerball", "$7"],
    ["1 + Powerball", "$4"],
    ["Powerball Only", "$4"]
]
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>{{ app_name }}</title>

<style>
body{
    font-family:Arial;
    color:white;
    padding:25px;

    background:
    linear-gradient(
        rgba(7,20,36,0.85),
        rgba(7,20,36,0.85)
    ),
    url('/static/uploads/background.jpg');

    background-size:cover;
    background-position:center;
    background-attachment:fixed;
}

h1{
    color:gold;
    font-size:42px;
}

.box{
    background:#10233d;
    padding:20px;
    border-radius:15px;
    margin-bottom:20px;
}

.grid{
    display:grid;
    grid-template-columns:repeat(3,1fr);
    gap:15px;
}

.card{
    background:#06101f;
    padding:20px;
    border-radius:15px;
    text-align:center;
}

button,input,select,textarea{
    width:100%;
    padding:12px;
    margin-top:10px;
    border-radius:8px;
    border:none;
    font-size:16px;
}

button{
    background:gold;
    font-weight:bold;
    cursor:pointer;
}

textarea{
    height:150px;
}

a.btn{
    display:block;
    background:#00c853;
    color:black;
    text-align:center;
    padding:12px;
    border-radius:8px;
    text-decoration:none;
    font-weight:bold;
    margin-top:10px;
}

a.link{
    color:gold;
    text-decoration:none;
    font-weight:bold;
}

.num{
    display:inline-block;
    background:gold;
    color:black;
    padding:13px 17px;
    margin:5px;
    border-radius:50%;
    font-weight:bold;
}

.pb{
    background:red;
    color:white;
}

.ai{
    background:#00c853;
    color:black;
}

.draw{
    background:#06101f;
    padding:15px;
    border-radius:10px;
    margin:10px 0;
}

.score{
    color:#00ff88;
    font-weight:bold;
}

.jackpot{
    font-size:32px;
    color:gold;
    font-weight:bold;
}

.cash{
    font-size:24px;
    color:#00ff88;
    font-weight:bold;
}

.top{
    border:2px solid gold;
}

.info{
    display:inline-block;
    margin:10px 20px 5px 0;
}

.nav{
    display:flex;
    gap:12px;
    flex-wrap:wrap;
    margin-bottom:20px;
}

.nav a{
    background:#06101f;
    color:white;
    padding:10px 14px;
    border-radius:8px;
    text-decoration:none;
}

.profile-pic{
    width:70px;
    height:70px;
    border-radius:50%;
    object-fit:cover;
    border:3px solid gold;
    vertical-align:middle;
    margin-right:12px;
}

.heat{
    display:inline-block;
    padding:10px 14px;
    margin:5px;
    border-radius:8px;
    background:#06101f;
    border:1px solid #00c853;
    color:#00ff88;
    font-weight:bold;
}

table{
    width:100%;
    background:white;
    color:black;
    border-collapse:collapse;
}

td,th{
    padding:10px;
    border:1px solid #ccc;
    text-align:center;
}

.note{
    color:#ccc;
    font-size:14px;
}

@media(max-width:900px){
    .grid{
        grid-template-columns:1fr;
    }

    h1{
        font-size:32px;
    }
}
</style>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>

<body>

<h1>🔮 {{ app_name }}</h1>

{% if user and user_photo %}
<div style="position:absolute; top:20px; right:20px; text-align:center;">
    <img src="/{{ user_photo }}"
         style="width:80px;height:80px;border-radius:50%;border:3px solid gold;">
    <br>
    <b>{{ user }}</b>
</div>
{% endif %}
<p>Powerball • Pick 4 • Cash4Life • Profile Photo • Elite AI • Heat Map</p>

<div class="nav">
<a href="/">Dashboard</a>

{% if user %}
<a href="/saved">My Saved Picks</a>
<a href="/profile">Profile</a>
<a href="/logout">Logout {{ user }}</a>
{% else %}
<a href="/login">Login</a>
<a href="/register">Register</a>
{% endif %}
</div>

<div class="box">
<form method="POST">

<label>Select Game</label>
<select name="game">
{% for g in games %}
<option value="{{ g }}" {% if selected_game == g %}selected{% endif %}>{{ g }}</option>
{% endfor %}
</select>

<label>How many smart picks?</label>
<input type="number" name="pick_count" value="{{ pick_count }}" min="1" max="50">

<label>Optional: Paste History</label>
<p class="note">
Powerball loads real recent winning numbers automatically.
For Pick 4 and Cash4Life, paste history one draw per line.
</p>

<textarea name="manual_history" placeholder="Example Powerball: 17 19 21 45 48 13&#10;Example Pick 4: 4 7 2 9&#10;Example Cash4Life: 7 14 22 38 55 3">{{ manual_history }}</textarea>

<button type="submit">Run v11 Analysis</button>
</form>

{% if result %}
<a class="btn" href="/export">Export Smart Picks to CSV</a>
{% endif %}
</div>

{% if error %}
<div class="box">
<h2>Error</h2>
<p>{{ error }}</p>
</div>
{% endif %}
{% if result %}

<div class="box top">
<h2>🏆 Top AI Pick - {{ selected_game }}</h2>

{% for n in result.top_pick.main %}
<span class="num ai">{{ n }}</span>
{% endfor %}

{% if result.top_pick.bonus is not none %}
<span class="num pb">{{ result.top_pick.bonus }}</span>
{% endif %}

<p class="score">
Elite AI Rating: {{ result.top_pick.grade }} | Strength {{ result.top_pick.elite_score }}
</p>

<p>Confidence Score: {{ result.top_pick.score }}%</p>
<p>{{ result.top_pick.reason }}</p>

{% if user %}
<form method="POST" action="/save_pick">
<input type="hidden" name="game" value="{{ selected_game }}">
<input type="hidden" name="numbers" value="{{ result.top_pick.main|join(' ') }}">
<input type="hidden" name="bonus" value="{{ result.top_pick.bonus }}">
<input type="hidden" name="score" value="{{ result.top_pick.score }}">
<input type="hidden" name="reason" value="{{ result.top_pick.reason }}">
<button type="submit">Save Top Pick to My Account</button>
</form>
{% else %}
<p><a class="link" href="/login">Login</a> to save picks.</p>
{% endif %}
</div>

<div class="grid">
<div class="card"><h2>Latest Draw</h2><p>{{ result.latest.date }}</p></div>
<div class="card"><h2>Total Draws</h2><p>{{ result.total_draws }}</p></div>
<div class="card"><h2>Engine</h2><p>v11 Elite AI</p></div>
</div>

{% if selected_game == "Powerball" %}
<div class="grid">
<div class="card"><h2>Jackpot</h2><p class="jackpot">{{ jackpot }}</p></div>
<div class="card"><h2>Cash Value</h2><p class="cash">{{ cash_value }}</p></div>
<div class="card"><h2>Countdown</h2><p id="countdown" class="cash">Loading...</p></div>
</div>
{% endif %}

<div class="box">
<h2>🏆 Latest Winning Numbers</h2>
<div class="draw">
<p><b>{{ result.latest.date }}</b></p>

{% for n in result.latest.main %}
<span class="num">{{ n }}</span>
{% endfor %}

{% if result.latest.bonus is not none %}
<span class="num pb">{{ result.latest.bonus }}</span>
{% endif %}

{% if selected_game == "Powerball" %}
<br><br>
<span class="info">⚡ Power Play: <b>{{ result.latest.multiplier }}</b></span>
<span class="info">💰 Jackpot: <b class="jackpot">{{ jackpot }}</b></span>
<span class="info">💵 Cash Value: <b class="cash">{{ cash_value }}</b></span>
<span class="info">📅 Next Draw: <b>{{ next_draw }}</b></span>
{% endif %}
</div>
</div>

<div class="box"><h2>🔥 Hot Numbers</h2>{% for n in result.hot %}<span class="num">{{ n }}</span>{% endfor %}</div>

<div class="box"><h2>❄️ Cold Numbers</h2>{% for n in result.cold %}<span class="num">{{ n }}</span>{% endfor %}</div>

<div class="box"><h2>⏳ Overdue Numbers</h2>{% for n in result.overdue %}<span class="num">{{ n }}</span>{% endfor %}</div>

<div class="box">
<h2>📊 v11 Charts + Heat Map Dashboard</h2>
<div class="grid">
<div class="card"><canvas id="hotChart"></canvas></div>
<div class="card"><canvas id="coldChart"></canvas></div>
<div class="card"><canvas id="rankingChart"></canvas></div>
</div>
</div>

<div class="box">
<h2>🔥 Number Heat Map</h2>
{% for item in result.heat_map %}
<span class="heat">#{{ loop.index }} &nbsp; {{ item.number }} | Heat {{ item.heat }}</span>
{% endfor %}
</div>
<div class="box">
<h2>🎯 Smart Picks</h2>

{% for p in result.picks %}
<div class="draw">

{% for n in p.main %}
<span class="num ai">{{ n }}</span>
{% endfor %}

{% if p.bonus is not none %}
<span class="num pb">{{ p.bonus }}</span>
{% endif %}

<p class="score">
{{ p.grade }} | AI Strength {{ p.elite_score }} | Confidence {{ p.score }}%
</p>

<p>{{ p.reason }}</p>
</div>
{% endfor %}
</div>

<div class="box">
<h2>📊 Number Ranking</h2>
{% for item in result.main_ranking %}
<div class="draw">#{{ loop.index }} Number {{ item.number }} — Score {{ item.score }}</div>
{% endfor %}
</div>

{% if result.bonus_ranking %}
<div class="box">
<h2>🔴 Bonus Ball Ranking</h2>
{% for item in result.bonus_ranking %}
<div class="draw">#{{ loop.index }} {{ result.bonus_name }} {{ item.number }} — Score {{ item.score }}</div>
{% endfor %}
</div>
{% endif %}

<div class="box">
<h2>🤝 Best Pairs</h2>
{% for pair in result.best_pairs %}
<div class="draw">{{ pair }}</div>
{% endfor %}
</div>

<div class="box">
<h2>🔺 Best Triples</h2>
{% for triple in result.best_triples %}
<div class="draw">{{ triple }}</div>
{% endfor %}
</div>

<div class="box">
<h2>⚖️ Pattern Analysis</h2>
<div class="draw">Best Odd/Even Pattern: {{ result.best_odd_even }}</div>
<div class="draw">Best Low/High Pattern: {{ result.best_low_high }}</div>
<div class="draw">Average Sum Range: {{ result.avg_sum }}</div>
</div>
{% if selected_game == "Powerball" %}
<div class="box">
<h2>💰 Prize Table</h2>
<table>
<tr><th>Match</th><th>Prize</th></tr>
{% for row in prize_table %}
<tr>
<td>{{ row[0] }}</td>
<td>{{ row[1] }}</td>
</tr>
{% endfor %}
</table>
</div>
{% endif %}

<div class="box">
<h2>📅 Previous Winning Numbers</h2>
{% for d in result.draws[:20] %}
<div class="draw">
<p><b>{{ d.date }}</b></p>

{% for n in d.main %}
<span class="num">{{ n }}</span>
{% endfor %}

{% if d.bonus is not none %}
<span class="num pb">{{ d.bonus }}</span>
{% endif %}
</div>
{% endfor %}
</div>

<div class="box">
<h2>Important Note</h2>
<p>Lottery is random. This app analyzes historical patterns but cannot guarantee winning numbers.</p>
</div>

{% endif %}

<script>
const nextDraw = new Date("{{ next_draw_js }}").getTime();

setInterval(function(){
    const el = document.getElementById("countdown");
    if(!el){return;}

    const now = new Date().getTime();
    const distance = nextDraw - now;

    if(distance <= 0){
        el.innerHTML = "Draw time";
        return;
    }

    const days = Math.floor(distance / (1000 * 60 * 60 * 24));
    const hours = Math.floor((distance / (1000 * 60 * 60)) % 24);
    const minutes = Math.floor((distance / (1000 * 60)) % 60);
    const seconds = Math.floor((distance / 1000) % 60);

    el.innerHTML = days + "d " + hours + "h " + minutes + "m " + seconds + "s";
}, 1000);
</script>

{% if result %}
<script>
const hotLabels = {{ result.hot|tojson }};
const coldLabels = {{ result.cold|tojson }};
const rankLabels = {{ result.chart_labels|tojson }};
const rankScores = {{ result.chart_scores|tojson }};

new Chart(document.getElementById('hotChart'), {
    type: 'bar',
    data: {
        labels: hotLabels,
        datasets: [{
            label: 'Hot Numbers',
            data: {{ result.hot_counts|tojson }}
        }]
    }
});

new Chart(document.getElementById('coldChart'), {
    type: 'bar',
    data: {
        labels: coldLabels,
        datasets: [{
            label: 'Cold Numbers',
            data: {{ result.cold_counts|tojson }}
        }]
    }
});

new Chart(document.getElementById('rankingChart'), {
    type: 'line',
    data: {
        labels: rankLabels,
        datasets: [{
            label: 'Top Number Scores',
            data: rankScores
        }]
    }
});
</script>
{% endif %}

</body>
</html>
"""
AUTH_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>{{ title }}</title>
<style>
body{
    font-family:Arial;
    background:#071424;
    color:white;
    padding:25px;
}
.box{
    background:#10233d;
    padding:25px;
    border-radius:15px;
    max-width:500px;
    margin:auto;
}
input,button{
    width:100%;
    padding:12px;
    margin-top:10px;
    border-radius:8px;
    border:none;
    font-size:16px;
}
button{
    background:gold;
    font-weight:bold;
    cursor:pointer;
}
a{color:gold}
</style>
</head>
<body>

<div class="box">
<h1>{{ title }}</h1>

{% if error %}
<p style="color:#ff6666">{{ error }}</p>
{% endif %}

<form method="POST">
<input name="username" placeholder="Username" required>
<input name="password" type="password" placeholder="Password" required>
<button type="submit">{{ button }}</button>
</form>

<p>{{ switch_text }} <a href="{{ switch_link }}">{{ switch_label }}</a></p>
<p><a href="/">Back to dashboard</a></p>
</div>

</body>
</html>
"""
SAVED_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Saved Picks</title>
<style>
body{
    font-family:Arial;
    background:#071424;
    color:white;
    padding:25px;
}
.box{
    background:#10233d;
    padding:20px;
    border-radius:15px;
    margin-bottom:15px;
}
.num{
    display:inline-block;
    background:#00c853;
    color:black;
    padding:12px 16px;
    margin:5px;
    border-radius:50%;
    font-weight:bold;
}
.pb{
    background:red;
    color:white;
}
a{color:gold}
</style>
</head>
<body>

<h1>💾 My Saved Picks</h1>
<p><a href="/">Back to dashboard</a> | <a href="/logout">Logout</a></p>

{% for p in picks %}
<div class="box">
<h2>{{ p.game }} — Score {{ p.score }}%</h2>

{% for n in p.numbers.split() %}
<span class="num">{{ n }}</span>
{% endfor %}

{% if p.bonus and p.bonus != "None" %}
<span class="num pb">{{ p.bonus }}</span>
{% endif %}

<p>{{ p.reason }}</p>
<p>Saved: {{ p.created_at }}</p>
</div>
{% endfor %}

{% if not picks %}
<p>No saved picks yet.</p>
{% endif %}

</body>
</html>
"""
PROFILE_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Profile</title>

<style>
body{
    font-family:Arial;
    background:#071424;
    color:white;
    padding:25px;
}

.box{
    background:#10233d;
    padding:20px;
    border-radius:15px;
    margin-bottom:15px;
}

.card{
    background:#06101f;
    padding:20px;
    border-radius:15px;
    text-align:center;
}

.grid{
    display:grid;
    grid-template-columns:repeat(3,1fr);
    gap:15px;
}

.profile-pic{
    width:120px;
    height:120px;
    border-radius:50%;
    object-fit:cover;
    border:4px solid gold;
}

input,button{
    width:100%;
    padding:12px;
    margin-top:10px;
    border-radius:8px;
    border:none;
    font-size:16px;
}

button{
    background:gold;
    font-weight:bold;
    cursor:pointer;
}

a{
    color:gold;
}

@media(max-width:900px){
    .grid{
        grid-template-columns:1fr;
    }
}
</style>
</head>

<body>

<h1>👤 Profile</h1>

<p>
<a href="/">Back to Dashboard</a> |
<a href="/saved">My Saved Picks</a> |
<a href="/logout">Logout</a>
</p>

<div class="box">

{% if photo %}
<img src="/{{ photo }}" class="profile-pic">
{% endif %}

<h2>{{ username }}</h2>

<p>
Welcome to Ahadi Predictive Insights v11.
</p>

<form method="POST"
      action="/upload_photo"
      enctype="multipart/form-data">

<input type="file"
       name="photo"
       accept="image/*">

<button type="submit">
Upload Profile Photo
</button>

</form>

</div>

<div class="grid">

<div class="card">
<h2>Total Saved Picks</h2>
<p>{{ total }}</p>
</div>

<div class="card">
<h2>Favorite Game</h2>
<p>{{ favorite_game }}</p>
</div>

<div class="card">
<h2>Best Saved Score</h2>
<p>{{ best_score }}%</p>
</div>

</div>

</body>
</html>
"""
def db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        photo TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS saved_picks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        game TEXT NOT NULL,
        numbers TEXT NOT NULL,
        bonus TEXT,
        score INTEGER,
        reason TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    try:
        conn.execute("ALTER TABLE users ADD COLUMN photo TEXT")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

def current_user():
    return session.get("username")

def current_user_id():
    return session.get("user_id")



def current_user_photo():

    if not current_user_id():
        return None

    conn = db()

    row = conn.execute(
        "SELECT photo FROM users WHERE id = ?",
        (current_user_id(),)
    ).fetchone()

    conn.close()

    if row:
        return row["photo"]

    return None

def nice_date(date_text):
    try:
        return datetime.fromisoformat(
            date_text.replace("Z", "")
        ).strftime("%a, %b %d, %Y")
    except:
        return date_text

def get_powerball_draws():
    data = requests.get(
        POWERBALL_API,
        timeout=10
    ).json()

    draws = []

    for row in data:
        nums = [
            int(x)
            for x in row.get("winning_numbers", "").replace(",", " ").split()
            if x.isdigit()
        ]

        if len(nums) >= 6:
            draws.append({
                "date": nice_date(row.get("draw_date", "")),
                "main": nums[:5],
                "bonus": nums[5],
                "multiplier": row.get("multiplier", "")
            })

    return draws
def parse_manual_history(text, game_name):
    rules = GAMES[game_name]
    needed = rules["main_count"] + (1 if rules["bonus_name"] else 0)
    draws = []

    for i, line in enumerate(text.strip().splitlines(), start=1):
        nums = [
            int(x)
            for x in line.replace(",", " ").split()
            if x.isdigit()
        ]

        if len(nums) >= needed:
            main = nums[:rules["main_count"]]
            bonus = nums[rules["main_count"]] if rules["bonus_name"] else None

            draws.append({
                "date": f"Manual Draw {i}",
                "main": main,
                "bonus": bonus,
                "multiplier": ""
            })

    return draws

def sample_draws_for_game(game_name):
    rules = GAMES[game_name]
    draws = []

    for i in range(80):
        main = sorted(
            random.sample(
                range(rules["main_min"], rules["main_max"] + 1),
                rules["main_count"]
            )
        )

        bonus = None

        if rules["bonus_name"]:
            bonus = random.randint(
                rules["bonus_min"],
                rules["bonus_max"]
            )

        draws.append({
            "date": f"Sample Draw {i + 1}",
            "main": main,
            "bonus": bonus,
            "multiplier": ""
        })

    return draws
def analyze(draws, game_name, pick_count):
    rules = GAMES[game_name]

    main_numbers = []
    bonus_numbers = []
    sums = []

    pair_counter = Counter()
    triple_counter = Counter()
    odd_even_counter = Counter()
    low_high_counter = Counter()

    for d in draws:
        main = sorted(d["main"])

        main_numbers.extend(main)
        sums.append(sum(main))

        if d["bonus"] is not None:
            bonus_numbers.append(d["bonus"])

        for pair in combinations(main, 2):
            pair_counter[pair] += 1

        if rules["main_count"] >= 3:
            for triple in combinations(main, 3):
                triple_counter[triple] += 1

        odd = sum(1 for n in main if n % 2 == 1)
        even = rules["main_count"] - odd
        odd_even_counter[f"{odd} odd / {even} even"] += 1

        middle = (rules["main_min"] + rules["main_max"]) // 2
        low = sum(1 for n in main if n <= middle)
        high = rules["main_count"] - low
        low_high_counter[f"{low} low / {high} high"] += 1

    main_counter = Counter(main_numbers)
    bonus_counter = Counter(bonus_numbers)

    all_main = list(range(rules["main_min"], rules["main_max"] + 1))

    hot = [n for n, c in main_counter.most_common(15)]
    cold = sorted(all_main, key=lambda n: main_counter[n])[:15]

    overdue_data = []

    for n in all_main:
        gap = 999

        for i, d in enumerate(draws):
            if n in d["main"]:
                gap = i
                break

        overdue_data.append((n, gap))

    overdue = [
        n for n, g in sorted(
            overdue_data,
            key=lambda x: x[1],
            reverse=True
        )[:15]
    ]

    overdue_map = dict(overdue_data)

    main_ranking = []

    for n in all_main:
        score = (
            main_counter[n] * 3
            + min(overdue_map.get(n, 0), 25)
            + (20 if n in hot else 0)
        )

        main_ranking.append({
            "number": n,
            "score": score
        })

    main_ranking = sorted(
        main_ranking,
        key=lambda x: x["score"],
        reverse=True
    )
    bonus_ranking = []

    if rules["bonus_name"]:
        for n in range(rules["bonus_min"], rules["bonus_max"] + 1):
            bonus_ranking.append({
                "number": n,
                "score": bonus_counter[n] * 4
            })

        bonus_ranking = sorted(
            bonus_ranking,
            key=lambda x: x["score"],
            reverse=True
        )

    best_pairs = [
        f"{p[0]} - {p[1]} appeared {c} times"
        for p, c in pair_counter.most_common(10)
    ]

    best_triples = [
        f"{t[0]} - {t[1]} - {t[2]} appeared {c} times"
        for t, c in triple_counter.most_common(10)
    ]

    if not best_triples:
        best_triples = ["Not enough numbers for triple analysis."]

    best_odd_even = odd_even_counter.most_common(1)[0][0]
    best_low_high = low_high_counter.most_common(1)[0][0]

    avg_center = int(sum(sums) / len(sums))
    avg_sum = f"{avg_center - 10} to {avg_center + 10}"

    top_numbers = [
        item["number"]
        for item in main_ranking[:min(30, len(main_ranking))]
    ]

    if len(top_numbers) < rules["main_count"]:
        top_numbers = all_main

    top_bonus = []

    if bonus_ranking:
        top_bonus = [
            item["number"]
            for item in bonus_ranking[:15]
        ]

    picks = []
    for _ in range(pick_count * 8):

        main_pick = sorted(
            random.sample(
                top_numbers,
                rules["main_count"]
            )
        )

        bonus_pick = None

        if rules["bonus_name"]:
            if top_bonus:
                bonus_pick = random.choice(top_bonus)
            else:
                bonus_pick = random.randint(
                    rules["bonus_min"],
                    rules["bonus_max"]
                )

        hot_count = len(
            set(main_pick) & set(hot)
        )

        overdue_count = len(
            set(main_pick) & set(overdue)
        )

        pair_score = sum(
            pair_counter[pair]
            for pair in combinations(main_pick, 2)
        )

        triple_score = 0

        if rules["main_count"] >= 3:
            triple_score = sum(
                triple_counter[triple]
                for triple in combinations(main_pick, 3)
            )

        odd = sum(
            1 for n in main_pick
            if n % 2 == 1
        )

        even = rules["main_count"] - odd

        odd_even_pattern = (
            f"{odd} odd / {even} even"
        )

        middle = (
            rules["main_min"]
            + rules["main_max"]
        ) // 2

        low = sum(
            1 for n in main_pick
            if n <= middle
        )

        high = rules["main_count"] - low

        low_high_pattern = (
            f"{low} low / {high} high"
        )

        total_sum = sum(main_pick)

        balance_score = 0

        if odd_even_pattern == best_odd_even:
            balance_score += 5

        if low_high_pattern == best_low_high:
            balance_score += 5

        if avg_center - 20 <= total_sum <= avg_center + 20:
            balance_score += 5

        score = min(
            99,
            60
            + hot_count * 5
            + overdue_count * 4
            + min(pair_score, 12)
            + min(triple_score, 8)
            + balance_score
        )

        reason = (
            f"{hot_count} hot numbers, "
            f"{overdue_count} overdue numbers, "
            f"pair score {pair_score}, "
            f"triple score {triple_score}, "
            f"pattern {odd_even_pattern}, "
            f"{low_high_pattern}."
        )

        picks.append({
            "main": main_pick,
            "bonus": bonus_pick,
            "score": score,
            "reason": reason
        })
    unique_picks = []
    seen = set()

    for p in sorted(picks, key=lambda x: x["score"], reverse=True):
        key = tuple(
            p["main"] +
            ([p["bonus"]] if p["bonus"] is not None else [])
        )

        if key not in seen:
            unique_picks.append(p)
            seen.add(key)

        if len(unique_picks) >= pick_count:
            break

    for p in unique_picks:
        elite_score = round(
            (p["score"] * 0.75)
            + (len(set(p["main"]) & set(hot)) * 3)
            + (len(set(p["main"]) & set(overdue)) * 2),
            1
        )

        p["elite_score"] = min(99.9, elite_score)

        if p["elite_score"] >= 95:
            p["grade"] = "A+ Elite Pick"
        elif p["elite_score"] >= 90:
            p["grade"] = "A Strong Pick"
        elif p["elite_score"] >= 85:
            p["grade"] = "B+ Good Pick"
        else:
            p["grade"] = "B Smart Pick"
    heat_map = []

    for item in main_ranking[:25]:
        n = item["number"]

        heat = (
            main_counter[n] * 3
            + (15 if n in hot else 0)
            + (10 if n in overdue else 0)
        )

        heat_map.append({
            "number": n,
            "heat": heat
        })

    return {
        "latest": draws[0],
        "draws": draws,
        "total_draws": len(draws),
        "hot": hot,
        "cold": cold,
        "overdue": overdue,

        "hot_counts": [main_counter[n] for n in hot],
        "cold_counts": [main_counter[n] for n in cold],
        "chart_labels": [item["number"] for item in main_ranking[:10]],
        "chart_scores": [item["score"] for item in main_ranking[:10]],

        "heat_map": heat_map,

        "main_ranking": main_ranking[:20],
        "bonus_ranking": bonus_ranking[:15],
        "bonus_name": rules["bonus_name"],

        "best_pairs": best_pairs,
        "best_triples": best_triples,
        "best_odd_even": best_odd_even,
        "best_low_high": best_low_high,
        "avg_sum": avg_sum,

        "picks": unique_picks,
        "top_pick": unique_picks[0]
    }
@app.route("/", methods=["GET", "POST"])
def home():
    global LAST_PICKS

    result = None
    error = None
    pick_count = 10
    selected_game = "Powerball"
    manual_history = ""

    try:
        if request.method == "POST":
            selected_game = request.form.get("game", "Powerball")
            pick_count = int(request.form.get("pick_count", 10))
            manual_history = request.form.get("manual_history", "")

        pick_count = max(1, min(pick_count, 50))

        manual_draws = parse_manual_history(manual_history, selected_game)

        if selected_game == "Powerball":
            draws = get_powerball_draws() + manual_draws
        else:
            draws = manual_draws if manual_draws else sample_draws_for_game(selected_game)

        result = analyze(draws, selected_game, pick_count)
        LAST_PICKS = result["picks"]

    except Exception:
        error = "Something went wrong. Check the code, internet, or pasted numbers."

    return render_template_string(
        HTML,
        app_name=APP_NAME,
        games=GAMES.keys(),
        selected_game=selected_game,
        result=result,
        error=error,
        pick_count=pick_count,
        prize_table=PRIZE_TABLE,
        jackpot=JACKPOT,
        cash_value=CASH_VALUE,
        next_draw=NEXT_DRAW,
        next_draw_js=NEXT_DRAW_JS,
        manual_history=manual_history,
        user=current_user(),
user_photo=current_user_photo()
    )
@app.route("/register", methods=["GET", "POST"])
def register():

    error = None

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]

        try:
            conn = db()

            conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (
                    username,
                    generate_password_hash(password)
                )
            )

            conn.commit()
            conn.close()

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            error = "Username already exists."

    return render_template_string(
        AUTH_HTML,
        title="Register",
        button="Create Account",
        error=error,
        switch_text="Already have an account?",
        switch_link="/login",
        switch_label="Login"
    )


@app.route("/login", methods=["GET", "POST"])
def login():

    error = None

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]

        conn = db()

        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(
            user["password_hash"],
            password
        ):

            session["user_id"] = user["id"]
            session["username"] = user["username"]

            return redirect(url_for("home"))

        error = "Wrong username or password."

    return render_template_string(
        AUTH_HTML,
        title="Login",
        button="Login",
        error=error,
        switch_text="Need an account?",
        switch_link="/register",
        switch_label="Register"
    )


@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )
@app.route("/save_pick", methods=["POST"])
def save_pick():

    if not current_user_id():
        return redirect(url_for("login"))

    conn = db()

    conn.execute("""
        INSERT INTO saved_picks (
            user_id,
            game,
            numbers,
            bonus,
            score,
            reason,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        current_user_id(),
        request.form.get("game"),
        request.form.get("numbers"),
        request.form.get("bonus"),
        int(request.form.get("score")),
        request.form.get("reason"),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("saved"))


@app.route("/saved")
def saved():

    if not current_user_id():
        return redirect(url_for("login"))

    conn = db()

    picks = conn.execute(
        "SELECT * FROM saved_picks WHERE user_id = ? ORDER BY id DESC",
        (current_user_id(),)
    ).fetchall()

    conn.close()

    return render_template_string(
        SAVED_HTML,
        picks=picks
    )


@app.route("/profile")
def profile():

    if not current_user_id():
        return redirect(url_for("login"))

    conn = db()

    rows = conn.execute(
        "SELECT * FROM saved_picks WHERE user_id = ?",
        (current_user_id(),)
    ).fetchall()

    conn.close()

    total = len(rows)
    favorite_game = "None"
    best_score = 0

    if rows:
        game_counts = Counter([r["game"] for r in rows])
        favorite_game = game_counts.most_common(1)[0][0]
        best_score = max([r["score"] or 0 for r in rows])

    return render_template_string(
        PROFILE_HTML,
        username=current_user(),
        total=total,
        favorite_game=favorite_game,
        best_score=best_score,
        photo=current_user_photo()
    )
@app.route("/upload_photo", methods=["POST"])
def upload_photo():

    if not current_user_id():
        return redirect(url_for("login"))

    file = request.files.get("photo")

    if not file or file.filename == "":
        return redirect(url_for("profile"))

    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()

    if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        return redirect(url_for("profile"))

    save_name = f"user_{current_user_id()}{ext}"
    save_path = os.path.join(UPLOAD_FOLDER, save_name)

    file.save(save_path)

    conn = db()

    conn.execute(
        "UPDATE users SET photo = ? WHERE id = ?",
        (
            save_path.replace("\\", "/"),
            current_user_id()
        )
    )

    conn.commit()
    conn.close()

    return redirect(url_for("profile"))


@app.route("/export")
def export_csv():

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Pick",
        "Numbers",
        "Bonus",
        "Score",
        "Reason"
    ])

    for i, p in enumerate(LAST_PICKS, start=1):
        writer.writerow([
            i,
            " ".join(str(n) for n in p["main"]),
            p["bonus"],
            p["score"],
            p["reason"]
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=ahadi_smart_picks_v11.csv"
        }
    )


if __name__ == "__main__":
    with app.app_context():
        init_db()

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5050
    )
with app.app_context():
    init_db()
