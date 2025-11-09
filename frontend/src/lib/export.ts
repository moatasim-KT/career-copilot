
export function exportToCSV<T>(data: T[], columns: (keyof T)[], fileName: string) {
  const header = columns.join(',');
  const rows = data.map((row) => {
    return columns
      .map((col) => {
        let value = row[col];
        if (typeof value === 'string') {
          value = `"${value.replace(/"/g, '""')}"`;
        }
        return value;
      })
      .join(',');
  });

  const csv = [header, ...rows].join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${fileName}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}
