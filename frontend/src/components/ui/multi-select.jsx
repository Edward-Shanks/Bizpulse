import React, { useState, useRef, useEffect } from 'react';
import { X, ChevronDown, Check } from 'lucide-react';
import { Checkbox } from '@/components/ui/checkbox';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

const MultiSelect = ({ 
  options = [], 
  value = [], 
  onChange, 
  placeholder = "Select options...",
  className = "",
  maxHeight = "200px"
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef(null);

  // Add animation styles
  useEffect(() => {
    const styleId = 'multi-select-styles';
    if (!document.getElementById(styleId)) {
      const style = document.createElement('style');
      style.id = styleId;
      style.textContent = `
        @keyframes multiSelectFadeIn {
          from {
            opacity: 0;
            transform: translateY(-4px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .multi-select-dropdown {
          animation: multiSelectFadeIn 0.15s ease-out;
        }
      `;
      document.head.appendChild(style);
    }
  }, []);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const toggleOption = (optionValue) => {
    const newValue = value.includes(optionValue)
      ? value.filter(v => v !== optionValue)
      : [...value, optionValue];
    onChange(newValue);
  };

  const removeOption = (optionValue, e) => {
    e.stopPropagation();
    onChange(value.filter(v => v !== optionValue));
  };

  const selectedOptions = options.filter(opt => value.includes(opt.value));

  return (
    <div ref={containerRef} className={cn("relative w-full", className)}>
      {/* Selected items display */}
      <div
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "min-h-[42px] w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm",
          "flex items-center gap-2 flex-wrap cursor-pointer",
          "hover:border-gray-400 focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500",
          "transition-all shadow-sm"
        )}
      >
        {selectedOptions.length === 0 ? (
          <span className="text-gray-500 py-1">{placeholder}</span>
        ) : (
          <>
            {selectedOptions.map((option) => (
              <span
                key={option.value}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-blue-50 text-blue-700 border border-blue-200 rounded-md text-xs font-medium hover:bg-blue-100 transition-colors"
              >
                {option.label}
                <button
                  type="button"
                  onClick={(e) => removeOption(option.value, e)}
                  className="hover:bg-blue-200 rounded-full p-0.5 transition-colors ml-0.5"
                  aria-label={`Remove ${option.label}`}
                >
                  <X className="w-3 h-3 text-blue-600" />
                </button>
              </span>
            ))}
          </>
        )}
        <ChevronDown className={cn("w-4 h-4 text-gray-500 ml-auto transition-transform flex-shrink-0", isOpen && "transform rotate-180")} />
      </div>

      {/* Dropdown menu */}
      {isOpen && (
        <div
          className={cn(
            "absolute z-50 w-full mt-1.5 rounded-md border border-gray-200 bg-white shadow-xl",
            "overflow-hidden multi-select-dropdown"
          )}
          style={{ maxHeight: `calc(${maxHeight} + 2px)` }}
        >
          <div className="overflow-y-auto py-1" style={{ maxHeight }}>
            {options.length === 0 ? (
              <div className="px-3 py-2 text-sm text-gray-500 text-center">No options available</div>
            ) : (
              options.map((option) => {
                const isSelected = value.includes(option.value);
                return (
                  <div
                    key={option.value}
                    onClick={() => toggleOption(option.value)}
                    className={cn(
                      "flex items-center gap-3 px-3 py-2.5 cursor-pointer transition-colors",
                      "hover:bg-gray-50 active:bg-gray-100",
                      isSelected && "bg-blue-50 hover:bg-blue-100"
                    )}
                  >
                    <Checkbox
                      checked={isSelected}
                      onCheckedChange={() => toggleOption(option.value)}
                      className="pointer-events-none flex-shrink-0"
                    />
                    <span className={cn("text-sm flex-1 text-gray-700", isSelected && "font-medium text-blue-900")}>
                      {option.label}
                    </span>
                    {isSelected && (
                      <Check className="w-4 h-4 text-blue-600 flex-shrink-0" />
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default MultiSelect;

