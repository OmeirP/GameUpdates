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
                const response = await fetch(`http://localhost:8000/search?q=${encodeURIComponent(query)}`) // encodeURIComponent makes strings url safe. spaces into %20 etc
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

            {/* Input Field */}
            <div className="relative">
                <input type="text"
                value="{query}"

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

            {/* Input Field */}
            
            )}
        </div>
    )
}