/** Wire views from the authenticated API. All strings and structured values are data. */
import type { Mode } from './api';
export interface Run {
  id: string;
  mode: Mode;
  state: string;
  objective: string;
  result: string | null;
  error: string | null;
  metadata: Record<string, unknown>;
  pending_tool: unknown;
  tool_count: number;
  created_at: string;
  updated_at: string;
  steps?: { state: string; summary: string; created_at: string }[];
}
export interface Approval {
  id: string;
  run_id: string;
  status: string;
  operation: unknown;
  operation_hash: string;
  expires_at: string;
}
export interface Project {
  id: string;
  kind: 'REGISTERED_CODE_PROJECT';
}
export interface ArtifactSummary {
  artifact_id: string;
  status: string;
}
