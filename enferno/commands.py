# -*- coding: utf-8 -*-
"""Click commands."""

import click
from flask.cli import with_appcontext
from flask_security.utils import hash_password
from rich.console import Console
from rich.markdown import Markdown
from enferno.extensions import db, openai
from enferno.user.models import User

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
@click.option('--class_name', default='Item', help='The name of the class')
@click.option('--fields', default='', help='Fields in a format: name:type name:type')
@with_appcontext
def generate_template(class_name, fields):
    """Generates a dynamic dashboard template for a specified class and fields."""
    # Parse fields input into a list of dictionaries
    fields_list = []
    for field in fields.split():
        name, type_ = field.split(':')
        fields_list.append({"name": name, "label": name.capitalize(), "type": type_})

    # Singular form of class_name for display purposes (simple naive approach)
    class_name_singular = class_name[:-1] if class_name.lower().endswith('s') else class_name

    # Setup Jinja2 environment
    env = Environment(
        loader=FileSystemLoader('enferno/templates'),
        autoescape=select_autoescape(['html', 'xml'])
    )

    # Load template
    template = env.get_template('core/dashboard.jinja2')

    # Render template with dynamic values
    rendered_template = template.render(class_name=class_name, class_name_singular=class_name_singular,
                                        fields=fields_list)

    # ASCII border
    border_line = '+' + '-' * 78 + '+'

    # Print the rendered template with ASCII borders
    print(border_line)
    console.print(rendered_template)
    print(border_line)
    print("\nCopy the template between the ASCII lines above.")


@click.command()
@click.option('--class_name', default='Item', help='The name of the class')
@click.option('--fields', default='', help='Optional: Fields in a format: name:type name:type')
@with_appcontext
def generate_api(class_name, fields):
    """Generates Flask view functions for API endpoints of a specified class."""
    # Setup Jinja2 environment
    env = Environment(
        loader=FileSystemLoader('enferno/templates'),
        autoescape=select_autoescape(['html', 'xml'])
    )

    # Load and render the API views template
    template = env.get_template('core/api.jinja2')
    rendered_template = template.render(class_name=class_name)

    # ASCII border for output
    border_line = '+' + '-' * 78 + '+'

    # Print the rendered template with ASCII borders
    print(border_line)
    console.print(rendered_template)
    print(border_line)
    print("\nCopy the API views from the ASCII lines above.")


import click
from jinja2 import Environment, FileSystemLoader, select_autoescape


@click.command()
@click.option('--class_name', prompt=True, help='The name of the class')
@click.option('--fields', prompt=True, help='Describe your fields')
def generate_model(class_name, fields):
    """Generates a Flask model class using OpenAI."""
    client = openai.client
    # Adjust the parsing to accommodate the new format

    sample = open('enferno/templates/core/model.jinja2').read()

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": f"Generate an Flask-SQLAlchemy model class including from_json and to_dict methods, dont import anything, use the following as a sample \n {sample}, no yap"
            },
            {
                "role": "user",
                "content": f"The class name is {class_name}  and fields are describe here: {fields}"
            },

        ],
        temperature=1,
        max_tokens=1024,

        # response_format={"type": "json_object"}
    )

    generated_code = response.choices[0].message.content

    # Print the generated code
    border_line = '+' + '-' * 78 + '+'
    print(border_line)

    console.print(generated_code)
    print(border_line)
    print("\nCopy and paste the model class from the ASCII lines above.")
