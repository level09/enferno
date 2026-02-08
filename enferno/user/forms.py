from quart_security import current_user, verify_password
from quart_security.forms import ChangePasswordForm, RegisterForm
from wtforms import StringField


class ExtendedRegisterForm(RegisterForm):
    name = StringField("Full Name")


class OAuthAwareChangePasswordForm(ChangePasswordForm):
    """Custom change password form that handles OAuth users.

    OAuth users have random passwords they don't know. This form
    skips current password validation for users with OAuth accounts.
    """

    def validate(self, **kwargs):
        if not super().validate(**kwargs):
            return False

        has_usable = getattr(current_user, "has_usable_password", True)

        if has_usable and current_user.password:
            if not self.password.data or not self.password.data.strip():
                self.password.errors.append("Current password is required")
                return False
            if not verify_password(self.password.data, current_user.password):
                self.password.errors.append("Invalid current password")
                return False
            if self.password.data == self.new_password.data:
                self.password.errors.append("New password must be different")
                return False

        return True
