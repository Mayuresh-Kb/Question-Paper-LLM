import React from "react";
import { useNavigate } from "react-router-dom";
import { Upload, Settings, Download } from "lucide-react";

const HowItWorks = () => {
  const navigate = useNavigate();

  const steps = [
    {
      number: "1",
      title: "Upload Question Bank",
      description: "Upload one numbered PDF, DOCX, or TXT question bank per unit.",
      icon: Upload,
      clickable: true,
    },
    {
      number: "2",
      title: "Configure Parameters",
      description: "Review questions, choose units and marks, and set difficulty preferences.",
      icon: Settings,
      clickable: false,
    },
    {
      number: "3",
      title: "Generate & Download",
      description: "Preview the PDF, replace questions, and download the final paper.",
      icon: Download,
      clickable: false,
    },
  ];

  return (
    <section id="how-it-works" className="bg-gray-50 py-16 border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-12">
          <h2 className="text-3xl font-light text-gray-900 mb-2">
            How It Works
          </h2>
          <p className="text-gray-600">
            3 Simple Steps to Generate Your Question Paper
          </p>
        </div>
        <div className="relative">
          {/* Connection line */}
          <div className="hidden md:block absolute top-12 left-1/4 right-1/4 h-0.5 bg-gray-200"></div>
          
          <div className="grid md:grid-cols-3 gap-8 relative">
            {steps.map((step, index) => {
              const Icon = step.icon;
              return (
                <div 
                  key={index} 
                  onClick={() => step.clickable && navigate('/upload')}
                  className={`relative ${step.clickable ? 'cursor-pointer group' : ''}`}
                >
                  <div className="flex flex-col items-center text-center">
                    <div className="w-24 h-24 bg-white border-2 border-gray-200 group-hover:border-blue-700 rounded-full flex items-center justify-center mb-4 relative z-10 transition-colors">
                      <Icon className="w-10 h-10 text-blue-700" />
                    </div>
                    <div className="mb-2">
                      <span className="inline-block px-3 py-1 bg-gray-200 group-hover:bg-blue-50 group-hover:text-blue-700 text-gray-700 text-xs font-semibold rounded-full transition-colors">
                        STEP {step.number}
                      </span>
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      {step.title}
                    </h3>
                    <p className="text-sm text-gray-600 leading-relaxed">
                      {step.description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
};

export default HowItWorks;

