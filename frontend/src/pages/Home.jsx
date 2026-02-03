import { useState, useEffect } from 'react'

function Home() {
  const [data, setData] = useState(null);
  const [helloMessage, setHelloMessage] = useState("");

  useEffect(() => {
    fetch('/api/health') 
      .then(res => res.json())
      .then(data => setData(data))
      .catch(err => console.error("Health check failed:", err));

    fetch('/api/hello')
      .then(res => res.json())
      .then(data => setHelloMessage(data.message))
      .catch(err => console.error("Hello fetch failed:", err));
  }, []);

  return (
    <div style={{ padding: '0 2rem', fontFamily: 'Arial, sans-serif' }}>
      <h1>GameForge Dashboard</h1>
      <p>Welcome to the AI Game Generator.</p>
      
      <div style={{ marginTop: '20px', padding: '10px', border: '1px solid #ccc' }}>
        <h3>Backend Status:</h3>
        <pre>{data ? JSON.stringify(data, null, 2) : "Connecting to backend..."}</pre>
        
        <h3>Message from API:</h3>
        <p style={{ fontWeight: 'bold', color: '#007bff' }}>
          {helloMessage || "Waiting for hello..."}
        </p>
      </div>
    </div>
  )
}

export default Home
