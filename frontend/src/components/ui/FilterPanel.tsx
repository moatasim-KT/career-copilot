
import { useState } from 'react';
import { ChevronDown, Filter } from 'lucide-react';

interface FilterCategory {
  id: string;
  name: string;
  options: string[];
}

export interface FilterPanelProps {
  categories: FilterCategory[];
  onFilterChange: (filters: Record<string, string[]>) => void;
}

export default function FilterPanel({ categories, onFilterChange }: FilterPanelProps) {
  const [openCategories, setOpenCategories] = useState<Record<string, boolean>>({});
  const [selectedFilters, setSelectedFilters] = useState<Record<string, string[]>>({});

  const toggleCategory = (categoryId: string) => {
    setOpenCategories(prev => ({ ...prev, [categoryId]: !prev[categoryId] }));
  };

  const handleFilter = (categoryId: string, option: string) => {
    const newFilters = { ...selectedFilters };
    if (!newFilters[categoryId]) {
      newFilters[categoryId] = [];
    }

    if (newFilters[categoryId].includes(option)) {
      newFilters[categoryId] = newFilters[categoryId].filter(item => item !== option);
    } else {
      newFilters[categoryId].push(option);
    }

    setSelectedFilters(newFilters);
    onFilterChange(newFilters);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Filters</h3>
        <Filter className="w-5 h-5 text-gray-500" />
      </div>
      {categories.map(category => (
        <div key={category.id} className="border-b border-gray-200 py-4">
          <button 
            className="w-full flex items-center justify-between text-left" 
            onClick={() => toggleCategory(category.id)}
          >
            <span className="font-medium text-gray-800">{category.name}</span>
            <ChevronDown 
              className={`w-5 h-5 text-gray-500 transition-transform ${openCategories[category.id] ? 'transform rotate-180' : ''}`} 
            />
          </button>
          {openCategories[category.id] && (
            <div className="mt-4 space-y-2">
              {category.options.map(option => (
                <label key={option} className="flex items-center">
                  <input 
                    type="checkbox" 
                    className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    checked={selectedFilters[category.id]?.includes(option) || false}
                    onChange={() => handleFilter(category.id, option)}
                  />
                  <span className="ml-3 text-sm text-gray-600">{option}</span>
                </label>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
