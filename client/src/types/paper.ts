export interface ChunkWithCoords {
  id: number;
  page: number;
  bbox: [number, number, number, number]; // [x0, y0, x1, y1]
  text: string;
  cluster_id: number;
}

export interface ChatMessage {
  role: 'user' | 'ai';
  content: string;
  chunkId: number;
}

export type ViewMode = 'list' | 'chat';
