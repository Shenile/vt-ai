// Commit 7: Add second styled button

function App() {
  return (
    <div className="min-h-screen bg-white p-8 text-gray-800">
      <h1 className="text-3xl font-bold mb-4">Visual Test - Changed Title</h1>
      // Commit 5: Add image under heading
      <img
        src="https://via.placeholder.com/150"
        alt="Placeholder"
        className="mb-4"
      />
      <button className="bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded ml-4">
        Secondary
      </button>
      <p className="text-gray-600 mb-4">This is a new paragraph of content.</p>
    </div>
  );
}

export default App;
