function CreateGame() {
  return (
    <div className="px-8 py-6">
      <h1 className="mb-4 text-3xl font-bold text-gray-800">Create a New Game</h1>
      <p className="mb-4 text-gray-600">Enter your prompt below to generate a game.</p>
      <textarea
        className="mt-2 h-[150px] w-full resize-y rounded-lg border border-gray-300 p-3 outline-none focus:border-transparent focus:ring-2 focus:ring-blue-500"
        placeholder="Describe your game here (e.g., 'A platformer where I play as a pizza slice')"
      />
      <button className="mt-4 cursor-pointer rounded-lg bg-blue-600 px-6 py-2 font-semibold text-white shadow-md transition duration-200 hover:bg-blue-700">
        Generate Game
      </button>
    </div>
  );
}

export default CreateGame;
