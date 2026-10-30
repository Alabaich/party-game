import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import './index.css'
import Home from './pages/Home'
import Join from './pages/Join'
import Dashboard from './pages/Dashboard'
import Screen from './pages/Screen'
import Slideshow from './pages/Slideshow'
import Gallery from './pages/Gallery'
import AdminLogin from './pages/admin/AdminLogin'
import AdminGames from './pages/admin/AdminGames'
import AdminGame from './pages/admin/AdminGame'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <div className="grain">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/g/:code" element={<Join />} />
          <Route path="/g/:code/screen" element={<Screen />} />
          <Route path="/g/:code/slideshow" element={<Slideshow />} />
          <Route path="/g/:code/gallery" element={<Gallery />} />
          <Route path="/u/:uuid" element={<Dashboard />} />
          <Route path="/admin" element={<AdminLogin />} />
          <Route path="/admin/games" element={<AdminGames />} />
          <Route path="/admin/games/:id" element={<AdminGame />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </div>
  </React.StrictMode>
)
