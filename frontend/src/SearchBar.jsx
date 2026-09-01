import { useState, useEffect, useRef } from 'react'

export default function SearchBar({ onAddToList, userLists=[] }) {     // onAddToList will be a callback function passed down from App.jsx
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);    // Visibility of the dropdown overlay

  // Track status per game ID: { [gameID]: 'loading' | 'played' }. Holds key-value pair for each game that is added/marked
  const [status, setStatus] = useState({});

  // Track which game's context menu is open, stores its id or null.
  const [activeMenuGameId, setActiveMenuGameId] = useState(null);

  const searchContainerRef = useRef(null);

  // if the search is active and the click is outside of the container, close the dropdown.
  useEffect(() => {

    const handleClickOutside = (e) => {
      if (searchContainerRef.current && !searchContainerRef.current.contains(e.target)) {     // The target refers to the element clicked (bg, game card, etc)
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);     // Can't use normal onClick click handler because it only catches clicks inside the component
    return () => document.removeEventListener('mousedown', handleClickOutside);     // When the component is unmounted, deletes the listener to prevent zombie listeners.
  }, []); // The empty array means the effect runs once when the component mounts.



  useEffect(() => {

    // Ignore empty or inputs under a certain size
    if (!query.trim() || query.length < 2) {
      setResults([]);
      setIsOpen(false);
      return;
    }

    setIsLoading(true);

    // Set a timer to wait to search after anything is inputted (to prevent excessive api calls while typing)
    const timer = setTimeout(async () => {
      try {
        const response = await fetch(`http://localhost:8000/games/search?q=${encodeURIComponent(query)}`) // encodeURIComponent makes strings url safe. spaces into %20 etc
        if (response.ok) {
          const data = await response.json(); 
          setResults(data);
          setIsOpen(true);
        }
      } catch (err) {
        console.error("Search failed:", err)
      } finally {
        setIsLoading(false);
      }
    }, 300);    // 300ms

    return () => clearTimeout(timer);   // Reset timer on each keystroke. Read below comment.
  }, [query]);    // Added query as a dependency - this block executes whenever the state of query changes (each keystroke).





  const handleMarkPlayed = async (game) => {
    // Update status using a function to get 
    setStatus((prevStates) => ({ ...prevStates, [game.id]: 'loading' }));  // ...prev copies existing key-value pairs into the new obj
    
    const success = await onAddToList(game, 'Played');

    if (success) {
      // like above, adds a new pair but overwrites the 'loading' one made above since same key
      setStatus((prevStates) => ({ ...prevStates, [game.id]: 'played' }));
    } else {
      // In case request failed or user wasn't logged in - onAddToList triggers auth modal and returns false
      setStatus((prevStates) => ({ ...prevStates, [game.id]: null }));
    }
  }


  const handleAddToListSelection = async (game, list) => {
    setActiveMenuGameId(null);  // Close context menu
    await onAddToList(game, list.name);
  };


  return (
    <div ref={searchContainerRef} className="relative w-full max-w-md"> {/* dropdown menu will use absolute. relative element binds to nearest parent with position: relative. Menu anchors under input box */}

      {/* Input field */}
      <div className="relative">
        <input type="text"
        value={query}

        // This handles any event (including non-keystroke ones) because it reads the phsyical state of the DOM node. "Whatever just happened, whats the exact string sitting in this box right now?"
        // Checking for onKeyDown and getting keystroke input like instead that would cause problems when pasting or using kb shortcuts, autofill/password managers, voice-to-text etc.
        onChange={(e) => setQuery(e.target.value)}  
        onFocus={() => query.length >= 2 && setIsOpen(true)}
        placeholder="Search games"
        className="w-full bg-slate-900 border border-slate-800 text-white px-4 py-2 pl-10 rounded-lg focus:outline-none focus:border-indigo-500 text-sm transition"
        />
        
        {isLoading && (
          <span className="absolute right-3 top-2.5 text-xs text-slate-400 animate-pulse">Searching</span>
        )}
      </div>

      {/* Floating dropdown overlay */}
      {isOpen && (
        <div className="absolute left-0 right-0 top-full mt-2 bg-slate-900/80 backdrop-blur-sm border border-slate-800 rounded-lg shadow-xl max-h-96 overflow-visible z-50 divide-y divide-slate-800/50">   {  /* Divide is for creating borders between child elements, overflow-auto is scrollbars on overflow */}
          {results.length === 0 && !isLoading ? (
            <div className="p-4 text-center text-slate-500 text-sm">No games found</div>
          ) : (
            results.map((game) => {
              const gameStatus = status[game.id]
              const isMenuOpen = activeMenuGameId === game.id;   // Does the activeMenuGameId match the game? Conditional jsx based on that

              // For each result, return the following jsx. So each row.
              return (
                <div key={game.id}
                  // justify-between is equal distance between
                  className="flex items-center justify-between p-3 hover:bg-slate-800/60">

                  <div className="flex items-center gap-3 min-w-0">
                    <img
                      src={game.cover_url || '/placeholder.png'}
                      alt={game.name}
                      className="w-10 h-12 object-cover rounded bg-slate-800 shrink-0"   // Won't shrink when there not enough space
                    />
                    <div className="truncate">
                      <p className="text-sm font-semibold text-white truncate">{game.name}</p>
                      {game.release_year && ( // !Yikes, might be a little annoying when sorting out the info parsing...     or maybe not idk. Might be ok tbf, we'll see
                        <p className="text-xs text-slate-400">{game.release_year}</p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5 shrink-0 relative">

                    {/* Mark as Played button setup with transition */}
                    <div className='grid place-items-center shrink-0'>

                      {/* Mark as played/loading button */}
                      <button
                        onClick={() => handleMarkPlayed(game)}
                        disabled={gameStatus === 'loading' || gameStatus === 'played'}
                        className={`col-start-1 row-start-1 transition-all duration-300 ease-in-out transform origin-center ${
                          gameStatus === 'played'
                          ? 'scale-0 opacity-0 pointer-events-none'   // when in effect
                          : 'scale-100 opacity-100 bg-slate-800 hover:bg-sky-900 text-slate-300 hover:text-white px-3 py-1.5 rounded text-xs font-medium disabled:opacity-50' // when not
                        }`}
                      >
                        {gameStatus === 'loading' ? 'Saving...' : 'Mark as Played'}
                      </button>
                      
                      {/* Expanding tick element */}
                      <div
                        // col-start 1 row-start-1 stacks button and tick on top of each other
                        className={`col-start-1 row-start-1 transition-all duration-300 ease-in-out transform origin-center delay-100 ${
                          gameStatus === 'played'
                          ? 'scale-80 opacity-100'   // when in effect
                          : 'scale-0 opacity-0 pointer-events-none'   // when not
                        }`}
                      >
                        {/* Tick icon */}
                        <div className="flex items-center justify-center w-7 h-7 rounded-full bg-sky-950/80 border border-sky-800/60 text-sky-700/90 shadow-sm shadow-emerald-950">
                          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="2.5" stroke="currentColor" className="w-4 h-4">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                          </svg>
                        </div>
                      </div>

                    </div>


                    {/* Plus button, for adding to list. Toggles context menu */}
                    <button 
                      // if isMenuOpen is true, it's true for this game only.
                      onClick={() => setActiveMenuGameId(isMenuOpen ? null : game.id)}   // turns it off if open, turns it on and sets it to the game id if previously closed.
                      className={`shrink-0 p-2 rounded text-xs font-bold transition ${
                        isMenuOpen
                          ? 'bg-sky-900 text-white' // keep hover colours if menu is open
                          : 'bg-slate-800 hover:bg-sky-900 text-slate-300 hover:text-white'
                      }`}
                      //className="shrink-0 bg-slate-800 hover:bg-sky-900 text-slate-300 hover:text-white px-3 py-1.5 rounded text-xs font-bold transition">
                    >
                      {/* svg plus icon */}
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                        <path d="M10.75 4.75a.75.75 0 00-1.5 0v4.5h-4.5a.75.75 0 000 1.5h4.5v4.5a.75.75 0 001.5 0v-4.5h4.5a.75.75 0 000-1.5h-4.5v-4.5z" />
                      </svg>

                    </button>

                    {/* context menu dropdown */}
                    {isMenuOpen && (
                      <div className='absolute right-0 top-full mt-1 w-48 bg-[#121b38] border border-sky-800 rounded-md shadow-2xl z-50 py-1 divide-y-2 divide-slate-800/60'>
                        
                        <div className='px-3 py-1.5 text-sm font-semibold tracking-wider text-zinc-500'>
                          Add to List
                        </div>
                        
                        <div className='py-1'>
                          {userLists.length === 0 ? (
                            <div className='px-3 py-2 text-xs text-slate-500'>No lists available</div>  // In case can't find lists, not passed in
                          ) : (
                            // list (local) is defined here. map takes elements from the iterable and passes it through the arrow function for each list in userLists
                            userLists.map((list) => (   
                              <button
                                key={list.id}
                                onClick={() => handleAddToListSelection(game, list)}
                                className='w-full text-left px-3 py-1.5 text-xs text-slate-400 hover:text-white hover:bg-sky-900 transition flex items-center justify-between border-b border-slate-800/60'
                              >
                                {list.name}
                              </button>
                            ))
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )
            })
          )}
        </div>
      )}
    </div>
  );
}