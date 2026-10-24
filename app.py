import os, sqlite3, json
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "instance", "fertilizer.db")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "smart-fertilizer-change-this-key")

CROPS = {
    "Rice": {"N": (60,120), "P": (30,60), "K": (30,80), "temp": (20,35), "moist": (60,90), "fert": "Urea + DAP + MOP", "why": "Rice needs sufficient nitrogen for leaf and tiller growth, phosphorus for root development, and potassium for strong plants and grain formation."},
    "Wheat": {"N": (50,100), "P": (25,55), "K": (25,70), "temp": (15,25), "moist": (45,75), "fert": "Urea + DAP + MOP", "why": "Wheat benefits from nitrogen for vegetative growth, phosphorus for roots, and potassium for plant strength and grain development."},
    "Maize": {"N": (70,130), "P": (30,60), "K": (35,80), "temp": (20,32), "moist": (50,80), "fert": "Urea + DAP + MOP", "why": "Maize has a high nitrogen demand and also needs phosphorus and potassium for roots, stalk strength, and cob development."},
    "Tomato": {"N": (50,100), "P": (30,60), "K": (60,120), "temp": (18,30), "moist": (55,80), "fert": "NPK 10:26:26 + MOP", "why": "Tomato needs balanced nutrients, with extra phosphorus for flowering and potassium for fruit quality and development."},
    "Potato": {"N": (50,100), "P": (30,60), "K": (60,120), "temp": (15,25), "moist": (55,80), "fert": "NPK 10:26:26 + MOP", "why": "Potato requires potassium for tuber formation and quality, along with nitrogen and phosphorus for healthy growth."},
    "Onion": {"N": (40,90), "P": (25,55), "K": (50,100), "temp": (13,30), "moist": (45,75), "fert": "NPK 10:26:26 + MOP", "why": "Onion benefits from nitrogen for foliage, phosphorus for roots and bulb development, and potassium for bulb quality."},
    "Groundnut": {"N": (20,50), "P": (25,55), "K": (30,70), "temp": (22,30), "moist": (45,70), "fert": "DAP + MOP + Gypsum", "why": "Groundnut needs phosphorus and potassium for pod development, while gypsum supplies calcium and sulfur important for pod filling."},
    "Chilli": {"N": (45,90), "P": (25,55), "K": (55,110), "temp": (20,32), "moist": (50,75), "fert": "NPK 10:26:26 + MOP", "why": "Chilli needs potassium for flowering, fruit development and quality, with nitrogen and phosphorus supporting plant growth."},
    "Cotton": {"N": (50,110), "P": (25,55), "K": (35,80), "temp": (21,35), "moist": (45,75), "fert": "Urea + DAP + MOP", "why": "Cotton needs nitrogen for canopy growth and potassium for boll development and plant strength."},
    "Sugarcane": {"N": (80,150), "P": (30,70), "K": (50,110), "temp": (22,35), "moist": (60,90), "fert": "Urea + DAP + MOP", "why": "Sugarcane has high nutrient demand; nitrogen supports cane growth while phosphorus and potassium support roots and sugar accumulation."},
    "Soybean": {"N": (25,55), "P": (30,60), "K": (35,80), "temp": (20,30), "moist": (50,75), "fert": "DAP + MOP", "why": "Soybean benefits strongly from phosphorus and potassium for root, nodulation, flowering and seed development."},
    "Cabbage": {"N": (50,100), "P": (30,60), "K": (50,100), "temp": (15,25), "moist": (55,80), "fert": "NPK 19:19:19 + MOP", "why": "Cabbage needs balanced nutrition for leaf formation and potassium for compact, healthy heads."},
    "Carrot": {"N": (35,75), "P": (25,55), "K": (45,90), "temp": (15,25), "moist": (45,75), "fert": "NPK 10:26:26 + MOP", "why": "Carrot needs phosphorus for root development and potassium for root size and quality."},
    "Beans": {"N": (25,60), "P": (25,55), "K": (35,80), "temp": (18,30), "moist": (50,75), "fert": "DAP + MOP", "why": "Beans need phosphorus and potassium for roots, flowering and pod development, with moderate nitrogen."},
    "Peanut": {"N": (20,50), "P": (25,55), "K": (30,70), "temp": (22,30), "moist": (45,70), "fert": "DAP + MOP + Gypsum", "why": "Peanut benefits from phosphorus and potassium for pod development, while calcium and sulfur support good pod filling."}
}

DISTRICTS = ["Kolar","Bangarapet","Bangalore Rural","Bangalore Urban","Belagavi","Ballari","Chikkaballapur","Chitradurga","Dakshina Kannada","Davanagere","Dharwad","Gadag","Hassan","Haveri","Kalaburagi","Kodagu","Mandya","Mysuru","Raichur","Ramanagara","Shivamogga","Tumakuru","Udupi","Uttara Kannada","Vijayapura","Yadgir","Bagalkot","Bidar","Chamarajanagar","Chikkamagaluru","Vijayanagara"]

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    con = db()
    con.executescript("""
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
      password TEXT NOT NULL, created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS readings (
      id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
      nitrogen REAL, phosphorus REAL, potassium REAL, temperature REAL, moisture REAL,
      crop1 TEXT, crop2 TEXT, fertilizer TEXT, why TEXT, created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS shops (
      id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
      state TEXT NOT NULL, district TEXT NOT NULL, address TEXT
    );
    CREATE TABLE IF NOT EXISTS sensor_live (
      id INTEGER PRIMARY KEY CHECK (id=1), nitrogen REAL DEFAULT 0,
      phosphorus REAL DEFAULT 0, potassium REAL DEFAULT 0, temperature REAL DEFAULT 0, moisture REAL DEFAULT 0,
      updated_at TEXT
    );
    INSERT OR IGNORE INTO sensor_live(id) VALUES(1);
    """)
    con.commit()
    con.close()

def login_required(f):
    @wraps(f)
    def wrapped(*a, **kw):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*a, **kw)
    return wrapped

def crop_score(c, n,p,k,t,m):
    x=CROPS[c]
    def closeness(v, lo, hi):
        if lo <= v <= hi: return 1.0
        d = lo-v if v < lo else v-hi
        return max(0.0, 1.0-d/max(1,(hi-lo)))
    return sum([
        closeness(n,*x["N"]), closeness(p,*x["P"]), closeness(k,*x["K"]),
        closeness(t,*x["temp"]), closeness(m,*x["moist"])
    ])

def advise(n,p,k,t,m):
    ranked=sorted(CROPS, key=lambda c: crop_score(c,n,p,k,t,m), reverse=True)
    c1,c2=ranked[:2]
    # fertilizer explanation is based on the nutrient furthest outside the selected crop's range
    x=CROPS[c1]
    deficiencies=[]
    for label,val,key in [("Nitrogen",n,"N"),("Phosphorus",p,"P"),("Potassium",k,"K")]:
        lo,hi=x[key]
        if val < lo: deficiencies.append(label)
    fert=x["fert"]
    why=x["why"]
    if deficiencies:
        why += " Current readings show relatively low " + ", ".join(deficiencies) + " for the selected crop profile, so the recommended fertilizer combination helps address those nutrient needs."
    return c1,c2,fert,why

def seed_shops():
    con=db()
    count=con.execute("SELECT COUNT(*) FROM shops").fetchone()[0]
    if count==0:
        rows=[]
        for d in DISTRICTS:
            rows += [
                (f"{d} Agro Fertilizer Center","Karnataka",d,f"Main Road, {d}"),
                (f"{d} Farmers Fertilizer Shop","Karnataka",d,f"Market Area, {d}"),
                (f"{d} Krishi Seva Kendra","Karnataka",d,f"Taluk Office Road, {d}")
            ]
        con.executemany("INSERT INTO shops(name,state,district,address) VALUES(?,?,?,?)",rows)
        con.commit()
    con.close()

@app.route("/")
def index():
    return redirect(url_for("dashboard") if "user_id" in session else url_for("login"))

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        u=request.form["username"].strip()
        p=request.form["password"]
        con=db(); user=con.execute("SELECT * FROM users WHERE username=?",(u,)).fetchone(); con.close()
        if user and check_password_hash(user["password"],p):
            session["user_id"]=user["id"]; session["username"]=user["username"]
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.")
    return render_template("login.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        u=request.form["username"].strip(); p=request.form["password"]; cp=request.form["confirm_password"]
        if not u or len(p)<4: flash("Enter a username and a password of at least 4 characters."); return render_template("register.html")
        if p!=cp: flash("Passwords do not match."); return render_template("register.html")
        try:
            con=db(); con.execute("INSERT INTO users(username,password,created_at) VALUES(?,?,?)",(u,generate_password_hash(p),datetime.now().isoformat(timespec="seconds"))); con.commit(); con.close()
            flash("Registration successful. Please login."); return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists.")
    return render_template("register.html")

@app.route("/forgot-password", methods=["GET","POST"])
def forgot():
    if request.method=="POST":
        u=request.form["username"].strip(); p=request.form["new_password"]
        con=db(); user=con.execute("SELECT id FROM users WHERE username=?",(u,)).fetchone()
        if user:
            con.execute("UPDATE users SET password=? WHERE id=?",(generate_password_hash(p),user["id"])); con.commit(); con.close()
            flash("Password updated successfully. You can login now."); return redirect(url_for("login"))
        con.close(); flash("Username not found.")
    return render_template("forgot.html")

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    con=db()
    live=con.execute("SELECT * FROM sensor_live WHERE id=1").fetchone()
    latest=con.execute("SELECT * FROM readings WHERE user_id=? ORDER BY id DESC LIMIT 1",(session["user_id"],)).fetchone()
    con.close()
    return render_template("dashboard.html",live=live,latest=latest)

@app.route("/api/sensor-data", methods=["POST"])
def sensor_data():
    data=request.get_json(silent=True) or request.form
    try:
        n=float(data.get("nitrogen",data.get("N",0))); p=float(data.get("phosphorus",data.get("P",0)))
        k=float(data.get("potassium",data.get("K",0))); t=float(data.get("temperature",0)); m=float(data.get("moisture",0))
    except Exception: return jsonify(error="Invalid sensor values"),400
    c1,c2,fert,why=advise(n,p,k,t,m)
    now=datetime.now().isoformat(timespec="seconds")
    con=db(); con.execute("""UPDATE sensor_live SET nitrogen=?,phosphorus=?,potassium=?,temperature=?,moisture=?,updated_at=? WHERE id=1""",(n,p,k,t,m,now))
    con.commit(); con.close()
    return jsonify(ok=True,nitrogen=n,phosphorus=p,potassium=k,temperature=t,moisture=m,crop1=c1,crop2=c2,fertilizer=fert,why=why,updated_at=now)

@app.route("/api/live")
@login_required
def live():
    con=db(); r=con.execute("SELECT * FROM sensor_live WHERE id=1").fetchone(); con.close()
    n,p,k,t,m=[r[x] or 0 for x in ["nitrogen","phosphorus","potassium","temperature","moisture"]]
    c1,c2,fert,why=advise(n,p,k,t,m)
    return jsonify(nitrogen=n,phosphorus=p,potassium=k,temperature=t,moisture=m,crop1=c1,crop2=c2,fertilizer=fert,why=why,updated_at=r["updated_at"])

@app.route("/api/save-reading", methods=["POST"])
@login_required
def save_reading():
    data=request.get_json(silent=True) or request.form
    n=float(data.get("nitrogen",0)); p=float(data.get("phosphorus",0)); k=float(data.get("potassium",0)); t=float(data.get("temperature",0)); m=float(data.get("moisture",0))
    c1,c2,fert,why=advise(n,p,k,t,m)
    con=db(); con.execute("""INSERT INTO readings(user_id,nitrogen,phosphorus,potassium,temperature,moisture,crop1,crop2,fertilizer,why,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",(session["user_id"],n,p,k,t,m,c1,c2,fert,why,datetime.now().isoformat(timespec="seconds"))); con.commit(); con.close()
    return jsonify(ok=True)

@app.route("/history")
@login_required
def history():
    con=db(); rows=con.execute("SELECT * FROM readings WHERE user_id=? ORDER BY id DESC",(session["user_id"],)).fetchall(); con.close()
    return render_template("history.html",rows=rows)

@app.route("/shops")
@login_required
def shops():
    state=request.args.get("state","Karnataka").strip()
    district=request.args.get("district","").strip()
    con=db()
    rows=con.execute("SELECT * FROM shops WHERE state=? AND district LIKE ? ORDER BY name",(state,f"%{district}%")).fetchall()
    con.close()
    return render_template("shops.html",rows=rows,state=state,district=district,districts=DISTRICTS)

@app.route("/api/chart")
@login_required
def chart():
    con=db(); rows=con.execute("SELECT created_at,nitrogen,phosphorus,potassium FROM readings WHERE user_id=? ORDER BY id DESC LIMIT 20",(session["user_id"],)).fetchall(); con.close()
    rows=list(reversed(rows))
    return jsonify(labels=[r["created_at"] for r in rows],nitrogen=[r["nitrogen"] for r in rows],phosphorus=[r["phosphorus"] for r in rows],potassium=[r["potassium"] for r in rows])

init_db(); seed_shops()

if __name__=="__main__":
    app.run(host="0.0.0.0",port=5000,debug=True)
