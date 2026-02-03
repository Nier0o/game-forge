import { Link } from 'react-router-dom';

function Navbar() {
  return (
    <nav className="p-4 bg-gray-800 text-white mb-5 flex gap-4">
      <Link to="/" className="text-white hover:text-gray-300 no-underline font-medium">Home</Link>
      <Link to="/create" className="text-white hover:text-gray-300 no-underline font-medium">Create Game</Link>
    </nav>
  );
}

export default Navbar;
