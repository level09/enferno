from enferno.extensions import db
from sqlalchemy import exc

class BaseMixin():

    def save(self, commit=True):
        db.session.add(self)
        if commit:
            try:
                db.session.commit()
                return self
            except exc.SQLAlchemyError as e:
                print(e)
                db.session.rollback()
                return None

    def delete(self, commit=True):
        db.session.delete(self)
        if commit:
            try:
                db.session.commit()
                return self
            except exc.SQLAlchemyError as e:
                print(e)
                db.session.rollback()
                return None
