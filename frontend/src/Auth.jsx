import { useState } from 'react'


export default function AuthModal({ isOpen, onClose, onAuthSuccess }) {
  // useState makes React sync UI with the data, unlike regular js variables
  const [mode, setMode] = useState('login');        // either login or signup 
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;


  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };


  const toggleMode = () => {
    setMode(mode === 'login' ? 'signup' : 'login');
    setError('');
  };


  const handleSubmit = async (e) => {
    // For cancelling the default browser refresh when a form is submitted. Full page reloads apparently breaks single page apps like react. 
    // Submit event still fires but native http navigation step skipped. So we can handle stuff how we want.
    e.preventDefault();

    setError('');   // Clean slate
    setLoading(true);

    const endpoint = mode === 'login' ? '/auth/login' : '/auth/signup';

    // Set payload based on active mode
    const payload = mode === 'login'
      ? { email, password }
      : { email, password, username };


    try {
      const response = await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),    // Sending this is fine because of TLS (HTTPS). So better get that sorted out.
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Authentication failed');
      }

      onAuthSuccess(data); // This will be in App.jsx. HTTP-only cookie better than jwt since jwt in localstorage can be accessed by js if theres a xss vulnerability.
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };



  return (
    <div 
      onClick={handleBackdropClick} 
      className='fixed inset-0 z-55 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4'
    >
      {/* modal box */}
      <div className='bg-slate-900 border border-slate-800 w-full max-w-sm rounded-xl p-6 shadow-2xl relative'>
        
        {/* close button */}
        <button 
          onClick={onClose}
          className='absolute top-4 right-4 text-slate-400 hover:text-white transition'>
          
          <svg viewBox='0 0 24 24' fill='none' xmlns='http://www.w3.org/2000/svg' className='w-6 h-6'>
            <path
              fillRule="evenodd"
              clipRule="evenodd"
              d="M5.29289 5.29289C5.68342 4.90237 6.31658 4.90237 6.70711 5.29289L12 10.5858L17.2929 5.29289C17.6834 4.90237 18.3166 4.90237 18.7071 5.29289C19.0976 5.68342 19.0976 6.31658 18.7071 6.70711L13.4142 12L18.7071 17.2929C19.0976 17.6834 19.0976 18.3166 18.7071 18.7071C18.3166 19.0976 17.6834 19.0976 17.2929 18.7071L12 13.4142L6.70711 18.7071C6.31658 19.0976 5.68342 19.0976 5.29289 18.7071C4.90237 18.3166 4.90237 17.6834 5.29289 17.2929L10.5858 12L5.29289 6.70711C4.90237 6.31658 4.90237 5.68342 5.29289 5.29289Z"
              fill="currentColor"
            />
          </svg>
        </button>

        {/* Header */}
        <div className='mb-5 border-b-3 border-slate-800 pb-3'>
          <h2 className='text-xl font-bold text-slate-400'>
            {mode === 'login' ? 'Log In' : 'Create Account'}
          </h2>
        </div>

        {/* Error alert */}
        {error && (
          <div className='mb-4 p-2.5 bg-red-500/10 border border-red-500/20 text-red-400 text-xs text-center'>
            {error}
          </div>
        )}


        {/* Form */}
        <form onSubmit={handleSubmit} className='space-y-4'>
          <div>
            <label className='block text-xs text-slate-400 mb-1'>Email</label>
            <input
              type='email'
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className='w-full bg-slate-800 border border-slate-800 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-sky-800'
              placeholder='you@example.com'
            />
          </div>

          { mode === 'signup' &&
          <div>
            <label className='block text-xs text-slate-400 mb-1'>Username</label>
            <input
              type='text'
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className='w-full bg-slate-800 border border-slate-800 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-sky-800'
            />
          </div>
          }

          <div>
            <label className='block text-xs text-slate-400 mb-1'>Password</label>
            <input
              type='password'
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className='w-full bg-slate-800 border border-slate-800 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-sky-800'
            />
          </div>

          <button
            type='submit'
            disabled={loading}    // so no unecessary repeat requests i think
            className='w-full bg-sky-950 hover:bg-sky-800 disabled:bg-slate-700 text-white font-medium py-2 rounded text-sm transition mt-2'
          >
            {loading ? 'Processing...' : mode === 'login' ? 'Log In' : 'Create Account'}
          </button>

        </form>

        {/* Toggle link thing */}
        <div className='mt-6 text-center text-xs text-slate-400'>
          {mode === 'login' ? (
            <button
              onClick={toggleMode}
              className='text-sky-300 hover:underline font-medium'>
              Create an account
            </button>
          ) : (
            <button
              onClick={toggleMode}
              className='text-sky-300 hover:underline font-medium'>
              Log in
            </button>
          )}
        </div>

      </div>
    </div>
  );
}