from flask_security import current_user
from flask_security.forms import ChangePasswordForm, RegisterForm, get_message
from flask_security.proxies import _security
from flask_security.utils import verify_password
from wtforms import StringField


class ExtendedRegisterForm(RegisterForm):
    name = StringField("Full Name")


class OAuthAwareChangePasswordForm(ChangePasswordForm):
    """Custom change password form that handles OAuth users.

    OAuth users have random passwords they don't know. This form
    skips current password validation for users with OAuth accounts.
    """

    def validate(self, **kwargs):
        if not super(ChangePasswordForm, self).validate(**kwargs):
            return False

        # Check if user has a usable password (not OAuth-only)
        has_usable = getattr(current_user, "has_usable_password", True)

        if has_usable and current_user.password:
            # User has a password they know - require current password
            if not self.password.data or not self.password.data.strip():
                self.password.errors.append(get_message("PASSWORD_NOT_PROVIDED")[0])
                return False

            self.password.data = _security.password_util.normalize(self.password.data)
            if not verify_password(self.password.data, current_user.password):
                self.password.errors.append(get_message("INVALID_PASSWORD")[0])
                return False
            if self.password.data == self.new_password.data:
                self.password.errors.append(get_message("PASSWORD_IS_THE_SAME")[0])
                return False

        # Validate new password
        pbad, self.new_password.data = _security.password_util.validate(
            self.new_password.data, False, user=current_user
        )
        if pbad:
            self.new_password.errors.extend(pbad)
            return False
        return True


class UserInfoForm:
    pass
