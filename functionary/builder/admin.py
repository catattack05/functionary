from django.contrib import admin

from builder.models import Build, BuildLog

admin.site.register(Build, admin.ModelAdmin)
admin.site.register(BuildLog, admin.ModelAdmin)
