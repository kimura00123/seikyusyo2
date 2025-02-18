import React from 'react';
import {
  Box,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Alert,
  AlertTitle,
} from '@mui/material';
import ErrorIcon from '@mui/icons-material/Error';
import WarningIcon from '@mui/icons-material/Warning';
import { useDocumentStore } from '../store/documentStore';

export const ValidationResults: React.FC = () => {
  const { validation } = useDocumentStore();

  if (!validation) return null;

  const errors = validation.errors.filter(e => e.severity === 'error');
  const warnings = validation.errors.filter(e => e.severity === 'warning');

  if (validation.is_valid && errors.length === 0 && warnings.length === 0) {
    return (
      <Box sx={{ mt: 2 }}>
        <Alert severity="success">
          <AlertTitle>検証成功</AlertTitle>
          すべての項目が正常です
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ mt: 2 }}>
      <Typography variant="h6" gutterBottom>
        検証結果
      </Typography>
      <Paper variant="outlined" sx={{ p: 2 }}>
        {errors.length > 0 && (
          <Box mb={warnings.length > 0 ? 2 : 0}>
            <Typography variant="subtitle1" color="error" gutterBottom>
              エラー ({errors.length})
            </Typography>
            <List dense>
              {errors.map((error, index) => (
                <ListItem key={`error-${index}`}>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <ErrorIcon color="error" />
                  </ListItemIcon>
                  <ListItemText
                    primary={error.message}
                    secondary={`フィールド: ${error.field}`}
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        )}

        {warnings.length > 0 && (
          <Box>
            <Typography variant="subtitle1" color="warning.main" gutterBottom>
              警告 ({warnings.length})
            </Typography>
            <List dense>
              {warnings.map((warning, index) => (
                <ListItem key={`warning-${index}`}>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <WarningIcon color="warning" />
                  </ListItemIcon>
                  <ListItemText
                    primary={warning.message}
                    secondary={`フィールド: ${warning.field}`}
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        )}
      </Paper>
    </Box>
  );
};
