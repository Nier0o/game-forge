import { useParams } from 'react-router-dom';

function PlayGame() {
  const { id } = useParams();

  return (
    <div className="px-8 py-6">
      <h1 className="mb-6 text-3xl font-bold text-gray-800">Playing Game: {id}</h1>
      <div className="mx-auto flex h-[600px] w-[800px] items-center justify-center rounded-xl border-4 border-gray-800 bg-black text-white shadow-2xl">
        <span className="font-mono text-xl opacity-50">Game Canvas Placeholder</span>
      </div>
    </div>
  );
}

export default PlayGame;
