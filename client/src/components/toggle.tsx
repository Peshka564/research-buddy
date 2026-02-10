import {
  Paper,
  Typography,
  ToggleButtonGroup,
  ToggleButton,
} from '@mui/material';
import type { ViewMode } from '../types/paper';
import {
  Segment as ViewListIcon,
  Reviews as ChatIcon,
} from '@mui/icons-material';

interface Props {
  viewMode: ViewMode;
  setViewMode: (viewMode: ViewMode) => void;
  isChatDisabled: boolean;
}

export function ToggleView({ viewMode, setViewMode, isChatDisabled }: Props) {
  return (
    <Paper
      elevation={1}
      sx={{
        p: 2,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        zIndex: 10,
        bgcolor: 'white',
      }}
    >
      <Typography variant="subtitle1" fontWeight="bold">
        {viewMode === 'list' ? 'Chunks' : 'Chat'}
      </Typography>

      <ToggleButtonGroup
        value={viewMode}
        exclusive
        onChange={(_, newView) => {
          if (newView != null) {
            setViewMode(newView);
          }
        }}
        size="small"
      >
        <ToggleButton value="list">
          <ViewListIcon sx={{ mr: 1, fontSize: 20 }} />
          List
        </ToggleButton>
        <ToggleButton
          value="chat"
          disabled={isChatDisabled && viewMode === 'list'}
        >
          <ChatIcon sx={{ mr: 1, fontSize: 20 }} />
          Chat
        </ToggleButton>
      </ToggleButtonGroup>
    </Paper>
  );
}
