"""Click commands."""

import os
import secrets
import string

import click
from flask.cli import AppGroup, with_appcontext
from flask_security.utils import hash_password
from rich.console import Console

from enferno.extensions import db
from enferno.user.models import User

console = Console()


@click.command()
@with_appcontext
def create_db():
    """creates db tables - import your models within commands.py to create the models."""
    db.create_all()
    print("Database structure created successfully")


@click.command()
@click.option("--email", "-e", help="Admin email (default: admin@example.com)")
@click.option(
    "--password", "-p", help="Admin password (auto-generated if not provided)"
)
@click.option("--non-interactive", "-n", is_flag=True, help="Non-interactive mode")
@with_appcontext
def install(email=None, password=None, non_interactive=False):
    """Install a default admin user and add an admin role to it."""
    # check if admin exists
    from enferno.user.models import Role

    # create admin role if it doesn't exist
    admin_role = db.session.execute(
        db.select(Role).where(Role.name == "admin")
    ).scalar_one_or_none()
    if not admin_role:
        admin_role = Role(name="admin")
        db.session.add(admin_role)
        db.session.commit()

    # check if admin users already installed
    admin_user = db.session.execute(
        db.select(User).where(User.roles.any(Role.name == "admin"))
    ).scalar_one_or_none()
    if admin_user:
        console.print(
            f"[yellow]An admin user already exists:[/] [blue]{admin_user.email}[/]"
        )
        return

    # Get email
    if email is None:
        if non_interactive:
            email = "admin@example.com"
        else:
            email = click.prompt("Admin email", default="admin@example.com")

    # Get or generate password
    if password is None:
        if non_interactive:
            # Generate a secure password for non-interactive mode
            password = "".join(
                secrets.choice(string.ascii_letters + string.digits + "@#$%^&*")
                for _ in range(32)
            )
        else:
            # Interactive mode - ask user if they want to generate or provide password
            generate_password = click.confirm(
                "Generate a secure random password?", default=True
            )
            if generate_password:
                password = "".join(
                    secrets.choice(string.ascii_letters + string.digits + "@#$%^&*")
                    for _ in range(32)
                )
            else:
                password = click.prompt("Enter admin password", hide_input=True)

    # Extract username from email for backwards compatibility
    username = email.split("@")[0]

    user = User(
        username=username,
        email=email,
        name="Super Admin",
        password=hash_password(password),
        active=True,
        is_superadmin=True,  # Set as super admin
    )
    user.roles.append(admin_role)
    db.session.add(user)
    db.session.commit()

    console.print("\n[green]✓[/] Super Admin user created successfully!")
    console.print(f"[blue]Email:[/] {email}")
    console.print(f"[blue]Password:[/] [red]{password}[/]")
    console.print(
        "\n[yellow]⚠️  Please save this password securely - you will not see it again![/]"
    )


@click.command()
@click.option("-e", "--email", prompt=True, default=None)
@click.option("-p", "--password", prompt=True, default=None)
@click.option(
    "--super-admin",
    is_flag=True,
    help="Create as super admin (bypasses UI restrictions)",
)
@with_appcontext
def create(email, password, super_admin):
    """Creates a user using an email."""
    a = db.session.execute(
        db.select(User).where(User.email == email)
    ).scalar_one_or_none()
    if a is not None:
        print("User already exists!")
    else:
        username = email.split("@")[0]
        user = User(
            username=username,
            email=email,
            password=hash_password(password),
            active=True,
            is_superadmin=super_admin,
        )
        db.session.add(user)
        db.session.commit()

        if super_admin:
            console.print(f"[green]✓[/] Super Admin user created: {email}")
            console.print("[yellow]⚠️  This user has full platform access![/]")
        else:
            console.print(f"[green]✓[/] User created: {email}")


@click.command()
@click.option("-e", "--email", prompt=True, default=None)
@click.option("-r", "--role", prompt=True, default="admin")
@with_appcontext
def add_role(email, role):
    """Adds a role to the specified user."""
    from enferno.user.models import Role

    u = db.session.execute(
        db.select(User).where(User.email == email)
    ).scalar_one_or_none()

    if u is None:
        print("Sorry, this user does not exist!")
    else:
        r = db.session.execute(db.select(Role).filter_by(name=role)).scalar_one()
        if r is None:
            print("Sorry, this role does not exist!")
            u = click.prompt("Would you like to create one? Y/N", default="N")
            if u.lower() == "y":
                r = Role(name=role)
                try:
                    db.session.add(r)
                    db.session.commit()
                    print("Role created successfully, you may add it now to the user")
                except Exception:
                    db.session.rollback()
        # add role to user
        u.roles.append(r)
        db.session.commit()


@click.command()
@click.option("-e", "--email", prompt="Email or username", default=None)
@click.option("-p", "--password", hide_input=True, prompt=True, default=None)
@with_appcontext
def reset(email, password):
    """Reset a user password using email or username"""
    try:
        pwd = hash_password(password)
        # Check if user exists with provided email or username
        u = db.session.execute(
            db.select(User).where((User.email == email) | (User.username == email))
        ).scalar_one_or_none()
        if not u:
            print(f'User with email or username "{email}" not found.')
            return

        u.password = pwd
        try:
            db.session.commit()
            print("User password has been reset successfully.")
        except Exception:
            db.session.rollback()
            print("Error committing to database.")
    except Exception as e:
        print(f"Error resetting user password: {e}")


i18n_cli = AppGroup("i18n")


@i18n_cli.command()
@click.argument("lang")
def init(lang):
    """Initialize a new language"""
    if os.system("pybabel init -i messages.pot -d enferno/translations -l " + lang):
        raise RuntimeError("init command failed")


@i18n_cli.command()
def extract():
    """Extract messages from code"""
    if os.system("pybabel extract -F babel.cfg -k _l -o messages.pot ."):
        raise RuntimeError("Extract command failed")


@i18n_cli.command()
def update():
    """Update translations"""
    if os.system("pybabel update -i messages.pot -d enferno/translations"):
        raise RuntimeError("Update command failed")


@i18n_cli.command()
def compile():
    """Compile translations"""
    if os.system("pybabel compile -d enferno/translations"):
        raise RuntimeError("Compile command failed")
