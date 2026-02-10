import {
  Box,
  Typography,
  CircularProgress,
  TextField,
  IconButton,
} from '@mui/material';
import type { ChatMessage, ChunkWithCoords } from '../types/paper';
import {
  AutoAwesome as MagicIcon,
  Send as SendIcon,
} from '@mui/icons-material';
import { useState } from 'react';
import { ChatMessage as ChatMessageComponent } from './message';

interface Props {
  chunk?: ChunkWithCoords;
  chatHistory: ChatMessage[];
  chatLoading: boolean;
  onSend: (input: string) => void;
}

export function ChatArea({ chunk, chatHistory, chatLoading, onSend }: Props) {
  const [input, setInput] = useState('');

  const handleSend = () => {
    setInput('');
    onSend(input);
  };

  if (!chunk) {
    return (
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Typography color="text.secondary">
          Click a text block on the left to start chatting.
        </Typography>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        overflowY: 'scroll',
      }}
    >
      <Box
        sx={{
          p: 2,
        }}
      >
        <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
          <MagicIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
          Chatting about Chunk {chunk.id + 1}
        </Typography>
        <Typography variant="caption" display="block">
          "{chunk.text.substring(0, 250)}..."
        </Typography>
      </Box>

      <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 2 }}>
        {chatHistory.length === 0 && (
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ mt: 4, textAlign: 'center' }}
          >
            Ask anything about this specific section.
          </Typography>
        )}
        {chatHistory.map((message, i) => (
          <ChatMessageComponent key={i} message={message} />
        ))}
        {chatLoading && <CircularProgress size={20} sx={{ ml: 2 }} />}
      </Box>

      <Box sx={{ p: 2, borderTop: '1px solid #eee' }}>
        <TextField
          fullWidth
          size="small"
          placeholder="Ask about this section..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          slotProps={{
            input: {
              endAdornment: (
                <IconButton onClick={() => handleSend()} color="primary">
                  <SendIcon />
                </IconButton>
              ),
            },
          }}
        />
      </Box>
    </Box>
  );
}
