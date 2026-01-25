from flask import Blueprint, render_template, redirect, url_for
import pandas as pd
import threading
import os
from app.services.background_fetcher import background_job

leetcode_bp = Blueprint("leetcode", __name__)

DATA_FILE = r"app/data/leetcodes_data.xlsx" 

@leetcode_bp.route("/", methods=["GET"])
def home():
    if os.path.exists(DATA_FILE):
        df = pd.read_excel(DATA_FILE, engine="openpyxl")
        table = df.to_html(index=False)
    else:
        table = None

    return render_template("leetcode.html", table=table)

@leetcode_bp.route("/fetch", methods=["POST"])
def fetch():
    threading.Thread(target=background_job, daemon=True).start()
    return redirect(url_for("leetcode.home"))
