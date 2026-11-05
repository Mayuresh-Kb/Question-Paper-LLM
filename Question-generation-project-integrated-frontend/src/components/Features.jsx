import React from "react";
import { Zap, Brain, Settings } from "lucide-react";

const Features = () => {
  const features = [
    {
      title: "A Complete Paper Workflow",
      description: "Upload a bank, review the extraction, configure units, and preview your paper.",
      icon: Zap,
    },
    {
      title: "Smart & Balanced",
      description:
        "Prefer a difficulty mix and topic variety using reviewed bank metadata.",
      icon: Brain,
    },
    {
      title: "Flexible Marking",
      description:
        "Set unequal marks per unit, adjust question counts, and replace selected questions.",
      icon: Settings,
    },
  ];

  return (
    <section className="bg-white py-16 border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-12">
          <h2 className="text-3xl font-light text-gray-900 mb-2">
            Why Choose Our Solution
          </h2>
          <p className="text-gray-600">
            Streamline your exam preparation with intelligent automation
          </p>
        </div>
        <div className="grid md:grid-cols-3 gap-8">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <div
                key={index}
                className="bg-white border border-gray-200 rounded-lg p-6 hover:border-gray-300 hover:shadow-sm transition-all"
              >
                <div className="w-12 h-12 bg-blue-50 rounded flex items-center justify-center mb-4">
                  <Icon className="w-6 h-6 text-blue-700" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-sm text-gray-600 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};

export default Features;

