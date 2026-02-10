import { AppBar, Toolbar, Typography } from '@mui/material';
import { Science as ScienceIcon } from '@mui/icons-material';

export function Navbar() {
  return (
    <AppBar position="static" sx={{ bgcolor: '#d32f2f' }}>
      <Toolbar>
        <ScienceIcon sx={{ mr: 2 }} />
        <Typography
          variant="h6"
          component="div"
          sx={{ flexGrow: 1, fontWeight: 'bold' }}
        >
          Research Buddy
        </Typography>
      </Toolbar>
    </AppBar>
  );
}
