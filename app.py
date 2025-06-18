from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
import sqlite3
import bcrypt
import platform
import psutil
import cpuinfo
import io
import datetime

app = Flask(__name__)
app.secret_key = "vxdpvx9081"  # Güvenlik için değiştirilmeli

DB_NAME = "valexsysinfo.db"

# Veritabanı bağlantısı
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# Veritabanını başlat
def init_db():
    conn = get_db()
    conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

# Sistem bilgisi al
def get_system_info():
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "cpu": cpuinfo.get_cpu_info()["brand_raw"],
        "cores": psutil.cpu_count(logical=False),
        "threads": psutil.cpu_count(logical=True),
        "ram": round(psutil.virtual_memory().total / (1024 ** 3), 2),
        "disk": round(psutil.disk_usage("/").total / (1024 ** 3), 2)
    }

@app.route("/")
def home():
    if "user" not in session:
        return redirect(url_for("login"))
    system_info = get_system_info()
    return render_template("index.html", info=system_info, username=session["user"])

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].encode("utf-8")

        if len(username) < 3 or len(password) < 5:
            flash("Kullanıcı adı en az 3, şifre en az 5 karakter olmalı.", "error")
            return redirect(url_for("register"))

        hashed_pw = bcrypt.hashpw(password, bcrypt.gensalt())

        try:
            conn = get_db()
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
            conn.commit()
            conn.close()
            flash("Kayıt başarılı! Giriş yapabilirsiniz.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Bu kullanıcı adı zaten alınmış.", "error")
            return redirect(url_for("register"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].encode("utf-8")

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and bcrypt.checkpw(password, user["password"]):
            session["user"] = username
            flash(f"Giriş yapıldı, hoşgeldin {username}!", "success")
            return redirect(url_for("home"))
        else:
            flash("Kullanıcı adı veya şifre yanlış.", "error")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Çıkış yapıldı.", "info")
    return redirect(url_for("login"))

@app.route("/rapor")
def rapor_olustur():
    buffer = io.BytesIO()
    from reportlab.pdfgen import canvas
    p = canvas.Canvas(buffer)

    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, 800, "VALEXDP - Sistem Bilgileri Raporu")

    p.setFont("Helvetica", 10)
    now = datetime.datetime.now()
    p.drawString(450, 785, now.strftime("%d/%m/%Y %H:%M"))

    y = 750
    spacing = 20

    bilgiler = {
        "İşletim Sistemi": platform.system(),
        "Sürüm": platform.version(),
        "Mimari": platform.machine(),
        "İşlemci": platform.processor(),
        "CPU Çekirdekleri": psutil.cpu_count(logical=False),
        "Toplam RAM": f"{psutil.virtual_memory().total // (1024**3)} GB",
        "Disk Kullanımı": f"{psutil.disk_usage('/').percent}%",
        "Sistem Açılış Zamanı": datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%d/%m/%Y %H:%M")
    }

    p.setFont("Helvetica", 12)
    for key, value in bilgiler.items():
        p.drawString(50, y, f"{key}: {value}")
        y -= spacing

    p.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="valexdp_sistem_raporu.pdf", mimetype='application/pdf')

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
