
import { ChevronLeft, ChevronRight } from 'lucide-react';

export interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export default function Pagination({ currentPage, totalPages, onPageChange }: PaginationProps) {
  const handlePrevious = () => {
    if (currentPage > 1) {
      onPageChange(currentPage - 1);
    }
  };

  const handleNext = () => {
    if (currentPage < totalPages) {
      onPageChange(currentPage + 1);
    }
  };

  const pageNumbers = [];
  for (let i = 1; i <= totalPages; i++) {
    pageNumbers.push(i);
  }

  return (
    <div className="flex items-center justify-between">
      <button 
        onClick={handlePrevious} 
        disabled={currentPage === 1}
        className="flex items-center px-4 py-2 text-sm font-medium text-gray-600 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
      >
        <ChevronLeft className="w-5 h-5 mr-2" />
        Previous
      </button>
      <div className="hidden md:flex">
        {pageNumbers.map(number => (
          <button 
            key={number} 
            onClick={() => onPageChange(number)} 
            className={`px-4 py-2 text-sm font-medium ${currentPage === number ? 'text-blue-600 bg-blue-50 border-blue-500' : 'text-gray-600 bg-white border-gray-300'} border rounded-md mx-1 hover:bg-gray-50`}
          >
            {number}
          </button>
        ))}
      </div>
      <button 
        onClick={handleNext} 
        disabled={currentPage === totalPages}
        className="flex items-center px-4 py-2 text-sm font-medium text-gray-600 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
      >
        Next
        <ChevronRight className="w-5 h-5 ml-2" />
      </button>
    </div>
  );
}
