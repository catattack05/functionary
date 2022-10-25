from drf_spectacular.utils import OpenApiParameter

HEADER_PARAMETERS = [
    OpenApiParameter(
        name="X-Environment-Id",
        type=str,
        location=OpenApiParameter.HEADER,
        description=("ID for the Environment to which this request corresponds"),
    ),
]
