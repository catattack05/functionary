""" Team serializers """
from rest_framework import serializers

from core.models import Environment, Team


class TeamEnvironmentSerializer(serializers.ModelSerializer):
    """Serializer for listing a Team's environments"""

    class Meta:
        model = Environment
        fields = ["id", "name", "default"]


class TeamSerializer(serializers.ModelSerializer):
    """Basic serializer for the Team model"""

    environments = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = ["id", "name", "environments"]

    def get_environments(self, team):
        """In the context of a request, filters the list of environments down to
        those of the requesting user."""

        request = self.context.get("request")

        # If we are using the serializer outside of the context of a request, do not
        # filter the environments.
        #
        # In the context of a request, if the user is a superuser or has a role on the
        # team itself we do not need to filter the environments.
        if (
            request is None
            or request.user.is_superuser
            or team.user_roles.filter(user=request.user).exists()
        ):
            environments = team.environments.all()
        else:
            environments = team.environments.filter(user_roles__user=request.user)

        return TeamEnvironmentSerializer(environments, many=True).data
