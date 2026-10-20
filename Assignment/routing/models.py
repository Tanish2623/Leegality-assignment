from django.db import models


class Node(models.Model):
    name = models.CharField(max_length=100, unique=True)

class Edge(models.Model):
    source = models.ForeignKey(Node, on_delete=models.CASCADE, related_name="outgoing_edges")
    destination = models.ForeignKey(Node, on_delete=models.CASCADE, related_name="incoming_edges")
    latency = models.FloatField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["source", "destination"],name="unique_directed_edge"),
            models.CheckConstraint(condition=models.Q(latency__gt=0),name="edge_latency_must_be_positive"),
        ]



class RouteHistory(models.Model):
    source = models.ForeignKey(Node,on_delete=models.SET_NULL,null=True,related_name="routes_started",)
    destination = models.ForeignKey(Node,on_delete=models.SET_NULL,null=True,related_name="routes_ended")
    total_latency = models.FloatField()
    path = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)