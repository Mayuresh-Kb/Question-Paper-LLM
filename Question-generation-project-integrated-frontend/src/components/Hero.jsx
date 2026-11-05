import React from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Check } from "lucide-react";

const Hero = () => {
  const navigate = useNavigate();

  return (
    <section className="bg-white pt-20 pb-16 border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          
          {/* Left Column */}
          <div>
            <div className="inline-block px-3 py-1 bg-blue-50 text-blue-700 text-xs font-semibold rounded mb-4">
              Marathwada Mitra Mandal's College of Engineering
            </div>

            <h1 className="text-4xl sm:text-5xl font-light text-gray-900 mb-4 leading-tight">
              Automated Question Paper Generator
            </h1>

            <p className="text-lg text-gray-600 mb-8 leading-relaxed font-light">
              Transform hours of manual work into minutes with our intelligent
              question paper generation system. Built for educators, designed
              for efficiency.
            </p>

            <div className="flex flex-wrap gap-3">
              <button 
                onClick={() => navigate('/upload')}
                className="inline-flex items-center gap-2 bg-blue-700 hover:bg-blue-800 text-white px-6 py-3 rounded font-medium text-sm transition-colors cursor-pointer"
              >
                <span>Get started</span>
                <ArrowRight className="w-4 h-4" />
              </button>
              
              <button 
                onClick={() => navigate('/about')}
                className="border border-gray-300 text-gray-700 hover:bg-gray-50 hover:border-gray-400 px-6 py-3 rounded font-medium text-sm transition-colors cursor-pointer"
              >
                Learn more
              </button>
            </div>
          </div>

          {/* Right Statistics Card */}
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-8">
            <div className="space-y-8">
              <div>
                <h3 className="text-xs font-semibold text-gray-900 uppercase tracking-wider mb-4">
                  From bank to examination
                </h3>
              </div>

              <div className="space-y-6">
                <div className="border-l-2 border-blue-700 pl-4">
                  <div className="text-xs text-gray-600 mb-1">Supported bank formats</div>
                  <div className="text-3xl font-light text-gray-900">3 formats</div>
                </div>

                <div className="border-l-2 border-blue-700 pl-4">
                  <div className="text-xs text-gray-600 mb-1">Selection methods</div>
                  <div className="text-3xl font-light text-gray-900">3 methods</div>
                </div>

                <div className="border-l-2 border-blue-700 pl-4">
                  <div className="text-xs text-gray-600 mb-1">Question review</div>
                  <div className="text-3xl font-light text-gray-900">Before export</div>
                </div>
              </div>

              <div className="pt-6 border-t border-gray-200">
                <div className="flex items-center gap-2 text-xs text-gray-600">
                  <div className="w-4 h-4 rounded-full bg-blue-50 text-blue-700 flex items-center justify-center">
                    <Check className="w-3 h-3" />
                  </div>
                  <span>Random and Balanced selection work without an API key</span>
                </div>
              </div>

            </div>
          </div>

        </div>
      </div>
    </section>
  );
};

export default Hero;

