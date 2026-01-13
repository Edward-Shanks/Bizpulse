import React from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Filter } from 'lucide-react';

const FilterBar = ({ filters, selectedFilters, onFilterChange }) => {
  return (
    <div className="professional-card p-4 mb-6 bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
      <div className="flex items-center gap-3 mb-3">
        <Filter className="w-4 h-4 text-blue-600 dark:text-blue-400" />
        <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Filters</h3>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {/* Year Filter */}
        <div>
          <label className="text-gray-700 dark:text-gray-300 text-xs mb-1 block font-medium">Year</label>
          <Select value={selectedFilters.year} onValueChange={(value) => onFilterChange('year', value)}>
            <SelectTrigger className="h-9 text-xs bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600">
              <SelectValue placeholder="All" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Years</SelectItem>
              {(filters?.years || []).map((year) => (
                <SelectItem key={year} value={year.toString()}>
                  {year}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Month Filter */}
        <div>
          <label className="text-gray-700 dark:text-gray-300 text-xs mb-1 block font-medium">Month</label>
          <Select value={selectedFilters.month} onValueChange={(value) => onFilterChange('month', value)}>
            <SelectTrigger className="h-9 text-xs bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600">
              <SelectValue placeholder="All" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Months</SelectItem>
              {(filters?.months || []).map((month) => (
                <SelectItem key={month} value={month}>
                  {month}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Business Filter */}
        <div>
          <label className="text-gray-700 dark:text-gray-300 text-xs mb-1 block font-medium">Business</label>
          <Select value={selectedFilters.business} onValueChange={(value) => onFilterChange('business', value)}>
            <SelectTrigger className="h-9 text-xs bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600">
              <SelectValue placeholder="All" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Businesses</SelectItem>
              {(filters?.businesses || []).map((business) => (
                <SelectItem key={business} value={business}>
                  {business}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Channel Filter */}
        <div>
          <label className="text-gray-700 dark:text-gray-300 text-xs mb-1 block font-medium">Channel</label>
          <Select value={selectedFilters.channel} onValueChange={(value) => onFilterChange('channel', value)}>
            <SelectTrigger className="h-9 text-xs bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600">
              <SelectValue placeholder="All" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Channels</SelectItem>
              {(filters?.channels || []).map((channel) => (
                <SelectItem key={channel} value={channel}>
                  {channel}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Brand Filter */}
        <div>
          <label className="text-gray-700 dark:text-gray-300 text-xs mb-1 block font-medium">Brand</label>
          <Select value={selectedFilters.brand} onValueChange={(value) => onFilterChange('brand', value)}>
            <SelectTrigger className="h-9 text-xs bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600">
              <SelectValue placeholder="All" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Brands</SelectItem>
              {(filters?.brands || []).map((brand) => (
                <SelectItem key={brand} value={brand}>
                  {brand}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Category Filter */}
        <div>
          <label className="text-gray-700 dark:text-gray-300 text-xs mb-1 block font-medium">Category</label>
          <Select value={selectedFilters.category} onValueChange={(value) => onFilterChange('category', value)}>
            <SelectTrigger className="h-9 text-xs bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600">
              <SelectValue placeholder="All" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Categories</SelectItem>
              {(filters?.categories || []).map((category) => (
                <SelectItem key={category} value={category}>
                  {category}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
    </div>
  );
};

export default FilterBar;