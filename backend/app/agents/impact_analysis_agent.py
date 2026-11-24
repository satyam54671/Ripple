"""Impact Analysis Agent: traces cascading downstream failures using TripDependencyGraph."""

from app.graph.trip_dependency_graph import TripDependencyGraph
from app.schemas.trip import DisruptionEvent, ImpactAnalysisResult, TripItinerary


class ImpactAnalysisAgent:
    """Evaluates how a verified disruption propagates to connections, transfers, hotels, and meetings."""

    def analyze(
        self, itinerary: TripItinerary, disruption: DisruptionEvent
    ) -> ImpactAnalysisResult:
        graph = TripDependencyGraph(itinerary)
        return graph.trace_disruption_impact(disruption)
