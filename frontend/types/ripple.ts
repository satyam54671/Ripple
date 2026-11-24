export type NodeType = "FLIGHT" | "HOTEL" | "TRANSFER" | "MEETING";
export type PriorityLevel = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
export type BookingStatus =
  | "CONFIRMED"
  | "ON_TIME"
  | "DELAYED"
  | "CANCELLED"
  | "MISSED_CONNECTION"
  | "AT_RISK"
  | "REBOOKED"
  | "RESCHEDULED";

export type TripStatus =
  | "ON_TRACK"
  | "DISRUPTED"
  | "AWAITING_APPROVAL"
  | "RECOVERED";

export interface TravelPolicy {
  max_rebooking_budget_inr: number;
  preferred_cabin: string;
  allow_business_upgrade_if_critical: boolean;
  min_connection_minutes: number;
  min_meeting_buffer_minutes: number;
  prioritize_client_meetings: boolean;
}

export interface TripNode {
  id: string;
  node_type: NodeType;
  title: string;
  provider: string;
  booking_reference: string;
  location: string;
  start_time: string;
  end_time: string;
  priority: PriorityLevel;
  status: BookingStatus;
  cost_inr: number;
  metadata: Record<string, unknown>;
}

export interface TripEdge {
  source_node_id: string;
  target_node_id: string;
  dependency_type: string;
  min_buffer_minutes: number;
  is_hard_dependency: boolean;
  description: string;
}

export interface TripItinerary {
  id: string;
  title: string;
  traveller_name: string;
  traveller_email: string;
  origin: string;
  destination: string;
  status: TripStatus;
  policy: TravelPolicy;
  nodes: TripNode[];
  edges: TripEdge[];
}

export interface DisruptionEvent {
  id: string;
  trip_id: string;
  node_id: string;
  disruption_type: "CANCELLATION" | "DELAY" | "MISSED_CONNECTION";
  severity: "CRITICAL" | "HIGH" | "MEDIUM";
  reason: string;
  source: string;
  verified: boolean;
  delay_minutes: number;
  detected_at: string;
}

export interface ImpactedNodeReport {
  node_id: string;
  title: string;
  node_type: NodeType;
  original_start: string;
  original_end: string;
  impact_level: "ROOT_CAUSE" | "BROKEN" | "AT_RISK" | "NEEDS_UPDATE" | "UNAFFECTED";
  recommended_action: string;
  reason: string;
  slack_minutes: number;
  dependency_path: string[];
}

export interface ImpactAnalysisResult {
  disruption_id: string;
  trip_id: string;
  root_node_id: string;
  impacted_nodes: ImpactedNodeReport[];
  total_affected: number;
  critical_commitments_at_risk: string[];
  summary: string;
}

export interface RecoveryActionStep {
  step_order: number;
  action_type: string;
  target_node_id: string;
  provider: string;
  description: string;
  requires_approval: boolean;
  estimated_cost_inr: number;
  inventory_source: "MOCK_INVENTORY" | "LIVE_API";
}

export interface RecoveryOption {
  id: string;
  label: string;
  summary: string;
  route_description: string;
  carrier_codes: string[];
  departure_time: string;
  arrival_time: string;
  additional_cost_inr: number;
  net_cost_after_refund_inr: number;
  stops: number;
  preserves_meeting: boolean;
  preserves_hotel_checkin: boolean;
  is_policy_compliant: boolean;
  meets_deadline: boolean;
  optimizer_score: number;
  rank: number;
  is_recommended: boolean;
  inventory_mode: "MOCK_INVENTORY" | "LIVE_API";
  constraint_notes: string[];
  actions: RecoveryActionStep[];
}

export interface ExecutionActionLog {
  step_order: number;
  action_type: string;
  provider: string;
  target_node_id: string;
  status: "EXECUTED" | "VERIFIED" | "SKIPPED" | "FAILED";
  confirmation_code: string;
  adapter_mode: "MOCK" | "LIVE";
  message: string;
  executed_at: string;
}

export interface WorkflowTraceEntry {
  stage: string;
  agent: string;
  status: "COMPLETED" | "WAITING_APPROVAL" | "FAILED" | "SKIPPED";
  message: string;
  timestamp: string;
  details: Record<string, unknown>;
}

export interface RecoveryWorkflowResponse {
  run_id: string;
  trip_id: string;
  current_stage: string;
  approval_status: "PENDING" | "APPROVED" | "REJECTED" | "EXECUTED";
  disruption: DisruptionEvent | null;
  impact_analysis: ImpactAnalysisResult | null;
  recovery_options: RecoveryOption[];
  recommended_option_id: string | null;
  selected_option_id: string | null;
  execution_logs: ExecutionActionLog[];
  verification_passed: boolean;
  verification_summary: string;
  workflow_trace: WorkflowTraceEntry[];
}

export interface HealthStatus {
  status: string;
  service: string;
  integration_mode: string;
  database_engine: string;
}

export interface MCPToolsResponse {
  server: string;
  tool_count: number;
  tools: Array<{
    name: string;
    description: string;
  }>;
}
