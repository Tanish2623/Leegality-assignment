from rest_framework import serializers


class NodeSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)


class EdgeSerializer(serializers.Serializer):
    source = serializers.CharField(max_length=100)
    destination = serializers.CharField(max_length=100)
    latency = serializers.FloatField(min_value=0)

    def validate_latency(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Latency must be greater than zero."
            )
        return value


class ShortestRouteSerializer(serializers.Serializer):
    source = serializers.CharField(max_length=100)
    destination = serializers.CharField(max_length=100)
