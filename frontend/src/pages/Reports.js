import React, { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import axios from 'axios';
import { API, useAuth } from '@/App';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Download, FileText } from 'lucide-react';
import { toast } from 'sonner';
import { useTheme } from '@/contexts/ThemeContext';

const Reports = () => {
  const { token } = useAuth();
  const { theme } = useTheme();
  const [filters, setFilters] = useState(null);
  const [selectedFilters, setSelectedFilters] = useState({});
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(null);

  useEffect(() => {
    fetchFilters();
  }, []);

  const fetchFilters = async () => {
    try {
      const response = await axios.get(`${API}/filters/options`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setFilters(response.data);
    } catch (error) {
      toast.error('Failed to load filter options');
    } finally {
      setLoading(false);
    }
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
      if (selectedFilters.year) params.append('years', selectedFilters.year);
      if (selectedFilters.business) params.append('businesses', selectedFilters.business);
      if (selectedFilters.brand) params.append('brands', selectedFilters.brand);
      if (selectedFilters.channel) params.append('channels', selectedFilters.channel);
      if (selectedFilters.category) params.append('categories', selectedFilters.category);
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
      toast.error(error.response?.data?.detail || 'Failed to generate report');
    } finally {
      setGenerating(false);
    }
  };

  const handlePredefinedReport = async (reportType, reportName) => {
    setGeneratingReport(reportType);
    try {
      const params = new URLSearchParams();
      
      // Add basic filters that apply to all reports
      if (selectedFilters.year) params.append('years', selectedFilters.year);
      if (selectedFilters.business) params.append('businesses', selectedFilters.business);
      
      // Add report-specific filters
      if (reportType === 'customer-performance' && selectedFilters.channel) {
        params.append('channels', selectedFilters.channel);
      }
      if (reportType === 'brand-analysis' && selectedFilters.brand) {
        params.append('brands', selectedFilters.brand);
      }
      if (reportType === 'category-insights' && selectedFilters.category) {
        params.append('categories', selectedFilters.category);
      }

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
      toast.error(error.response?.data?.detail || `Failed to generate ${reportName}`);
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

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {/* Year Filter */}
            <div>
              <label className="text-gray-700 dark:text-gray-300 text-sm mb-2 block font-medium">Year</label>
              <Select onValueChange={(value) => setSelectedFilters({ ...selectedFilters, year: value })}>
                <SelectTrigger className="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600">
                  <SelectValue placeholder="Select Year" />
                </SelectTrigger>
                <SelectContent>
                  {(filters?.years || []).map((year) => (
                    <SelectItem key={year} value={year.toString()}>
                      {year}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Business Filter */}
            <div>
              <label className="text-gray-700 dark:text-gray-300 text-sm mb-2 block font-medium">Business</label>
              <Select onValueChange={(value) => setSelectedFilters({ ...selectedFilters, business: value })}>
                <SelectTrigger className="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600">
                  <SelectValue placeholder="Select Business" />
                </SelectTrigger>
                <SelectContent>
                  {(filters?.businesses || []).map((business) => (
                    <SelectItem key={business} value={business}>
                      {business}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Brand Filter */}
            <div>
              <label className="text-gray-700 dark:text-gray-300 text-sm mb-2 block font-medium">Brand</label>
              <Select onValueChange={(value) => setSelectedFilters({ ...selectedFilters, brand: value })}>
                <SelectTrigger className="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600">
                  <SelectValue placeholder="Select Brand" />
                </SelectTrigger>
                <SelectContent>
                  {(filters?.brands || []).map((brand) => (
                    <SelectItem key={brand} value={brand}>
                      {brand}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Channel Filter */}
            <div>
              <label className="text-gray-700 dark:text-gray-300 text-sm mb-2 block font-medium">Channel</label>
              <Select onValueChange={(value) => setSelectedFilters({ ...selectedFilters, channel: value })}>
                <SelectTrigger className="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600">
                  <SelectValue placeholder="Select Channel" />
                </SelectTrigger>
                <SelectContent>
                  {(filters?.channels || []).map((channel) => (
                    <SelectItem key={channel} value={channel}>
                      {channel}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Category Filter */}
            <div>
              <label className="text-gray-700 dark:text-gray-300 text-sm mb-2 block font-medium">Category</label>
              <Select onValueChange={(value) => setSelectedFilters({ ...selectedFilters, category: value })}>
                <SelectTrigger className="bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600">
                  <SelectValue placeholder="Select Category" />
                </SelectTrigger>
                <SelectContent>
                  {(filters?.categories || []).map((category) => (
                    <SelectItem key={category} value={category}>
                      {category}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
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