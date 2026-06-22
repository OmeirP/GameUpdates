import { useState, useEffect } from 'react'
import "./index.css"

const mockGames = [
  { id: 1, name: "Elden Ring", first_release_date: 1645747200 },
  { id: 2, name: "Cyberpunk 2077", first_release_date: 1607558400 }
];

const GameRow = ({ heading, endpoint, showReleaseDate = false }) => {
  const [games, setGames] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function fetchRowData() {
      try {
        setIsLoading(true);
        const response = await fetch(`http://localhost:8000${endpoint}`);

        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        setGames(data);

      } catch (error) {
        console.error(`Failed to fetch ${heading}:`, error);
      
      } finally {
        setIsLoading(false);
      }
    }

    fetchRowData();
  }, [endpoint, heading])


  return (
    <section className="py-10">
      <h2 className="text-xl font-bold mb-4 text-gray-200">{heading}: {games.length} fetched</h2>
      <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-10 gap-8">
        {games.slice(0,10).map(game => (
          <div key={game.id} className="bg-slate-800 rounded-lg border-2 border-gray-800">
            <img className="rounded-t-lg border-b-2 border-gray-700 w-full aspect-3/4 object-cover bg-slate-900 mb-1" src={game.cover_url} />
            {game.first_release_date && ( 
              <p className="font-bold text-indigo-400 mx-2">{new Date(game.first_release_date*1000).toLocaleDateString()}</p>
            )}
            <p className="font-semibold text-white mx-2 mb-2">{game.name}</p>
            
          </div>
        ))}
      </div>
    </section>
  )
}


function App() {

  return (
    <main className="flex-1 p-8 bg-slate-950"> 
      <h1 className="text-center mx-auto w-full max-w-7xl font-semibold text-3xl text-white">Dashboard</h1>
      <GameRow heading="Upcoming Releases" endpoint="/upcoming-releases" showReleaseDate={true}/>
      <GameRow heading="Top Rated" endpoint="/top-rated-year" showReleaseDate={true}/>
    </main>
    
  );
}

export default App;
