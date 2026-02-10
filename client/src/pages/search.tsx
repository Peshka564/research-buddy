import { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Typography,
  Container,
  Box,
  Paper,
  InputBase,
  IconButton,
  CssBaseline,
  CircularProgress,
  Button,
} from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';
import { type SearchResult, type SearchResponse } from '../types/search';
import { Navbar } from '../components/navbar';
import { useNavigate } from 'react-router-dom';

export function SearchPage() {
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [error, setError] = useState<string | undefined>();

  const executeSearch = async (query: string) => {
    if (!query.trim()) return;

    setLoading(true);
    setError(undefined);
    try {
      const response = await axios.get<SearchResponse>(
        'http://localhost:5000/smart_search',
        {
          params: {
            query: query,
            k: 5,
          },
        }
      );

      console.log('Search Results:', response.data);
      setResults(response.data.results);
      setError(undefined);
    } catch (error) {
      setError('Error performing search');
    } finally {
      setLoading(false);
    }
  };

  const navigate = useNavigate();

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      if (searchQuery) {
        executeSearch(searchQuery);
      }
    }, 800);

    return () => clearTimeout(delayDebounceFn);
  }, [searchQuery]);

  return (
    <>
      <CssBaseline />
      <Box sx={{ flexGrow: 1, minHeight: '100vh', bgcolor: '#f5f5f5' }}>
        <Navbar />

        <Container
          maxWidth="md"
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            mt: '100px',
          }}
        >
          <Typography
            variant="h4"
            gutterBottom
            sx={{ color: '#555', mb: 4, fontWeight: 500 }}
          >
            Search through ArXiv papers
          </Typography>

          <Paper
            component="form"
            elevation={3}
            sx={{
              p: '2px 4px',
              display: 'flex',
              alignItems: 'center',
              width: '100%',
              maxWidth: 600,
              borderRadius: '50px',
            }}
            onSubmit={e => {
              e.preventDefault();
              executeSearch(searchQuery);
            }}
          >
            <InputBase
              sx={{ ml: 3, flex: 1 }}
              placeholder="Search papers (e.g., 'Papers about retrieval augmented generation')..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
            />

            <Box sx={{ p: '10px' }}>
              {loading && (
                <CircularProgress size={24} sx={{ color: '#d32f2f' }} />
              )}
              <IconButton
                type="button"
                sx={{ color: '#d32f2f' }}
                onClick={() => executeSearch(searchQuery)}
              >
                <SearchIcon />
              </IconButton>
            </Box>
          </Paper>

          {loading && (
            <Typography
              variant="caption"
              sx={{ mt: 2, color: 'text.secondary' }}
            >
              Searching...
            </Typography>
          )}
          {error && (
            <Typography variant="caption" sx={{ mt: 2, color: 'text.error' }}>
              {error}
            </Typography>
          )}
        </Container>
        <Container
          maxWidth="md"
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            mt: '50px',
          }}
        >
          {results.map((paper, index) => (
            <Button
              onClick={() => navigate(`/paper/${paper.id}`)}
              sx={{
                p: 0,
                mb: 2,
                width: '100%',
              }}
            >
              <Paper
                key={index}
                sx={{
                  p: 2,
                  borderLeft: '6px solid #d32f2f',
                  width: '100%',
                }}
              >
                <Typography variant="h6" sx={{ color: '#d32f2f' }}>
                  {paper.title}
                </Typography>
                <Typography variant="subtitle2" color="text.secondary">
                  {paper.year} | {paper.categories} | Score:{' '}
                  {paper.similarity_score.toFixed(2)}
                </Typography>
                <Typography variant="body2" sx={{ mt: 1 }}>
                  {paper.abstract}
                </Typography>
              </Paper>
            </Button>
          ))}
        </Container>
      </Box>
    </>
  );
}
