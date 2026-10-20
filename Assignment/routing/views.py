from datetime import datetime, time

from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import BasicAuthentication

from .models import Edge, Node, RouteHistory
from .serializers import EdgeSerializer, NodeSerializer, ShortestRouteSerializer
from .services import find_shortest_path



class NodeD(APIView):

    def get(self, request):
        nodes = Node.objects.all().values("id", "name")
        return Response(list(nodes), status=status.HTTP_200_OK)

    def post(self, request):
        serializer = NodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        name = serializer.validated_data["name"]

        if not name:
            return Response(
                {"error": "Name is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            node = Node.objects.create(name=name)
        except IntegrityError:
            return Response(
                {"error": "A node with this name already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"id": node.id, "name": node.name},
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request, id):
        try:
            node = Node.objects.get(id=id)
        except Node.DoesNotExist:
            return Response(
                {"error": "Node not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        node.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class EdgeD(APIView):

    def get(self, request):
        edges = Edge.objects.select_related("source", "destination")

        response_data = [
            {
                "id": edge.id,
                "source": edge.source.name,
                "destination": edge.destination.name,
                "latency": edge.latency,
            }
            for edge in edges
        ]

        return Response(response_data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = EdgeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if not data["source"] or not data["destination"]:
            return Response(
                {"error": "Source or destination is missing or both."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if data["source"] == data["destination"]:
            return Response(
                {"error": "Source and destination must be different."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            source = Node.objects.get(name=data["source"])
            destination = Node.objects.get(name=data["destination"])
        except Node.DoesNotExist:
            return Response(
                {"error": "Source or destination node was not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            edge = Edge.objects.create(
                source=source,
                destination=destination,
                latency=data["latency"],
            )
        except IntegrityError:
            return Response(
                {"error": "This edge already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "id": edge.id,
                "source": source.name,
                "destination": destination.name,
                "latency": edge.latency,
            },
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request, id):
        try:
            edge = Edge.objects.get(id=id)
        except Edge.DoesNotExist:
            return Response(
                {"error": "Edge not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        edge.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class shortestPath(APIView):

    def post(self, request):
        serializer = ShortestRouteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            source = Node.objects.get(name=data["source"])
            destination = Node.objects.get(name=data["destination"])
        except Node.DoesNotExist:
            return Response(
                {"error": "Source or destination node was not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        path, total_latency = find_shortest_path(source.name, destination.name)

        if path is None:
            return Response(
                {"error": (f"No path exists between {source.name} and {destination.name}")},
                status=status.HTTP_404_NOT_FOUND,
            )

        RouteHistory.objects.create(
            source=source,
            destination=destination,
            total_latency=total_latency,
            path=path,
        )

        return Response(
            {"total_latency": total_latency, "path": path},
            status=status.HTTP_200_OK,
        )


def get_date_filter(value, end_of_d=False):
    parsed = parse_datetime(value)

    if parsed is None:
        day = parse_date(value)
        if day is None:
            raise ValueError("Use YYYY-MM-DD or an ISO datetime for dates.")
        parsed = datetime.combine(day, time.max if end_of_d else time.min)

    return parsed


class pathHistory(APIView):
    authentication_classes = (BasicAuthentication,)

    def get(self, request):
        filter_criteria = {}

        source = request.query_params.get("source", '')
        destination = request.query_params.get("destination", '')
        date_from = request.query_params.get("date_from", '')
        date_to = request.query_params.get("date_to", '')
        limit_value = request.query_params.get("limit", '')

        if source:
            filter_criteria["source__name"] = source
        if destination:
            filter_criteria["destination__name"] = destination
        try:
            if date_from:
                filter_criteria["created_at__gte"] = get_date_filter(date_from)
            if date_to:
                filter_criteria["created_at__lte"] = get_date_filter(
                    date_to, end_of_d=True
                )
            if date_from and date_to:
                start_date = get_date_filter(date_from)
                end_date = get_date_filter(date_to, end_of_d=True)
                if start_date > end_date:
                    return Response(
                        {"error": "date_from must not be later than date_to."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
        except ValueError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        records = RouteHistory.objects.select_related(
            "source", "destination"
        ).filter(**filter_criteria)

        if limit_value:
            try:
                limit = int(limit_value)
                if limit < 1:
                    raise ValueError
            except ValueError:
                return Response(
                    {"error": "Limit must be a positive integer."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            records = records[:limit]

        response_data = [
            {
                "id": item.id,
                "source": item.source.name if item.source else None,
                "destination": (
                    item.destination.name if item.destination else None
                ),
                "total_latency": item.total_latency,
                "path": item.path,
                "created_at": item.created_at.isoformat(),
            }
            for item in records
        ]
        return Response(response_data, status=status.HTTP_200_OK)