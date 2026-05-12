from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)

admin.site.site_header = _("Teodoro Administration")
admin.site.site_title = _("Teodoro Admin")
admin.site.index_title = _("Welcome to Teodoro Administration")

admin.site.unregister(BlacklistedToken)
admin.site.unregister(OutstandingToken)
