import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, X, Search } from 'lucide-react';

const MultiSelectFilter = ({ label, options = [], selectedValues = [], onChange, placeholder = 'Select...' }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleToggle = (value) => {
    const newSelected = selectedValues.includes(value)
      ? selectedValues.filter(v => v !== value)
      : [...selectedValues, value];
    onChange(newSelected);
  };

  const handleClear = (e) => {
    e.stopPropagation();
    onChange([]);
  };

  const handleSelectAll = (e) => {
    e.stopPropagation();
    if (selectedValues.length === options.length) {
      onChange([]);
    } else {
      onChange(options);
    }
  };

  const displayText = selectedValues.length === 0 
    ? placeholder 
    : selectedValues.length === 1 
    ? selectedValues[0] 
    : `${selectedValues.length} selected`;

  // Filter options based on search query
  const filteredOptions = options.filter(option =>
    option.toString().toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Reset search when dropdown closes
  useEffect(() => {
    if (!isOpen) {
      setSearchQuery('');
    }
  }, [isOpen]);

  return (
    <div className="relative" ref={dropdownRef}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      )}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-3 py-2 bg-white border border-gray-300 rounded-lg hover:border-gray-400 transition text-sm"
      >
        <span className={`truncate ${selectedValues.length === 0 ? 'text-gray-500' : 'text-gray-900'}`}>
          {displayText}
        </span>
        <div className="flex items-center gap-1">
          {selectedValues.length > 0 && (
            <div
              onClick={handleClear}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  handleClear(e);
                }
              }}
              role="button"
              tabIndex={0}
              className="p-0.5 hover:bg-gray-200 rounded transition cursor-pointer focus:outline-none focus:ring-2 focus:ring-gray-400"
              aria-label="Clear selection"
            >
              <X className="w-4 h-4 text-gray-500" />
            </div>
          )}
          <ChevronDown className={`w-4 h-4 text-gray-500 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </div>
      </button>

      {isOpen && (
        <div className="absolute z-50 mt-1 w-full bg-white border border-gray-300 rounded-lg shadow-lg max-h-64 overflow-hidden flex flex-col">
          {/* Search Input */}
          <div className="sticky top-0 bg-gray-50 border-b border-gray-200 p-2">
            <div className="relative">
              <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onClick={(e) => e.stopPropagation()}
                className="w-full pl-8 pr-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                autoFocus
              />
            </div>
          </div>
          
          {/* Select All Button */}
          <div className="sticky top-[41px] bg-gray-50 border-b border-gray-200 p-2">
            <button
              onClick={handleSelectAll}
              className="w-full text-left px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-100 rounded transition"
            >
              {selectedValues.length === filteredOptions.length && filteredOptions.length > 0 ? '✓ Deselect All' : 'Select All'}
            </button>
          </div>
          
          {/* Options List */}
          <div className="overflow-y-auto flex-1 p-1">
            {filteredOptions.length > 0 ? (
              filteredOptions.map((option) => (
                <label
                  key={option}
                  className="flex items-center gap-2 px-3 py-2 hover:bg-gray-50 rounded cursor-pointer transition"
                >
                  <input
                    type="checkbox"
                    checked={selectedValues.includes(option)}
                    onChange={() => handleToggle(option)}
                    className="w-4 h-4 text-amber-600 border-gray-300 rounded focus:ring-amber-500"
                  />
                  <span className="text-sm text-gray-700">{option}</span>
                </label>
              ))
            ) : (
              <div className="px-3 py-2 text-sm text-gray-500 text-center">
                No options found
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default MultiSelectFilter;
