import React from "react";
import { Link } from "react-router-dom";
import { MapPin, Code } from "lucide-react";

const Footer = () => {
  return (
    <footer className="bg-white border-t border-gray-200 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          
          {/* Col 1: Brand */}
          <div className="md:col-span-1 space-y-3">
            <Link to="/" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-blue-700 rounded flex items-center justify-center">
                <span className="text-white text-sm font-semibold">M</span>
              </div>
              <span className="font-semibold text-gray-900">MMCOE</span>
            </Link>
            <div className="flex items-start gap-2 text-sm text-gray-600">
              <MapPin className="w-4 h-4 mt-0.5 shrink-0 text-gray-500" />
              <span>Pune, Maharashtra</span>
            </div>
          </div>
          
          {/* Col 2: Navigation */}
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-3">Navigation</h4>
            <ul className="space-y-2">
              <li>
                <Link to="/" className="text-sm text-gray-600 hover:text-blue-700 transition-colors">
                  Home
                </Link>
              </li>
              <li>
                <Link to="/upload" className="text-sm text-gray-600 hover:text-blue-700 transition-colors">
                  Create Paper
                </Link>
              </li>
              <li>
                <Link to="/about" className="text-sm text-gray-600 hover:text-blue-700 transition-colors">
                  About Us
                </Link>
              </li>
            </ul>
          </div>
          
          {/* Col 3: Resources */}
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-3">Resources</h4>
            <ul className="space-y-2">
              <li>
                <a href="/#how-it-works" className="text-sm text-gray-600 hover:text-blue-700 transition-colors">
                  How it Works
                </a>
              </li>
              <li>
                <Link to="/about" className="text-sm text-gray-600 hover:text-blue-700 transition-colors">
                  C.O.D.E Club
                </Link>
              </li>
            </ul>
          </div>
          
          {/* Col 4: Developed By */}
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-3">Developed By</h4>
            <div className="flex items-start gap-2 text-sm text-gray-600">
              <Code className="w-4 h-4 mt-0.5 shrink-0 text-gray-500" />
              <div>
                <p>Department of Computer Engineering</p>
                <p className="font-medium text-gray-900">C.O.D.E Club</p>
              </div>
            </div>
          </div>
        </div>
        
        {/* Bottom Bar */}
        <div className="border-t border-gray-200 pt-6 flex flex-col md:flex-row justify-between items-center gap-4 text-xs text-gray-600">
          <p>© {new Date().getFullYear()} Marathwada Mitra Mandal's College of Engineering. All rights reserved.</p>
          <div className="flex gap-4">
            <Link to="/about" className="hover:text-blue-700 transition-colors">About Us</Link>
            <Link to="/upload" className="hover:text-blue-700 transition-colors">Generate Paper</Link>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;

