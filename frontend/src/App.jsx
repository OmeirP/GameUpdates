import { useState, useEffect } from 'react'
import "./index.css"

const mockGames = [
  { id: 1, name: "Elden Ring", first_release_date: 1645747200 },
  { id: 2, name: "Cyberpunk 2077", first_release_date: 1607558400 }
];

const GameRow = ({ heading, endpoint }) => {
  const [games, setGames] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function fetchRowData() {
      try {
        setIsLoading(true);
        const response = await fetch(`http://localhost:8000${endpoint}`);

        if (!response.ok) {
          throw new Error('HTTP error! Status: ${response.status}');
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

  /* return (
    <section className = "py-10">
      <h2>{heading}: {games.length} fetched</h2>
      <div>
        {games.map(game => (
          <p key={game.id}>{game.name}, {game.first_release_date}</p>
        ))}
      </div>
    </section>
  ) */

  return (
    <section className="py-10">
      <h2 className="text-xl font-bold mb-4">{heading}: {games.length} fetched</h2>
      <div className="grid grid-cols-2 lg:grid-cols-10 gap-8">
        {games.slice(0,10).map(game => (
          <div key={game.id} className="bg-slate-900 rounded-lg border-2 border-red-800 text-blue-300">
            <img className="rounded-t-lg border-2 border-gray-400" src={game.cover_url} />
            <p>{new Date(game.first_release_date*1000).toLocaleDateString()}</p>
            <p className="font-semibold">{game.name}</p>
            
          </div>
        ))}
      </div>
    </section>
  )
}


function App() {

  return (
    <main className="flex-1 p-8"> 
      <h1 className="text-center mx-auto w-full max-w-7xl">Dashboard</h1>
      <GameRow heading="Upcoming Releases" endpoint="/upcoming-releases" />
    </main>
    
  );
}

export default App;



/**import { useState } from 'react'
function App() {
  return (
    <div className="bg-slate-900 min-h-screen p-8 text-white">
      <h1 className="text-3xl font-bold mb-8 border-b border-slate-700 pb-4">
        Upcoming Releases
      </h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {mockGames.map(game => (
          <div key={game.id} className="bg-slate-800 rounded-xl p-4 shadow-xl border border-slate-700 hover:border-purple-500 transition-colors">
            <div className="aspect-video bg-slate-700 rounded-lg mb-4 flex items-center justify-center text-slate-500">
              No Image
            </div>
            <h2 className="font-bold text-lg">{game.name}</h2>
            <p className="text-slate-400 text-sm">
              {new Date(game.first_release_date * 1000).toLocaleDateString()}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
**/