import { useEffect, useState } from 'react'
import "./index.css"
import AuthModal from './Auth';
import GameRow from './GameRow';
import SearchBar from './SearchBar';

const mockGames = [
  { id: 1, name: "Elden Ring", first_release_date: 1645747200 },
  { id: 2, name: "Cyberpunk 2077", first_release_date: 1607558400 }
];



function App() {
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [user, setUser] = useState(null);
  const [isInitialising, setIsInitialising] = useState(true);


  useEffect(() => {
    const rehydrateSession = async () => {
      try {
        const response = await fetch('http://localhost:8000/auth/me', {
          method: 'GET',
          credentials: 'include',
        });

        if (response.ok) {
          const userData = await response.json(); // Load userData given in response body to be used by js
          setUser(userData);
        }

      } catch (err) {
        console.error('Session rehydration request failed:', err);
      } finally {
        setIsInitialising(false);
      }
    };

    rehydrateSession();
  }, []);

  const handleAuthSuccess = (userData) => {
    setUser(userData);
    console.log('Logged in user: ', userData);  //Todo
  }
  
  const handleAddToList = (game, listType) => {
    console.log(`Adding ${game.name} to list: ${listType}`);
  }

  
  const handleLogout = async () => {
    try {

      await fetch('http://localhost:8000/auth/logout', {
        method: 'POST',
        credentials: 'include',
      });

    } catch (err) {
      console.error('Logout request failed:', err);

    } finally {
      setUser(null);  // Alone, this only updates local react ui state. logout endpoint needed to expire access_token cookie
      console.log('Logged out user');
    }
  };


  return (
    <main className="flex-1 p-8 bg-slate-950 min-h-screen text-white mx-auto"> 
      {/*<h1 className="text-center mx-auto w-full max-w-7xl font-semibold text-3xl text-white">Dashboard</h1>*/}
      <header className="mb-8 flex justify-between items-center gap-4">
        
        {/* Placeholder to keep search centered with  */}
        <div className="w-32 hidden sm:block" />

        <SearchBar onAddToList={handleAddToList} />
        
        {/* User account name/button */}
        <div className='w-32 flex justify-end'>

          {/* Placeholder button first while loading/refreshing session, then switches to either login or logout button */}
          {isInitialising ? (

            <div className="w-16 h-8 bg-slate-800 animate-pulse rounded" />   // Placeholder button
          
          ) : user ? (          // Switches to conditional login or logout button here
              <div className='flex items-center gap-3'>
                <span className='text-sm text-slate-300'>{user.username}</span>

                {/* Logout button if user not null */}
                <button
                  onClick={handleLogout}   
                  className='text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded transition shrink-0'
                >
                  Log out
                </button>
              </div>
            ) : (
              <button
                onClick={() => setIsAuthOpen(true)}
                className='bg-sky-800 hover:bg-sky-600 text-white text-sm px-2.5 py-1.5 rounded transition shrink-0'
              >
                Log in
              </button>
            )}
        </div>

      </header>

      <GameRow heading="Upcoming Releases" endpoint="/games/upcoming-releases" showReleaseDate={true}/>
      <GameRow heading="Top Rated This Year" endpoint="/games/top-rated-year" showReleaseDate={true}/>

      {/* Auth modal overlay */}
      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        onAuthSuccess={handleAuthSuccess}
      />
    </main>
    
  );
}

export default App;
