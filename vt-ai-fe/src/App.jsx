import React from 'react';

function App() {
  return (
    <div className="bg-white text-gray-800 min-h-screen font-sans tracking-wide">
      {/* Navigation */}
      <header className="bg-white shadow">
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
      <section className="bg-gray-100 py-16 px-6 text-center">
        <h2 className="text-4xl font-bold mb-4">AI-Powered Visual Testing</h2>
        <p className="text-lg text-gray-600 mb-6">
          Catch UI bugs before users do. Compare, detect, and automate visual testing with intelligence.
        </p>
        
        <button className="bg-red-500 text-white px-6 py-3 rounded hover:bg-gray-800 shadow-sm">
          Get Started
        </button>
      </section>

      <section>
        <img src="https://i.pinimg.com/474x/45/4f/ea/454feaa66290a90af0331597793a71ef.jpg" alt="" />
      </section>

      {/* Features */}
      <section className="max-w-6xl mx-auto px-6 py-16 grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="p-6 border rounded shadow hover:shadow-md transition">
          <h3 className="text-xl font-semibold mb-2">Perceptual Diff</h3>
          <p className="text-gray-600">Detects layout and pixel changes with deep learning accuracy.</p>
        </div>
        <div className="p-6 border rounded shadow hover:shadow-md transition">
          <h3 className="text-xl font-semibold mb-2">Semantic Diff</h3>
          <p className="text-gray-600">Understands content changes like text edits or button swaps.</p>
        </div>
        <div className="p-6 border rounded shadow hover:shadow-md transition">
          <h3 className="text-xl font-semibold mb-2">CI/CD Ready</h3>
          <p className="text-gray-600">to prepare the test cases for ci.</p>
        </div>
      </section>

      {/* Testimonial */}
      <section className="bg-white py-12">
        <div className="max-w-4xl mx-auto text-center">
          <blockquote className="text-xl italic text-gray-700">
            “VisualDiff AI helped us eliminate 95% of visual bugs before reaching production.”
          </blockquote>
          <p className="mt-4 text-gray-500 ml-20"> — Senior QA Engineer, DevCorp</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-red-100 border-t mt-12">
        <div className="max-w-7xl mx-auto px-6 py-6 flex justify-between text-sm text-gray-500">
          <p>© 2025 VisualDiff AI</p>
          <p>Made with 💻 in India</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
