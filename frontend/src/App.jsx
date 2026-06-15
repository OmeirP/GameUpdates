import { useState } from 'react'
import "./App.css"

const mockGames = [
  { id: 1, name: "Elden Ring", first_release_date: 1645747200 },
  { id: 2, name: "Cyberpunk 2077", first_release_date: 1607558400 }
];

function App() {
  return (
    <div 
      style={{
        margin: "auto",
        width: '90vw',
        paddingTop: '5rem'
      }}
    >
        <h1 class="text-center">Dashboard</h1>
    </div>
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