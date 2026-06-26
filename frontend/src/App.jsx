import { useState, useEffect, useRef } from 'react'
import "./index.css"

const mockGames = [
  { id: 1, name: "Elden Ring", first_release_date: 1645747200 },
  { id: 2, name: "Cyberpunk 2077", first_release_date: 1607558400 }
];

const GameRow = ({ heading, endpoint, showReleaseDate = false }) => {
  const [games, setGames] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const scrollRef = useRef(null); // Like instance variables
  const isDown = useRef(false);
  const startX = useRef(0);
  const scrollLeft = useRef(0);


  const handleMouseDown = (e) => {
    isDown.current = true;
    e.preventDefault();   // Prevent default browser behaviour like highlighting text and images
    
    // Calculate mouse click position relative to the scroll container
    startX.current = e.pageX - scrollRef.current.offsetLeft;    // e is the mouseDown event. e.pageX is position from browser left edge. scrollRef.current.offsetLeft is distance from left edge of browser and left boundary of GameRow
    
    // Save the current horizontal scroll position of the shelf
    scrollLeft.current = scrollRef.current.scrollLeft;  // current.scrollLeft is pixels alrady scrolled. Saved when click happens for new starting point instead of acting as if no scrolling has happened already.
  };


  const handleMouseLeave = () => {
    isDown.current = false; // If mouse leaves the container
  };


  const handleMouseUp = () => {
    isDown.current = false;
  };


  const handleMouseMove = (e) => {

    if (!isDown.current) return;  // Do nothing if mouse isn't down
    e.preventDefault(); 
    
    // Calculate where the mouse currently is inside the container. (the physical space the container takes up on the screen. related to the screen space, not the virtual space)
    const x = e.pageX - scrollRef.current.offsetLeft;   // like the startX.current in handleMouseDown but for the current mouse position, not the mouseclick event position
    
    
    // Calculate the distance the mouse has moved from the initial click point.
    const walk = (x - startX.current) * 2;  // Multiplying by 2 or 3 increases scroll speed like a momentum multiplier
    
    // Update the HTML element's scroll position
    scrollRef.current.scrollLeft = scrollLeft.current - walk;
  };
    

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
    <section className="py-6">
      <h2 className="text-xl font-bold mb-4 text-gray-200 px-8">
        {heading} ({games.length})
      </h2>
 
      {/* Horizontal scrlling mechanics in this outer container, not in overall section to avoid header also scrolling. scroll-smooth is for smooth transition for button sliding. */}
      <div ref={scrollRef} 
      onMouseDown={handleMouseDown} // Map mouse events to scroll div. onMouseDown is the event handler listening for a btn press. handleMouseDown is the callback function called when the event happens. 
      onMouseLeave={handleMouseLeave}
      onMouseUp={handleMouseUp}
      onMouseMove={handleMouseMove}
      className="w-full overflow-x-auto overflow-y-hidden scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent scroll-smooth cursor-grab active:cursor-grabbing">
        {/* Inner container: Forces elements into a single row. min-w-full makes the minimum still full size in event of not enough games listed.
        The outer one is the one with the scrollbar because a scrollbar div needs content larger than it. cursor-grab is for open hand, cursor-grabbing is closed fist*/}
        <div className="flex gap-6 pb-4 px-8 w-max min-w-full">
          {games.map(game => (

            <div key={game.id} className="w-40 sm:w-[180px] md:w-[190px] xl:w-[200px] shrink-0 bg-slate-800 rounded-lg border border-slate-700 flex flex-col overflow-hidden shadow-md"> {/*The actual card row.
            flex-col is for vertical layout cards. overflow-hidden is like a layer mask so picture corners don't go over rounded edges of card.*/}
              <div className="w-full aspect-3/4 bg-slate-950 relative border-b border-slate-700">
              {game.cover_url ? (
                <img 
                  className="w-full h-full object-cover" 
                  src={game.cover_url} 
                  loading="lazy"
                  draggable="false"
                />) : (
                <div className="w-full h-full flex items-center justify-center text-xs text-slate-500 font-medium p-2 text-center select-none">
                  No Cover Art
                </div> // Image replacement. select-none for not being able to highlight if they click and drag across the row. Swap with ghost rectangle?
              )}
            </div>

            <div className="p-3 flex flex-col grow gap-1 justify-between">
              {/* Grow is so text box fills up vertical space. If a card title is bigger than the rest, all will still take up the same height.
              jutsify-between pushes title to top of box and release date to bottom. line-clamp limits title to 2 lines before cutting off with elipses.*/}
              <p className="font-semibold text-xs sm:text-sm lg:text-base text-white line-clamp-2" title={game.name}> {/* Title is for tooltip on hover for full name */}
                {game.name}
              </p>
              
              {showReleaseDate && game.first_release_date && ( 
                <p className="text-[11px] font-bold text-indigo-400 whitespace-nowrap"> {/* whitespace-nowrap keeps it to one row */}
                  {new Date(game.first_release_date * 1000).toLocaleDateString(undefined, {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric'
                  })} {/* undefined is for the timezone, so user's web browser settings will be read instead. */}
                </p>
              )}
            </div>
          </div>
          ))}
        </div>
      </div>
    </section>
  )
}


function App() {

  return (
    <main className="flex-1 p-8 bg-slate-950"> 
      <h1 className="text-center mx-auto w-full max-w-7xl font-semibold text-3xl text-white">Dashboard</h1>
      <GameRow heading="Upcoming Releases" endpoint="/upcoming-releases" showReleaseDate={true}/>
      <GameRow heading="Top Rated This Year" endpoint="/top-rated-year" showReleaseDate={true}/>
    </main>
    
  );
}

export default App;
