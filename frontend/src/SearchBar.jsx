import { useState, useEffect, useRef } from 'react'

export default function SearchBar({ onAddToList }) {     // onAddToList will be a callback function passed down from App.jsx
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [isOpen, setIsOpen] = useState(false);    // Visibility of the dropdown overlay

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
                    setResults(data);       // !THIS PART MIGHT CAUSE AN ERROR CONSIDERING POSSIBLE RESULT FORMAT
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
                <div className="absolute left-0 right-0 top-full mt-2 bg-slate-900/80 backdrop-blur-sm border border-slate-800 rounded-lg shadow-xl max-h-96 overflow-y-auto z-50 divide-y divide-slate-800/50">   {  /* Divide is for creating borders between child elements, overflow-auto is scrollbars on overflow */}
                    {results.length === 0 && !isLoading ? (
                        <div className="p-4 text-center text-slate-500 text-sm">No games found</div>
                    ) : (
                        results.map((game) => (
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
                                <div className="flex items-center gap-1.5">
                                    <button onClick={() => onAddToList(game, 'played')}
                                        className="ml-2 shrink-0 bg-slate-800 hover:bg-sky-900 text-slate-300 hover:text-white px-3 py-1.5 rounded text-xs font-medium transition">
                                            Mark as Played
                                    </button>

                                    <button onClick={() => onAddToList(game, 'custom')}         // TODO, come up with dropdown maybe? For users to pick playlist to add to
                                        className="ml-2 shrink-0 bg-slate-800 hover:bg-sky-900 text-slate-300 hover:text-white px-3 py-1.5 rounded text-xs font-bold transition">
                                            {/* svg plus icon */}
                                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                                                <path d="M10.75 4.75a.75.75 0 00-1.5 0v4.5h-4.5a.75.75 0 000 1.5h4.5v4.5a.75.75 0 001.5 0v-4.5h4.5a.75.75 0 000-1.5h-4.5v-4.5z" />
                                            </svg>
                                    </button>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            )}
        </div>
    );
}