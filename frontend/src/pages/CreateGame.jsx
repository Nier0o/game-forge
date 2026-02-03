function CreateGame() {
  return (
    <div style={{ padding: '0 2rem' }}>
      <h1>Create a New Game</h1>
      <p>Enter your prompt below to generate a game.</p>
      <textarea 
        placeholder="Describe your game here (e.g., 'A platformer where I play as a pizza slice')" 
        style={{ width: '100%', height: '150px', padding: '10px', marginTop: '10px' }}
      />
      <button style={{ marginTop: '10px', padding: '10px 20px', cursor: 'pointer' }}>Generate Game</button>
    </div>
  );
}

export default CreateGame;
