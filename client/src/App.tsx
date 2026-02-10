import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { SearchPage } from './pages/search';
import { PaperReaderPage } from './pages/paper';

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/search" replace />} />
        {/* <Route path="/register" element={<RegisterPage />} />
        <Route path="/login" element={<LoginPage />} /> */}

        <Route path="/search" element={<SearchPage />} />
        <Route path="/paper/:id" element={<PaperReaderPage />} />
        {/* <Route path="*" element={<Navigate to="/login" replace />} /> */}
      </Routes>
    </BrowserRouter>
  );
}
