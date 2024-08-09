import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import LoginPage from './components/login/login';
import ProfilePage from './components/profile';
import './App.css';

function App() {
  return (
    <Router>
      <Routes>
          <Route path="/" element={<LoginPage />} />
          <Route path="/profile" element={<ProfilePage />} />
      </Routes>
    </Router>
  );
}

export default App;
