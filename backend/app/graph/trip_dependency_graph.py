"""Trip Dependency Graph for modeling interconnected travel commitments and tracing cascade impact."""

from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from app.schemas.trip import (
    DisruptionEvent,
    ImpactAnalysisResult,
    ImpactedNodeReport,
    NodeType,
    PriorityLevel,
    TripEdge,
    TripItinerary,
    TripNode,
)


class TripDependencyGraph:
    """
    Models a unified trip itinerary as a Directed Acyclic Graph (DAG):
    - Nodes represent flights, transfers, hotels, and meetings.
    - Directed edges encode temporal & operational dependencies with buffer constraints.
    """

    def __init__(self, itinerary: TripItinerary):
        self.itinerary = itinerary
        self.nodes: Dict[str, TripNode] = {node.id: node for node in itinerary.nodes}
        self.adjacency: Dict[str, List[TripEdge]] = defaultdict(list)
        self.reverse_adjacency: Dict[str, List[TripEdge]] = defaultdict(list)
        for edge in itinerary.edges:
            if edge.source_node_id in self.nodes and edge.target_node_id in self.nodes:
                self.adjacency[edge.source_node_id].append(edge)
                self.reverse_adjacency[edge.target_node_id].append(edge)

    def get_downstream_edges(self, node_id: str) -> List[TripEdge]:
        return self.adjacency.get(node_id, [])

    def get_all_downstream_nodes(self, root_node_id: str) -> List[Tuple[str, List[str], TripEdge]]:
        """Breadth-first traversal returning (node_id, dependency_path, incoming_edge)."""
        visited = {root_node_id}
        queue: deque[Tuple[str, List[str]]] = deque([(root_node_id, [root_node_id])])
        downstream: List[Tuple[str, List[str], TripEdge]] = []

        while queue:
            current_id, path = queue.popleft()
            for edge in self.adjacency.get(current_id, []):
                target_id = edge.target_node_id
                new_path = path + [target_id]
                downstream.append((target_id, new_path, edge))
                if target_id not in visited:
                    visited.add(target_id)
                    queue.append((target_id, new_path))
        return downstream

    def trace_disruption_impact(self, disruption: DisruptionEvent) -> ImpactAnalysisResult:
        """
        Trace downstream cascade impact when a flight or booking node is cancelled or delayed.
        Computes slack minutes, classifies severity (BROKEN / AT_RISK / NEEDS_UPDATE),
        and produces actionable recovery guidance for each affected commitment.
        """
        root_id = disruption.node_id
        root_node = self.nodes.get(root_id)
        if not root_node:
            raise ValueError(f"Node '{root_id}' does not exist in trip '{self.itinerary.id}'")

        reports: Dict[str, ImpactedNodeReport] = {}
        reports[root_id] = ImpactedNodeReport(
            node_id=root_id,
            title=root_node.title,
            node_type=root_node.node_type,
            original_start=root_node.start_time,
            original_end=root_node.end_time,
            impact_level="ROOT_CAUSE",
            recommended_action=(
                "Cancel/refund disrupted leg and rebook primary transport"
                if disruption.disruption_type == "CANCELLATION"
                else f"Absorb {disruption.delay_minutes}m delay or rebook"
            ),
            reason=disruption.reason,
            slack_minutes=0,
            dependency_path=[root_id],
        )

        is_cancelled = disruption.disruption_type == "CANCELLATION"
        effective_root_end: Optional[datetime] = (
            None
            if is_cancelled
            else root_node.end_time + timedelta(minutes=disruption.delay_minutes)
        )

        # Propagate impact through the DAG in BFS order
        node_effective_end: Dict[str, Optional[datetime]] = {root_id: effective_root_end}
        queue: deque[Tuple[str, List[str]]] = deque([(root_id, [root_id])])

        while queue:
            src_id, path = queue.popleft()
            src_report = reports[src_id]
            src_end = node_effective_end.get(src_id)

            for edge in self.adjacency.get(src_id, []):
                tgt_id = edge.target_node_id
                tgt_node = self.nodes[tgt_id]
                new_path = path + [tgt_id]

                slack_minutes = int(
                    (tgt_node.start_time - self.nodes[src_id].end_time).total_seconds() // 60
                )

                # Determine impact status on target node
                if is_cancelled or src_report.impact_level == "BROKEN" or src_end is None:
                    if tgt_node.node_type == NodeType.FLIGHT and edge.is_hard_dependency:
                        impact_level = "BROKEN"
                        action = "Cancel/rebook missed connecting flight"
                        reason = (
                            f"Missed connection: upstream leg {self.nodes[src_id].title} is "
                            f"{'cancelled' if is_cancelled else 'severely disrupted'}."
                        )
                        node_effective_end[tgt_id] = None
                    elif tgt_node.node_type == NodeType.TRANSFER:
                        impact_level = "NEEDS_UPDATE"
                        action = "Reschedule airport pickup to match new arrival flight"
                        reason = (
                            "Airport transfer depends on flight arrival time; "
                            "driver grace period will expire without update."
                        )
                        node_effective_end[tgt_id] = None
                    elif tgt_node.node_type == NodeType.HOTEL:
                        impact_level = "AT_RISK"
                        action = "Notify hotel of late check-in / modify reservation hold"
                        reason = (
                            "Room check-in cutoff (04:00 AM) at risk of no-show cancellation "
                            "if arrival shifts past morning."
                        )
                        node_effective_end[tgt_id] = tgt_node.end_time
                    elif tgt_node.node_type == NodeType.MEETING:
                        impact_level = "AT_RISK"
                        action = "Ensure recovery arrival before 08:45 AM deadline or notify client"
                        reason = (
                            f"CRITICAL commitment at {tgt_node.start_time.strftime('%H:%M')} IST "
                            "cannot be reached under current broken itinerary."
                        )
                        node_effective_end[tgt_id] = tgt_node.end_time
                    else:
                        impact_level = "AT_RISK"
                        action = "Review downstream commitment"
                        reason = f"Depends on disrupted node {src_id}."
                        node_effective_end[tgt_id] = None
                else:
                    # Delay propagation check
                    required_arrival = tgt_node.start_time - timedelta(
                        minutes=edge.min_buffer_minutes
                    )
                    projected_slack = int((tgt_node.start_time - src_end).total_seconds() // 60)
                    slack_minutes = projected_slack
                    if src_end > required_arrival:
                        if tgt_node.node_type == NodeType.FLIGHT and edge.is_hard_dependency:
                            impact_level = "BROKEN"
                            action = "Rebook missed connecting flight"
                            reason = (
                                f"Projected arrival leaves {projected_slack}m (< {edge.min_buffer_minutes}m MCT)."
                            )
                            node_effective_end[tgt_id] = None
                        elif tgt_node.node_type == NodeType.TRANSFER:
                            impact_level = "NEEDS_UPDATE"
                            action = "Adjust pickup time for flight delay"
                            reason = f"Buffer reduced to {projected_slack}m."
                            node_effective_end[tgt_id] = src_end + (
                                tgt_node.end_time - tgt_node.start_time
                            )
                        else:
                            impact_level = "AT_RISK"
                            action = "Monitor arrival buffer / notify stakeholder"
                            reason = f"Arrival buffer drops below required {edge.min_buffer_minutes}m."
                            node_effective_end[tgt_id] = tgt_node.end_time
                    else:
                        impact_level = "UNAFFECTED"
                        action = "No change required"
                        reason = f"Sufficient buffer remains ({projected_slack}m)."
                        node_effective_end[tgt_id] = tgt_node.end_time

                # Keep highest severity if reachable by multiple paths
                severity_rank = {
                    "ROOT_CAUSE": 5,
                    "BROKEN": 4,
                    "AT_RISK": 3,
                    "NEEDS_UPDATE": 2,
                    "UNAFFECTED": 1,
                }
                existing = reports.get(tgt_id)
                if not existing or severity_rank[impact_level] > severity_rank[existing.impact_level]:
                    reports[tgt_id] = ImpactedNodeReport(
                        node_id=tgt_id,
                        title=tgt_node.title,
                        node_type=tgt_node.node_type,
                        original_start=tgt_node.start_time,
                        original_end=tgt_node.end_time,
                        impact_level=impact_level,
                        recommended_action=action,
                        reason=reason,
                        slack_minutes=slack_minutes,
                        dependency_path=new_path,
                    )
                queue.append((tgt_id, new_path))

        # Include any non-reachable nodes as UNAFFECTED
        for node_id, node in self.nodes.items():
            if node_id not in reports:
                reports[node_id] = ImpactedNodeReport(
                    node_id=node_id,
                    title=node.title,
                    node_type=node.node_type,
                    original_start=node.start_time,
                    original_end=node.end_time,
                    impact_level="UNAFFECTED",
                    recommended_action="No change required",
                    reason="Not downstream of disrupted booking.",
                    slack_minutes=999,
                    dependency_path=[node_id],
                )

        ordered_reports = sorted(reports.values(), key=lambda r: r.original_start)
        affected = [
            r for r in ordered_reports if r.impact_level in {"BROKEN", "AT_RISK", "NEEDS_UPDATE"}
        ]
        critical_at_risk = [
            r.title
            for r in affected
            if self.nodes[r.node_id].priority == PriorityLevel.CRITICAL
            or r.node_type in {NodeType.MEETING, NodeType.FLIGHT}
        ]

        summary = (
            f"Disruption on {root_node.title} cascades to {len(affected)} downstream commitment(s): "
            + ", ".join(r.title for r in affected)
            if affected
            else f"Disruption on {root_node.title} has no downstream impact."
        )

        return ImpactAnalysisResult(
            disruption_id=disruption.id,
            trip_id=self.itinerary.id,
            root_node_id=root_id,
            impacted_nodes=ordered_reports,
            total_affected=len(affected),
            critical_commitments_at_risk=critical_at_risk,
            summary=summary,
        )
