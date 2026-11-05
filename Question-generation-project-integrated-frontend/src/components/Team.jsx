import React from "react";
import { useNavigate } from "react-router-dom";
import { Users, ArrowRight } from "lucide-react";

const Team = () => {
  const navigate = useNavigate();

  return (
    <section className="bg-gray-50 py-16 border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center">
              <Users className="w-8 h-8 text-blue-700" />
            </div>
          </div>
          <h2 className="text-3xl font-light text-gray-900 mb-4">
            Developed by C.O.D.E Club
          </h2>
          <p className="text-gray-600 mb-8 max-w-2xl mx-auto leading-relaxed">
            This innovative solution is crafted by students of the Department of
            Computer Engineering at Marathwada Mitra Mandal's College of
            Engineering.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <button 
              onClick={() => navigate('/upload')}
              className="inline-flex items-center gap-2 bg-blue-700 hover:bg-blue-800 text-white px-6 py-2.5 rounded font-medium text-sm transition-colors cursor-pointer"
            >
              <span>Get Started</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button 
              onClick={() => navigate('/about')}
              className="inline-flex items-center gap-2 border-2 border-blue-700 text-blue-700 px-6 py-2.5 rounded font-medium text-sm hover:bg-blue-50 transition-colors cursor-pointer"
            >
              <span>Meet the Team</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Team;

