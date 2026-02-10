import { Box } from '@mui/material';
import type { ChunkWithCoords } from '../types/paper';
import { getClusterColor } from '../utils/color';

interface Props {
  scale: number;
  chunk: ChunkWithCoords;
  onChunkSelect: (c: ChunkWithCoords) => void;
}

export function ChunkEmbedded({ chunk, scale, onChunkSelect }: Props) {
  const [x0, y0, x1, y1] = chunk.bbox;
  const baseColor = getClusterColor(chunk.cluster_id, 0.2);
  const hoverColor = getClusterColor(chunk.cluster_id, 0.4);
  const borderColor = getClusterColor(chunk.cluster_id, 0.8);
  return (
    <Box
      key={chunk.id}
      onClick={() => onChunkSelect(chunk)}
      sx={{
        position: 'absolute',
        left: x0 * scale - 10,
        top: y0 * scale - 15,
        width: (x1 - x0) * scale + 10,
        height: (y1 - y0) * scale + 10,
        backgroundColor: baseColor,
        border: `1px solid ${borderColor}`,
        cursor: 'pointer',
        zIndex: 10,
        transition: 'background-color 0.2s',
        '&:hover': {
          backgroundColor: hoverColor,
        },
      }}
      className="hover-highlight"
    />
  );
}
