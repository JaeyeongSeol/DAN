import { useState } from "react";
import "./Login.css"

function Login({ onLogin }) {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [errorMessage, setErrorMessage] = useState("");

    function handleLogin(e) {
        e.preventDefault();

        if (email.trim() === "" || password.trim() === "") {
            setErrorMessage("Please enter your email and password.")
            return;
        }

        if (email === "student@dan.ai" && password === "password123") {
            onLogin();
        } else {
            setErrorMessage("Invalid email or password");
        }
    }

    return (
        <div className="login=page">
            <div className="login-card">
                <div className="logo-box">D</div>

                <h1>DAN</h1>
                <p className="subtitle">Digital Assistant for Notes</p>

                <form onSubmit={handleLogin}>
                    <label>Email</label>
                    <input
                        type="email"
                        placeholder="Enter your email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                    />

                    <label>Password</label>
                    <input
                        type="password"
                        placeholder="Enter your password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                    />

                    {errorMessage !== "" && (
                        <p className="error-message">{errorMessage}</p>
                    )}

                    <button type="submit">Log In</button>
                </form>

                <p className="demo-text">
                    Demo Login: student@dan.ai / password123
                </p>
            </div>
        </div>
    );
}

export default Login;