""" Task serializers """
from django.core.exceptions import ValidationError
from rest_framework import serializers

from core.models import Function, Task


class TaskSerializer(serializers.ModelSerializer):
    """Basic serializer for the Task model"""

    class Meta:
        model = Task
        fields = "__all__"


class TaskCreateByIdSerializer(serializers.ModelSerializer):
    """Serializer for creating a Task using the function id"""

    class Meta:
        model = Task
        fields = ["function", "parameters"]

    def create(self, validated_data):
        """Custom create that calls clean() on the task instance"""

        try:
            Task(**validated_data).clean()
        except ValidationError as exc:
            raise serializers.ValidationError(serializers.as_serializer_error(exc))

        return super().create(validated_data)


class TaskCreateByNameSerializer(serializers.ModelSerializer):
    """Serializer for creating a Task using the function and package name"""

    function_name = serializers.CharField()
    package_name = serializers.CharField()

    class Meta:
        model = Task
        fields = ["function_name", "package_name", "parameters"]

    def create(self, validated_data):
        """Custom create that calls clean() on the task instance"""
        # pop here to remove fields that are not part of the Task model
        function_name = validated_data.pop("function_name")
        package_name = validated_data.pop("package_name")

        try:
            validated_data["function"] = Function.objects.get(
                name=function_name,
                package__name=package_name,
                package__environment=validated_data["environment"],
            )
        except Function.DoesNotExist:
            raise serializers.ValidationError(
                f"No function {function_name} found for package {package_name}"
            )

        try:
            Task(**validated_data).clean()
        except ValidationError as exc:
            raise serializers.ValidationError(exc.message)

        return super().create(validated_data)


class TaskCreateResponseSerializer(serializers.ModelSerializer):
    """Serializer for returning the task id after creation"""

    class Meta:
        model = Task
        fields = ["id"]


class TaskResultSerializer(serializers.ModelSerializer):
    """Basic serializer for the TaskResult model"""

    # SerializerMethodField is used because the actual data type of the result varies
    result = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ["result"]

    def get_result(self, task: Task):
        return task.result
