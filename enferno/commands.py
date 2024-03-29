# -*- coding: utf-8 -*-
"""Click commands."""

import click
from flask.cli import with_appcontext, AppGroup
from flask_security.utils import hash_password
from rich.console import Console

from enferno.extensions import db, openai
from enferno.user.models import User
from rich.progress import Progress, SpinnerColumn

console = Console()


@click.command()
@with_appcontext
def create_db():
    """creates db tables - import your models within commands.py to create the models.
    """
    db.create_all()
    print('Database structure created successfully')


@click.command()
@with_appcontext
def install():
    """Install a default admin user and add an admin role to it.
    """
    # check if admin exists
    from enferno.user.models import Role
    # create admin role if it doesn't exist
    admin_role = Role.query.filter(Role.name == 'admin').first()
    if not admin_role:
        admin_role = Role(name='admin').save()

    # check if admin users already installed
    admin_user = User.query.filter(User.roles.any(Role.name == 'admin')).first()
    if admin_user:
        print('An admin user already exists: {}'.format(admin_user.username))
        return

    # else : create a new admin user
    username = click.prompt('Admin username', default='admin')
    password = click.prompt('Admin Password (min 8 characters)?', default='enferno09')

    user = User(username=username, password=hash_password(password), active=1)
    user.roles.append(admin_role)
    user.save()
    print('User {} has been created successfuly'.format(username))


@click.command()
@click.option('-e', '--email', prompt=True, default=None)
@click.option('-p', '--password', prompt=True, default=None)
@with_appcontext
def create(email, password):
    """Creates a user using an email.
    """
    a = User.query.filter(User.email == email).first()
    if a != None:
        print('User already exists!')
    else:
        user = User(email=email, password=hash_password(password), active=True)
        user.save()


@click.command()
@click.option('-e', '--email', prompt=True, default=None)
@click.option('-r', '--role', prompt=True, default='admin')
@with_appcontext
def add_role(email, role):
    """Adds a role to the specified user.
        """
    from enferno.user.models import Role
    u = User.query.filter(User.email == email).first()

    if u is None:
        print('Sorry, this user does not exist!')
    else:
        r = db.session.execute(db.select(Role).filter_by(name=role)).scalar_one()
        if r is None:
            print('Sorry, this role does not exist!')
            u = click.prompt('Would you like to create one? Y/N', default='N')
            if u.lower() == 'y':
                r = Role(name=role)
                try:
                    db.session.add(r)
                    db.session.commit()
                    print('Role created successfully, you may add it now to the user')
                except Exception as e:
                    db.session.rollback()
        # add role to user
        u.roles.append(r)


@click.command()
@click.option('-e', '--email', prompt=True, default=None)
@click.option('-p', '--password', hide_input=True, confirmation_prompt=True, prompt=True, default=None)
@with_appcontext
def reset(email, password):
    """Reset a user password
    """
    try:
        pwd = hash_password(password)
        u = User.query.filter(User.email == email).first()
        u.password = pwd
        try:
            db.session.commit()
            print('User password has been reset successfully.')
        except:
            db.session.rollback()
    except Exception as e:
        print('Error resetting user password: %s' % e)


@click.command()
@click.option('--class_name', prompt=True, help='The name of the class')
@click.option('--fields', prompt=True, help='Describe your fields in a natural language')
@with_appcontext
def generate_dashboard(class_name, fields):
    """Generates a dynamic dashboard template for a specified class and fields."""
    # Parse fields input into a list of dictionaries

    sample = open('enferno/templates/core/dashboard.jinja2').read()

    with Progress(SpinnerColumn(), "[progress.description]{task.description}") as progress:
        task = progress.add_task("[cyan]Generating dashboard...", total=None)  # total=None for indefinite tasks

        # Simulate progress
        progress.update(task, advance=30)  # Start the task with some progress

        response = openai.client.chat.completions.create(
            model="gpt-4-0125-preview",
            messages=[
                {
                    "role": "system",
                    "content": f"""
                    Generate an jinja template by copying exactly the following SAMPLE,
                    Note the delimiters being used, you will need to replace project and their attributes with the 
                    following class name and fields,
                    class name: {class_name}
                    Fields: {fields}
                    Sample: {sample} 
                     no yap, just output code
                    """
                },
                {
                    "role": "user",
                    "content": f"The class name is {class_name}  and fields are describe here: {fields}"
                },

            ],
            temperature=0,
            max_tokens=4096,

            # response_format={"type": "json_object"}
        )
        progress.remove_task(task)  # Remove or complete the task once the API call is done

        generated_code = response.choices[0].message.content

    # Print the rendered template with ASCII borders
    console.print(generated_code)




@click.command()
@click.option('--class_name', prompt=True, help='The name of the class')
@click.option('--fields', prompt=True, help='Describe your fields in a natural language')
@with_appcontext
def generate_api(class_name, fields):
    """Generates Flask view functions for API endpoints of a specified class."""

    sample = open('enferno/templates/core/api.jinja2').read()

    with Progress(SpinnerColumn(), "[progress.description]{task.description}") as progress:
        task = progress.add_task("[cyan]Generating API Endpoints ...", total=None)  # total=None for indefinite tasks

        response = openai.client.chat.completions.create(
            model="gpt-4-0125-preview",
            messages=[
                {
                    "role": "system",
                    "content": f"""Generate Flask Endpoints by copying and modifying the following sample,
                     you will need to replace project and adapt the attributes with the given class name and fields,
                        sample: {sample}
                      no yap, don't import libs,  just output code
                    """
                },
                {
                    "role": "user",
                    "content": f"The class name is {class_name}  and fields are describe here: {fields}"
                },

            ],
            temperature=0,
            max_tokens=4096,

            # response_format={"type": "json_object"}
        )

    # Load and render the API views template
    progress.remove_task(task)  # Remove or complete the task once the API call is done

    generated_code = response.choices[0].message.content
    console.print(generated_code)



import click
from jinja2 import Environment, FileSystemLoader, select_autoescape


@click.command()
@click.option('--class_name', prompt=True, help='The name of the class')
@click.option('--fields', prompt=True, help='Describe your fields in a natural language')
def generate_model(class_name, fields):
    """Generates a Flask model class using OpenAI."""
    # Adjust the parsing to accommodate the new format

    sample = open('enferno/templates/core/model.jinja2').read()

    with Progress(SpinnerColumn(), "[progress.description]{task.description}") as progress:
        task = progress.add_task("[cyan]Generating SqlAlchemy Model ...", total=None)  # total=None for indefinite tasks

        response = openai.client.chat.completions.create(
            model="gpt-4-0125-preview",
            messages=[
                {
                    "role": "system",
                    "content": f"Generate an Flask-SQLAlchemy model class including from_json and to_dict methods, dont import anything, use the following as a sample \n {sample}, no yap, just output code"
                },
                {
                    "role": "user",
                    "content": f"The class name is {class_name}  and fields are describe here: {fields}"
                },

            ],
            temperature=0,
            max_tokens=1024,

            # response_format={"type": "json_object"}
        )
        progress.remove_task(task)  # Remove or complete the task once the API call is done

        generated_code = response.choices[0].message.content
        console.print(generated_code)


# Translations Management
i18n_cli = AppGroup("translate", short_help="commands to help with translation management")


@i18n_cli.command()
@click.argument('lang')
def init(lang):
    if os.system(f'pybabel init -i messages.pot -d enferno/translations -l {lang}'):
        raise RuntimeError("Init command failed")

@i18n_cli.command()
def extract():
    if os.system("pybabel extract -F babel.cfg -k _l -o messages.pot ."):
        raise RuntimeError("Extract command failed")


@i18n_cli.command()
def update():
    if os.system("pybabel update -i messages.pot -d enferno/translations"):
        raise RuntimeError("Update command failed")


@i18n_cli.command()
def compile():
    if os.system("pybabel compile -d enferno/translations"):
        raise RuntimeError("Compile command failed")