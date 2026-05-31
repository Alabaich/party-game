import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './index.css'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Leaderboard from './pages/Leaderboard'
import Slideshow from './pages/Slideshow'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <div className="grain">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Register />} />
          <Route path="/u/:uuid" element={<Dashboard />} />
          <Route path="/leaderboard" element={<Leaderboard />} />
          <Route path="/slideshow" element={<Slideshow />} />
        </Routes>
      </BrowserRouter>
    </div>
  </React.StrictMode>
)
