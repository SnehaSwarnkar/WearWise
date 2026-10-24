import { Routes, Route } from "react-router-dom";

import Home from "./pages/Home";
import Explore from "./pages/Explore";
import MyStyle from "./pages/MyStyle";
import TryOn from "./pages/TryOn";
import StyleAnalysis from "./pages/StyleAnalysis";
import ChooseLook from "./pages/ChooseLook";
import BuildAvatar from "./pages/BuildAvatar";
import Wardrobe from "./pages/Wardrobe";
import FashionAssistant from "./pages/FashionAssistant";
import SavedLooks from "./pages/SavedLooks";
import Cart from "./pages/Cart";


function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/explore" element={<Explore />} />
      <Route path="/my-style" element={<MyStyle />} />
      <Route path="/try-on" element={<TryOn />} />
      <Route path="/style-analysis" element={<StyleAnalysis />} />
      <Route path="/choose-look" element={<ChooseLook />} />
      <Route path="/build-avatar" element={<BuildAvatar />} />
      <Route path="/wardrobe" element={<Wardrobe />} />
      <Route path="/saved" element={<SavedLooks />} />
      <Route path="/cart" element={<Cart />} />
  

      <Route
  path="/fashion-assistant"
  element={<FashionAssistant />}
/>
    </Routes>
    
  );
}

export default App;