import React, { useCallback } from 'react';
import { Box, Button, Typography, CircularProgress } from '@mui/material';
import { useDropzone } from 'react-dropzone';
import { useDocumentStore } from '../store/documentStore';

export const FileUpload: React.FC = () => {
  const { status, uploadDocument, reset, approvedDetails } = useDocumentStore();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      // ファイルアップロード前に状態をリセット
      reset();
      
      // ファイルをアップロード
      uploadDocument(acceptedFiles[0]);
    }
  }, [uploadDocument, reset]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    multiple: false,
  });

  if (status === 'uploading' || status === 'processing') {
    return (
      <Box
        display="flex"
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
        p={3}
      >
        <CircularProgress />
        <Typography variant="body1" mt={2}>
          {status === 'uploading' ? 'アップロード中...' : '処理中...'}
        </Typography>
      </Box>
    );
  }

  return (
    <Box
      {...getRootProps()}
      sx={{
        border: '2px dashed',
        borderColor: isDragActive ? 'primary.main' : 'grey.300',
        borderRadius: 1,
        p: 3,
        textAlign: 'center',
        cursor: 'pointer',
        '&:hover': {
          borderColor: 'primary.main',
          bgcolor: 'action.hover',
        },
      }}
    >
      <input {...getInputProps()} />
      <Typography variant="body1" mb={2}>
        {isDragActive
          ? 'ファイルをドロップしてください'
          : 'クリックまたはドラッグ&ドロップでPDFファイルをアップロード'}
      </Typography>
      <Button variant="contained" color="primary">
        ファイルを選択
      </Button>
    </Box>
  );
};
