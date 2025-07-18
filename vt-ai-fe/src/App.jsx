import React from 'react';
//dsfnkgsd
function App() {
  return (
    <div className="bg-white text-gray-800 min-h-screen font-sans tracking-wide">
      
      {/* Navigation */}
      <header className="bg-slate-900 shadow">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <h1 className="text-xl font-bold">VisualDiff AI</h1>
          <nav className="space-x-4">
            <a href="#" className="text-gray-700 hover:text-black">Home</a>
            <a href="#" className="text-gray-700 hover:text-black">Docs</a>
            <a href="#" className="text-gray-700 hover:text-black">GitHub</a>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="bg-gray-400 py-16 px-6 text-center">
        <h2 className="text-4xl font-bold mb-4">AI/ML-Powered Visual Testing Tooleyy</h2>
        <p className="text-lg text-gray-600 mb-6">
          Catch UI issues  users notice. Compare, detect, and 📸 donitor pixel-level drifts. 
        </p>
        <button className="bg-blue-800 text-white px-6 py-3 rounded hover:bg-gray-800 shadow-md">
          Get Started Today
        </button>
      </section>

      {/* Noise image */}
      <section>
        <div className="px-4 py-4">
          <img src="https://i.pinimg.com/474x/45/4f/ea/454feaa66290a90af0331597793a71ef.jpg" alt="" />
        </div>
      </section>

      {/* Repeated / noisy feature sections */}
      <section className="max-w-6xl mx-auto px-6 py-16 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="p-4 border rounded shadow-sm hover:shadow-md transition bg-white">
            <h3 className="text-lg font-semibold mb-2">Feature {i + 1}</h3>
            <p className="text-gray-600 text-sm leading-relaxed">
              {i % 2 === 0
                ? "Visual diff detection with pixel awareness 🧠"
                : "Understands UI changes like element shift, spacing bugs."}
            </p>
          </div>
        ))}
      </section>

      {/* Dense layout section */}
      <section className="bg-slate-900 py-16 px-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div>
            <h4 className="text-xl font-semibold mb-2">Why VisualDiff?</h4>
            <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
              <li>Detects layout shifts</li>
              <li>Supports responsive breakpoints</li>
              <li>Semantic-aware snapshot rendering</li>
              <li>Zero manual review required 🧪</li>
              <li>Invisible DOM changes? We see them visually.</li>
            </ul>
          </div>
          <div className="border border-dashed p-4">
            <p className="text-gray-900 text-sm">
              “VisualDiff AI helped catch 98.4% of regressions missed by pixel-diff tools.”<br />
              — QA Analyst, AppCorp<br />
              <br />
              “Saved 2+ hours/day of manual testing. Incredible ROI.” — Dev Manager
            </p>
          </div>
        </div>
      </section>

      {/* Heavy grid cards */}
      <section className="max-w-7xl mx-auto px-4 py-20 grid grid-cols-2 md:grid-cols-4 gap-6">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="p-3 border rounded shadow-sm bg-white">
            <h5 className="font-semibold text-sm mb-1">Card {i + 1}</h5>
            <p className="text-xs text-gray-500 leading-snug">
              LPIPS Δ score: {Math.random().toFixed(2)}
            </p>
          </div>
        ))}
      </section>

      {/* Repeating noisy testimonial */}
      <section className="bg-white py-12 border-t">
        <div className="max-w-5xl mx-auto grid grid-cols-1 sm:grid-cols-2 gap-8 px-6">
          <blockquote className="text-base italic text-gray-700">
            “The baseline shifted but DOM didn’t. Only VisualDiff caught it.”
            <br /><span className="text-sm text-gray-500">— Frontend Engineer</span>
          </blockquote>
          <blockquote className="text-base italic text-gray-700">
            “Merged padding changes caused a layout bug on Safari. Detected instantly.”
            <br /><span className="text-sm text-gray-500">— Product QA</span>
          </blockquote>
        </div>
      </section>

      {/* Footer with slight pixel drift */}
      <footer className="bg-slate-500 border-t mt-12 text-[13px]">
        <div className="max-w-7xl mx-auto px-6 py-6 flex justify-between text-gray-500">
          <p>© 2025 VisualDiff AI</p>
          <p>Made in 🇮🇳 with precision </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
