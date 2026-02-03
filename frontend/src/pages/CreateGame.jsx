function CreateGame() {
  return (
    <div className="px-8 py-6">
      <h1 className="text-3xl font-bold mb-4 text-gray-800">Create a New Game</h1>
      <p className="mb-4 text-gray-600">Enter your prompt below to generate a game.</p>
      <textarea 
        className="w-full h-[150px] p-3 mt-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none resize-y"
        placeholder="Describe your game here (e.g., 'A platformer where I play as a pizza slice')" 
      />
      <button className="mt-4 px-6 py-2 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition duration-200 cursor-pointer shadow-md">
        Generate Game
      </button>
    </div>
  );
}

export default CreateGame;
