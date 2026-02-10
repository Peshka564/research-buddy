export interface SearchResult {
  id: string;
  title: string;
  abstract: string;
  authors: string;
  year: number;
  categories: string;
  similarity_score: number;
}

export interface SearchResponse {
  original_query: string;
  interpreted_intent: string;
  results: SearchResult[];
}
