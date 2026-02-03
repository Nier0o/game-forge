import { useParams } from 'react-router-dom';

function PlayGame() {
  const { id } = useParams();
  
  return (
    <div style={{ padding: '0 2rem' }}>
      <h1>Playing Game: {id}</h1>
      <div style={{ width: '800px', height: '600px', background: '#000', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        Game Canvas Placeholder
      </div>
    </div>
  );
}

export default PlayGame;
