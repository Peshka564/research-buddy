import { useEffect, useState } from 'react';
import axios from 'axios';
import { Box, Grid, Button, Typography } from '@mui/material';
import type { ChatMessage, ChunkWithCoords } from '../types/paper';
import { useNavigate, useParams } from 'react-router-dom';
import { PdfOverlay } from '../components/pdf-preview';
import { Navbar } from '../components/navbar';
import { Chunk } from '../components/chunk';
import { ChatArea } from '../components/chat';
import { ToggleView } from '../components/toggle';

export function PaperReaderPage() {
  const { id: arxivId } = useParams();

  const [viewMode, setViewMode] = useState<'list' | 'chat'>('list');

  const [activeChunk, setActiveChunk] = useState<ChunkWithCoords | null>(null);
  const [chunks, setChunks] = useState<ChunkWithCoords[]>([]);

  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [chatLoading, setChatLoading] = useState(false);

  const navigate = useNavigate();

  useEffect(() => {
    if (!arxivId) {
      return;
    }
    axios
      .get(`http://localhost:5000/process_paper_with_coords/${arxivId}`)
      .then(res => setChunks(res.data.chunks))
      .catch(err => console.error(err));
  }, [arxivId]);

  const handleChunkSelect = (chunk: ChunkWithCoords) => {
    if (chunk.id === activeChunk?.id) return;

    setActiveChunk(chunk);
    setViewMode('list');

    // Wait for the DOM to load
    setTimeout(() => {
      const element = document.getElementById(`chunk-card-${chunk.id}`);
      if (element) {
        element.scrollIntoView({
          behavior: 'smooth',
          block: 'center',
        });
      }
    }, 100);
  };

  const handleSend = async (message: string) => {
    if (!message.trim() || !activeChunk) return;

    const newMessage: ChatMessage = {
      role: 'user',
      content: message,
      chunkId: activeChunk.id,
    };
    setChatHistory([...chatHistory, newMessage]);
    setChatLoading(true);

    try {
      const res = await axios.post('http://localhost:5000/chat_with_chunk', {
        chunk_text: activeChunk.text,
        question: message,
        history: chatHistory,
      });

      setChatHistory(prev => [
        ...prev,
        { role: 'ai', content: res.data.answer, chunkId: activeChunk.id },
      ]);
    } catch (err) {
      console.error(err);
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <Box
      sx={{
        height: '97vh',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      <Navbar>
        <Button sx={{ color: '#fff' }} onClick={() => navigate('/search')}>
          Back to Search
        </Button>
      </Navbar>

      <Grid container spacing={1} sx={{ overflow: 'hidden', height: '100%' }}>
        {arxivId && (
          <Grid size={6.5} sx={{ height: '100%', overflowY: 'auto' }}>
            <PdfOverlay
              pdfUrl={`https://arxiv.org/pdf/${arxivId}`}
              onChunkSelect={handleChunkSelect}
              chunks={chunks}
            />
          </Grid>
        )}

        <Grid
          size={5.5}
          sx={{
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            bgcolor: '#f5f5f5',
            minHeight: 0,
          }}
        >
          {activeChunk ? (
            <>
              {/* 1. The Active Chunk Display (Fixed at top, scrollable if text is huge) */}
              {/* <Box
                sx={{
                  p: 3,
                  bgcolor: '#fff',
                  borderBottom: '1px solid #ddd',
                  boxShadow: '0 4px 6px -4px rgba(0,0,0,0.1)',
                  maxHeight: '40vh', // Don't let the chunk take up the whole screen
                  overflowY: 'auto',
                }}
              >
                <Typography
                  variant="overline"
                  color="text.secondary"
                  fontWeight="bold"
                >
                  Selected Context
                </Typography>
                <Chunk
                  chunk={activeChunk}
                  isActive={true}
                  onSelect={() => {}} // No-op since it's already selected
                />
              </Box> */}

              {/* 2. The Chat Area (Fills remaining space) */}
              <Box
                sx={{
                  flexGrow: 1,
                  overflow: 'hidden',
                  display: 'flex',
                  flexDirection: 'column',
                }}
              >
                <ChatArea
                  chunk={activeChunk}
                  chatHistory={chatHistory}
                  chatLoading={chatLoading}
                  onSend={handleSend}
                />
              </Box>
            </>
          ) : (
            /* Empty State */
            // <Box
            //   sx={{
            //     height: '100%',
            //     display: 'flex',
            //     flexDirection: 'column',
            //     justifyContent: 'center',
            //     alignItems: 'center',
            //     color: 'text.secondary',
            //     p: 4,
            //     textAlign: 'center',
            //   }}
            // >
            //   <Paper
            //     elevation={0}
            //     sx={{
            //       p: 4,
            //       bgcolor: 'transparent',
            //       display: 'flex',
            //       flexDirection: 'column',
            //       alignItems: 'center',
            //     }}
            //   >
            //     <TouchAppIcon sx={{ fontSize: 60, mb: 2, color: '#ccc' }} />
            //     <Typography variant="h6" gutterBottom>
            //       No Context Selected
            //     </Typography>
            //     <Typography variant="body2">
            //       Click on any highlighted box in the PDF on the left
            //       <br />
            //       to start chatting with that specific section.
            //     </Typography>
            //   </Paper>
            // </Box>
            <></>
          )}
        </Grid>

        {/* We also render the chunks with summarization for easy chatting */}
        {/* <Grid
          size={5.5}
          sx={{ height: '100%', overflowY: 'auto', p: 4, bgcolor: '#fafafa' }}
        >
          <ToggleView
            viewMode={viewMode}
            setViewMode={setViewMode}
            isChatDisabled={!activeChunk}
          />

          <Box
            sx={{ flexGrow: 1, overflowY: 'auto', p: 0, position: 'relative' }}
          >
            {viewMode === 'list' && (
              <Box sx={{ p: 2 }}>
                {chunks.map(chunk => (
                  <div id={`chunk-card-${chunk.id}`} key={chunk.id}>
                    <Chunk
                      chunk={chunk}
                      onSelect={handleChunkSelect}
                      isActive={activeChunk?.id === chunk.id}
                    />
                  </div>
                ))}
              </Box>
            )}

            {viewMode === 'chat' && (
              <ChatArea
                chatHistory={chatHistory}
                chatLoading={chatLoading}
                onSend={input => handleSend(input)}
              />
            )}
          </Box>
        </Grid> */}
      </Grid>
    </Box>
  );
}
