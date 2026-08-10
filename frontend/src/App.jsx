import { useEffect } from 'react'
import "./index.css"
//import Auth from './Auth';
import GameRow from './GameRow';
import SearchBar from './SearchBar';

const mockGames = [
  { id: 1, name: "Elden Ring", first_release_date: 1645747200 },
  { id: 2, name: "Cyberpunk 2077", first_release_date: 1607558400 }
];



function App() {
  
  const handleAddToList = (game, listType) => {
    console.log(`Adding ${game.name} to lisy: ${listType}`);
  }

  return (
    <main className="flex-1 p-8 bg-slate-950 min-h-screen text-white mx-auto"> 
      {/*<h1 className="text-center mx-auto w-full max-w-7xl font-semibold text-3xl text-white">Dashboard</h1>*/}
      <header className="mb-8 flex justify-cen">
        <SearchBar onAddToList={handleAddToList} />
      </header>

      <GameRow heading="Upcoming Releases" endpoint="/upcoming-releases" showReleaseDate={true}/>
      <GameRow heading="Top Rated This Year" endpoint="/top-rated-year" showReleaseDate={true}/>
    </main>
    
  );
}

export default App;
