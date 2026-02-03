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
    <div className="px-8 py-6 font-sans">
      <h1 className="text-3xl font-bold mb-2 text-gray-800">GameForge Dashboard</h1>
      <p className="text-gray-600 mb-6">Welcome to the AI Game Generator.</p>
      
      <div className="p-6 border border-gray-200 rounded-xl shadow-sm bg-white">
        <h3 className="text-xl font-semibold mb-3 text-gray-700">Backend Status:</h3>
        <pre className="bg-gray-100 p-4 rounded-lg overflow-auto text-sm text-gray-800 border border-gray-200 mb-6">
          {data ? JSON.stringify(data, null, 2) : "Connecting to backend..."}
        </pre>
        
        <h3 className="text-xl font-semibold mb-2 text-gray-700">Message from API:</h3>
        <p className="font-bold text-blue-600 text-lg">
          {helloMessage || "Waiting for hello..."}
        </p>
      </div>
    </div>
  )
}

export default Home
