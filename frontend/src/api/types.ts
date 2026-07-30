export type JobStatus = "queued" | "running" | "done" | "failed";
export type JobStage = "queued" | "ingest" | "parse" | "graph" | "analyze" | "embed" | "diagram" | "report" | "done";

export interface Job {
  id: string;
  repository_id: string;
  status: JobStatus;
  stage: JobStage;
  progress: number;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface Repository {
  id: string;
  name: string;
  source_type: "git_url" | "zip" | "local";
  created_at: string;
}

export interface FolderTreeNode {
  name: string;
  path: string;
  type: "dir" | "file";
  language?: string;
  loc?: number;
  file_count?: number;
  primary_language?: string | null;
  children?: FolderTreeNode[];
}

export interface RepoSummary {
  total_files: number;
  total_loc: number;
  languages: Record<string, { files: number; loc: number }>;
  primary_language: string | null;
  frameworks: string[];
  package_managers: string[];
  folder_tree: FolderTreeNode;
}

export interface ArchitectureCandidate {
  style: string;
  confidence: number;
  evidence: string[];
}

export interface ArchitectureResult {
  primary_style: string;
  confidence: number;
  evidence: string[];
  all_candidates: ArchitectureCandidate[];
}

export interface DbColumn {
  name: string;
  type: string;
  primary_key: boolean;
  foreign_key: string | null;
}

export interface DbTable {
  name: string;
  orm: string;
  file: string;
  columns: DbColumn[];
}

export interface DatabaseSchema {
  orms_detected: string[];
  tables: DbTable[];
  relationships: { from: string; to: string; via: string }[];
}

export interface ApiEndpoint {
  method: string;
  path: string;
  file: string;
  line: number;
  framework: string;
}

export interface ApiSurface {
  protocols: string[];
  endpoints: ApiEndpoint[];
  endpoint_count: number;
  auth: { detected: boolean; mechanisms: string[] };
}

export interface PatternMatch {
  pattern: string;
  file: string;
  symbol: string | null;
  line: number;
  reason: string;
}

export interface PatternsResult {
  summary: Record<string, number>;
  matches: PatternMatch[];
}

export interface SolidViolation {
  principle: string;
  file: string;
  symbol: string;
  line: number;
  message: string;
}

export interface SolidResult {
  summary: Record<string, number>;
  violations: SolidViolation[];
}

export interface Finding {
  category: string;
  severity: "info" | "low" | "medium" | "high" | "critical";
  file: string;
  message: string;
  line: number;
  symbol: string | null;
}

export interface FindingsResult {
  metrics?: Record<string, number>;
  summary?: Record<string, number>;
  findings: Finding[];
}

export interface ScoreEntry {
  score: number;
  reasoning: string[];
}

export type Scores = Record<string, ScoreEntry>;

export interface AnalysisResultBundle {
  summary: RepoSummary;
  architecture: ArchitectureResult;
  folders: FolderTreeNode;
  database_schema: DatabaseSchema;
  api_surface: ApiSurface;
  patterns: PatternsResult;
  solid: SolidResult;
  quality: FindingsResult;
  security: FindingsResult;
  performance: FindingsResult;
  scores: Scores;
}

export interface DiagramNode {
  id: string;
  type: string;
  data: Record<string, unknown> & { label: string };
}

export interface DiagramEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
  type?: string;
  data?: Record<string, unknown>;
}

export interface DiagramData {
  type: string;
  nodes: DiagramNode[];
  edges: DiagramEdge[];
  truncated: boolean;
}

export interface ChatSource {
  file: string;
  start_line: number | null;
  end_line: number | null;
  symbol: string | null;
}

export interface ChatResponse {
  answer: string;
  sources: ChatSource[];
}

export interface SourceChunk {
  text: string;
  start_line: number | null;
  end_line: number | null;
  symbol: string | null;
}
