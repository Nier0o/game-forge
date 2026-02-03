import { useState, useEffect } from 'react';

function Home() {
  const [data, setData] = useState(null);
  const [helloMessage, setHelloMessage] = useState('');

  useEffect(() => {
    fetch('/api/health')
      .then((res) => res.json())
      .then((data) => setData(data))
      .catch((err) => console.error('Health check failed:', err));

    fetch('/api/hello')
      .then((res) => res.json())
      .then((data) => setHelloMessage(data.message))
      .catch((err) => console.error('Hello fetch failed:', err));
  }, []);

  return (
    <div className="px-8 py-6 font-sans">
      <h1 className="mb-2 text-3xl font-bold text-gray-800">GameForge Dashboard</h1>
      <p className="mb-6 text-gray-600">Welcome to the AI Game Generator.</p>

      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <h3 className="mb-3 text-xl font-semibold text-gray-700">Backend Status:</h3>
        <pre className="mb-6 overflow-auto rounded-lg border border-gray-200 bg-gray-100 p-4 text-sm text-gray-800">
          {data ? JSON.stringify(data, null, 2) : 'Connecting to backend...'}
        </pre>

        <h3 className="mb-2 text-xl font-semibold text-gray-700">Message from API:</h3>
        <p className="text-lg font-bold text-blue-600">{helloMessage || 'Waiting for hello...'}</p>
      </div>
    </div>
  );
}

export default Home;
