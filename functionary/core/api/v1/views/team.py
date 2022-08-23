from rest_framework.viewsets import ReadOnlyModelViewSet

from core.models import Team

from ..serializers import TeamSerializer


class TeamViewSet(ReadOnlyModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer

    def get_queryset(self):
        """Filter Team queryset down to those to which the requesting user is assigned
        a role, either directly or through one of the Team's environments."""

        if self.request.user.is_superuser:
            return self.queryset
        else:
            return (
                self.queryset.filter(environments__user_roles__user=self.request.user)
                | self.queryset.filter(user_roles__user=self.request.user)
            ).distinct()
