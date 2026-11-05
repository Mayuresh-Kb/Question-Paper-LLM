import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Menu, X, Home, Upload, Info } from "lucide-react";

const Navbar = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const navItems = [
    { name: "Home", path: "/", icon: Home },
    { name: "Create Paper", path: "/upload", icon: Upload },
    { name: "About", path: "/about", icon: Info },
  ];

  const isActive = (path) => {
    if (path === "/" && location.pathname === "/") return true;
    if (path === "/upload" && (location.pathname === "/upload" || location.pathname === "/configure" || location.pathname === "/download")) return true;
    if (path !== "/" && location.pathname === path) return true;
    return false;
  };

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo and College Info */}
          <Link to="/" className="flex items-center space-x-3">
            <div className="w-9 h-9 bg-blue-700 rounded flex items-center justify-center">
              <span className="text-white text-lg font-semibold">M</span>
            </div>
            <div className="hidden lg:flex flex-col">
              <h1 className="text-sm font-semibold text-gray-900 leading-tight">
                Marathwada Mitra Mandal's College of Engineering
              </h1>
              <p className="text-xs text-gray-600 leading-tight">
                AICTE Approved | NAAC 'A++' | Autonomous | C.O.D.E Club
              </p>
            </div>
            <div className="lg:hidden flex flex-col">
              <h1 className="text-sm font-semibold text-gray-900">MMCOE</h1>
              <p className="text-[11px] text-gray-600">Question Paper Generator</p>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-2">
            {navItems.map((item) => {
              const active = isActive(item.path);
              return (
                <Link
                  key={item.name}
                  to={item.path}
                  className={`px-3 py-2 rounded text-xs font-semibold transition-colors ${
                    active
                      ? "text-blue-700 bg-blue-50"
                      : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                  }`}
                >
                  {item.name}
                </Link>
              );
            })}

            {/* Quick CTA to Upload */}
            <div className="pl-2">
              <button
                onClick={() => navigate("/upload")}
                className="bg-blue-700 hover:bg-blue-800 text-white text-xs font-medium px-4 py-2 rounded transition-colors cursor-pointer"
              >
                Generate Paper
              </button>
            </div>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle navigation menu"
            className="md:hidden p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Menu Dropdown */}
        {mobileMenuOpen && (
          <div className="md:hidden pb-3 pt-2 border-t border-gray-200 space-y-1">
            {navItems.map((item) => {
              const active = isActive(item.path);
              return (
                <Link
                  key={item.name}
                  to={item.path}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`w-full flex items-center px-4 py-2.5 rounded text-sm font-medium transition-colors ${
                    active
                      ? "bg-blue-50 text-blue-700 font-semibold"
                      : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                  }`}
                >
                  {item.name}
                </Link>
              );
            })}
            <div className="pt-2 px-2">
              <button
                onClick={() => {
                  setMobileMenuOpen(false);
                  navigate("/upload");
                }}
                className="w-full bg-blue-700 text-white font-medium py-2.5 px-4 rounded text-sm"
              >
                Start Paper Generation
              </button>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;

