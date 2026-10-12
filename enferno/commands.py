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
    from flask_migrate import stamp

    db.create_all()
    stamp()
    print("Database structure created successfully")


@click.command()
@click.option("-e", "--email", default=None, help="Admin email")
@click.option("-p", "--password", default=None, help="Admin password")
@with_appcontext
def install(email, password):
    """Install a default admin user and add an admin role to it."""
    from enferno.user.models import Role

    # create admin role if it doesn't exist
    admin_role = Role.query.filter(Role.name == "admin").first()
    if not admin_role:
        admin_role = Role(name="admin").save()

    # check if admin users already installed
    admin_user = User.query.filter(User.roles.any(Role.name == "admin")).first()
    if admin_user:
        console.print(
            f"[yellow]An admin user already exists:[/] [blue]{admin_user.email}[/]"
        )
        return

    # Interactive mode if no args provided
    if not email:
        email = click.prompt("Admin email", default="admin@example.com")

    # Generate password if not provided
    generated = False
    if not password:
        password = "".join(
            secrets.choice(string.ascii_letters + string.digits + "@#$%^&*")
            for _ in range(32)
        )
        generated = True

    user = User(
        email=email,
        name="Super Admin",
        password=hash_password(password),
        active=True,
    )
    user.roles.append(admin_role)
    user.save()

    console.print("\n[green]✓[/] Admin user created successfully!")
    console.print(f"[blue]Email:[/] {email}")
    if generated:
        console.print(f"[blue]Password:[/] [red]{password}[/]")
        console.print(
            "\n[yellow]⚠️  Please save this password securely - you will not see it again![/]"
        )


@click.command()
@click.option("-e", "--email", prompt=True, default=None)
@click.option("-p", "--password", prompt=True, default=None)
@with_appcontext
def create(email, password):
    """Creates a user using an email."""
    a = User.query.filter(User.email == email).first()
    if a is not None:
        print("User already exists!")
    else:
        user = User(email=email, password=hash_password(password), active=True)
        user.save()


@click.command()
@click.option("-e", "--email", prompt=True, default=None)
@click.option("-r", "--role", prompt=True, default="admin")
@with_appcontext
def add_role(email, role):
    """Adds a role to the specified user."""
    from enferno.user.models import Role

    u = db.session.execute(db.select(User).filter_by(email=email)).scalar()
    if u is None:
        raise click.ClickException("This user does not exist.")

    r = db.session.execute(db.select(Role).filter_by(name=role)).scalar()
    if r is None:
        click.confirm(f"Role '{role}' does not exist. Create it?", abort=True)
        r = Role(name=role)
    if r not in u.roles:
        u.roles.append(r)
    db.session.commit()
    print(f"User {email} now has the role {role}.")


@click.command()
@click.option("-e", "--email", prompt="Email", default=None)
@click.option("-p", "--password", hide_input=True, prompt=True, default=None)
@with_appcontext
def reset(email, password):
    """Reset a user password using email"""
    try:
        pwd = hash_password(password)
        u = User.query.filter(User.email == email).first()
        if not u:
            print(f'User with email "{email}" not found.')
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
