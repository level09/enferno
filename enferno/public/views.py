from flask import request, Blueprint, send_from_directory, flash, redirect, url_for, current_app
from flask.templating import render_template
from flask_security import login_user, current_user, logout_user
from flask_dance.contrib.google import google
from flask_dance.consumer import oauth_authorized, oauth_error
from sqlalchemy.orm.exc import NoResultFound
from enferno.extensions import db, google_bp
from enferno.user.models import User, OAuth
import datetime
import warnings
from oauthlib.oauth2.rfc6749.errors import OAuth2Error

public = Blueprint('public',__name__, static_folder='../static')

def get_real_ip():
    """Get real IP address with Cloudflare and proxy support."""
    # First check for Cloudflare
    cf_connecting_ip = request.headers.get('CF-Connecting-IP')
    if cf_connecting_ip:
        return cf_connecting_ip
    
    # Then check X-Forwarded-For
    x_forwarded_for = request.headers.get('X-Forwarded-For')
    if x_forwarded_for:
        # Get the first IP in the list
        return x_forwarded_for.split(',')[0].strip()
    
    # Then check X-Real-IP
    x_real_ip = request.headers.get('X-Real-IP')
    if x_real_ip:
        return x_real_ip
    
    # Finally fall back to remote_addr
    return request.remote_addr

@public.route('/')
def index():
    return render_template('index.html')

@public.route('/robots.txt')
def static_from_root():
    return send_from_directory(public.static_folder, request.path[1:])

# Handle pre-OAuth login check
@google_bp.before_app_request
def before_google_login():
    if request.endpoint == 'google.login' and current_user.is_authenticated:
        flash("Please sign out before proceeding.", category="warning")
        return redirect(url_for('portal.dashboard'))

# create/login local user on successful OAuth login
@oauth_authorized.connect_via(google_bp)
def google_logged_in(blueprint, token):
    if not token:
        current_app.logger.error("OAuth login failed: No token received")
        flash("Authentication failed.", category="error")
        return False

    try:
        resp = blueprint.session.get("/oauth2/v2/userinfo")
        if not resp.ok:
            current_app.logger.error(f"Failed to fetch user info: {resp.text}")
            flash("Authentication failed.", category="error")
            return False

        info = resp.json()
        user_id = info["id"]

        query = OAuth.query.filter_by(provider=blueprint.name, provider_user_id=user_id)
        try:
            oauth = query.one()
        except NoResultFound:
            oauth = OAuth(provider=blueprint.name, provider_user_id=user_id, token=token)

        now = datetime.datetime.now()
        real_ip = get_real_ip()
        
        if oauth.user:
            if current_user.is_authenticated and current_user.id != oauth.user.id:
                logout_user()
            # Update login tracking
            oauth.user.last_login_at = oauth.user.current_login_at
            oauth.user.current_login_at = now
            oauth.user.last_login_ip = oauth.user.current_login_ip
            oauth.user.current_login_ip = real_ip
            oauth.user.login_count = (oauth.user.login_count or 0) + 1
            db.session.add(oauth.user)
            db.session.commit()
            login_user(oauth.user)
        else:
            # Create new user with tracking fields
            user = User(
                email=info["email"],
                username=info["email"],
                name=info.get("name", ""),
                password=User.random_password(),
                active=True,
                confirmed_at=now,
                current_login_at=now,
                current_login_ip=real_ip,
                login_count=1
            )
            oauth.user = user
            db.session.add_all([user, oauth])
            db.session.commit()
            login_user(user)

        flash("Successfully signed in.")
        return redirect(url_for("portal.dashboard"))

    except OAuth2Error as e:
        current_app.logger.error(f"OAuth2Error during login: {str(e)}")
        flash("Authentication failed.", category="error")
        return False

# notify on OAuth provider error
@oauth_error.connect_via(google_bp)
def google_error(blueprint, message, response):
    current_app.logger.error(f"OAuth error from {blueprint.name}: {message}, Response: {response}")
    flash("Authentication failed.", category="error")