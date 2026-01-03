import datetime

import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client
from flask_security import current_user, login_user, logout_user
from quart import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)

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


def create_oauth_user(provider_data, ip_address):
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


@public.route("/")
async def index():
    return await render_template("index.html")


@public.route("/robots.txt")
async def static_from_root():
    return await send_from_directory(public.static_folder, request.path[1:])


# --- OAuth Routes (Authlib) ---


async def handle_oauth_callback(provider_name, token, user_info):
    """Common handler for OAuth callbacks from any provider."""
    if not token:
        current_app.logger.error(
            f"OAuth login failed: No token received for {provider_name}"
        )
        await flash("Authentication failed.", category="error")
        return redirect(url_for("security.login"))

    # Extract provider user ID and email based on provider
    if provider_name == "google":
        provider_user_id = user_info.get("sub")
        email = user_info.get("email")
        name = user_info.get("name", "")
    elif provider_name == "github":
        provider_user_id = str(user_info.get("id"))
        email = user_info.get("email")
        name = user_info.get("name") or user_info.get("login", "")
    else:
        current_app.logger.error(f"Unknown OAuth provider: {provider_name}")
        await flash("Authentication failed.", category="error")
        return redirect(url_for("security.login"))

    if not email:
        current_app.logger.error(f"OAuth login failed: No email from {provider_name}")
        await flash("Could not retrieve email from provider.", category="error")
        return redirect(url_for("security.login"))

    real_ip = get_real_ip()

    # Check if OAuth account already exists
    oauth_account = OAuth.query.filter_by(
        provider=provider_name, provider_user_id=provider_user_id
    ).first()

    if oauth_account and oauth_account.user:
        # Existing OAuth user - log them in
        if current_user.is_authenticated and current_user.id != oauth_account.user.id:
            logout_user()
        update_user_login_info(oauth_account.user, real_ip)
        login_user(oauth_account.user)
        return redirect(url_for("portal.dashboard"))

    # Check if user with this email exists
    existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        # Link OAuth to existing user
        if not oauth_account:
            oauth_account = OAuth(
                provider=provider_name,
                provider_user_id=provider_user_id,
                token=dict(token),
                user=existing_user,
            )
            db.session.add(oauth_account)
            db.session.commit()
        update_user_login_info(existing_user, real_ip)
        login_user(existing_user)
        await flash("Account linked successfully.", category="success")
        return redirect(url_for("portal.dashboard"))

    # Create new user
    provider_data = {"email": email, "name": name}
    new_user = create_oauth_user(provider_data, real_ip)
    oauth_account = OAuth(
        provider=provider_name,
        provider_user_id=provider_user_id,
        token=dict(token),
        user=new_user,
    )
    db.session.add_all([new_user, oauth_account])
    db.session.commit()
    login_user(new_user)
    await flash("Successfully signed in.", category="success")
    return redirect(url_for("portal.dashboard"))


# --- Google OAuth ---

GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"


def get_google_client():
    """Create Google OAuth client from app config."""
    return AsyncOAuth2Client(
        client_id=current_app.config.get("GOOGLE_OAUTH_CLIENT_ID"),
        client_secret=current_app.config.get("GOOGLE_OAUTH_CLIENT_SECRET"),
    )


@public.route("/login/google")
async def google_login():
    """Initiate Google OAuth login."""
    if current_user.is_authenticated:
        await flash("Please sign out before proceeding.", category="warning")
        return redirect(url_for("portal.dashboard"))

    if not current_app.config.get("GOOGLE_AUTH_ENABLED"):
        await flash("Google login is not configured.", category="error")
        return redirect(url_for("security.login"))

    # Get Google's OAuth endpoints from discovery document
    async with httpx.AsyncClient() as client:
        resp = await client.get(GOOGLE_DISCOVERY_URL)
        google_config = resp.json()

    # Store state in session for CSRF protection
    from secrets import token_urlsafe

    state = token_urlsafe(32)
    session["oauth_state"] = state

    redirect_uri = url_for("public.google_callback", _external=True)
    authorization_url = google_config["authorization_endpoint"]

    # Build authorization URL
    params = {
        "client_id": current_app.config.get("GOOGLE_OAUTH_CLIENT_ID"),
        "redirect_uri": redirect_uri,
        "scope": "openid profile email",
        "response_type": "code",
        "state": state,
    }
    from urllib.parse import urlencode

    auth_url = f"{authorization_url}?{urlencode(params)}"
    return redirect(auth_url)


@public.route("/login/google/callback")
async def google_callback():
    """Handle Google OAuth callback."""
    try:
        # Verify state
        state = request.args.get("state")
        if state != session.get("oauth_state"):
            await flash("Invalid state parameter.", category="error")
            return redirect(url_for("security.login"))
        session.pop("oauth_state", None)

        code = request.args.get("code")
        if not code:
            await flash("No authorization code received.", category="error")
            return redirect(url_for("security.login"))

        # Get Google's OAuth endpoints
        async with httpx.AsyncClient() as client:
            resp = await client.get(GOOGLE_DISCOVERY_URL)
            google_config = resp.json()

        redirect_uri = url_for("public.google_callback", _external=True)

        # Exchange code for token
        oauth_client = get_google_client()
        token = await oauth_client.fetch_token(
            google_config["token_endpoint"],
            grant_type="authorization_code",
            code=code,
            redirect_uri=redirect_uri,
        )

        # Get user info
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {token['access_token']}"}
            resp = await client.get(google_config["userinfo_endpoint"], headers=headers)
            user_info = resp.json()

        return await handle_oauth_callback("google", token, user_info)
    except Exception as e:
        current_app.logger.error(f"Google OAuth error: {str(e)}")
        await flash("Authentication failed.", category="error")
        return redirect(url_for("security.login"))


# --- GitHub OAuth ---

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_URL = "https://api.github.com"


def get_github_client():
    """Create GitHub OAuth client from app config."""
    return AsyncOAuth2Client(
        client_id=current_app.config.get("GITHUB_OAUTH_CLIENT_ID"),
        client_secret=current_app.config.get("GITHUB_OAUTH_CLIENT_SECRET"),
    )


@public.route("/login/github")
async def github_login():
    """Initiate GitHub OAuth login."""
    if current_user.is_authenticated:
        await flash("Please sign out before proceeding.", category="warning")
        return redirect(url_for("portal.dashboard"))

    if not current_app.config.get("GITHUB_AUTH_ENABLED"):
        await flash("GitHub login is not configured.", category="error")
        return redirect(url_for("security.login"))

    # Store state in session for CSRF protection
    from secrets import token_urlsafe

    state = token_urlsafe(32)
    session["oauth_state"] = state

    redirect_uri = url_for("public.github_callback", _external=True)

    # Build authorization URL
    from urllib.parse import urlencode

    params = {
        "client_id": current_app.config.get("GITHUB_OAUTH_CLIENT_ID"),
        "redirect_uri": redirect_uri,
        "scope": "read:user user:email",
        "state": state,
    }
    auth_url = f"{GITHUB_AUTHORIZE_URL}?{urlencode(params)}"
    return redirect(auth_url)


@public.route("/login/github/callback")
async def github_callback():
    """Handle GitHub OAuth callback."""
    try:
        # Verify state
        state = request.args.get("state")
        if state != session.get("oauth_state"):
            await flash("Invalid state parameter.", category="error")
            return redirect(url_for("security.login"))
        session.pop("oauth_state", None)

        code = request.args.get("code")
        if not code:
            await flash("No authorization code received.", category="error")
            return redirect(url_for("security.login"))

        redirect_uri = url_for("public.github_callback", _external=True)

        # Exchange code for token
        oauth_client = get_github_client()
        token = await oauth_client.fetch_token(
            GITHUB_TOKEN_URL,
            grant_type="authorization_code",
            code=code,
            redirect_uri=redirect_uri,
        )

        # Get user profile
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {token['access_token']}",
                "Accept": "application/json",
            }
            resp = await client.get(f"{GITHUB_API_URL}/user", headers=headers)
            user_info = resp.json()

            # GitHub may not include email in profile, fetch separately
            if not user_info.get("email"):
                email_resp = await client.get(
                    f"{GITHUB_API_URL}/user/emails", headers=headers
                )
                emails = email_resp.json()
                primary_email = next(
                    (e["email"] for e in emails if e.get("primary")), None
                )
                if primary_email:
                    user_info["email"] = primary_email

        return await handle_oauth_callback("github", token, user_info)
    except Exception as e:
        current_app.logger.error(f"GitHub OAuth error: {str(e)}")
        await flash("Authentication failed.", category="error")
        return redirect(url_for("security.login"))
