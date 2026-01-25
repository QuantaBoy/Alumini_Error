from flask import Blueprint, render_template, request
from flask_login import login_required, current_user

message_bp = Blueprint("message", __name__)

@message_bp.route("/")
@login_required
def message_home():
    """Main message page showing all conversations"""
    return render_template("chat_interface.html",
                           username=current_user.username)

@message_bp.route("/<partner>")
@login_required
def message_with_partner(partner):
    username = request.args.get("username") or current_user.username
    return render_template("chat_interface.html",
                           username=username,
                           target_partner=partner)
