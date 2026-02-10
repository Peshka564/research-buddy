import { Box, Button, Chip, Paper, Typography } from '@mui/material';
import type { ChunkWithCoords } from '../types/paper';
import { getClusterColor } from '../utils/color';

interface Props {
  chunk: ChunkWithCoords;
  onSelect: (chunk: ChunkWithCoords) => void;
  isActive: boolean;
}

export function Chunk({ chunk, onSelect, isActive }: Props) {
  const baseColor = getClusterColor(chunk.cluster_id, 0.2);
  const borderColor = getClusterColor(chunk.cluster_id, 0.8);

  return (
    <Button onClick={() => onSelect(chunk)}>
      <Paper
        key={chunk.id}
        elevation={isActive ? 4 : 1}
        sx={{
          p: 2,
          mb: 2,
          cursor: 'pointer',
          borderLeft: `6px solid ${borderColor}`,
          bgcolor: isActive ? '#fff' : 'rgba(255,255,255,0.7)',
          transition: 'all 0.2s',
          '&:hover': { transform: 'translateX(5px)' },
        }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Chip
            label={`Chunk ${chunk.cluster_id + 1}`}
            size="small"
            sx={{
              bgcolor: baseColor,
              fontWeight: 'bold',
            }}
          />
          <Typography variant="caption" color="text.secondary">
            Page {chunk.page}
          </Typography>
        </Box>
        <Typography
          variant="body2"
          component="div"
          sx={{
            color: 'text.primary',
            lineHeight: 1.6,
            fontSize: '0.9rem',
          }}
        >
          {chunk.text}
        </Typography>
      </Paper>
    </Button>
  );
}
