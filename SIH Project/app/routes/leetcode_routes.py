from flask import Blueprint, render_template, redirect, url_for
import pandas as pd
import threading
import os
from app.services.background_fetcher import background_job

leetcode_bp = Blueprint("leetcode", __name__)

@leetcode_bp.route("/", methods=["GET"])
def home():
    # User requested to remove unused datafile logic
    table = None
    return render_template("leetcode.html", table=table)

@leetcode_bp.route("/fetch", methods=["POST"])
def fetch():
    threading.Thread(target=background_job, daemon=True).start()
    return redirect(url_for("leetcode.home"))
