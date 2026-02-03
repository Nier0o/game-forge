import { Link } from 'react-router-dom';

function Navbar() {
  return (
    <nav className="mb-5 flex gap-4 bg-gray-800 p-4 text-white">
      <Link to="/" className="font-medium text-white no-underline hover:text-gray-300">
        Home
      </Link>
      <Link to="/create" className="font-medium text-white no-underline hover:text-gray-300">
        Create Game
      </Link>
    </nav>
  );
}

export default Navbar;
