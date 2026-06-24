"""
app/auth/routes.py
==================
Authentication blueprint — Login, Logout, Password Change.
"""
from datetime import datetime
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, session)
from flask_login import login_user, logout_user, login_required, current_user
from ..models import User
from .. import db

auth_bp = Blueprint("auth", __name__)


# ── Login ─────────────────────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username   = request.form.get("username", "").strip()
        password   = request.form.get("password", "")
        remember   = bool(request.form.get("remember"))

        user = User.query.filter_by(username=username).first()

        if user and user.is_active and user.check_password(password):
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()
            flash(f"Welcome back, {user.username}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard.index"))

        flash("Invalid username or password.", "danger")

    return render_template("auth/login.html", title="Login")


# ── Logout ────────────────────────────────────────────────────────────────────
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


# ── Change Password ───────────────────────────────────────────────────────────
@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        old_pw  = request.form.get("old_password", "")
        new_pw  = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")

        if not current_user.check_password(old_pw):
            flash("Current password is incorrect.", "danger")
        elif new_pw != confirm:
            flash("New passwords do not match.", "warning")
        elif len(new_pw) < 8:
            flash("Password must be at least 8 characters.", "warning")
        else:
            current_user.set_password(new_pw)
            db.session.commit()
            flash("Password changed successfully!", "success")
            return redirect(url_for("dashboard.index"))

    return render_template("auth/change_password.html", title="Change Password")
