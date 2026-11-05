import React from "react";

const Metrics = () => {
  const metrics = [
    { value: "3", label: "Input Formats", sublabel: "PDF, DOCX and TXT" },
    { value: "2", label: "Alternatives per Unit", sublabel: "Validated marks totals" },
    { value: "Local", label: "Selection Available", sublabel: "No API key needed" },
    { value: "PDF", label: "Preview & Export", sublabel: "Review before use" },
  ];

  return (
    <section className="bg-gray-50 py-12 border-y border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {metrics.map((metric, index) => (
            <div key={index} className="text-center">
              <div className="text-4xl font-light text-gray-900 mb-1">
                {metric.value}
              </div>
              <div className="text-sm font-semibold text-gray-900 mb-1">
                {metric.label}
              </div>
              <div className="text-xs text-gray-600">
                {metric.sublabel}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Metrics;

