import React from "react";
import { Bot, BarChart3, FolderOpen, FileText, FileDown, GitBranch, Lock, Cloud } from "lucide-react";

const Capabilities = () => {
  const capabilities = [
    { icon: Bot, title: "Optional Gemini" },
    { icon: BarChart3, title: "Bloom Summary" },
    { icon: FolderOpen, title: "Multi-Format" },
    { icon: FileText, title: "Exam Presets" },
    { icon: FileDown, title: "PDF Export" },
    { icon: GitBranch, title: "Question Review" },
    { icon: Lock, title: "Session Access" },
    { icon: Cloud, title: "Refresh Recovery" },
  ];

  return (
    <section className="bg-white py-16 border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-12">
          <h2 className="text-3xl font-light text-gray-900 mb-2">
            Comprehensive Capabilities
          </h2>
          <p className="text-gray-600">
            Everything you need in one platform
          </p>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {capabilities.map((capability, index) => {
            const Icon = capability.icon;
            return (
              <div
                key={index}
                className="bg-white border border-gray-200 rounded-lg p-5 text-center hover:border-gray-300 hover:shadow-sm transition-all"
              >
                <div className="flex justify-center mb-3">
                  <div className="w-10 h-10 bg-gray-50 rounded-full flex items-center justify-center">
                    <Icon className="w-5 h-5 text-gray-700" />
                  </div>
                </div>
                <h3 className="text-sm font-semibold text-gray-900">
                  {capability.title}
                </h3>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};

export default Capabilities;

