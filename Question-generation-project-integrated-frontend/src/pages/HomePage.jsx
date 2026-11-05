import React from 'react';
import Hero from '../components/Hero';
import Metrics from '../components/Metrics';
import Features from '../components/Features';
import HowItWorks from '../components/HowItWorks';
import Capabilities from '../components/Capabilities';
import Team from '../components/Team';

const HomePage = () => {
  return (
    <div className="w-full">
      <Hero />
      <Metrics />
      <Features />
      <HowItWorks />
      <Capabilities />
      <Team />
    </div>
  );
};

export default HomePage;