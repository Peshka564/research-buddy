import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { SearchPage } from './pages/search';

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/search" replace />} />
        {/* <Route path="/register" element={<RegisterPage />} />
        <Route path="/login" element={<LoginPage />} /> */}

        <Route path="/search" element={<SearchPage />} />
        {/* <Route
          path="/create-workflow"
          element={
            <AuthGuard>
              <ReactFlowProvider>
                <Layout>
                  <WorkflowPage allNodes={allNodes} />
                </Layout>
              </ReactFlowProvider>
            </AuthGuard>
          }
        /> */}
        {/* <Route path="*" element={<Navigate to="/login" replace />} /> */}
      </Routes>
    </BrowserRouter>
  );
}
