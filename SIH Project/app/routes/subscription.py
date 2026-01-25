from flask import Blueprint, render_template, redirect, url_for

subscription_bp = Blueprint('Subscribe', __name__)

@subscription_bp.route('/')
def subscribe():
    return render_template('PricingPage.html')