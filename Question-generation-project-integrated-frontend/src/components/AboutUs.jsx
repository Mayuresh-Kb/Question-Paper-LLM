import React from "react";
import { useNavigate } from "react-router-dom";
import { Briefcase, Lightbulb, Users, FileText, BookOpen, MessageCircle, ArrowRight } from "lucide-react";

const AboutUs = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-white">

      {/* Hero Section */}
      <section className="bg-white pt-20 pb-16 border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="inline-block px-3 py-1 bg-blue-50 text-blue-700 text-xs font-semibold rounded mb-4">
            Department of Computer Engineering
          </div>
          <h1 className="text-4xl sm:text-5xl font-light text-gray-900 mb-4">About C.O.D.E</h1>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto font-light leading-relaxed">
            The Community of Development and Engineering — Where Innovation Meets Academic Excellence
          </p>
        </div>
      </section>

      {/* Who We Are Section */}
      <section className="bg-white py-16 border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-2 gap-16 items-start">
            <div>
              <h2 className="text-3xl font-light text-gray-900 mb-6">
                Who We Are
              </h2>
              <div className="text-gray-600 leading-relaxed space-y-4 text-sm sm:text-base font-light">
                <p>
                  <strong className="text-gray-900 font-medium">
                    C.O.D.E (Community of Development and Engineering)
                  </strong>{" "}
                  is the official technical club of the Computer Engineering
                  Department at Marathwada Mitra Mandal's College of
                  Engineering, Pune.
                </p>
                <p>
                  We are a vibrant community dedicated to fostering innovation,
                  technical excellence, and collaborative learning among
                  students passionate about technology and software development.
                </p>
                <p>
                  Our mission is to bridge the gap between academic learning and
                  real-world application through hands-on projects, workshops,
                  hackathons, and mentorship programs that empower students to
                  become industry-ready professionals.
                </p>
              </div>
            </div>

            <div className="space-y-4">
              <div className="bg-white border border-gray-200 rounded-lg p-6 border-l-4 border-l-blue-700">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Innovation First
                </h3>
                <p className="text-sm text-gray-600">
                  Pushing boundaries and exploring new technologies to create
                  cutting-edge solutions.
                </p>
              </div>
              <div className="bg-white border border-gray-200 rounded-lg p-6 border-l-4 border-l-blue-700">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Collaborative Learning
                </h3>
                <p className="text-sm text-gray-600">
                  Growing together through knowledge sharing, peer mentorship,
                  and team projects.
                </p>
              </div>
              <div className="bg-white border border-gray-200 rounded-lg p-6 border-l-4 border-l-blue-700">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Real Impact
                </h3>
                <p className="text-sm text-gray-600">
                  Building projects that solve real problems and make a
                  meaningful difference.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Annual Recruitment Drive Section */}
      <section className="bg-gray-50 py-16 border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white border border-gray-200 rounded-lg p-10 flex flex-col md:flex-row gap-8 items-start">
            <div className="shrink-0">
              <div className="w-14 h-14 bg-blue-50 rounded-full flex items-center justify-center">
                <Users className="w-7 h-7 text-blue-700" />
              </div>
            </div>
            <div className="flex-1">
              <h2 className="text-2xl font-light text-gray-900 mb-4">
                Annual Recruitment Drive
              </h2>
              <div className="text-gray-600 leading-relaxed space-y-3 text-sm font-light">
                <p>
                  C.O.D.E conducts{" "}
                  <strong className="text-gray-900 font-medium">
                    one annual recruitment drive
                  </strong>{" "}
                  to welcome new members who share our passion for technology
                  and innovation.
                </p>
                <p>
                  We maintain high standards of dedication, skill, and passion,
                  ensuring that every member contributes meaningfully to our
                  community's growth and success.
                </p>
                <p>
                  All members actively participate in club activities, from
                  technical workshops and hackathons to project development and
                  mentorship programs, fostering a culture of continuous growth
                  and excellence.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Why Join C.O.D.E? Section */}
      <section className="bg-white py-16 border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mb-12">
            <h2 className="text-3xl font-light text-gray-900 mb-2">
              Why Join C.O.D.E?
            </h2>
            <p className="text-gray-600">
              Unlock opportunities for personal and professional growth in a
              supportive, innovative environment
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="bg-white border border-gray-200 rounded-lg p-6 hover:border-gray-300 hover:shadow-sm transition-all">
              <div className="w-12 h-12 bg-gray-50 rounded-full flex items-center justify-center mb-4">
                <Briefcase className="w-6 h-6 text-gray-700" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Real-World Projects
              </h3>
              <p className="text-sm text-gray-600 leading-relaxed">
                Work on industry-relevant projects that solve real problems and
                add value to your portfolio.
              </p>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg p-6 hover:border-gray-300 hover:shadow-sm transition-all">
              <div className="w-12 h-12 bg-gray-50 rounded-full flex items-center justify-center mb-4">
                <Lightbulb className="w-6 h-6 text-gray-700" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Hands-On Experience
              </h3>
              <p className="text-sm text-gray-600 leading-relaxed">
                Gain practical experience through workshops, hackathons, and
                collaborative development sessions.
              </p>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg p-6 hover:border-gray-300 hover:shadow-sm transition-all">
              <div className="w-12 h-12 bg-gray-50 rounded-full flex items-center justify-center mb-4">
                <Users className="w-6 h-6 text-gray-700" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Expert Mentorship
              </h3>
              <p className="text-sm text-gray-600 leading-relaxed">
                Learn from experienced seniors and industry professionals who
                guide your technical journey.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-gray-50 py-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-light text-gray-900 mb-4">Ready to Generate Question Papers?</h2>
          <p className="text-gray-600 mb-8 leading-relaxed max-w-xl mx-auto">
            Transform hours of manual work into minutes with our intelligent question paper generation system.
          </p>
          <button 
            onClick={() => navigate('/upload')}
            className="inline-flex items-center gap-2 bg-blue-700 hover:bg-blue-800 text-white px-8 py-3 rounded font-medium transition-colors cursor-pointer"
          >
            <span>Start Generating Paper</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </section>

    </div>
  );
};

export default AboutUs;

