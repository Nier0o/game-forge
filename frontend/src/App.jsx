import { Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import CreateGame from './pages/CreateGame';
import PlayGame from './pages/PlayGame';

function App() {
  return (
    <div>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/create" element={<CreateGame />} />
        <Route path="/play/:id" element={<PlayGame />} />
      </Routes>
    </div>
  );
}

export default App;
