from django.contrib import admin
from django.contrib.auth.models import Group

from core.models import (
    Environment,
    EnvironmentUserRole,
    Function,
    Package,
    Task,
    TaskLog,
    TaskResult,
    Team,
    TeamUserRole,
    User,
    Variable,
)

from .user import UserAdmin

admin.site.register(Environment, admin.ModelAdmin)
admin.site.register(EnvironmentUserRole, admin.ModelAdmin)
admin.site.register(Function, admin.ModelAdmin)
admin.site.register(Package, admin.ModelAdmin)
admin.site.register(Task, admin.ModelAdmin)
admin.site.register(TaskLog, admin.ModelAdmin)
admin.site.register(TaskResult, admin.ModelAdmin)
admin.site.register(Team, admin.ModelAdmin)
admin.site.register(TeamUserRole, admin.ModelAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(Variable, admin.ModelAdmin)
admin.site.unregister(Group)
