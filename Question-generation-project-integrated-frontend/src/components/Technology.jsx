import React from "react";

const Technology = () => {
  const features = [
    "AI-Powered Algorithms",
    "Robust Architecture",
    "User-Centric Design",
  ];

  const stats = [
    { label: "Input", level: "PDF, DOCX, TXT", width: "100%" },
    { label: "Selection", level: "Local or Gemini-assisted", width: "100%" },
    { label: "Output", level: "Reviewed PDF", width: "100%" },
  ];

  return (
    <section className="bg-white py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Built With Modern Technology
          </h2>
        </div>
        <div className="grid md:grid-cols-2 gap-16 items-center">
          <div>
            <ul className="space-y-4">
              {features.map((feature, index) => (
                <li key={index} className="flex items-center text-lg">
                  <svg
                    className="w-6 h-6 text-blue-600 mr-3"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  <span className="text-gray-700 font-medium">{feature}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="space-y-6">
            {stats.map((stat, index) => (
              <div key={index}>
                <div className="flex justify-between mb-2">
                  <span className="text-gray-700 font-medium">
                    {stat.label}
                  </span>
                  <span className="text-blue-600 font-semibold">
                    {stat.level}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className="bg-blue-600 h-3 rounded-full transition-all"
                    style={{ width: stat.width }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

export default Technology;
