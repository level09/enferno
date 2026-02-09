"""Click commands."""

import asyncio
import secrets
import string

import click
from quart_security import hash_password
from rich.console import Console
from sqlalchemy import select

import enferno.extensions as ext
from enferno.user.models import User

console = Console()


def run_async(coro):
    """Run an async function in sync context (for CLI commands)."""
    return asyncio.run(coro)


@click.command()
def create_db():
    """creates db tables - import your models within commands.py to create the models."""

    async def _run():
        async with ext.engine.begin() as conn:
            await conn.run_sync(ext.Base.metadata.create_all)

    run_async(_run())
    print("Database structure created successfully")


@click.command()
@click.option("-e", "--email", default=None, help="Admin email")
@click.option("-p", "--password", default=None, help="Admin password")
def install(email, password):
    """Install a default admin user and add an admin role to it."""

    async def _run():
        from enferno.user.models import Role

        async with ext.async_session_factory() as session:
            admin_role = (
                await session.execute(select(Role).filter(Role.name == "admin"))
            ).scalar_one_or_none()
            if not admin_role:
                admin_role = Role(name="admin")
                session.add(admin_role)
                await session.commit()

            admin_user = (
                await session.execute(
                    select(User).filter(User.roles.any(Role.name == "admin"))
                )
            ).scalar_one_or_none()
            if admin_user:
                console.print(
                    f"[yellow]An admin user already exists:[/] [blue]{admin_user.email}[/]"
                )
                return

            nonlocal email, password
            if not email:
                email = click.prompt("Admin email", default="admin@example.com")

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
            session.add(user)
            await session.commit()

            console.print("\n[green]✓[/] Admin user created successfully!")
            console.print(f"[blue]Email:[/] {email}")
            if generated:
                console.print(f"[blue]Password:[/] [red]{password}[/]")
                console.print(
                    "\n[yellow]⚠️  Please save this password securely - you will not see it again![/]"
                )

    run_async(_run())


@click.command()
@click.option("-e", "--email", prompt=True, default=None)
@click.option("-p", "--password", prompt=True, default=None)
def create(email, password):
    """Creates a user using an email."""

    async def _run():
        async with ext.async_session_factory() as session:
            existing = (
                await session.execute(select(User).filter(User.email == email))
            ).scalar_one_or_none()
            if existing is not None:
                print("User already exists!")
            else:
                user = User(email=email, password=hash_password(password), active=True)
                session.add(user)
                await session.commit()

    run_async(_run())


@click.command()
@click.option("-e", "--email", prompt=True, default=None)
@click.option("-r", "--role", prompt=True, default="admin")
def add_role(email, role):
    """Adds a role to the specified user."""

    async def _run():
        from enferno.user.models import Role

        async with ext.async_session_factory() as session:
            u = (
                await session.execute(select(User).filter(User.email == email))
            ).scalar_one_or_none()

            if u is None:
                print("Sorry, this user does not exist!")
            else:
                r = (
                    await session.execute(select(Role).filter_by(name=role))
                ).scalar_one_or_none()
                if r is None:
                    print("Sorry, this role does not exist!")
                    answer = click.prompt(
                        "Would you like to create one? Y/N", default="N"
                    )
                    if answer.lower() == "y":
                        r = Role(name=role)
                        try:
                            session.add(r)
                            await session.commit()
                            print(
                                "Role created successfully, you may add it now to the user"
                            )
                        except Exception:
                            await session.rollback()
                if r:
                    u.roles.append(r)
                    await session.commit()

    run_async(_run())


@click.command()
@click.option("-e", "--email", prompt="Email", default=None)
@click.option("-p", "--password", hide_input=True, prompt=True, default=None)
def reset(email, password):
    """Reset a user password using email"""
    try:
        pwd = hash_password(password)

        async def _run():
            async with ext.async_session_factory() as session:
                u = (
                    await session.execute(select(User).filter(User.email == email))
                ).scalar_one_or_none()
                if not u:
                    print(f'User with email "{email}" not found.')
                    return

                u.password = pwd
                try:
                    await session.commit()
                    print("User password has been reset successfully.")
                except Exception:
                    await session.rollback()
                    print("Error committing to database.")

        run_async(_run())
    except Exception as e:
        print(f"Error resetting user password: {e}")
