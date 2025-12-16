import datetime

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    request,
    send_from_directory,
    url_for,
)
from flask.templating import render_template
from flask_dance.consumer import oauth_authorized, oauth_error
from flask_security import current_user, login_user, logout_user
from oauthlib.oauth2.rfc6749.errors import OAuth2Error
from sqlalchemy.orm.exc import NoResultFound

from enferno.extensions import db
from enferno.user.models import OAuth, User

public = Blueprint("public", __name__, static_folder="../static")


def get_real_ip():
    """Get real IP address with Cloudflare and proxy support."""
    # First check for Cloudflare
    cf_connecting_ip = request.headers.get("CF-Connecting-IP")
    if cf_connecting_ip:
        return cf_connecting_ip

    # Then check X-Forwarded-For
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        # Get the first IP in the list
        return x_forwarded_for.split(",")[0].strip()

    # Then check X-Real-IP
    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip:
        return x_real_ip

    # Finally fall back to remote_addr
    return request.remote_addr


def update_user_login_info(user, ip_address):
    """Update user login tracking information."""
    now = datetime.datetime.now()
    user.last_login_at = user.current_login_at
    user.current_login_at = now
    user.last_login_ip = user.current_login_ip
    user.current_login_ip = ip_address
    user.login_count = (user.login_count or 0) + 1
    db.session.add(user)
    db.session.commit()


def create_oauth_user(provider_data, oauth_token, ip_address):
    """Create a new user from OAuth data."""
    now = datetime.datetime.now()
    user = User(
        email=provider_data.get("email"),
        username=provider_data.get("email"),
        name=provider_data.get("name", ""),
        password=User.random_password(),
        password_set=False,  # OAuth users don't know their random password
        active=True,
        confirmed_at=now,
        current_login_at=now,
        current_login_ip=ip_address,
        login_count=1,
    )
    return user


def get_oauth_user_data(blueprint):
    """Get user data from OAuth provider."""
    if not blueprint:
        return None

    if blueprint.name == "google":
        resp = blueprint.session.get("/oauth2/v2/userinfo")
        if not resp.ok:
            current_app.logger.error(f"Failed to fetch user info: {resp.text}")
            return None
        return resp.json()
    elif blueprint.name == "github":
        # Get user profile
        resp = blueprint.session.get("/user")
        if not resp.ok:
            current_app.logger.error(f"Failed to fetch GitHub user info: {resp.text}")
            return None
        data = resp.json()

        # GitHub doesn't return email in basic profile if private, need separate call
        if not data.get("email"):
            email_resp = blueprint.session.get("/user/emails")
            if email_resp.ok:
                emails = email_resp.json()
                primary_email = next(
                    (email["email"] for email in emails if email["primary"]), None
                )
                if primary_email:
                    data["email"] = primary_email

        # Normalize the data structure to match our needs
        return {
            "id": str(data["id"]),  # Convert to string to match Google's ID format
            "email": data.get("email"),
            "name": data.get("name")
            or data.get("login"),  # Fallback to username if name not set
        }
    return None


@public.route("/")
def index():
    return render_template("index.html")


@public.route("/robots.txt")
def static_from_root():
    return send_from_directory(public.static_folder, request.path[1:])


# Handle pre-OAuth login check
def before_oauth_login():
    if (
        request.endpoint in ["google.login", "github.login"]
        and current_user.is_authenticated
    ):
        flash("Please sign out before proceeding.", category="warning")
        return redirect(url_for("portal.dashboard"))


# Register the check for all OAuth routes
public.before_app_request(before_oauth_login)


@oauth_authorized.connect
def oauth_logged_in(blueprint, token):
    if not token:
        current_app.logger.error(
            f"OAuth login failed: No token received for {blueprint.name}"
        )
        flash("Authentication failed.", category="error")
        return False

    try:
        # Get user info from provider
        provider_data = get_oauth_user_data(blueprint)
        if not provider_data:
            return False

        user_id = provider_data["id"]
        real_ip = get_real_ip()

        # First check if we already have OAuth entry
        query = OAuth.query.filter_by(provider=blueprint.name, provider_user_id=user_id)
        try:
            oauth = query.one()
        except NoResultFound:
            oauth = OAuth(
                provider=blueprint.name, provider_user_id=user_id, token=token
            )

        if oauth.user:
            if current_user.is_authenticated and current_user.id != oauth.user.id:
                logout_user()
            update_user_login_info(oauth.user, real_ip)
            login_user(oauth.user)
        else:
            # Check if user exists with this email
            existing_user = User.query.filter_by(
                email=provider_data.get("email")
            ).first()
            if existing_user:
                # Link OAuth to existing user
                oauth.user = existing_user
                db.session.add(oauth)
                db.session.commit()
                update_user_login_info(existing_user, real_ip)
                login_user(existing_user)
                flash("Account linked successfully.", category="success")
            else:
                # Create new user
                user = create_oauth_user(provider_data, token, real_ip)
                oauth.user = user
                db.session.add_all([user, oauth])
                db.session.commit()
                login_user(user)
                flash("Successfully signed in.")

        return redirect(url_for("portal.dashboard"))

    except OAuth2Error as e:
        current_app.logger.error(f"OAuth2Error during {blueprint.name} login: {str(e)}")
        flash("Authentication failed.", category="error")
        return False


@oauth_error.connect
def oauth_error(blueprint, message, response):
    current_app.logger.error(
        f"OAuth error from {blueprint.name}: {message}, Response: {response}"
    )
    flash("Authentication failed.", category="error")
