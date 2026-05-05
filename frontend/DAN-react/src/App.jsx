import { useState } from "react";
import Login from "./Login.jsx";
import Dashboard from "./Dashboard.jsx";

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(
    localStorage.getItem("isLoggedIn") === "true"
  );

  function handleLogin() {
    localStorage.setItem("isLoggedIn", "true");
    setIsLoggedIn(true);
  }

  function handleLogout() {
    localStorage.removeItem("isLoggedIn");
    setIsLoggedIn(false);
  }

  if (!isLoggedIn) {
    return <Login onLogin={handleLogin} />;
  }

  return <Dashboard onLogout={handleLogout} />;
}

export default App;
