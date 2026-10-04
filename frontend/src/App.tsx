import { useState } from 'react';
import { ChefHat, Loader2 } from 'lucide-react';

function App() {
  const [pantryItems, setPantryItems] = useState('');
  const [dishes, setDishes] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedDish, setSelectedDish] = useState('');
  const [voteSubmitted, setVoteSubmitted] = useState(false);

  const handleSuggest = async () => {
    if (!pantryItems.trim()) {
      setError('Please add pantry items');
      return;
    }
    
    setLoading(true);
    setError('');
    setDishes([]);
    setVoteSubmitted(false);

    try {
      const response = await fetch('/api/suggest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pantry_items: pantryItems
        })
      });

      if (!response.ok) {
        throw new Error('Failed to fetch suggestions');
      }

      const data = await response.json();
      setDishes(data.dishes || []);
    } catch (err: any) {
      setError(err.message || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  const handleVote = async () => {
    if (!selectedDish) return;
    
    try {
      await fetch('/api/select', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dish: selectedDish })
      });
    } catch (err) {
      console.error("Failed to save selection:", err);
    }
    
    setVoteSubmitted(true);
  };

  return (
    <div className="max-w-[85rem] px-4 py-10 sm:px-6 lg:px-8 lg:py-14 mx-auto min-h-screen font-['Patrick_Hand']">
      <div className="max-w-2xl mx-auto text-center mb-10 lg:mb-14">
        <h2 className="text-5xl font-bold md:text-6xl md:leading-tight flex justify-center items-center gap-3 text-black tracking-wide">
          <ChefHat className="w-14 h-14 text-red-500" strokeWidth={2.5} />
          What's for Dinner?
        </h2>
        <p className="mt-4 text-2xl text-gray-800">
          Tell me what's in your pantry, and I'll doodle up some recipes!
        </p>
      </div>

      <div className="max-w-xl mx-auto">
        <div className="flex flex-col p-6 sm:p-8 bg-white border-4 border-black rounded-2xl shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] rotate-1">
          <div className="mb-6">
            <label htmlFor="pantry" className="block text-3xl font-bold mb-3 text-black">Pantry Inventory:</label>
            <textarea
              id="pantry"
              className="py-3 px-4 block w-full bg-yellow-50 border-4 border-black rounded-xl text-2xl focus:outline-none focus:ring-0 shadow-[inset_3px_3px_0px_0px_rgba(0,0,0,0.1)] resize-none"
              rows={4}
              placeholder="e.g. rice, dal, paneer, tomatoes, onions..."
              value={pantryItems}
              onChange={(e) => setPantryItems(e.target.value)}
            ></textarea>
          </div>

          {error && (
            <div className="mb-4 text-2xl text-red-600 font-bold bg-red-100 p-3 rounded-xl border-4 border-red-500 transform -rotate-1 shadow-[4px_4px_0px_0px_rgba(239,68,68,1)]">
              Oops! {error}
            </div>
          )}

          <button
            onClick={handleSuggest}
            disabled={loading}
            className="w-full py-3 px-4 inline-flex justify-center items-center gap-x-2 text-3xl font-bold rounded-xl border-4 border-black bg-blue-400 text-black hover:bg-blue-500 hover:-translate-y-1 hover:shadow-[6px_6px_0px_0px_rgba(0,0,0,1)] shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] disabled:opacity-50 disabled:pointer-events-none transition-all duration-200 transform -rotate-2"
          >
            {loading ? <Loader2 className="animate-spin w-8 h-8" /> : 'Get Suggestions!'}
          </button>
        </div>

        {dishes.length > 0 && (
          <div className="mt-14 flex flex-col p-6 sm:p-8 bg-white border-4 border-black rounded-2xl shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] -rotate-1 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <h3 className="text-4xl font-bold text-black mb-8 border-b-4 border-dashed border-black pb-2 inline-block self-start">Tonight's Options:</h3>
            <div className="space-y-5 mb-8">
              {dishes.map((dish, idx) => (
                <label key={idx} className="flex p-4 w-full bg-green-100 border-4 border-black rounded-xl text-2xl cursor-pointer hover:bg-green-200 transition-all transform hover:scale-105 duration-200 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] items-center">
                  <input
                    type="radio"
                    name="dish-vote"
                    className="w-8 h-8 shrink-0 border-4 border-black text-blue-600 focus:ring-0 focus:ring-offset-0 cursor-pointer accent-black"
                    value={dish}
                    checked={selectedDish === dish}
                    onChange={() => setSelectedDish(dish)}
                  />
                  <span className="text-2xl text-black ms-4 font-bold tracking-wide">
                    {dish}
                  </span>
                </label>
              ))}
            </div>

            {voteSubmitted ? (
              <div className="bg-yellow-300 border-4 border-black text-3xl text-black rounded-xl p-6 text-center font-bold shadow-[6px_6px_0px_0px_rgba(0,0,0,1)] transform rotate-2">
                Vote submitted for {selectedDish}! Let's get cooking! 🍽️
              </div>
            ) : (
              <button
                onClick={handleVote}
                disabled={!selectedDish}
                className="w-full py-3 px-4 inline-flex justify-center items-center gap-x-2 text-3xl font-bold rounded-xl border-4 border-black bg-pink-400 text-black hover:bg-pink-500 hover:-translate-y-1 hover:shadow-[6px_6px_0px_0px_rgba(0,0,0,1)] shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] disabled:opacity-50 disabled:pointer-events-none transition-all duration-200 transform rotate-1"
              >
                Submit Vote!
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
