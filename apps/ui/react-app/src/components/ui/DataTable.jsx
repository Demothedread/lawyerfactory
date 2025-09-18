// DataTable component for displaying tabular data with sorting, filtering, and pagination
import React, { useState, useMemo } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Paper,
  TextField,
  Box,
  TablePagination,
  Chip,
  IconButton,
  Tooltip
} from '@mui/material';
import { Search, FilterList, Sort } from '@mui/icons-material';

const DataTable = ({
  data,
  columns,
  title,
  searchable = true,
  sortable = true,
  paginated = true,
  rowsPerPageOptions = [5, 10, 25, 50],
  defaultRowsPerPage = 10,
  onRowClick,
  actions
}) => {
  const [order, setOrder] = useState('asc');
  const [orderBy, setOrderBy] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(defaultRowsPerPage);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({});

  // Filter and search data
  const filteredData = useMemo(() => {
    let filtered = data;

    // Apply search
    if (searchTerm) {
      filtered = filtered.filter(row =>
        columns.some(column =>
          String(row[column.field] || '').toLowerCase().includes(searchTerm.toLowerCase())
        )
      );
    }

    // Apply filters
    Object.entries(filters).forEach(([field, value]) => {
      if (value) {
        filtered = filtered.filter(row =>
          String(row[field] || '').toLowerCase().includes(value.toLowerCase())
        );
      }
    });

    return filtered;
  }, [data, searchTerm, filters, columns]);

  // Sort data
  const sortedData = useMemo(() => {
    if (!orderBy) return filteredData;

    return [...filteredData].sort((a, b) => {
      const aValue = a[orderBy];
      const bValue = b[orderBy];

      if (aValue < bValue) return order === 'asc' ? -1 : 1;
      if (aValue > bValue) return order === 'asc' ? 1 : -1;
      return 0;
    });
  }, [filteredData, order, orderBy]);

  // Paginate data
  const paginatedData = useMemo(() => {
    if (!paginated) return sortedData;
    return sortedData.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);
  }, [sortedData, page, rowsPerPage, paginated]);

  const handleRequestSort = (property) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({
      ...prev,
      [field]: value
    }));
    setPage(0);
  };

  const renderCell = (row, column) => {
    const value = row[column.field];

    if (column.render) {
      return column.render(value, row);
    }

    if (column.type === 'chip' && Array.isArray(value)) {
      return (
        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
          {value.map((item, index) => (
            <Chip key={index} label={item} size="small" variant="outlined" />
          ))}
        </Box>
      );
    }

    if (column.type === 'boolean') {
      return (
        <Chip
          label={value ? 'Yes' : 'No'}
          color={value ? 'success' : 'default'}
          size="small"
        />
      );
    }

    return String(value || '');
  };

  return (
    <Paper sx={{ width: '100%', mb: 2 }}>
      <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        {title && <h3 style={{ margin: 0 }}>{title}</h3>}
        {searchable && (
          <TextField
            variant="outlined"
            size="small"
            placeholder="Search..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: <Search sx={{ mr: 1, color: 'action.active' }} />
            }}
            sx={{ minWidth: 250 }}
          />
        )}
      </Box>

      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              {columns.map((column) => (
                <TableCell
                  key={column.field}
                  sortDirection={orderBy === column.field ? order : false}
                  sx={{ fontWeight: 'bold' }}
                >
                  {sortable && column.sortable !== false ? (
                    <TableSortLabel
                      active={orderBy === column.field}
                      direction={orderBy === column.field ? order : 'asc'}
                      onClick={() => handleRequestSort(column.field)}
                    >
                      {column.headerName}
                    </TableSortLabel>
                  ) : (
                    column.headerName
                  )}
                  {column.filterable && (
                    <TextField
                      size="small"
                      placeholder={`Filter ${column.headerName}`}
                      value={filters[column.field] || ''}
                      onChange={(e) => handleFilterChange(column.field, e.target.value)}
                      sx={{ ml: 1, width: 120 }}
                    />
                  )}
                </TableCell>
              ))}
              {actions && <TableCell sx={{ fontWeight: 'bold' }}>Actions</TableCell>}
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedData.map((row, index) => (
              <TableRow
                key={row.id || index}
                hover
                onClick={() => onRowClick && onRowClick(row)}
                sx={{ cursor: onRowClick ? 'pointer' : 'default' }}
              >
                {columns.map((column) => (
                  <TableCell key={column.field}>
                    {renderCell(row, column)}
                  </TableCell>
                ))}
                {actions && (
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      {actions.map((action, actionIndex) => (
                        <Tooltip key={actionIndex} title={action.tooltip || ''}>
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              action.onClick(row);
                            }}
                            color={action.color || 'primary'}
                          >
                            {action.icon}
                          </IconButton>
                        </Tooltip>
                      ))}
                    </Box>
                  </TableCell>
                )}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {paginated && (
        <TablePagination
          component="div"
          count={sortedData.length}
          page={page}
          onPageChange={handleChangePage}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          rowsPerPageOptions={rowsPerPageOptions}
        />
      )}
    </Paper>
  );
};

export default DataTable;