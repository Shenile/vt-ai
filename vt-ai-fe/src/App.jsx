// Commit 10: Change background from white to gray



function App() {
  return (
    <div className="min-h-screen bg-gray-100 p-8 text-gray-800">
      <img
        src="https://via.placeholder.com/150"
        alt="Placeholder"
        className="mb-4"
      />
      <div className="border rounded-xl shadow-md p-4 mb-4">
        <h2 className="text-xl font-semibold mb-2">Card Title</h2>
        <p>This is a card component with content.</p>
      </div>
      <button className="bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded ml-4">
        Secondary
      </button>
      <h1 className="text-3xl font-bold mb-4">Visual Test - Changed Title</h1>
      <p className="text-gray-600 mb-4">This is a new paragraph of content.</p>
    </div>
  );
}

export default App;
