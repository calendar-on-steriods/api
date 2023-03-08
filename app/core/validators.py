from django.db.utils import IntegrityError
from django.utils.translation import gettext_lazy as _

from core import models


def validate_phone_is_unique(phone):
    """Checks if phone is unique"""

    is_phone = models.User.objects.filter(phone_number=phone).exists()
    if phone != "" and is_phone:
        raise IntegrityError(_("This Phone Number Exists"))
    else:
        return phone
