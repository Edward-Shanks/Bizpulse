import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import axios from 'axios';
import { API, useAuth } from '@/App';
import { Button } from '@/components/ui/button';
import MultiSelectFilter from '@/components/MultiSelectFilter';
import { Download, FileText, X } from 'lucide-react';
import { toast } from 'sonner';
import { useTheme } from '@/contexts/ThemeContext';

const Reports = () => {
  const { token } = useAuth();
  const { theme } = useTheme();
  const [filters, setFilters] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(null);

  // Multi-select filter states
  const [selectedYears, setSelectedYears] = useState([]);
  const [selectedMonths, setSelectedMonths] = useState([]);
  const [selectedBusinesses, setSelectedBusinesses] = useState([]);
  const [selectedChannels, setSelectedChannels] = useState([]);
  const [selectedBrands, setSelectedBrands] = useState([]);
  const [selectedCategories, setSelectedCategories] = useState([]);

  // Fetch dynamic filters whenever any filter changes
  useEffect(() => {
    if (!token) return;
    fetchDynamicFilters();
  }, [token, selectedYears, selectedMonths, selectedBusinesses, selectedChannels, selectedBrands, selectedCategories]);

  const fetchDynamicFilters = async () => {
    try {
      // Build query params with current filter selections for dynamic filtering
      const params = new URLSearchParams();
      if (selectedYears.length) params.set('years', selectedYears.join(','));
      if (selectedMonths.length) params.set('months', selectedMonths.join(','));
      if (selectedBusinesses.length) params.set('businesses', selectedBusinesses.join(','));
      if (selectedChannels.length) params.set('channels', selectedChannels.join(','));
      if (selectedBrands.length) params.set('brands', selectedBrands.join(','));
      if (selectedCategories.length) params.set('categories', selectedCategories.join(','));

      const url = `${API}/filters/options${params.toString() ? `?${params.toString()}` : ''}`;
      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const newFilters = response.data;
      setFilters(newFilters);

      // Remove invalid selections (selections that no longer exist in the filtered options)
      if (selectedYears.length > 0) {
        const validYears = selectedYears.filter(y => newFilters.years.includes(y));
        if (validYears.length !== selectedYears.length) setSelectedYears(validYears);
      }
      if (selectedMonths.length > 0) {
        const validMonths = selectedMonths.filter(m => newFilters.months.includes(m));
        if (validMonths.length !== selectedMonths.length) setSelectedMonths(validMonths);
      }
      if (selectedBusinesses.length > 0) {
        const validBusinesses = selectedBusinesses.filter(b => newFilters.businesses.includes(b));
        if (validBusinesses.length !== selectedBusinesses.length) setSelectedBusinesses(validBusinesses);
      }
      if (selectedChannels.length > 0) {
        const validChannels = selectedChannels.filter(c => newFilters.channels.includes(c));
        if (validChannels.length !== selectedChannels.length) setSelectedChannels(validChannels);
      }
      if (selectedBrands.length > 0) {
        const validBrands = selectedBrands.filter(b => newFilters.brands.includes(b));
        if (validBrands.length !== selectedBrands.length) setSelectedBrands(validBrands);
      }
      if (selectedCategories.length > 0) {
        const validCategories = selectedCategories.filter(c => newFilters.categories.includes(c));
        if (validCategories.length !== selectedCategories.length) setSelectedCategories(validCategories);
      }
    } catch (error) {
      console.error('Failed to load filters', error);
      toast.error('Failed to load filter options');
      setFilters({ years: [], months: [], businesses: [], channels: [], brands: [], categories: [] });
    } finally {
      setLoading(false);
    }
  };

  const handleClearFilters = () => {
    setSelectedYears([]);
    setSelectedMonths([]);
    setSelectedBusinesses([]);
    setSelectedChannels([]);
    setSelectedBrands([]);
    setSelectedCategories([]);
    toast.success('Filters cleared');
  };

  const downloadFile = (blob, filename) => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  const handleGenerateReport = async () => {
    setGenerating(true);
    try {
      // Build query parameters
      const params = new URLSearchParams();
      if (selectedYears.length) params.append('years', selectedYears.join(','));
      if (selectedMonths.length) params.append('months', selectedMonths.join(','));
      if (selectedBusinesses.length) params.append('businesses', selectedBusinesses.join(','));
      if (selectedChannels.length) params.append('channels', selectedChannels.join(','));
      if (selectedBrands.length) params.append('brands', selectedBrands.join(','));
      if (selectedCategories.length) params.append('categories', selectedCategories.join(','));
      params.append('format', 'excel');

      const response = await axios.get(`${API}/reports/generate?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });

      // Extract filename from Content-Disposition header or use default
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'custom_report.xlsx';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/i);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      downloadFile(response.data, filename);
      toast.success('Report generated successfully!');
    } catch (error) {
      console.error('Error generating report:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to generate report';
      
      // Show more helpful error for empty data
      if (errorMessage.includes('No data found')) {
        toast.error(errorMessage, { duration: 5000 });
      } else {
        toast.error(errorMessage);
      }
    } finally {
      setGenerating(false);
    }
  };

  const handlePredefinedReport = async (reportType, reportName) => {
    setGeneratingReport(reportType);
    try {
      const params = new URLSearchParams();
      
      // Add all filters
      if (selectedYears.length) params.append('years', selectedYears.join(','));
      if (selectedMonths.length) params.append('months', selectedMonths.join(','));
      if (selectedBusinesses.length) params.append('businesses', selectedBusinesses.join(','));
      if (selectedChannels.length) params.append('channels', selectedChannels.join(','));
      if (selectedBrands.length) params.append('brands', selectedBrands.join(','));
      if (selectedCategories.length) params.append('categories', selectedCategories.join(','));

      const response = await axios.get(`${API}/reports/${reportType}?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });

      const contentDisposition = response.headers['content-disposition'];
      let filename = `${reportType}.xlsx`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/i);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      downloadFile(response.data, filename);
      toast.success(`${reportName} downloaded successfully!`);
    } catch (error) {
      console.error(`Error generating ${reportName}:`, error);
      const errorMessage = error.response?.data?.detail || `Failed to generate ${reportName}`;
      
      // Show more helpful error for empty data
      if (errorMessage.includes('No data found')) {
        toast.error(errorMessage, { duration: 5000 });
      } else {
        toast.error(errorMessage);
      }
    } finally {
      setGeneratingReport(null);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">Loading reports...</p>
          </div>
        </div>
      </Layout>
    );
  };

  return (
    <Layout>
      <div className="space-y-6" data-testid="reports-page">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100" style={{ fontFamily: 'Space Grotesk' }}>
            Reports
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">Generate and download custom reports</p>
        </div>

        {/* Report Generator */}
        <div 
          className="p-8 rounded-[10px] bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700"
          style={theme === 'dark' 
            ? {
                background: 'linear-gradient(180deg, #1e293b 0%, #334155 100%)',
                border: '1px solid rgba(255, 255, 255, 0.1)'
              }
            : {
                background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
                border: '1px solid rgba(0, 0, 0, 0.1)'
              }
          }
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-blue-50 rounded-lg">
              <FileText className="w-6 h-6 text-blue-600" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100" style={{ fontFamily: 'Space Grotesk' }}>
              Report Generator
            </h2>
          </div>

          {/* Dynamic Multi-Select Filters */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
            <MultiSelectFilter
              label="Year"
              options={filters?.years || []}
              selectedValues={selectedYears}
              onChange={setSelectedYears}
              placeholder="All Years"
            />
            <MultiSelectFilter
              label="Month"
              options={filters?.months || []}
              selectedValues={selectedMonths}
              onChange={setSelectedMonths}
              placeholder="All Months"
            />
            <MultiSelectFilter
              label="Business"
              options={filters?.businesses || []}
              selectedValues={selectedBusinesses}
              onChange={setSelectedBusinesses}
              placeholder="All Businesses"
            />
            <MultiSelectFilter
              label="Channel"
              options={filters?.channels || []}
              selectedValues={selectedChannels}
              onChange={setSelectedChannels}
              placeholder="All Channels"
            />
            <MultiSelectFilter
              label="Brand"
              options={filters?.brands || []}
              selectedValues={selectedBrands}
              onChange={setSelectedBrands}
              placeholder="All Brands"
            />
            <MultiSelectFilter
              label="Category"
              options={filters?.categories || []}
              selectedValues={selectedCategories}
              onChange={setSelectedCategories}
              placeholder="All Categories"
            />
          </div>

          {/* Filter Info and Clear Button */}
          <div className="flex items-center justify-between mb-6">
            <div className="text-sm text-gray-600 dark:text-gray-400">
              {(selectedYears.length + selectedMonths.length + selectedBusinesses.length + 
                selectedChannels.length + selectedBrands.length + selectedCategories.length) > 0 ? (
                <span>
                  {selectedYears.length + selectedMonths.length + selectedBusinesses.length + 
                   selectedChannels.length + selectedBrands.length + selectedCategories.length} filter(s) applied
                </span>
              ) : (
                <span>No filters applied - showing all data</span>
              )}
            </div>
            {(selectedYears.length + selectedMonths.length + selectedBusinesses.length + 
              selectedChannels.length + selectedBrands.length + selectedCategories.length) > 0 && (
              <Button
                onClick={handleClearFilters}
                variant="outline"
                size="sm"
                className="text-xs"
              >
                <X className="mr-1 w-3 h-3" />
                Clear Filters
              </Button>
            )}
          </div>

          <Button
            onClick={handleGenerateReport}
            className="w-full md:w-auto text-white hover:opacity-90 disabled:opacity-50"
            style={{ backgroundColor: '#184464' }}
            data-testid="generate-report-button"
            disabled={generating}
          >
            {generating ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                Generating...
              </>
            ) : (
              <>
                <Download className="mr-2 w-5 h-5" />
                Generate Report
              </>
            )}
          </Button>
        </div>

        {/* Pre-defined Reports */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4" style={{ fontFamily: 'Space Grotesk' }}>
            Pre-defined Reports
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              { name: 'Executive Summary Report', type: 'executive-summary' },
              { name: 'Customer Performance Report', type: 'customer-performance' },
              { name: 'Brand Analysis Report', type: 'brand-analysis' },
              { name: 'Category Insights Report', type: 'category-insights' },
              { name: 'YoY Comparison Report', type: 'yoy-comparison' },
              { name: 'Monthly Trends Report', type: 'monthly-trends' }
            ].map((report) => {
              const isGenerating = generatingReport === report.type;
              return (
                <div
                  key={report.type}
                  className={`p-6 cursor-pointer hover:shadow-lg transition rounded-[10px] bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 ${isGenerating ? 'opacity-60' : ''}`}
                  style={theme === 'dark' 
                    ? {
                        background: 'linear-gradient(180deg, #1e293b 0%, #334155 100%)',
                        border: '1px solid rgba(255, 255, 255, 0.1)'
                      }
                    : {
                        background: 'linear-gradient(180deg, #F6FAFF 0%, #AAB8CC 100%)',
                        border: '1px solid rgba(0, 0, 0, 0.1)'
                      }
                  }
                  onClick={() => !isGenerating && handlePredefinedReport(report.type, report.name)}
                >
                  {isGenerating ? (
                    <div className="flex items-center justify-center mb-3">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    </div>
                  ) : (
                    <FileText className="w-8 h-8 text-blue-600 mb-3" />
                  )}
                  <h3 className="text-gray-900 dark:text-gray-100 font-semibold mb-2">{report.name}</h3>
                  <p className="text-gray-600 dark:text-gray-400 text-sm">
                    {isGenerating ? 'Generating report...' : 'Download pre-configured report'}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Reports;