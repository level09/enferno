from enferno.extensions import db


class BaseMixin(object):

    def save(self, commit=True):
        try:
            db.session.add(self)
            if commit:
                db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            return None

    def delete(self, commit=True):
        try:
            db.session.delete(self)
            if commit:
                db.session.commit()
            return self
        except Exception as e:
            db.session.rollback()
            return None
