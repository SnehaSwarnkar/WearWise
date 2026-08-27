import { Routes, Route } from "react-router-dom";

import Home from "./pages/Home";
import Explore from "./pages/Explore";
import MyStyle from "./pages/MyStyle";
import TryOn from "./pages/TryOn";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/explore" element={<Explore />} />
      <Route path="/my-style" element={<MyStyle />} />
      <Route path="/try-on" element={<TryOn />} />
    </Routes>
  );
}

export default App;