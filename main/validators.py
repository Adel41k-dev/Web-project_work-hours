import re
from django.core.exceptions import ValidationError

class StrongPasswordValidator:
    def validate(self, password, user=None):
        if not re.search(r'[A-Za-z]', password):
            raise ValidationError("The password must contain at least one letter")

        if not re.search(r'\d', password):
            raise ValidationError("The password must contain at least one digit")

        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
            raise ValidationError("The password must contain a special character")

    def get_help_text(self):
        return "The password must contain letters, numbers, and special characters"



class NotSimilarToOldPasswordValidator:
    def validate(self, password, user=None):
        if user and user.check_password(password):
            raise ValidationError("The new password must not match the old one")

    def get_help_text(self):
        return "The password must not match the previous one"