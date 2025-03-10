import React from 'react';
import { CssBaseline, Container, AppBar, Toolbar, Typography, Box } from '@mui/material';
import { FileUpload } from './components/FileUpload';
import { DetailList } from './components/DetailList';
import { ValidationResults } from './components/ValidationResults';
import { ExcelExportButton } from './components/ExcelExportButton';
import { useDocumentStore } from './store/documentStore';

function App() {
  const { status, error } = useDocumentStore();

  return (
    <>
      <CssBaseline />
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            請求書構造化システム
          </Typography>
          {status === 'completed' && (
            <ExcelExportButton />
          )}
        </Toolbar>
      </AppBar>
      <Container maxWidth="lg">
        <Box sx={{ mt: 4 }}>
          {error && (
            <Typography color="error" mb={2}>
              {error}
            </Typography>
          )}
          <FileUpload />
          {status === 'completed' && (
            <>
              <Typography color="success.main" mt={2} mb={2}>
                処理が完了しました
              </Typography>
              <ValidationResults />
              <DetailList />
            </>
          )}
        </Box>
      </Container>
    </>
  );
}

export default App;
