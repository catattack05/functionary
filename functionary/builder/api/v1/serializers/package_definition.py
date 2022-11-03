""" Serializers for defining a package """
from rest_framework import serializers

LANGUAGES = [("python", "Python"), ("javascript", "JavaScript")]
PARAMETER_TYPES = [
    ("integer", "Integer"),
    ("string", "String"),
    ("text", "String (Long)"),
    ("float", "Float"),
    ("boolean", "Boolean"),
    ("date", "Date"),
    ("datetime", "Date Time"),
    ("json", "JSON"),
]
RETURN_TYPES = PARAMETER_TYPES[:]


class ParameterOptionSerializer(serializers.Serializer):
    name = serializers.CharField()

    # TODO: This should probably preserve numeric values rather than convert
    #       them to a string
    value = serializers.CharField()


class ParameterSerializer(serializers.Serializer):
    """Serializer for parameter description"""

    name = serializers.CharField()
    display_name = serializers.CharField(required=False)
    description = serializers.CharField(required=False)

    type = serializers.ChoiceField(choices=PARAMETER_TYPES, required=True)

    required = serializers.BooleanField(default=False)
    options = ParameterOptionSerializer(many=True, required=False)

    # TODO: This should probably preserve numeric values rather than convert
    #       them to a string
    default = serializers.CharField(required=False)


class FunctionSerializer(serializers.Serializer):
    """Serializer for function description"""

    name = serializers.CharField()
    display_name = serializers.CharField(required=False)
    summary = serializers.CharField(max_length=128, required=False)
    description = serializers.CharField(required=False)
    variables = serializers.ListField(
        child=serializers.CharField(max_length=256, required=False),
        required=False,
    )
    parameters = ParameterSerializer(many=True)
    return_type = serializers.ChoiceField(choices=RETURN_TYPES, required=False)


class PackageDefinitionSerializer(serializers.Serializer):
    """Serializer for package description"""

    name = serializers.CharField()
    display_name = serializers.CharField(required=False)
    summary = serializers.CharField(max_length=128, required=False)
    description = serializers.CharField(required=False)
    language = serializers.ChoiceField(choices=LANGUAGES, required=False)
    filename = serializers.CharField(required=False)
    environment = serializers.DictField(child=serializers.CharField(), required=False)
    functions = FunctionSerializer(many=True)


class PackageDefinitionWithVersionSerializer(serializers.Serializer):
    """Serializer for full package.yaml"""

    version = serializers.CharField()
    package = PackageDefinitionSerializer()
