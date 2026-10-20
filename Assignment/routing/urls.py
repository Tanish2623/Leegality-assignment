from django.urls import path

from .views import NodeD, EdgeD, shortestPath, pathHistory

urlpatterns = [
    path("nodes", NodeD.as_view(), name="nodes"),
    path("nodes/<int:id>", NodeD.as_view(), name="node-detail"),
    path("edges", EdgeD.as_view(), name="edges"),
    path("edges/<int:id>", EdgeD.as_view(), name="edge-detail"),
    path("routes/shortest", shortestPath.as_view(), name="shortest-path"),
    path("routes/history", pathHistory.as_view(), name="path-history"),
]
