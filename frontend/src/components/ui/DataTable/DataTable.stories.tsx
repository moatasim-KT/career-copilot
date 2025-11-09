
import React from 'react';
import { Meta, Story } from '@storybook/react';
import { DataTable } from './DataTable';
import { ColumnDef } from '@tanstack/react-table';

export default {
  title: 'Components/DataTable',
  component: DataTable,
} as Meta;

const columns: ColumnDef<{ id: number; name: string; value: number }>[] = [
  {
    accessorKey: 'id',
    header: 'ID',
  },
  {
    accessorKey: 'name',
    header: 'Name',
  },
  {
    accessorKey: 'value',
    header: 'Value',
  },
];

const data = [
  { id: 1, name: 'Item 1', value: 10 },
  { id: 2, name: 'Item 2', value: 20 },
  { id: 3, name: 'Item 3', value: 30 },
];

const Template: Story<any> = (args) => <DataTable {...args} />;

export const Default = Template.bind({});
Default.args = {
  columns,
  data,
};

export const WithSorting = Template.bind({});
WithSorting.args = {
  columns,
  data,
};

export const WithFiltering = Template.bind({});
WithFiltering.args = {
  columns,
  data,
};

export const WithPagination = Template.bind({});
WithPagination.args = {
  columns,
  data,
};

export const WithRowSelection = Template.bind({});
WithRowSelection.args = {
  columns,
  data,
};

export const WithExpandableRows = Template.bind({});
WithExpandableRows.args = {
  columns,
  data,
  renderSubComponent: (row) => (
    <div className="p-4 bg-gray-100">
      <p>ID: {row.id}</p>
      <p>Name: {row.name}</p>
      <p>Value: {row.value}</p>
    </div>
  ),
};

export const WithAllFeatures = Template.bind({});
WithAllFeatures.args = {
  columns,
  data,
  renderSubComponent: (row) => (
    <div className="p-4 bg-gray-100">
      <p>ID: {row.id}</p>
      <p>Name: {row.name}</p>
      <p>Value: {row.value}</p>
    </div>
  ),
};
