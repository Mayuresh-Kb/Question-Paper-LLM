// src/components/ProgressBar.jsx
import React from 'react';
import { Check, Upload, Settings, Download } from 'lucide-react';
import { useForm } from '../context/formState';

const ProgressBar = () => {
  const { currentStep, goToStep, uploadId, pdfId } = useForm();

  const steps = [
    { number: 1, title: 'Upload Bank', description: 'PDF, DOCX, TXT', icon: Upload, enabled: true },
    { number: 2, title: 'Review & Configure', description: 'Marks & Units', icon: Settings, enabled: Boolean(uploadId) },
    { number: 3, title: 'Review & Download', description: 'Exam Paper', icon: Download, enabled: Boolean(pdfId) },
  ];

  return (
    <div className="w-full max-w-3xl mx-auto mb-8">
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="grid grid-cols-3 gap-3">
          {steps.map((step) => {
            const isCompleted = currentStep > step.number;
            const isCurrent = currentStep === step.number;
            const Icon = step.icon;

            return (
              <button
                key={step.number}
                type="button"
                onClick={() => step.enabled && goToStep(step.number)}
                disabled={!step.enabled}
                className={`flex flex-col sm:flex-row items-center sm:items-start gap-2.5 p-2 rounded text-left transition-colors ${
                  isCurrent
                    ? 'bg-blue-50 text-blue-900'
                    : step.enabled
                    ? 'hover:bg-gray-50 cursor-pointer text-gray-700'
                    : 'opacity-50 cursor-not-allowed text-gray-400'
                }`}
              >
                {/* Step Circle */}
                <div
                  className={`w-8 h-8 rounded flex items-center justify-center font-semibold text-xs shrink-0 ${
                    isCompleted
                      ? 'bg-blue-700 text-white'
                      : isCurrent
                      ? 'bg-blue-700 text-white'
                      : 'bg-gray-100 text-gray-500 border border-gray-300'
                  }`}
                >
                  {isCompleted ? <Check className="w-4 h-4" /> : step.number}
                </div>

                {/* Step Text */}
                <div className="min-w-0 text-center sm:text-left">
                  <span className="text-[10px] font-semibold uppercase text-gray-500 block">
                    Step {step.number}
                  </span>
                  <h4
                    className={`text-xs sm:text-sm font-medium truncate ${
                      isCurrent ? 'text-blue-900 font-semibold' : 'text-gray-900'
                    }`}
                  >
                    {step.title}
                  </h4>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default ProgressBar;