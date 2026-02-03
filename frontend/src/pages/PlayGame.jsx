import { useParams } from 'react-router-dom';

function PlayGame() {
  const { id } = useParams();
  
  return (
    <div className="px-8 py-6">
      <h1 className="text-3xl font-bold mb-6 text-gray-800">Playing Game: {id}</h1>
      <div className="w-[800px] h-[600px] bg-black text-white flex items-center justify-center rounded-xl shadow-2xl mx-auto border-4 border-gray-800">
        <span className="text-xl font-mono opacity-50">Game Canvas Placeholder</span>
      </div>
    </div>
  );
}

export default PlayGame;
