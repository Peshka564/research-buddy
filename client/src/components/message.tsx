import { Box, Paper } from '@mui/material';
import type { ChatMessage } from '../types/paper';
import ReactMarkdown from 'react-markdown';

interface Props {
  message: ChatMessage;
}

export function ChatMessage({ message }: Props) {
  return (
    <Box
      sx={{
        mb: 2,
        textAlign: message.role === 'user' ? 'right' : 'left',
      }}
    >
      <Paper
        sx={{
          display: 'inline-block',
          p: 1.5,
          bgcolor: message.role === 'user' ? '#1976d2' : '#f1f1f1',
          color: message.role === 'user' ? 'white' : 'black',
          maxWidth: '85%',
        }}
      >
        {message.role === 'user' ? (
          message.content
        ) : (
          <ReactMarkdown>{message.content}</ReactMarkdown>
        )}
      </Paper>
    </Box>
  );
}
